"""
recompute_metrics_from_dataset.py
=================================
Backfill F1 for LEGACY baseline CSVs that lack the `ground_truth`/`predicted`
columns, by re-loading the HF datasets and re-extracting predictions from the
stored verifier `response_text`. Writes corrected `*_stats.json` files.

When NOT to use this: new-schema CSVs (produced by run_experiment.py) already carry
ground_truth/predicted/f1, so `scripts/validate_baselines.py` and
`aggregate_results.py` compute everything OFFLINE — no dataset reload needed. Use
this script only for the older truncated/legacy CSVs.

Caveat: F1 from a TRUNCATED CSV is unreliable (the answer span may be cut off). The
script flags high truncation and sets F1 to null rather than emit a misleading value.

Requires: datasets, pandas. ASCII-only output (Windows-safe).
Usage: python scripts/recompute_metrics_from_dataset.py
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.metrics import (
    extract_hotpotqa_answer, hotpotqa_compute_f1, compute_experiment_stats,
)
from src.evaluation.csv_io import per_problem_records, read_rows, dedup_by_problem_role
from src.utils.config import RESULTS_DIR, MODEL_CONFIG

DATASETS = {
    "gsm8k": ("openai/gsm8k", "main", "test"),
    "hotpotqa": ("hotpotqa/hotpot_qa", "distractor", "validation"),
    "musique": ("bdsaglam/musique", "answerable", "validation"),
}


def _final_answer_present(text: str) -> bool:
    return bool(re.search(r"([Ff]inal\s*[Aa]nswer|answer\s+is)\s*[:\-]?\s*\S", text or ""))


def main():
    from datasets import load_dataset  # heavy import; only here

    baselines = RESULTS_DIR / "baselines"
    csvs = sorted(baselines.glob("*.csv"))
    if not csvs:
        print("No baseline CSVs found.")
        return

    cache = {}
    print(f"Found {len(csvs)} CSVs in {baselines}\n")
    for csv_path in csvs:
        name = csv_path.stem
        dataset = next((d for d in DATASETS if d in name), None)
        tier = next((t for t in (1, 2, 3, 4) if f"tier{t}" in name), None)
        if not dataset or not tier:
            print(f"  skip {name}: cannot parse dataset/tier")
            continue

        if dataset not in cache:
            hid, cfg, split = DATASETS[dataset]
            print(f"Loading {hid} [{cfg}/{split}] ...")
            cache[dataset] = list(load_dataset(hid, cfg, split=split))
        ds = cache[dataset]

        rows = dedup_by_problem_role(read_rows(csv_path))
        pids = sorted({p for (p, _) in rows})
        results, trunc = [], 0
        for pid in pids:
            v = rows.get((pid, "verifier"))
            if v is None or "[ERROR]" in str(v.get("response_text", "")) or pid >= len(ds):
                continue
            is_correct = str(v.get("correct", "")).strip().lower() == "true"
            rec = {"problem_id": pid, "correct": is_correct,
                   "total_cost": 0.0, "total_input_tokens": 0,
                   "total_output_tokens": 0, "total_latency": 0.0}
            for role in ("analyzer", "solver", "verifier"):
                r = rows.get((pid, role))
                if r:
                    rec["total_cost"] += float(r.get("cost_usd", 0) or 0)
                    rec["total_input_tokens"] += int(float(r.get("input_tokens", 0) or 0))
                    rec["total_output_tokens"] += int(float(r.get("output_tokens", 0) or 0))
                    rec["total_latency"] += float(r.get("latency_s", 0) or 0)
            if dataset != "gsm8k":
                resp = str(v.get("response_text", ""))
                if not _final_answer_present(resp):
                    trunc += 1
                gt = ds[pid]["answer"]
                rec["f1"] = 1.0 if is_correct else hotpotqa_compute_f1(extract_hotpotqa_answer(resp), gt)
            results.append(rec)

        stats = compute_experiment_stats(results)
        stats.update({"tier": tier, "model": MODEL_CONFIG[tier]["name"],
                      "experiment_id": name, "n_problems": len(results)})
        trunc_rate = (trunc / len(results) * 100) if results else 0
        if dataset != "gsm8k" and trunc_rate > 30:
            stats["avg_f1"] = None
            stats["note_f1"] = (f"F1 nulled: {trunc_rate:.0f}% of verifier responses are "
                                f"truncated; re-run with run_experiment.py for valid F1.")
        out = baselines / f"{name}_stats.json"
        out.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        f1s = stats.get("avg_f1")
        print(f"  {name:30} N={len(results):3}  EM={stats['accuracy']:.1f}%  "
              f"F1={f1s if f1s is not None else 'null':>6}  trunc={trunc_rate:.0f}%")

    print("\nDone. For new-schema CSVs prefer: python scripts/validate_baselines.py")


if __name__ == "__main__":
    main()
