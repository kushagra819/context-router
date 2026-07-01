"""
Experiment driver
=================
Runs ONE (dataset x router) experiment through the unified RoutedPipeline and
logs every agent call. Baselines and routed runs share this exact code path:

    baseline  == router "fixed_t{N}"  -> results/baselines/{dataset}_baseline_tier{N}.csv
    routed     == any other router      -> results/routing/{dataset}_{router}.csv
    mock mode  -> results/_mock/...      (never clobbers real data; no API calls)

Features: resume (skip completed problems), fresh-start backup, stats JSON,
graceful stop on API-key exhaustion. The model wrappers throttle internally, so
no extra sleeping is needed here.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.models.base import BaseMultiKeyModel
from src.models.registry import ModelRegistry
from src.pipeline.dataset_adapters import get_adapter
from src.pipeline.routed_pipeline import RoutedPipeline
from src.router import get_router
from src.utils.config import RESULTS_DIR
from src.utils.logger import ExperimentLogger
from src.evaluation.csv_io import per_problem_records


def _is_fixed_tier(router_name: str) -> int | None:
    if router_name.startswith("fixed_t") and router_name[7:].isdigit():
        return int(router_name[7:])
    return None


def _resolve_output(dataset: str, router_name: str, mock: bool) -> tuple[Path, str, str]:
    """Return (out_dir, experiment_id, router_type)."""
    tier = _is_fixed_tier(router_name)
    if mock:
        out_dir = RESULTS_DIR / "_mock"
        if tier:
            return out_dir, f"{dataset}_baseline_tier{tier}", "none"
        return out_dir, f"{dataset}_{router_name}", router_name
    if tier:
        return RESULTS_DIR / "baselines", f"{dataset}_baseline_tier{tier}", "none"
    return RESULTS_DIR / "routing", f"{dataset}_{router_name}", router_name


def _completed_ids(csv_path: Path) -> set[int]:
    if not csv_path.exists():
        return set()
    recs = per_problem_records(csv_path)  # already requires all 3 roles + no [ERROR]
    return set(recs.keys())


def run_experiment(
    dataset: str,
    router_name: str,
    num_problems: int = 200,
    resume: bool = False,
    mock: bool = False,
    router_kwargs: dict | None = None,
    cost_budget: float = float("inf"),
) -> dict:
    adapter = get_adapter(dataset)
    router = get_router(router_name, **(router_kwargs or {}))
    out_dir, experiment_id, router_type = _resolve_output(dataset, router_name, mock)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{experiment_id}.csv"

    print(f"\n{'='*64}")
    print(f"  {dataset.upper()}  |  router={router_name}  |  {'MOCK' if mock else 'LIVE'}")
    print(f"  experiment_id={experiment_id}  problems={num_problems}  resume={resume}")
    print(f"{'='*64}\n")

    # Fresh start: archive any existing CSV so we never append to an old schema.
    if csv_path.exists() and not resume:
        backup = out_dir / f"{experiment_id}.prev.csv"
        csv_path.replace(backup)
        print(f"  Archived existing CSV -> {backup.name}")

    skip_ids = _completed_ids(csv_path) if resume else set()
    if resume:
        print(f"  Resume: {len(skip_ids)} problems already complete.\n")

    print("  Loading dataset...")
    problems = adapter.load(num_problems)
    print(f"  Loaded {len(problems)} problems.\n")

    registry = ModelRegistry(mock=mock)
    pipeline = RoutedPipeline(adapter, registry, cost_budget=cost_budget)
    logger = ExperimentLogger(experiment_id, out_dir)

    correct = 0
    f1_sum = 0.0
    processed = 0
    stopped_early = False

    for problem in problems:
        if problem.id in skip_ids:
            continue
        try:
            result = pipeline.run_problem(problem, router)
        except RuntimeError as e:
            if "exhausted" in str(e).lower():
                print(f"\n  FATAL: {e}\n  Saving progress and stopping.")
                stopped_early = True
                break
            print(f"  Problem {problem.id} failed: {e}")
            continue

        if result.correct:
            correct += 1
        f1_sum += result.f1
        processed += 1

        for call in result.calls:
            logger.log_call(
                problem_id=problem.id,
                dataset=dataset,
                agent_role=call.role,
                tier=call.tier,
                model_name=call.response.model_name,
                router_type=router_type,
                input_tokens=call.response.input_tokens,
                output_tokens=call.response.output_tokens,
                latency_s=call.response.latency,
                cost_usd=call.response.cost_usd,
                correct=result.correct,
                f1=result.f1,
                ground_truth=str(result.ground_truth),
                predicted=str(result.predicted),
                confidence=call.confidence,
                confidence_source=call.confidence_source,
                mean_logprob=call.response.mean_logprob,
                routing_reason=call.decision.reason,
                escalated_from=call.decision.escalated_from,
                response_text=call.response.text,
            )

        if processed % 10 == 0:
            done = len(skip_ids) + processed
            acc = correct / processed * 100
            print(f"  [{done}/{num_problems}] session EM={acc:.1f}%  F1={f1_sum/processed*100:.1f}%")

    stats = {
        "experiment_id": experiment_id,
        "dataset": dataset,
        "router": router_name,
        "router_type": router_type,
        "mock": mock,
        "session_processed": processed,
        "session_correct": correct,
        "session_em": round(correct / processed * 100, 2) if processed else 0.0,
        "session_f1": round(f1_sum / processed * 100, 2) if processed else 0.0,
        "resumed_from_previous": len(skip_ids),
        "stopped_early": stopped_early,
        "generated": datetime.now().isoformat(),
        "note": "Session-only stats. Use scripts/validate_baselines.py / "
                "aggregate_results.py for authoritative full-CSV metrics.",
    }
    stats_path = out_dir / f"{experiment_id}_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    logger.print_summary()

    reg_models = [m for m in registry._cache.values() if isinstance(m, BaseMultiKeyModel)]
    for m in reg_models:
        m.print_final_status()

    print(f"  Stats -> {stats_path}")
    print(f"  Log   -> {csv_path}\n")
    return stats
