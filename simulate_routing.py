"""
Offline routing simulation CLI.

Estimates router cost/quality from the BASELINE CSVs with NO API calls, under the
independence assumption documented in src/evaluation/simulate.py. This is what
lets the office machine produce preliminary router results and figures before the
live runs. Exact for single-tier and oracle; estimates for mixed/random/content.

Examples
--------
  # Simulate content-free routers on a dataset with complete 4-tier baselines:
  python simulate_routing.py --dataset gsm8k

  # Include content-based routers by loading questions from the dataset:
  python simulate_routing.py --dataset gsm8k --with-questions --routers complexity learned

Writes results/routing_sim/<dataset>_sim.json and a combined markdown table.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.evaluation.simulate import simulate, CONTENT_FREE, NEEDS_QUESTION, NOT_SIMULABLE
from src.pipeline.dataset_adapters import available_datasets, get_adapter
from src.utils.config import RESULTS_DIR

DEFAULT_ROUTERS = ["oracle", "fixed_t1", "fixed_t2", "fixed_t3", "fixed_t4", "fixed_mixed", "random"]


def load_questions(dataset: str, n: int) -> dict[int, str]:
    adapter = get_adapter(dataset)
    return {p.id: p.question for p in adapter.load(n)}


def main():
    ap = argparse.ArgumentParser(description="Offline routing simulation from baseline CSVs.")
    ap.add_argument("--dataset", choices=available_datasets(), default=None,
                    help="Dataset to simulate (default: all that have 4 complete tiers).")
    ap.add_argument("--routers", nargs="+", default=DEFAULT_ROUTERS)
    ap.add_argument("--with-questions", action="store_true",
                    help="Load dataset questions so complexity/learned can be simulated.")
    ap.add_argument("--num-problems", type=int, default=200)
    args = ap.parse_args()

    datasets = [args.dataset] if args.dataset else available_datasets()
    out_dir = RESULTS_DIR / "routing_sim"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_summaries = []
    for dataset in datasets:
        questions = load_questions(dataset, args.num_problems) if args.with_questions else None
        results = {}
        print(f"\n=== Simulating routers on {dataset} ===")
        for router in args.routers:
            if router in NOT_SIMULABLE:
                print(f"  skip {router}: not simulable offline (needs live confidence).")
                continue
            if router in NEEDS_QUESTION and not questions:
                print(f"  skip {router}: needs --with-questions.")
                continue
            try:
                out = simulate(router, dataset, questions=questions)
                results[router] = out["summary"]
                all_summaries.append(out["summary"])
                s = out["summary"]
                print(f"  {router:12} EM={s['em']:5.1f}%  cost=${s['total_cost_usd']:.4f}  "
                      f"routeAcc={s['routing_accuracy']:5.1f}%  tiers={s['tier_distribution']}")
            except (RuntimeError, ValueError) as e:
                print(f"  skip {router}: {e}")
        if results:
            (out_dir / f"{dataset}_sim.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Combined markdown table.
    if all_summaries:
        md = ["# Routing Simulation (offline estimates)", "",
              "> EXACT for single-tier & oracle; ESTIMATE for mixed/random/content "
              "(verifier-tier proxy). Confirm with live `run_experiment.py`.", "",
              "| dataset | router | N | EM% | cost$ | routeAcc% | over% | under% |",
              "|" + "---|" * 8]
        for s in all_summaries:
            md.append(f"| {s['dataset']} | {s['router']} | {s['n']} | {s['em']} | "
                      f"{s['total_cost_usd']} | {s['routing_accuracy']} | "
                      f"{s['over_provision_rate']} | {s['under_provision_rate']} |")
        (out_dir / "simulation_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"\nWrote {out_dir / 'simulation_table.md'}")


if __name__ == "__main__":
    main()
