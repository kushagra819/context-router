"""
validate_baselines.py
=====================
Canonical, OFFLINE baseline validator. CSV files are the single source of truth
(see docs/DECISIONS/ADR-001-Baseline-Truth-Source.md).

This script:
  1. Scans both results/baselines/ (active) and results/baselines_backup/ (legacy).
  2. De-duplicates rows by (problem_id, agent_role), keeping the LAST attempt
     (handles resume artifacts).
  3. Reports per CSV: total rows, unique problems, complete problems, missing IDs,
     duplicate IDs, error rows, and verifier truncation rate.
  4. Recomputes Exact Match (EM) from the CSV `correct` column (always reliable —
     it is computed at run time from the full, untruncated response).
  5. Recomputes token-level F1 ONLY if the CSV contains `ground_truth` + `predicted`
     columns (new-format runs). Legacy CSVs lack them, so F1 is marked "pending".
  6. Aggregates cost / tokens / latency per problem.
  7. Picks the BEST AVAILABLE source per (dataset, tier): a complete active CSV if
     one exists, otherwise the backup.
  8. Writes a machine-readable report to results/baseline_validation.json.

Pure standard library. No network, no API calls, ASCII-only output (Windows-safe).
Run from anywhere:  python scripts/validate_baselines.py
"""

import argparse
import csv
import json
import re
import string
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Allow large response_text fields.
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ACTIVE_DIR = PROJECT_ROOT / "results" / "baselines"
BACKUP_DIR = PROJECT_ROOT / "results" / "baselines_backup"
OUTPUT_JSON = PROJECT_ROOT / "results" / "baseline_validation.json"

DATASETS = ["gsm8k", "hotpotqa", "musique"]
TIERS = [1, 2, 3, 4]
EXPECTED_PROBLEMS = 200
EXPECTED_ROLES = {"analyzer", "solver", "verifier"}

MODEL_NAMES = {
    1: "Gemma 4 E4B",
    2: "Llama 3.3 70B",
    3: "GPT-OSS 120B (Groq)",
    4: "GPT-4.1 (GitHub)",
}


