"""
Run MuSiQue baseline experiments — all agents use the SAME model (no routing).

Usage:
    python run_musique_baseline.py --tier 1 --num-problems 200
    python run_musique_baseline.py --tier 2 --num-problems 200
    python run_musique_baseline.py --tier 3 --num-problems 50 --rate-limit 2
    python run_musique_baseline.py --tier 4 --num-problems 200 --resume
"""

import sys
import os
import argparse
import json
import time
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tqdm import tqdm
from datasets import load_dataset

from src.models import get_model
from src.agents.musique_agents import create_musique_agents, run_musique_pipeline
from src.evaluation.metrics import (
    extract_hotpotqa_answer,
    hotpotqa_check_correct,
    hotpotqa_compute_f1,
    compute_experiment_stats,
)
from src.utils.logger import ExperimentLogger
from src.utils.config import RESULTS_DIR, RATE_LIMITS, MODEL_CONFIG


def _find_completed_problems(experiment_id: str) -> set[int]:
    """Find which problem IDs were already successfully completed (no [ERROR])."""
    csv_path = RESULTS_DIR / "baselines" / f"{experiment_id}.csv"
    if not csv_path.exists():
        return set()

    try:
        df = pd.read_csv(csv_path)
        # A problem is "done" if its verifier row exists and has no [ERROR]
        verifier = df[df.agent_role == "verifier"]
        done = set()
        for _, row in verifier.iterrows():
            resp = str(row.get("response_text", ""))
            if "[ERROR]" not in resp:
                done.add(int(row["problem_id"]))
        return done
    except Exception:
        return set()


def _remove_error_rows(experiment_id: str, problem_ids: set[int]):
    """Remove rows for specific problem IDs from the CSV (so they can be re-run cleanly)."""
    csv_path = RESULTS_DIR / "baselines" / f"{experiment_id}.csv"
    if not csv_path.exists():
        return
    try:
        df = pd.read_csv(csv_path)
        before = len(df)
        df = df[~df.problem_id.fillna(-1).astype(int).isin(problem_ids)]
        df.to_csv(csv_path, index=False)
        removed = before - len(df)
        if removed > 0:
            print(f"  🧹 Cleaned {removed} error rows from previous run.")
    except Exception as e:
        print(f"  ⚠️ Error cleaning CSV: {e}")


