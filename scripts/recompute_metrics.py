"""
Recompute all baseline metrics from CSV truth-source files.

This script:
1. Reads each baseline CSV
2. Checks for completeness (200 unique problems, 3 agents each)
3. Handles duplicates (from resume runs)
4. Recomputes EM, F1, cost, latency, token counts
5. Compares against stored stats JSON
6. Outputs a validation report

Usage:
    python scripts/recompute_metrics.py
"""

import os
import sys
import csv
import json
import re
import string
from collections import Counter
from pathlib import Path

BASELINES_DIR = Path(__file__).parent.parent / "results" / "baselines"
EXPECTED_PROBLEMS = 200

# ── Metric functions (copied from src/evaluation/metrics.py for standalone use) ──

def normalize_answer(s: str) -> str:
    if not s:
        return ""
    def remove_articles(text): return re.sub(r'\b(a|an|the)\b', ' ', text)
    def white_space_fix(text): return ' '.join(text.split())
    def remove_punc(text): return ''.join(ch for ch in text if ch not in set(string.punctuation))
    def lower(text): return text.lower()
    return white_space_fix(remove_articles(remove_punc(lower(s))))


def compute_f1(predicted: str, ground_truth: str) -> float:
    if not predicted or not ground_truth:
        return 0.0
    pred_tokens = normalize_answer(predicted).split()
    gold_tokens = normalize_answer(ground_truth).split()
    if len(pred_tokens) == 0 or len(gold_tokens) == 0:
        return 1.0 if pred_tokens == gold_tokens else 0.0
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(gold_tokens)
    return (2 * precision * recall) / (precision + recall)


