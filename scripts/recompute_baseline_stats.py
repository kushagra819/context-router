"""
Recompute baseline stats JSONs from the CSV source of truth.
Also triggers validate_baselines.py and aggregate_results.py to ensure
all master validation and master results files are fully updated and synchronized.
"""
import sys
import csv
import json
import re
import string
from pathlib import Path
from collections import Counter

# Set field size limit for large verifier responses
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_ROOT / "results" / "baselines"

DATASETS = ["gsm8k", "hotpotqa", "musique"]
TIERS = [1, 2, 3, 4]
EXPECTED_ROLES = {"analyzer", "solver", "verifier"}

MODEL_NAMES = {
    1: "Gemma 4 E4B",
    2: "Llama 3.3 70B",
    3: "Llama 3.1 405B (GitHub)",
    4: "GPT-4.1 (GitHub)",
}

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

def compute_stats_from_csv(csv_path: Path, dataset: str, tier: int):
    if not csv_path.exists():
        return None
    
    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        for row in reader:
            rows.append(row)
            
    has_gt_cols = "ground_truth" in columns and "predicted" in columns
    has_f1_col = "f1" in columns
    
    by_key = {}
    for row in rows:
        try:
            pid = int(float(row.get("problem_id", "")))
        except (ValueError, TypeError):
            continue
        role = (row.get("agent_role") or "").strip()
        by_key[(pid, role)] = row
        
    pids = sorted({pid for (pid, _) in by_key})
    
    complete_pids = []
    correct_count = 0
    f1_sum, f1_n = 0.0, 0
    total_cost = 0.0
    total_tokens = 0
    total_latency = 0.0
    
    for pid in pids:
        roles_present = {r for (p, r) in by_key if p == pid}
        if not EXPECTED_ROLES.issubset(roles_present):
            continue
        vrow = by_key.get((pid, "verifier"))
        if vrow is None:
            continue
        resp = str(vrow.get("response_text", ""))
        if "[ERROR]" in resp:
            continue
            
        complete_pids.append(pid)
        
        if str(vrow.get("correct", "")).strip().lower() == "true":
            correct_count += 1
            
        # Cost / tokens / latency across all roles of this problem.
        for role in EXPECTED_ROLES:
            r = by_key.get((pid, role))
            if not r:
                continue
            try:
                total_cost += float(r.get("cost_usd", 0) or 0)
                total_tokens += int(float(r.get("input_tokens", 0) or 0)) + int(float(r.get("output_tokens", 0) or 0))
                total_latency += float(r.get("latency_s", 0) or 0)
            except (ValueError, TypeError):
                pass
                
        # F1 calculation
        if dataset != "gsm8k":
            if has_gt_cols:
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
            elif has_f1_col:
                # If there are no GT/predicted columns, but there is f1 column
                f1_val = vrow.get("f1")
                if f1_val not in (None, ""):
                    try:
                        f1_sum += float(f1_val)
                        f1_n += 1
                    except (ValueError, TypeError):
                        pass

    n = len(complete_pids)
    if n == 0:
        return None
        
    accuracy = round(correct_count / n * 100, 2)
    avg_cost = round(total_cost / n, 6)
    avg_tokens = round(total_tokens / n, 1)
    avg_latency = round(total_latency / n, 2)
    
    stats = {
        "total_problems": n,
        "correct": correct_count,
        "accuracy": accuracy,
        "total_cost_usd": round(total_cost, 6),
        "avg_cost_per_problem": avg_cost,
        "total_tokens": total_tokens,
        "avg_tokens_per_problem": avg_tokens,
        "total_latency_s": round(total_latency, 2),
        "avg_latency_per_problem": avg_latency,
    }
    
    if dataset != "gsm8k" and f1_n > 0:
        stats["avg_f1"] = round(f1_sum / f1_n * 100, 2)
        stats["note_f1"] = "F1 calculated from CSV is a conservative lower bound because verifier responses are truncated in the CSV."
        
    stats["tier"] = tier
    stats["model"] = MODEL_NAMES[tier]
    stats["experiment_id"] = f"{dataset}_baseline_tier{tier}"
    stats["note"] = f"Recomputed from CSV of size {len(rows)} rows. Found {len(pids)} unique problems."
    
    return stats

def check_and_update_json(json_path: Path, new_stats: dict) -> bool:
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            # Compare key metrics
            keys_to_compare = [
                "total_problems", "correct", "accuracy", 
                "total_cost_usd", "avg_cost_per_problem", 
                "total_tokens", "avg_tokens_per_problem", 
                "total_latency_s", "avg_latency_per_problem",
                "tier", "model", "experiment_id"
            ]
            if new_stats.get("avg_f1") is not None:
                keys_to_compare.append("avg_f1")
                
            mismatch = False
            for k in keys_to_compare:
                if existing.get(k) != new_stats.get(k):
                    print(f"Mismatch in {json_path.name} for '{k}': existing={existing.get(k)}, new={new_stats.get(k)}")
                    mismatch = True
                    break
            
            if not mismatch:
                # If no mismatch, don't change
                return False
        except Exception as e:
            print(f"Error reading existing JSON {json_path.name}: {e}. Will overwrite.")
            
    # Write new JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(new_stats, f, indent=2)
    return True

def main():
    print("Starting recomputation of baseline stats...")
    updated_files = []
    
    for dataset in DATASETS:
        for tier in TIERS:
            key = f"{dataset}_baseline_tier{tier}"
            csv_path = BASE_DIR / f"{key}.csv"
            json_path = BASE_DIR / f"{key}_stats.json"
            
            if not csv_path.exists():
                continue
                
            stats = compute_stats_from_csv(csv_path, dataset, tier)
            if stats is None:
                print(f"Skipping {key} (no complete problems found in CSV).")
                continue
                
            was_updated = check_and_update_json(json_path, stats)
            if was_updated:
                print(f"Updated {json_path.name}")
                updated_files.append(json_path.name)
            else:
                print(f"Checked {json_path.name} (already correct, no change).")
                
    # Run baseline validation and results aggregation if any updates were made
    print("\nSynchronizing master files...")
    
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    sys.path.insert(0, str(PROJECT_ROOT))
    
    try:
        import validate_baselines
        import aggregate_results
    except ImportError as e:
        print(f"Could not import validation/aggregation scripts: {e}")
        return
        
    # Run validate_baselines
    print("Running validate_baselines.py...")
    backup_argv = sys.argv
    sys.argv = [sys.argv[0], "--quiet"]
    try:
        validate_baselines.main()
        print("  Updated baseline_validation.json")
    except Exception as e:
        print(f"Error running validate_baselines.py: {e}")
    finally:
        sys.argv = backup_argv
        
    # Run aggregate_results
    print("Running aggregate_results.py...")
    backup_argv = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        aggregate_results.main()
        print("  Updated master_results JSON/CSV/MD")
    except Exception as e:
        print(f"Error running aggregate_results.py: {e}")
    finally:
        sys.argv = backup_argv
        
    print("\nRecomputation and sync complete!")
    if updated_files:
        print(f"Updated JSON files: {', '.join(updated_files)}")
    else:
        print("No JSON files needed updating.")

if __name__ == "__main__":
    main()
