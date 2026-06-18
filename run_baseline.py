"""
Run baseline experiments — all agents use the SAME model (no routing).

Usage:
    python run_baseline.py --tier 1 --num-problems 200
    python run_baseline.py --tier 2 --num-problems 200
    python run_baseline.py --tier 3 --num-problems 50 --rate-limit 2
    python run_baseline.py --tier 4 --num-problems 200 --resume

This produces the control data that we compare our router against.
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
from src.agents.gsm8k_agents import create_gsm8k_agents, run_gsm8k_pipeline
from src.evaluation.metrics import (
    extract_gsm8k_answer,
    extract_gsm8k_ground_truth,
    gsm8k_check_correct,
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


def run_gsm8k_baseline(tier: int, num_problems: int, rate_limit_rpm: int | None = None, resume: bool = False):
    """Run GSM8K baseline with all agents using the specified tier."""

    experiment_id = f"gsm8k_baseline_tier{tier}"
    model_name = MODEL_CONFIG[tier]["name"]

    print(f"\n{'='*60}")
    print(f"  GSM8K Baseline — Tier {tier} ({model_name})")
    print(f"  Problems: {num_problems}")
    if resume:
        print(f"  Mode: RESUME (skipping already-completed problems)")
    print(f"{'='*60}\n")

    # Load dataset
    print("Loading GSM8K dataset...")
    dataset = load_dataset("openai/gsm8k", "main", split="test")
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
            error_ids_in_csv = error_ids  # These had [ERROR] rows or missing rows
            _remove_error_rows(experiment_id, error_ids_in_csv)
            remaining = num_problems - len(skip_ids)
            print(f"  ✅ Found {len(skip_ids)} completed problems from previous run.")
            print(f"  📋 {remaining} problems remaining to process.\n")
        else:
            print(f"  ℹ️  No previous results found — starting fresh.\n")

    # Create model and agents
    model = get_model(tier)
    agents = create_gsm8k_agents(model)

    from src.models.base import BaseMultiKeyModel
    if isinstance(model, BaseMultiKeyModel):
        model.print_key_status(startup=True)

    # Set up logger (appends to existing CSV)
    logger = ExperimentLogger(experiment_id, RESULTS_DIR / "baselines")

    # Rate limiting
    if rate_limit_rpm is None:
        provider = MODEL_CONFIG[tier]["provider"]
        rate_limit_rpm = RATE_LIMITS.get(provider, 30)
    delay_between_calls = 60.0 / rate_limit_rpm if rate_limit_rpm < 100 else 0

    # Run pipeline on each problem
    all_results = []
    correct_count = 0
    processed_count = 0

    for i, item in enumerate(tqdm(problems, desc=f"Tier {tier}")):
        # Skip already-completed problems in resume mode
        if i in skip_ids:
            continue

        if processed_count > 0 and processed_count % 25 == 0:
            if isinstance(model, BaseMultiKeyModel):
                model.print_key_status(startup=False)

        problem_text = item["question"]
        ground_truth_text = item["answer"]
        ground_truth = extract_gsm8k_ground_truth(ground_truth_text)

        try:
            # Run 3-agent pipeline
            result = run_gsm8k_pipeline(agents, problem_text)

            # Extract predicted answer
            predicted = extract_gsm8k_answer(result["final_output"])
            correct = gsm8k_check_correct(predicted, ground_truth)

            if correct:
                correct_count += 1

            result["problem_id"] = i
            result["ground_truth"] = ground_truth
            result["predicted"] = predicted
            result["correct"] = correct

            # Log each agent's call
            for agent_role, response in result["agent_responses"].items():
                logger.log_call(
                    problem_id=i,
                    dataset="gsm8k",
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
            total_correct = correct_count  # Only counts this session
            if total_done % 10 == 0 or processed_count % 10 == 0:
                if processed_count > 0:
                    session_acc = correct_count / processed_count * 100
                    print(f"  [{total_done}/{num_problems}] Session accuracy: {session_acc:.1f}%")

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
                "error": str(e),
                "total_cost": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_latency": 0,
            })
            processed_count += 1

    # Compute and print stats (re-read full CSV for accurate totals if resuming)
    if resume and skip_ids:
        print(f"\n  Re-computing stats from full CSV (including resumed data)...")
        # Stats from this session only
        stats = compute_experiment_stats(all_results)
        stats["note"] = f"Session processed {processed_count} problems. {len(skip_ids)} were from previous run."
    else:
        stats = compute_experiment_stats(all_results)

    stats["tier"] = tier
    stats["model"] = model_name
    stats["experiment_id"] = experiment_id

    print(f"\n{'='*60}")
    print(f"  RESULTS — Tier {tier} ({model_name})")
    print(f"{'='*60}")
    print(f"  Accuracy:    {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total_problems']})")
    print(f"  Total cost:  ${stats['total_cost_usd']:.4f}")
    print(f"  Avg cost:    ${stats['avg_cost_per_problem']:.6f} per problem")
    print(f"  Total tokens: {stats['total_tokens']:,}")
    print(f"  Avg latency: {stats['avg_latency_per_problem']:.1f}s per problem")
    if resume and skip_ids:
        print(f"  Resumed:     {len(skip_ids)} problems from previous run")
        print(f"  New:         {processed_count} problems this session")
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


def main():
    parser = argparse.ArgumentParser(description="Run GSM8K baseline experiments")
    parser.add_argument("--tier", type=int, required=True, choices=[1, 2, 3, 4],
                        help="Model tier to use (1=Gemma 4B, 2=Llama 70B, 3=Llama 405B, 4=GPT-4.1)")
    parser.add_argument("--num-problems", type=int, default=200,
                        help="Number of GSM8K problems to evaluate (default: 200)")
    parser.add_argument("--rate-limit", type=int, default=None,
                        help="Override requests per minute (default: auto from config)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from a previous run, skipping already-completed problems")
    args = parser.parse_args()

    run_gsm8k_baseline(
        tier=args.tier,
        num_problems=args.num_problems,
        rate_limit_rpm=args.rate_limit,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
