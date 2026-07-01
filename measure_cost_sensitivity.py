"""
Cost-sensitivity driver.

Recomputes the oracle cost-savings vs all-Tier-4 under several plausible price
vectors (real per-problem token counts; only prices change) to show the savings
conclusion does NOT hinge on the hypothetical Tier-4 output price (reviewer R10).

Writes results/cost_sensitivity.json (+ a console table). Pure standard library.
  python measure_cost_sensitivity.py [--metric em|f1]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.evaluation.cost_sensitivity import run, PRICE_VECTORS
from src.utils.config import RESULTS_DIR


def main():
    ap = argparse.ArgumentParser(description="Cost-sensitivity of oracle savings vs price vector.")
    ap.add_argument("--metric", choices=["em", "f1"], default="f1")
    args = ap.parse_args()

    report = run(metric=args.metric)
    out = RESULTS_DIR / "cost_sensitivity.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 84)
    print(f"  COST SENSITIVITY  (oracle savings vs all-Tier-4; metric={args.metric})")
    print("=" * 84)
    vnames = list(PRICE_VECTORS.keys())
    print(f"  {'dataset':10}" + "".join(f"{v:>16}" for v in vnames))
    print("  " + "-" * 80)
    for d in report["datasets"]:
        if not d.get("n"):
            print(f"  {d['dataset']:10}  (no data)")
            continue
        cells = "".join(f"{d['vectors'][v]['oracle_savings_pct_vs_t4']:>15.1f}%" for v in vnames)
        print(f"  {d['dataset']:10}{cells}")
        print(f"  {'':10}  -> oracle savings range: "
              f"{d['oracle_savings_min_pct']}% .. {d['oracle_savings_max_pct']}%")
    print("\n  Interpretation: if oracle savings stays large across ALL vectors, the")
    print("  efficiency conclusion is robust to the assumed (hypothetical) prices.")
    print(f"\n  Full report -> {out}")


if __name__ == "__main__":
    main()