def run_musique_baseline(tier: int, num_problems: int, rate_limit_rpm: int | None = None, resume: bool = False):
    """Run MuSiQue baseline with all agents using the specified tier."""

    experiment_id = f"musique_baseline_tier{tier}"
    model_name = MODEL_CONFIG[tier]["name"]

    print(f"\n{'='*60}")
    print(f"  MuSiQue Baseline — Tier {tier} ({model_name})")
    print(f"  Problems: {num_problems}")
    if resume:
        print(f"  Mode: RESUME (skipping already-completed problems)")
    print(f"{'='*60}\n")

    # Load dataset
    print("Loading MuSiQue dataset (bdsaglam/musique 'answerable' validation split)...")
    dataset = load_dataset("bdsaglam/musique", "answerable", split="validation")
    problems = list(dataset)[:num_problems]
    print(f"Loaded {len(problems)} problems.\n")

    # Check for resume
    skip_ids: set[int] = set()
    if resume:
        skip_ids = _find_completed_problems(experiment_id)
        if skip_ids:
            # Find error problem IDs to clean up
            all_ids = set(range(num_problems))
            error_ids = all_ids - skip_ids
            _remove_error_rows(experiment_id, error_ids)
            remaining = num_problems - len(skip_ids)
            print(f"  ✅ Found {len(skip_ids)} completed problems from previous run.")
            print(f"  📋 {remaining} problems remaining to process.\n")
        else:
            print(f"  ℹ️  No previous results found — starting fresh.\n")

    # Create model and agents
    model = get_model(tier)
    agents = create_musique_agents(model)

    from src.models.base import BaseMultiKeyModel
    if isinstance(model, BaseMultiKeyModel):
        model.print_key_status(startup=True)

    # Set up logger (appends to existing CSV)
    logger = ExperimentLogger(experiment_id, RESULTS_DIR / "baselines")

    # Rate limiting
    if rate_limit_rpm is None:
        provider = MODEL_CONFIG[tier]["provider"]
        rate_limit_rpm = RATE_LIMITS.get(provider, 30)

    # Run pipeline on each problem
    all_results = []
    correct_count = 0
    total_f1 = 0.0
    processed_count = 0

    for i, item in enumerate(tqdm(problems, desc=f"Tier {tier}")):
        # Skip already-completed problems in resume mode
        if i in skip_ids:
            continue

        if processed_count > 0 and processed_count % 25 == 0:
            if isinstance(model, BaseMultiKeyModel):
                model.print_key_status(startup=False)

        question_text = item["question"]
        ground_truth = item["answer"]
        paragraphs_list = item["paragraphs"]

        try:
            # Run 3-agent pipeline
            result = run_musique_pipeline(agents, question_text, paragraphs_list)

            # Extract predicted answer (reusing HotpotQA extractor since it checks Final Answer: [text])
            predicted = extract_hotpotqa_answer(result["final_output"])
            correct = hotpotqa_check_correct(predicted, ground_truth)
            f1 = hotpotqa_compute_f1(predicted, ground_truth)

            if correct:
                correct_count += 1
            total_f1 += f1

            result["problem_id"] = i
            result["ground_truth"] = ground_truth
            result["predicted"] = predicted
            result["correct"] = correct
            result["f1"] = f1

            # Log each agent's call
            for agent_role, response in result["agent_responses"].items():
                logger.log_call(
                    problem_id=i,
                    dataset="musique",
                    agent_role=agent_role,
                    tier=tier,
                    model_name=model.model_name,
                    router_type="none",
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    latency_s=response.latency,
                    cost_usd=response.cost_usd,
                    correct=correct,
                    response_text=response.text,
                )

            all_results.append(result)
            processed_count += 1

            # Progress update every 10 problems
            total_done = len(skip_ids) + processed_count
            if total_done % 10 == 0 or processed_count % 10 == 0:
                if processed_count > 0:
                    session_acc = correct_count / processed_count * 100
                    session_f1 = total_f1 / processed_count * 100
                    print(f"  [{total_done}/{num_problems}] Session EM: {session_acc:.1f}% | Session F1: {session_f1:.1f}%")

        except RuntimeError as e:
            if "API keys exhausted" in str(e):
                print(f"\n❌ FATAL: {e}")
                print("Saving progress/results gathered so far and stopping benchmark...")
                break
            else:
                print(f"  ⚠️  Problem {i} failed: {e}")
                all_results.append({
                    "problem_id": i,
                    "correct": False,
                    "f1": 0.0,
                    "error": str(e),
                    "total_cost": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_latency": 0,
                })
                processed_count += 1
        except Exception as e:
            print(f"  ⚠️  Problem {i} failed: {e}")
            all_results.append({
                "problem_id": i,
                "correct": False,
                "f1": 0.0,
                "error": str(e),
                "total_cost": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_latency": 0,
            })
            processed_count += 1

    # Compute and print stats
    if resume and skip_ids:
        print(f"\n  Re-computing stats from full CSV (including resumed data)...")
        # Load the updated CSV file to compute accurate totals
        csv_path = RESULTS_DIR / "baselines" / f"{experiment_id}.csv"
        try:
            df = pd.read_csv(csv_path)
            verifier_df = df[df.agent_role == "verifier"]
            
            # Reconstruct results format for compute_experiment_stats
            reconstructed_results = []
            for _, row in verifier_df.iterrows():
                pid = int(row["problem_id"])
                corr = bool(row["correct"]) if not pd.isna(row["correct"]) else False
                
                # Fetch matching answers from validation dataset to compute F1
                actual_item = validation_problems[pid] if pid < len(problems) else None
                if actual_item:
                    pred = extract_hotpotqa_answer(str(row["response_text"]))
                    gt = actual_item["answer"]
                    f1_val = hotpotqa_compute_f1(pred, gt)
                else:
                    f1_val = 1.0 if corr else 0.0
                
                # We need input/output tokens, cost, latency per problem (summed across all roles for this problem_id)
                prob_rows = df[df.problem_id == pid]
                tot_cost = float(prob_rows["cost_usd"].sum())
                tot_in = int(prob_rows["input_tokens"].sum())
                tot_out = int(prob_rows["output_tokens"].sum())
                tot_lat = float(prob_rows["latency_s"].sum())
                
                reconstructed_results.append({
                    "problem_id": pid,
                    "correct": corr,
                    "f1": f1_val,
                    "total_cost": tot_cost,
                    "total_input_tokens": tot_in,
                    "total_output_tokens": tot_out,
                    "total_latency": tot_lat,
                })
            stats = compute_experiment_stats(reconstructed_results)
            stats["note"] = f"Session processed {processed_count} problems. {len(skip_ids)} were from previous run."
        except Exception as csv_err:
            print(f"  ⚠️  Could not reconstruct full stats from CSV: {csv_err}. Showing session stats instead.")
            stats = compute_experiment_stats(all_results)
    else:
        stats = compute_experiment_stats(all_results)

    stats["tier"] = tier
    stats["model"] = model_name
    stats["experiment_id"] = experiment_id

    print(f"\n{'='*60}")
    print(f"  RESULTS — Tier {tier} ({model_name})")
    print(f"{'='*60}")
    print(f"  Exact Match (EM): {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total_problems']})")
    if "avg_f1" in stats:
        print(f"  F1 Score:         {stats['avg_f1']:.1f}%")
    print(f"  Total cost:       ${stats['total_cost_usd']:.4f}")
    print(f"  Avg cost:         ${stats['avg_cost_per_problem']:.6f} per problem")
    print(f"  Total tokens:     {stats['total_tokens']:,}")
    print(f"  Avg latency:      {stats['avg_latency_per_problem']:.1f}s per problem")
    if resume and skip_ids:
        print(f"  Resumed:          {len(skip_ids)} problems from previous run")
        print(f"  New:              {processed_count} problems this session")
    print(f"{'='*60}\n")

    # Save stats JSON
    stats_file = RESULTS_DIR / "baselines" / f"{experiment_id}_stats.json"
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to: {stats_file}")

    logger.print_summary()

    from src.models.base import BaseMultiKeyModel
    if isinstance(model, BaseMultiKeyModel):
        model.print_final_status()

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MuSiQue baseline experiments")
    parser.add_argument("--tier", type=int, required=True, choices=[1, 2, 3, 4],
                        help="Model tier to use (1=Gemma 4B, 2=Llama 70B, 3=Llama 405B, 4=GPT-4.1)")
    parser.add_argument("--num-problems", type=int, default=200,
                        help="Number of MuSiQue problems to evaluate (default: 200)")
    parser.add_argument("--rate-limit", type=int, default=None,
                        help="Override requests per minute (default: auto from config)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from a previous run, skipping already-completed problems")
    args = parser.parse_args()

    # Define validation_problems globally so resume path can access it if needed
    validation_problems = list(load_dataset("bdsaglam/musique", "answerable", split="validation"))[:args.num_problems]

    run_musique_baseline(
        tier=args.tier,
        num_problems=args.num_problems,
        rate_limit_rpm=args.rate_limit,
        resume=args.resume,
    )