# --------------------------------------------------------------------------- #
# Metric helpers (self-contained copies of src/evaluation/metrics.py so this
# validator runs even when third-party deps are missing).
# --------------------------------------------------------------------------- #
def normalize_answer(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def compute_f1(predicted: str, ground_truth: str) -> float:
    if not predicted or not ground_truth:
        return 0.0
    pred_tokens = normalize_answer(predicted).split()
    gold_tokens = normalize_answer(ground_truth).split()
    if not pred_tokens or not gold_tokens:
        return 1.0 if pred_tokens == gold_tokens else 0.0
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return (2 * precision * recall) / (precision + recall)


def has_final_answer(text: str) -> bool:
    """Heuristic truncation check: does a verifier response end with an answer marker?"""
    if not text:
        return False
    return bool(re.search(r"([Ff]inal\s*[Aa]nswer|answer\s+is)\s*[:\-]?\s*\S", text))


# --------------------------------------------------------------------------- #
# CSV analysis
# --------------------------------------------------------------------------- #
def analyze_csv(csv_path: Path, dataset: str) -> dict:
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    has_gt_cols = "ground_truth" in columns and "predicted" in columns
    has_f1_col = "f1" in columns

    # De-duplicate by (problem_id, agent_role); last attempt wins.
    by_key = {}
    raw_role_counter = Counter()
    for row in rows:
        try:
            pid = int(float(row.get("problem_id", "")))
        except (ValueError, TypeError):
            continue
        role = (row.get("agent_role") or "").strip()
        raw_role_counter[role] += 1
        by_key[(pid, role)] = row

    pids = sorted({pid for (pid, _) in by_key})
    duplicate_rows = len(rows) - len(by_key)

    complete_pids, error_pids = [], []
    correct_count = 0
    f1_sum, f1_n = 0.0, 0
    total_cost = total_in = total_out = 0
    total_latency = 0.0
    verifier_total = verifier_with_answer = 0

    for pid in pids:
        roles_present = {r for (p, r) in by_key if p == pid}
        if not EXPECTED_ROLES.issubset(roles_present):
            continue
        vrow = by_key.get((pid, "verifier"))
        if vrow is None:
            continue
        resp = str(vrow.get("response_text", ""))
        if "[ERROR]" in resp:
            error_pids.append(pid)
            continue

        complete_pids.append(pid)

        verifier_total += 1
        if dataset != "gsm8k" and has_final_answer(resp):
            verifier_with_answer += 1
        elif dataset == "gsm8k":
            verifier_with_answer += 1  # not used for gsm8k truncation

        # EM from the authoritative `correct` column.
        if str(vrow.get("correct", "")).strip().lower() == "true":
            correct_count += 1

        # F1 only when the CSV carries ground truth + prediction.
        if dataset != "gsm8k" and has_gt_cols:
            gt = str(vrow.get("ground_truth", ""))
            pred = str(vrow.get("predicted", ""))
            if has_f1_col and (vrow.get("f1") not in (None, "")):
                try:
                    f1_sum += float(vrow["f1"])
                    f1_n += 1
                except (ValueError, TypeError):
                    f1_sum += compute_f1(pred, gt)
                    f1_n += 1
            else:
                f1_sum += compute_f1(pred, gt)
                f1_n += 1

        # Cost / tokens / latency across all roles of this problem.
        for role in EXPECTED_ROLES:
            r = by_key.get((pid, role))
            if not r:
                continue
            try:
                total_cost += float(r.get("cost_usd", 0) or 0)
                total_in += int(float(r.get("input_tokens", 0) or 0))
                total_out += int(float(r.get("output_tokens", 0) or 0))
                total_latency += float(r.get("latency_s", 0) or 0)
            except (ValueError, TypeError):
                pass

    n = len(complete_pids)
    missing = sorted(set(range(EXPECTED_PROBLEMS)) - set(pids))
    trunc_rate = (
        round((verifier_total - verifier_with_answer) / verifier_total * 100, 1)
        if dataset != "gsm8k" and verifier_total else 0.0
    )

    return {
        "file": csv_path.name,
        "columns": list(columns),
        "has_ground_truth_cols": has_gt_cols,
        "size_bytes": csv_path.stat().st_size,
        "total_rows": len(rows),
        "unique_problems": len(pids),
        "complete_problems": n,
        "error_problems": len(error_pids),
        "duplicate_rows": duplicate_rows,
        "missing_count": len(missing),
        "missing_ids_preview": missing[:10],
        "em_accuracy": round(correct_count / n * 100, 2) if n else 0.0,
        "correct": correct_count,
        "f1": round(f1_sum / f1_n * 100, 2) if f1_n else None,
        "f1_status": "computed" if f1_n else "pending (no ground_truth/predicted columns)",
        "truncation_rate": trunc_rate,
        "total_cost_usd": round(total_cost, 6),
        "avg_cost_per_problem": round(total_cost / n, 6) if n else 0.0,
        "total_tokens": total_in + total_out,
        "avg_latency_per_problem": round(total_latency / n, 2) if n else 0.0,
    }


def empty_record(name: str) -> dict:
    return {"file": name, "exists": False, "complete_problems": 0}


def main():
    ap = argparse.ArgumentParser(description="Offline baseline CSV validator (source of truth).")
    ap.add_argument("--quiet", action="store_true", help="Suppress the per-file console table.")
    args = ap.parse_args()

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "expected_problems": EXPECTED_PROBLEMS,
        "active_dir": str(ACTIVE_DIR),
        "backup_dir": str(BACKUP_DIR),
        "cells": {},        # "dataset_tierN" -> best-available analysis
        "active": {},
        "backup": {},
        "needs_rerun": [],
        "locked": [],
    }

    for dataset in DATASETS:
        for tier in TIERS:
            key = f"{dataset}_baseline_tier{tier}"
            active_csv = ACTIVE_DIR / f"{key}.csv"
            backup_csv = BACKUP_DIR / f"{key}.csv"

            active = analyze_csv(active_csv, dataset) if active_csv.exists() else empty_record(active_csv.name)
            backup = analyze_csv(backup_csv, dataset) if backup_csv.exists() else empty_record(backup_csv.name)
            report["active"][key] = active
            report["backup"][key] = backup

            # Choose best available source.
            active_ok = active.get("complete_problems", 0) >= EXPECTED_PROBLEMS
            backup_ok = backup.get("complete_problems", 0) >= EXPECTED_PROBLEMS

            if active_ok:
                best, src = active, "active"
            elif active.get("complete_problems", 0) > 0:
                best, src = active, "active(partial)"
            elif backup_ok:
                best, src = backup, "backup"
            elif backup.get("complete_problems", 0) > 0:
                best, src = backup, "backup(partial)"
            else:
                report["cells"][key] = {"dataset": dataset, "tier": tier, "source": "MISSING",
                                        "model": MODEL_NAMES[tier], "complete_problems": 0,
                                        "status": "MISSING"}
                report["needs_rerun"].append(key)
                continue

            complete = best.get("complete_problems", 0) >= EXPECTED_PROBLEMS
            # GSM8K needs no F1; multi-hop needs F1 columns to be fully locked.
            f1_ready = dataset == "gsm8k" or best.get("f1_status") == "computed"
            status = "LOCKED" if (src == "active" and complete and f1_ready) else (
                "EM-ONLY (active complete, F1 pending)" if (src == "active" and complete) else
                "PARTIAL" if "partial" in src else
                "BACKUP (EM reliable, F1 unreliable/truncated)"
            )

            cell = {
                "dataset": dataset, "tier": tier, "model": MODEL_NAMES[tier],
                "source": src, "status": status,
                "complete_problems": best.get("complete_problems", 0),
                "em_accuracy": best.get("em_accuracy"),
                "f1": best.get("f1"), "f1_status": best.get("f1_status"),
                "total_cost_usd": best.get("total_cost_usd"),
                "avg_cost_per_problem": best.get("avg_cost_per_problem"),
                "avg_latency_per_problem": best.get("avg_latency_per_problem"),
                "truncation_rate": best.get("truncation_rate"),
                "duplicate_rows": best.get("duplicate_rows"),
            }
            report["cells"][key] = cell

            if status == "LOCKED":
                report["locked"].append(key)
            else:
                report["needs_rerun"].append(key)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if not args.quiet:
        print("=" * 92)
        print("  BASELINE VALIDATION  (CSV = source of truth; offline)")
        print("=" * 92)
        hdr = f"{'cell':<26}{'source':<18}{'N':>5}{'EM%':>8}{'F1%':>8}{'cost$':>10}{'trunc%':>8}  status"
        print(hdr)
        print("-" * 92)
        for key, c in report["cells"].items():
            if c["source"] == "MISSING":
                print(f"{key:<26}{'MISSING':<18}{0:>5}{'-':>8}{'-':>8}{'-':>10}{'-':>8}  MISSING")
                continue
            f1 = "-" if c["f1"] is None else f"{c['f1']:.1f}"
            print(f"{key:<26}{c['source']:<18}{c['complete_problems']:>5}"
                  f"{c['em_accuracy']:>8.1f}{f1:>8}{c['total_cost_usd']:>10.4f}"
                  f"{(c['truncation_rate'] or 0):>8.1f}  {c['status']}")
        print("-" * 92)
        print(f"  LOCKED       ({len(report['locked'])}): {', '.join(report['locked']) or 'none'}")
        print(f"  NEEDS WORK   ({len(report['needs_rerun'])}): {', '.join(report['needs_rerun']) or 'none'}")
        print(f"\n  Full machine-readable report -> {OUTPUT_JSON}")
    return report


if __name__ == "__main__":
    main()
