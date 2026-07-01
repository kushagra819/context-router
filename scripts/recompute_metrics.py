"""
recompute_metrics.py  --  authoritative, OFFLINE-FIRST metric recomputation
===========================================================================
Re-derives the per-row ``predicted`` / ``correct`` / ``f1`` columns of the
baseline CSVs from the immutable ``response_text`` using the SINGLE canonical
answer extractor (``src/evaluation/metrics``), then regenerates the
``*_stats.json`` files. CSVs remain the source of truth (ADR-001): we only
recompute *derived* columns from the raw model output, never the output itself.

Why this exists
---------------
The legacy extractor returned the bare Markdown marker ``**`` as the "answer"
when a frontier model wrote ``**Final Answer:** <span>``. This silently
mis-scored Tier-4 (GPT-4.1) on the multi-hop sets -- the documented "Tier-4 EM
anomaly" -- which corrupts oracle labels, QRR-vs-T4, and every downstream
comparison. The fixed extractor (metrics._strip_markdown + last-marker logic) is
applied IDENTICALLY to every tier, so this corrects a harness bug without
favouring any model (verified: terse tiers are unchanged; only T4 moves).

Ground-truth source
-------------------
1. Embedded ``ground_truth`` column (new-schema CSVs) -> fully OFFLINE. Default.
2. ``--use-hf`` re-loads the HF dataset to backfill legacy CSVs that lack the
   ``ground_truth`` column (hotpotqa T2/T3). API-free (no LLM calls), needs the
   ``datasets`` package + network. Expected to be ~a no-op for those terse tiers.

Safety
------
* The original CSV is backed up to ``<name>.prev.csv`` (only if no backup exists).
* GSM8K is skipped (numeric EM is already correct; no Markdown / no embedded GT).
* A machine-readable provenance report is written to
  ``results/recompute_provenance.json`` (old EM/F1 -> new EM/F1 per cell).

Usage
-----
  python scripts/recompute_metrics.py                 # offline, embedded GT only
  python scripts/recompute_metrics.py --use-hf        # also backfill legacy cells
  python scripts/recompute_metrics.py --dry-run       # report, write nothing
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

from src.evaluation.metrics import (  # noqa: E402
    extract_hotpotqa_answer, hotpotqa_check_correct, hotpotqa_compute_f1,
    compute_experiment_stats,
)
from src.evaluation.csv_io import read_rows  # noqa: E402
from src.utils.config import RESULTS_DIR, MODEL_CONFIG  # noqa: E402

DATASETS = ["hotpotqa", "musique"]   # GSM8K intentionally excluded (numeric EM)
TIERS = [1, 2, 3, 4]
HF_SPECS = {
    "hotpotqa": ("hotpotqa/hotpot_qa", "distractor", "validation"),
    "musique": ("bdsaglam/musique", "answerable", "validation"),
}


def _dataset_of(name: str) -> str | None:
    return next((d for d in DATASETS if d in name), None)


def _tier_of(name: str) -> int | None:
    return next((t for t in TIERS if f"tier{t}" in name), None)


def _is_truncated(text: str) -> bool:
    # Legacy logger stored response_text[:500]; such rows cannot be re-extracted reliably.
    return len(text or "") == 500


def recompute_csv(path: Path, hf_answers: dict[int, str] | None, dry_run: bool) -> dict | None:
    """Recompute one CSV in place (with backup). Returns a provenance dict or None."""
    rows = read_rows(path)
    if not rows:
        return None
    columns = list(rows[0].keys())
    has_gt = "ground_truth" in columns
    if not has_gt and hf_answers is None:
        return {"file": path.name, "status": "SKIPPED (no embedded ground_truth; pass --use-hf)",
                "changed": 0}

    # Ensure derived columns exist in the schema we will write back.
    for col in ("predicted", "correct", "f1", "ground_truth"):
        if col not in columns:
            columns.append(col)

    changed = 0
    old_correct = new_correct = 0
    old_f1_sum = new_f1_sum = 0.0
    n_scored = 0
    truncated = 0
    for r in rows:
        if (r.get("agent_role") or "").strip() != "verifier":
            continue
        try:
            pid = int(float(r.get("problem_id", "")))
        except (ValueError, TypeError):
            continue
        resp = r.get("response_text") or ""
        if "[ERROR]" in resp:
            continue
        gt = (r.get("ground_truth") or "").strip()
        if not gt and hf_answers is not None:
            gt = (hf_answers.get(pid) or "").strip()
            r["ground_truth"] = gt
        if not gt:
            continue
        if _is_truncated(resp):
            truncated += 1
            continue  # cannot trust a 500-char-truncated span

        n_scored += 1
        # old (logged) values for provenance
        try:
            old_em_flag = 1 if str(r.get("correct", "")).strip().lower() == "true" else 0
        except Exception:
            old_em_flag = 0
        try:
            old_f1_val = float(r.get("f1")) if r.get("f1") not in (None, "") else (1.0 if old_em_flag else 0.0)
        except (ValueError, TypeError):
            old_f1_val = float(old_em_flag)

        pred = extract_hotpotqa_answer(resp)
        is_correct = hotpotqa_check_correct(pred, gt)
        f1 = hotpotqa_compute_f1(pred, gt)

        old_correct += old_em_flag
        new_correct += 1 if is_correct else 0
        old_f1_sum += old_f1_val
        new_f1_sum += f1
        if (str(r.get("predicted", "")) != pred or
                (str(r.get("correct", "")).strip().lower() == "true") != is_correct):
            changed += 1
        r["predicted"] = pred
        r["correct"] = str(bool(is_correct))
        r["f1"] = f"{f1:.6f}"

    prov = {
        "file": path.name,
        "n_scored": n_scored,
        "truncated_skipped": truncated,
        "rows_changed": changed,
        "em_old": round(100 * old_correct / n_scored, 2) if n_scored else None,
        "em_new": round(100 * new_correct / n_scored, 2) if n_scored else None,
        "f1_old": round(100 * old_f1_sum / n_scored, 2) if n_scored else None,
        "f1_new": round(100 * new_f1_sum / n_scored, 2) if n_scored else None,
    }
    if n_scored == 0:
        prov["status"] = "SKIPPED (no scorable verifier rows; likely truncated/legacy)"
        return prov

    if dry_run:
        prov["status"] = "DRY-RUN (no files written)"
        return prov

    # Back up original (once) then rewrite with the (possibly extended) schema.
    backup = path.with_suffix(".prev.csv")
    if not backup.exists():
        backup.write_bytes(path.read_bytes())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})

    # Regenerate stats JSON (offline) from the rewritten rows.
    _write_stats(path, rows)
    prov["status"] = "REWRITTEN"
    prov["backup"] = backup.name
    return prov


def _write_stats(path: Path, rows: list[dict]):
    """Regenerate <name>_stats.json from per-problem aggregation of the rewritten rows."""
    name = path.stem
    tier = _tier_of(name)
    by_key = {}
    for r in rows:
        try:
            pid = int(float(r.get("problem_id", "")))
        except (ValueError, TypeError):
            continue
        by_key[(pid, (r.get("agent_role") or "").strip())] = r
    pids = sorted({p for (p, _) in by_key})
    results = []
    for pid in pids:
        v = by_key.get((pid, "verifier"))
        if v is None or "[ERROR]" in str(v.get("response_text", "")):
            continue
        if not {"analyzer", "solver", "verifier"}.issubset({rr for (pp, rr) in by_key if pp == pid}):
            continue
        rec = {"problem_id": pid,
               "correct": str(v.get("correct", "")).strip().lower() == "true",
               "total_cost": 0.0, "total_input_tokens": 0,
               "total_output_tokens": 0, "total_latency": 0.0}
        fv = v.get("f1")
        if fv not in (None, ""):
            try:
                rec["f1"] = float(fv)
            except (ValueError, TypeError):
                pass
        for role in ("analyzer", "solver", "verifier"):
            rr = by_key.get((pid, role))
            if rr:
                rec["total_cost"] += float(rr.get("cost_usd", 0) or 0)
                rec["total_input_tokens"] += int(float(rr.get("input_tokens", 0) or 0))
                rec["total_output_tokens"] += int(float(rr.get("output_tokens", 0) or 0))
                rec["total_latency"] += float(rr.get("latency_s", 0) or 0)
        results.append(rec)
    stats = compute_experiment_stats(results)
    stats.update({"tier": tier, "model": MODEL_CONFIG[tier]["name"] if tier else "?",
                  "experiment_id": name, "n_problems": len(results),
                  "note": "Recomputed by scripts/recompute_metrics.py (canonical Markdown-robust extractor)."})
    (path.parent / f"{name}_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Offline-first recompute of baseline EM/F1 with the canonical extractor.")
    ap.add_argument("--use-hf", action="store_true", help="Backfill legacy CSVs lacking ground_truth via the HF dataset.")
    ap.add_argument("--dry-run", action="store_true", help="Report changes without writing.")
    args = ap.parse_args()

    hf_cache: dict[str, dict[int, str]] = {}
    if args.use_hf:
        from datasets import load_dataset
        for ds, (hid, cfg, split) in HF_SPECS.items():
            print(f"Loading {hid} [{cfg}/{split}] for ground-truth backfill ...")
            data = list(load_dataset(hid, cfg, split=split))
            hf_cache[ds] = {i: str(item["answer"]) for i, item in enumerate(data)}

    provenance = {"dry_run": args.dry_run, "cells": []}
    base = RESULTS_DIR / "baselines"
    print("=" * 90)
    print(f"{'cell':<34}{'N':>4}{'EM old->new':>16}{'F1 old->new':>16}  status")
    print("-" * 90)
    for csv_path in sorted(base.glob("*.csv")):
        if csv_path.name.endswith(".prev.csv"):
            continue
        ds = _dataset_of(csv_path.stem)
        if ds is None:
            continue  # gsm8k or unknown -> skip
        hf_answers = hf_cache.get(ds) if args.use_hf else None
        prov = recompute_csv(csv_path, hf_answers, args.dry_run)
        if prov is None:
            continue
        provenance["cells"].append(prov)
        em = (f"{prov.get('em_old')}->{prov.get('em_new')}" if prov.get("em_old") is not None else "-")
        f1 = (f"{prov.get('f1_old')}->{prov.get('f1_new')}" if prov.get("f1_old") is not None else "-")
        print(f"{csv_path.stem:<34}{prov.get('n_scored', 0):>4}{em:>16}{f1:>16}  {prov.get('status', '')}")

    if not args.dry_run:
        out = RESULTS_DIR / "recompute_provenance.json"
        out.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
        print("-" * 90)
        print(f"Provenance -> {out}")
        print("Next: python scripts/validate_baselines.py && python aggregate_results.py")


if __name__ == "__main__":
    main()
