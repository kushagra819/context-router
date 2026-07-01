"""
Cost-sensitivity analysis
=========================
The cost axis uses HYPOTHETICAL per-token prices (all models are free in
practice; see docs/03_MODEL_MATRIX.md, R10). All four reviewers flagged that the
savings narrative might be an artefact of one number -- the Tier-4 output price
(8.00/1M), 4x the Tier-3 price. This module quantifies how robust the
cost-savings conclusion is to the assumed price vector, using REAL per-problem
token counts from the baselines (so only the prices vary, not the workload).

For each price vector we compute, per dataset:
  * total cost of each fixed-tier baseline,
  * total cost of the per-problem ORACLE (cheapest EM/F1-correct tier),
  * cost savings of the oracle vs all-Tier-4.
If the oracle's savings stays large across every plausible vector, the efficiency
conclusion does not depend on the T4 output price. Pure standard library.
"""

from __future__ import annotations

from pathlib import Path

from src.evaluation.csv_io import per_problem_records
from src.router.training_data import tier_correctness, cheapest_correct_tier
from src.utils.config import RESULTS_DIR, MODEL_CONFIG

TIERS = (1, 2, 3, 4)

# (in_price, out_price) per 1M tokens, per tier. Each vector probes a different
# assumption about how the frontier is priced. NOTE: when the existing CSVs were
# collected, Tier 3 = Llama-3.1-405B; the token counts reflect that run. The
# "published" vector below auto-syncs to whatever MODEL_CONFIG currently holds, so
# after re-running Tier 3 on Llama-4-Maverick it prices the new tokens correctly.
PRICE_VECTORS: dict[str, dict[int, tuple[float, float]]] = {
    # The repo's headline assumption (current MODEL_CONFIG list prices).
    "published": {t: (MODEL_CONFIG[t]["cost_per_1m_input"], MODEL_CONFIG[t]["cost_per_1m_output"])
                  for t in TIERS},
    # Removes the 4x T4 output skew the reviewers say drives the story.
    "t4_flat_output": {1: (0.03, 0.06), 2: (0.59, 0.79), 3: (2.66, 2.66), 4: (2.00, 2.00)},
    # Frontier tiers priced cheaply (open-weight-style): stresses savings the other way.
    "cheap_frontier": {1: (0.03, 0.06), 2: (0.59, 0.79), 3: (0.90, 0.90), 4: (1.00, 1.00)},
    # Representative real 2025 hosted prices (Llama-70B, Llama-405B, GPT-4.1-class).
    "market_2025": {1: (0.05, 0.10), 2: (0.59, 0.79), 3: (3.00, 3.00), 4: (2.00, 8.00)},
    # Compressed spread: every tier within ~3x (conservative -> smallest savings).
    "compressed": {1: (0.10, 0.20), 2: (0.50, 0.60), 3: (0.80, 0.90), 4: (1.00, 1.20)},
}


def _cost(in_tok: int, out_tok: int, price: tuple[float, float]) -> float:
    return in_tok / 1e6 * price[0] + out_tok / 1e6 * price[1]


def _best_records(dataset: str, tier: int, baselines_dir: Path) -> dict[int, dict]:
    backup = baselines_dir.parent / "baselines_backup"
    fname = f"{dataset}_baseline_tier{tier}.csv"
    best: dict[int, dict] = {}
    for path in (baselines_dir / fname, backup / fname):
        if path.exists():
            recs = per_problem_records(path)
            if len(recs) > len(best):
                best = recs
    return best


def analyze_dataset(dataset: str, baselines_dir: Path | None = None, metric: str = "em") -> dict:
    baselines_dir = baselines_dir or (RESULTS_DIR / "baselines")
    recs = {t: _best_records(dataset, t, baselines_dir) for t in TIERS}
    pids = sorted(set.intersection(*[set(recs[t].keys()) for t in TIERS])) if all(recs[t] for t in TIERS) else []
    if not pids:
        return {"dataset": dataset, "n": 0}

    correct, _, _ = tier_correctness(dataset, metric, baselines_dir=baselines_dir, restrict_intersection=True)

    out = {"dataset": dataset, "n": len(pids), "metric": metric, "vectors": {}}
    for vname, prices in PRICE_VECTORS.items():
        tier_cost = {t: sum(_cost(recs[t][p]["input_tokens"], recs[t][p]["output_tokens"], prices[t])
                            for p in pids) for t in TIERS}
        # Oracle: cheapest correct tier per problem, costed at that tier's tokens.
        oracle_cost = 0.0
        for p in pids:
            ot = cheapest_correct_tier(correct, p) or 1   # unsolvable -> T1 (spend least)
            oracle_cost += _cost(recs[ot][p]["input_tokens"], recs[ot][p]["output_tokens"], prices[ot])
        ref = tier_cost[4]
        out["vectors"][vname] = {
            "tier_cost": {f"t{t}": round(tier_cost[t], 4) for t in TIERS},
            "oracle_cost": round(oracle_cost, 4),
            "oracle_savings_pct_vs_t4": round((1 - oracle_cost / ref) * 100, 2) if ref else None,
            "t1_savings_pct_vs_t4": round((1 - tier_cost[1] / ref) * 100, 2) if ref else None,
        }
    # Robustness summary: spread of the oracle-savings across vectors.
    sav = [v["oracle_savings_pct_vs_t4"] for v in out["vectors"].values() if v["oracle_savings_pct_vs_t4"] is not None]
    out["oracle_savings_min_pct"] = round(min(sav), 2) if sav else None
    out["oracle_savings_max_pct"] = round(max(sav), 2) if sav else None
    return out


def run(datasets=("gsm8k", "hotpotqa", "musique"), baselines_dir: Path | None = None, metric: str = "em") -> dict:
    return {"price_vectors": {k: {str(t): v[t] for t in TIERS} for k, v in PRICE_VECTORS.items()},
            "datasets": [analyze_dataset(d, baselines_dir, metric) for d in datasets]}
