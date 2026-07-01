"""
Unified experiment runner (baselines + routed experiments).

A baseline is just the pipeline driven by a fixed-tier router, so the SAME code
path produces baselines and routed runs -- the only thing that changes is the
routing policy. This is the fair comparison the research relies on.

Examples
--------
  # Reproduce a baseline (Tier 2, all agents) -> results/baselines/
  python run_experiment.py --dataset gsm8k --router fixed_t2 --num-problems 200

  # Run the proposed router live -> results/routing/
  python run_experiment.py --dataset hotpotqa --router cascade --num-problems 200

  # Resume an interrupted run
  python run_experiment.py --dataset musique --router adaptive --resume

  # Smoke-test the whole flow with NO API calls (writes to results/_mock/)
  python run_experiment.py --dataset gsm8k --router cascade --num-problems 5 --mock

See docs/16_EXPERIMENT_MANIFEST.md for the full command list.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline.dataset_adapters import available_datasets
from src.pipeline.experiment import run_experiment
from src.router import list_routers


def main():
    ap = argparse.ArgumentParser(description="Run a (dataset x router) experiment.")
    ap.add_argument("--dataset", required=True, choices=available_datasets())
    ap.add_argument("--router", required=True, choices=list_routers(),
                    help="fixed_t1..fixed_t4 reproduce baselines; others are routed runs.")
    ap.add_argument("--num-problems", type=int, default=200)
    ap.add_argument("--resume", action="store_true", help="Skip already-completed problems.")
    ap.add_argument("--mock", action="store_true",
                    help="Use deterministic offline MockModel (no API). Writes to results/_mock/.")
    ap.add_argument("--cost-budget", type=float, default=float("inf"),
                    help="Per-problem hypothetical cost budget (USD) for budget-aware routers.")
    args = ap.parse_args()

    run_experiment(
        dataset=args.dataset,
        router_name=args.router,
        num_problems=args.num_problems,
        resume=args.resume,
        mock=args.mock,
        cost_budget=args.cost_budget,
    )


if __name__ == "__main__":
    main()