def extract_final_answer(text: str) -> str:
    """Extract 'Final Answer: ...' from verifier output."""
    if not text:
        return ""
    match = re.search(r"[Ff]inal\s*[Aa]nswer\s*[:\-]\s*(.*)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(r"answer\s+is\s*[:\-]?\s*(.*)$", text, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        return lines[-1].strip(".")
    return text.strip()


def extract_gsm8k_answer(text: str):
    if not text:
        return None
    match = re.search(r"[Ff]inal\s*[Aa]nswer\s*[:\-]\s*\$?\s*([\-\d,\.]+)", text)
    if match:
        return _clean_number(match.group(1))
    match = re.search(r"####\s*([\-\d,\.]+)", text)
    if match:
        return _clean_number(match.group(1))
    match = re.search(r"answer\s+is\s*[:\-]?\s*\$?\s*([\-\d,\.]+)", text, re.IGNORECASE)
    if match:
        return _clean_number(match.group(1))
    match = re.search(r"=\s*\$?\s*([\-\d,\.]+)\s*$", text, re.MULTILINE)
    if match:
        return _clean_number(match.group(1))
    numbers = re.findall(r"[\-\d,\.]+", text)
    if numbers:
        return _clean_number(numbers[-1])
    return None


def _clean_number(num_str: str) -> str:
    cleaned = num_str.replace(",", "").strip(".")
    try:
        num = float(cleaned)
        if num == int(num):
            return str(int(num))
        return str(num)
    except ValueError:
        return cleaned


def gsm8k_check_correct(predicted, ground_truth):
    if predicted is None or ground_truth is None:
        return False
    try:
        return abs(float(predicted) - float(ground_truth)) < 1e-6
    except ValueError:
        return predicted.strip() == ground_truth.strip()


# ── CSV Processing ──

def process_csv(csv_path: Path) -> dict:
    """Process a single baseline CSV and compute metrics."""
    fname = csv_path.name
    dataset = None
    tier = None
    
    # Parse filename
    if "gsm8k" in fname:
        dataset = "gsm8k"
    elif "hotpotqa" in fname:
        dataset = "hotpotqa"
    elif "musique" in fname:
        dataset = "musique"
    
    match = re.search(r"tier(\d)", fname)
    if match:
        tier = int(match.group(1))
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Group by problem_id, keeping only the LAST occurrence of each (problem_id, agent_role) pair
    # This handles duplicates from resume runs
    problem_data = {}
    for row in rows:
        pid = int(row["problem_id"])
        role = row["agent_role"]
        key = (pid, role)
        problem_data[key] = row  # Last one wins
    
    # Reconstruct per-problem records
    unique_pids = sorted(set(pid for (pid, _) in problem_data.keys()))
    
    results = {
        "file": fname,
        "dataset": dataset,
        "tier": tier,
        "total_rows_in_csv": len(rows),
        "unique_problems": len(unique_pids),
        "problem_id_range": f"{min(unique_pids)}-{max(unique_pids)}" if unique_pids else "N/A",
        "duplicate_rows": len(rows) - len(problem_data),
    }
    
    # Check completeness
    expected_roles = {"analyzer", "solver", "verifier"}
    complete_problems = 0
    incomplete_problems = []
    
    for pid in unique_pids:
        roles_present = {role for (p, role) in problem_data.keys() if p == pid}
        if roles_present >= expected_roles:
            complete_problems += 1
        else:
            incomplete_problems.append((pid, roles_present))
    
    results["complete_problems"] = complete_problems
    results["incomplete_problems"] = len(incomplete_problems)
    if incomplete_problems:
        results["incomplete_details"] = [(pid, list(roles)) for pid, roles in incomplete_problems[:5]]
    
    # Compute metrics
    correct_count = 0
    total_f1 = 0.0
    total_cost = 0.0
    total_tokens = 0
    total_latency = 0.0
    error_count = 0
    
    for pid in unique_pids:
        verifier_key = (pid, "verifier")
        if verifier_key not in problem_data:
            error_count += 1
            continue
        
        verifier_row = problem_data[verifier_key]
        response = str(verifier_row.get("response_text", ""))
        
        # Check for errors
        if "[ERROR]" in response:
            error_count += 1
            continue
        
        # Correctness (from CSV 'correct' column)
        is_correct = str(verifier_row.get("correct", "")).lower() == "true"
        if is_correct:
            correct_count += 1
        
        # Cost, tokens, latency (sum across all 3 agents for this problem)
        for role in expected_roles:
            key = (pid, role)
            if key in problem_data:
                row = problem_data[key]
                try:
                    total_cost += float(row.get("cost_usd", 0))
                    total_tokens += int(row.get("input_tokens", 0)) + int(row.get("output_tokens", 0))
                    total_latency += float(row.get("latency_s", 0))
                except (ValueError, TypeError):
                    pass
    
    valid_problems = complete_problems - error_count
    results["valid_problems"] = valid_problems
    results["error_problems"] = error_count
    results["correct"] = correct_count
    results["em_accuracy"] = round(correct_count / valid_problems * 100, 2) if valid_problems > 0 else 0
    results["total_cost_usd"] = round(total_cost, 6)
    results["avg_cost_per_problem"] = round(total_cost / valid_problems, 6) if valid_problems > 0 else 0
    results["total_tokens"] = total_tokens
    results["avg_tokens_per_problem"] = round(total_tokens / valid_problems, 1) if valid_problems > 0 else 0
    results["total_latency_s"] = round(total_latency, 2)
    results["avg_latency_per_problem"] = round(total_latency / valid_problems, 2) if valid_problems > 0 else 0
    
    # Note: F1 cannot be recomputed without ground truth answers from the dataset
    # We can only report EM from the 'correct' column in the CSV
    
    return results


def load_stats_json(csv_path: Path) -> dict | None:
    """Load the corresponding stats JSON for comparison."""
    stats_path = csv_path.with_suffix("").with_suffix("") 
    # Actually: same name but _stats.json
    stats_name = csv_path.stem + "_stats.json"
    stats_path = csv_path.parent / stats_name
    if stats_path.exists():
        with open(stats_path, "r") as f:
            return json.load(f)
    return None


def compare_metrics(recomputed: dict, stored: dict) -> list:
    """Compare recomputed vs stored metrics, return list of mismatches."""
    mismatches = []
    
    comparisons = [
        ("correct", "correct", "Correct count"),
        ("em_accuracy", "accuracy", "EM/Accuracy %"),
        ("total_cost_usd", "total_cost_usd", "Total cost"),
        ("total_tokens", "total_tokens", "Total tokens"),
    ]
    
    for recomp_key, stored_key, label in comparisons:
        rv = recomputed.get(recomp_key)
        sv = stored.get(stored_key)
        if rv is not None and sv is not None:
            if isinstance(rv, float) and isinstance(sv, float):
                if abs(rv - sv) > 0.01:
                    mismatches.append(f"{label}: recomputed={rv}, stored={sv}")
            elif rv != sv:
                mismatches.append(f"{label}: recomputed={rv}, stored={sv}")
    
    # Check for F1 < EM bug
    stored_f1 = stored.get("avg_f1")
    stored_em = stored.get("accuracy")
    if stored_f1 is not None and stored_em is not None:
        if stored_f1 < stored_em:
            mismatches.append(f"🐛 BUG: Stored F1 ({stored_f1}%) < EM ({stored_em}%) — mathematically impossible")
    
    return mismatches


def main():
    print("=" * 70)
    print("  BASELINE CSV VALIDATION & METRIC RECOMPUTATION")
    print("=" * 70)
    print()
    
    csv_files = sorted(BASELINES_DIR.glob("*.csv"))
    
    all_results = []
    all_mismatches = {}
    
    for csv_path in csv_files:
        print(f"Processing: {csv_path.name}")
        print("-" * 50)
        
        result = process_csv(csv_path)
        all_results.append(result)
        
        # Print summary
        status = "✅" if result["complete_problems"] >= EXPECTED_PROBLEMS else "⚠️"
        print(f"  {status} Unique problems: {result['unique_problems']}")
        print(f"  Complete: {result['complete_problems']}, Errors: {result['error_problems']}")
        if result["duplicate_rows"] > 0:
            print(f"  ⚠️ Duplicate rows (from resume): {result['duplicate_rows']}")
        print(f"  EM Accuracy: {result['em_accuracy']}% ({result['correct']}/{result['valid_problems']})")
        print(f"  Total cost: ${result['total_cost_usd']:.4f}")
        print(f"  Total tokens: {result['total_tokens']:,}")
        print(f"  Avg latency: {result['avg_latency_per_problem']:.1f}s")
        
        # Compare with stored stats
        stored = load_stats_json(csv_path)
        if stored:
            mismatches = compare_metrics(result, stored)
            if mismatches:
                all_mismatches[csv_path.name] = mismatches
                print(f"  ❌ MISMATCHES with stored JSON:")
                for m in mismatches:
                    print(f"     - {m}")
            else:
                print(f"  ✅ Matches stored JSON")
        else:
            print(f"  ⚠️ No stats JSON found")
        
        print()
    
    # Summary
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    
    complete_count = sum(1 for r in all_results if r["complete_problems"] >= EXPECTED_PROBLEMS)
    print(f"\n  Complete baselines: {complete_count}/{len(all_results)}")
    
    if all_mismatches:
        print(f"\n  Files with JSON mismatches: {len(all_mismatches)}")
        for fname, ms in all_mismatches.items():
            print(f"    {fname}:")
            for m in ms:
                print(f"      - {m}")
    else:
        print(f"\n  ✅ All stored JSONs match recomputed metrics")
    
    # Check for reruns needed
    reruns_needed = [r for r in all_results if r["complete_problems"] < EXPECTED_PROBLEMS]
    if reruns_needed:
        print(f"\n  ⚠️ RERUNS NEEDED:")
        for r in reruns_needed:
            print(f"    {r['file']}: only {r['complete_problems']}/{EXPECTED_PROBLEMS} complete")
    else:
        print(f"\n  ✅ No reruns needed — all baselines have {EXPECTED_PROBLEMS}+ complete problems")
    
    # Output as JSON for programmatic use
    output_path = BASELINES_DIR.parent / "baseline_validation.json"
    output = {
        "validation_timestamp": __import__("datetime").datetime.now().isoformat(),
        "results": all_results,
        "mismatches": {k: v for k, v in all_mismatches.items()},
        "reruns_needed": [r["file"] for r in reruns_needed] if reruns_needed else [],
        "all_complete": len(reruns_needed) == 0,
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Full report saved to: {output_path}")
    
    print()


if __name__ == "__main__":
    main()
