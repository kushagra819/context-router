"""
Generate all paper/presentation figures into results/figures/.

Schematic figures are always produced. Data figures use, in priority order:
  1. results/master_results.json        (from aggregate_results.py — live runs)
  2. results/routing_sim/*_sim.json     (from simulate_routing.py — offline estimates)
If neither exists, data figures are skipped with a message.

Example
-------
  python make_figures.py
  python make_figures.py --datasets gsm8k
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.config import RESULTS_DIR
from src.pipeline.dataset_adapters import available_datasets
from src.visualization import figures as F


def load_rows() -> tuple[list[dict], str]:
    master = RESULTS_DIR / "master_results.json"
    if master.exists():
        data = json.loads(master.read_text(encoding="utf-8"))
        return data.get("rows", []), "master_results.json (live/aggregated)"
    sim_dir = RESULTS_DIR / "routing_sim"
    rows = []
    if sim_dir.exists():
        for p in sorted(sim_dir.glob("*_sim.json")):
            for router, s in json.loads(p.read_text(encoding="utf-8")).items():
                rows.append({
                    "dataset": s["dataset"], "label": s["router"], "n": s["n"],
                    "em": s["em"], "cost_per_task": s["cost_per_task"],
                    "tier_distribution": s.get("tier_distribution", {}),
                    "escalation_rate": s.get("escalation_rate", 0),
                })
    return rows, "routing_sim/*.json (offline simulation)"


def main():
    ap = argparse.ArgumentParser(description="Generate all figures.")
    ap.add_argument("--datasets", nargs="+", default=available_datasets(),
                    choices=available_datasets())
    args = ap.parse_args()

    print("Generating schematic figures...")
    for fn in F.SCHEMATICS:
        path = fn()
        print(f"  {path}")

    rows, source = load_rows()
    print(f"\nData figures source: {source} ({len(rows)} rows)")
    if not rows:
        print("  No results yet -> run simulate_routing.py or aggregate_results.py first.")
        return

    for dataset in args.datasets:
        for fn in F.DATA_FIGURES:
            path = fn(rows, dataset)
            if path:
                print(f"  {path}")
            else:
                print(f"  [skip] {fn.__name__} for {dataset} (insufficient data)")


if __name__ == "__main__":
    main()
