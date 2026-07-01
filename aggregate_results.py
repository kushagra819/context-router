"""
Aggregate all experiment CSVs into the master results table.

Reads results/baselines/ and results/routing/ (CSV = source of truth) and writes:
    results/master_results.json   (full metrics, machine-readable)
    results/master_results.csv    (flat table for spreadsheets/figures)
    results/master_results.md     (human-readable comparison table)

Every metric is defined in docs/13_METRICS_AND_FORMULAS.md and implemented in
src/evaluation/routing_metrics.py. Pure standard library.

Example
-------
  python aggregate_results.py
  python aggregate_results.py --datasets gsm8k hotpotqa
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.evaluation.aggregate import build_master, write_outputs
from src.pipeline.dataset_adapters import available_datasets


def main():
    ap = argparse.ArgumentParser(description="Build master results table from CSVs.")
    ap.add_argument("--datasets", nargs="+", default=available_datasets(),
                    choices=available_datasets())
    args = ap.parse_args()

    master = build_master(args.datasets)
    paths = write_outputs(master)

    print(f"Aggregated {paths['n_rows']} experiment rows.")
    print(f"  JSON -> {paths['json']}")
    print(f"  CSV  -> {paths['csv']}")
    print(f"  MD   -> {paths['md']}")

    # Console preview. retain% is vs the BEST baseline tier (honest ceiling), not T4.
    print(f"\n  cost ref = {master.get('cost_reference')}; "
          f"quality ref = {master.get('quality_reference')}")
    print("\n  dataset    router          N    EM%    cost$     save%  retain%(best)")
    print("  " + "-" * 68)
    for r in master["rows"]:
        if not r.get("n"):
            continue
        print(f"  {r['dataset']:<10} {r['label']:<14} {r['n']:>4} "
              f"{r.get('em', 0):>6} {r.get('total_cost_usd', 0):>9.4f} "
              f"{r.get('cost_savings_pct_vs_t4', ''):>7} {r.get('quality_retention_pct_vs_best', ''):>9}")


if __name__ == "__main__":
    main()
