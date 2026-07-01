"""
Results aggregation
===================
Builds the master comparison table from experiment CSVs (the source of truth).
Works for BOTH baseline logs (results/baselines/) and routed logs
(results/routing/), computing every metric in docs/13_METRICS_AND_FORMULAS.md.

Pure standard library (csv/json) — no pandas — so it runs anywhere.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.evaluation.csv_io import per_problem_records
from src.evaluation import routing_metrics as RM
from src.utils.config import RESULTS_DIR

TIERS = (1, 2, 3, 4)
REFERENCE_TIER = 4  # all-Tier-4 pipeline = quality ceiling / cost reference


# --------------------------------------------------------------------------- #
# Per-experiment summary
# --------------------------------------------------------------------------- #
def summarize_experiment(path: Path, dataset: str, label: str,
                         oracle_tiers: dict[int, int | None] | None = None) -> dict:
    recs = per_problem_records(path)
    pids = sorted(recs.keys())
    n = len(pids)
    if n == 0:
        return {"label": label, "dataset": dataset, "n": 0, "file": path.name}

    correct = [recs[p]["correct"] for p in pids]
    f1 = [recs[p]["f1"] for p in pids if recs[p]["f1"] is not None]
    total_cost = sum(recs[p]["cost"] for p in pids)
    total_tokens = sum(recs[p]["input_tokens"] + recs[p]["output_tokens"] for p in pids)
    total_latency = sum(recs[p]["latency"] for p in pids)
    correct_count = sum(1 for c in correct if c)

    # Tier usage + escalations.
    verifier_tiers = [recs[p]["tiers"].get("verifier", 0) for p in pids]
    tier_dist = {f"t{t}": sum(1 for vt in verifier_tiers if vt == t) for t in TIERS}
    escalated_any = [recs[p]["escalations"] > 0 for p in pids]

    em = RM.exact_match(correct)
    summary = {
        "label": label,
        "dataset": dataset,
        "file": path.name,
        "n": n,
        "em": round(em * 100, 2),
        "correct": correct_count,
        "f1": round(RM.mean_f1(f1) * 100, 2) if f1 else None,
        "total_cost_usd": round(total_cost, 6),
        "cost_per_task": round(RM.cost_per_task(total_cost, n), 6),
        "total_tokens": total_tokens,
        "token_efficiency": round(RM.token_efficiency(correct_count, total_tokens), 2),
        "avg_latency_s": round(total_latency / n, 2),
        "throughput_per_min": round(RM.throughput_per_min(n, total_latency), 3),
        "escalation_rate": round(RM.escalation_rate(escalated_any) * 100, 2),
        "tier_distribution": tier_dist,
        "_correct_flags": [1.0 if c else 0.0 for c in correct],  # for CI; stripped on write
    }

    # Routing-quality metrics vs the oracle (when available).
    if oracle_tiers:
        chosen = verifier_tiers
        otiers = [oracle_tiers.get(p) for p in pids]
        summary["routing_accuracy"] = round(RM.routing_accuracy(chosen, otiers) * 100, 2)
        summary["over_provision_rate"] = round(RM.over_provision_rate(chosen, otiers) * 100, 2)
        summary["under_provision_rate"] = round(
            RM.under_provision_rate(chosen, otiers, correct) * 100, 2)
    return summary


# --------------------------------------------------------------------------- #
# Oracle tiers from baselines
# --------------------------------------------------------------------------- #
def oracle_tiers_for(dataset: str, baselines_dir: Path) -> dict[int, int | None]:
    backup = baselines_dir.parent / "baselines_backup"
    per_tier_correct: dict[int, dict[int, bool]] = {}
    for tier in TIERS:
        fname = f"{dataset}_baseline_tier{tier}.csv"
        best: dict[int, dict] = {}
        for path in (baselines_dir / fname, backup / fname):
            if path.exists():
                recs = per_problem_records(path)
                if len(recs) > len(best):
                    best = recs
        per_tier_correct[tier] = {pid: bool(r["correct"]) for pid, r in best.items()}

    all_pids = set()
    for d in per_tier_correct.values():
        all_pids.update(d.keys())
    return {pid: RM.oracle_tier({t: per_tier_correct[t].get(pid, False) for t in TIERS})
            for pid in all_pids}


# --------------------------------------------------------------------------- #
# Master table
# --------------------------------------------------------------------------- #
def build_master(datasets: list[str] | None = None,
                 baselines_dir: Path | None = None,
                 routing_dir: Path | None = None) -> dict:
    baselines_dir = baselines_dir or (RESULTS_DIR / "baselines")
    routing_dir = routing_dir or (RESULTS_DIR / "routing")
    datasets = datasets or ["gsm8k", "hotpotqa", "musique"]

    rows: list[dict] = []
    for dataset in datasets:
        oracle = oracle_tiers_for(dataset, baselines_dir)

        # Baselines: fixed_t1..t4.
        for tier in TIERS:
            p = baselines_dir / f"{dataset}_baseline_tier{tier}.csv"
            if not p.exists():
                p = baselines_dir.parent / "baselines_backup" / f"{dataset}_baseline_tier{tier}.csv"
            if p.exists():
                rows.append(summarize_experiment(p, dataset, f"baseline_t{tier}", oracle))

        # Routed experiments.
        if routing_dir.exists():
            for p in sorted(routing_dir.glob(f"{dataset}_*.csv")):
                label = p.stem.replace(f"{dataset}_", "")
                rows.append(summarize_experiment(p, dataset, label, oracle))

        # Derived cross-experiment metrics.
        #   * COST is referenced to the most EXPENSIVE tier (all-Tier-4): cost
        #     savings vs the frontier-everywhere pipeline.
        #   * QUALITY is referenced to the BEST-PERFORMING baseline tier, NOT
        #     fixed_t4. On multi-hop, GPT-4.1 (T4) is verbose and is NOT the
        #     quality ceiling, so "retention vs T4" exceeds 100% and is
        #     misleading; "retention vs best tier" is the honest ceiling. We also
        #     keep the vs_t4 columns for transparency. (Fixes the QRR>100%
        #     artifact flagged in the reviewer pre-mortem.)
        dset_baselines = [r for r in rows if r["dataset"] == dataset
                          and r["label"].startswith("baseline_t") and r.get("n")]
        ref_t4 = next((r for r in dset_baselines if r["label"] == f"baseline_t{REFERENCE_TIER}"), None)
        best_em_ref = max(dset_baselines, key=lambda r: r["em"], default=None)
        best_f1_ref = max((r for r in dset_baselines if r["f1"] is not None),
                          key=lambda r: r["f1"], default=None)
        if ref_t4:
            ref_cost, ref_em = ref_t4["total_cost_usd"], ref_t4["em"] / 100.0
            ref_f1 = (ref_t4["f1"] / 100.0) if ref_t4["f1"] is not None else None
            best_em = best_em_ref["em"] / 100.0 if best_em_ref else None
            best_f1 = (best_f1_ref["f1"] / 100.0) if best_f1_ref else None
            for r in rows:
                if r["dataset"] != dataset or not r.get("n"):
                    continue
                r["cost_savings_pct_vs_t4"] = round(
                    RM.cost_savings_pct(ref_cost, r["total_cost_usd"]), 2)
                r["cost_reduction_factor_vs_t4"] = round(
                    RM.cost_reduction_factor(ref_cost, r["total_cost_usd"]), 2)
                # Transparency: retention vs the (possibly-not-ceiling) T4.
                r["quality_retention_pct_vs_t4"] = round(
                    RM.quality_retention_pct(r["em"] / 100.0, ref_em), 2)
                if ref_f1 and r["f1"] is not None:
                    r["f1_retention_pct_vs_t4"] = round(
                        RM.quality_retention_pct(r["f1"] / 100.0, ref_f1), 2)
                # Honest ceiling: retention vs the best-performing baseline tier.
                if best_em:
                    r["quality_retention_pct_vs_best"] = round(
                        RM.quality_retention_pct(r["em"] / 100.0, best_em), 2)
                    r["best_quality_tier_em"] = best_em_ref["label"]
                if best_f1 and r["f1"] is not None:
                    r["f1_retention_pct_vs_best"] = round(
                        RM.quality_retention_pct(r["f1"] / 100.0, best_f1), 2)
                    r["best_quality_tier_f1"] = best_f1_ref["label"]

    return {"reference_tier": REFERENCE_TIER,
            "cost_reference": "all-Tier-4 (most expensive)",
            "quality_reference": "best-performing baseline tier per dataset",
            "rows": rows}


def write_outputs(master: dict, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or RESULTS_DIR
    rows = master["rows"]

    # Strip private fields for the on-disk JSON/CSV.
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]

    (out_dir / "master_results.json").write_text(
        json.dumps({"reference_tier": master["reference_tier"], "rows": clean}, indent=2),
        encoding="utf-8")

    cols = ["dataset", "label", "n", "em", "f1", "total_cost_usd", "cost_per_task",
            "cost_savings_pct_vs_t4", "cost_reduction_factor_vs_t4",
            "quality_retention_pct_vs_best", "f1_retention_pct_vs_best",
            "quality_retention_pct_vs_t4", "best_quality_tier_em",
            "routing_accuracy", "over_provision_rate",
            "under_provision_rate", "escalation_rate", "avg_latency_s", "token_efficiency"]
    lines = [",".join(cols)]
    for r in clean:
        lines.append(",".join(str(r.get(c, "")) for c in cols))
    (out_dir / "master_results.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Markdown table.
    md = ["# Master Results", "",
          f"> COST reference = all-Tier-{master['reference_tier']} pipeline (most expensive). "
          f"QUALITY reference (`retain%`) = best-performing baseline tier per dataset "
          f"(NOT T4, which is not the multi-hop quality ceiling). "
          f"Generated by `aggregate_results.py`.", ""]
    header = "| dataset | router | N | EM% | F1% | cost$ | save% | x cheaper | retain%(best) | bestTier | routeAcc% |"
    md.append(header)
    md.append("|" + "---|" * 11)
    for r in clean:
        md.append(("| {dataset} | {label} | {n} | {em} | {f1} | {cost} | {save} | {red} | "
                   "{ret} | {bt} | {ra} |").format(
            dataset=r["dataset"], label=r["label"], n=r.get("n", ""),
            em=r.get("em", ""), f1=r.get("f1", ""),
            cost=r.get("total_cost_usd", ""), save=r.get("cost_savings_pct_vs_t4", ""),
            red=r.get("cost_reduction_factor_vs_t4", ""),
            ret=r.get("quality_retention_pct_vs_best", ""),
            bt=r.get("best_quality_tier_em", ""),
            ra=r.get("routing_accuracy", "")))
    (out_dir / "master_results.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    return {
        "json": str(out_dir / "master_results.json"),
        "csv": str(out_dir / "master_results.csv"),
        "md": str(out_dir / "master_results.md"),
        "n_rows": len(clean),
    }
