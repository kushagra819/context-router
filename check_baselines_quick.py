"""Quick baseline status check — prints actual CSV state."""
import sys, csv, os
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

BASE = Path(__file__).parent / "results" / "baselines"
BACKUP = Path(__file__).parent / "results" / "baselines_backup"
ROLES = ("analyzer", "solver", "verifier")
DATASETS = ("gsm8k", "hotpotqa", "musique")
TIERS = (1, 2, 3, 4)


def count_complete(path):
    """Count complete problems (all 3 roles, no [ERROR])."""
    if not path.exists():
        return 0, 0, 0, 0, False
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    total_rows = len(rows)
    # Group by problem_id
    by_pid = {}
    for r in rows:
        try:
            pid = int(float(r.get("problem_id", "")))
        except:
            continue
        role = (r.get("agent_role") or "").strip()
        by_pid.setdefault(pid, {})[role] = r

    complete = 0
    correct = 0
    has_f1 = False
    for pid, roles in by_pid.items():
        if set(ROLES).issubset(roles.keys()):
            vrow = roles.get("verifier", {})
            if "[ERROR]" not in str(vrow.get("response_text", "")):
                complete += 1
                if str(vrow.get("correct", "")).strip().lower() == "true":
                    correct += 1
                f1v = vrow.get("f1")
                if f1v not in (None, "", "None"):
                    has_f1 = True
    
    # Check response truncation
    max_resp_len = 0
    for r in rows:
        resp = r.get("response_text", "")
        if resp and len(resp) > max_resp_len:
            max_resp_len = len(resp)
    
    return total_rows, complete, correct, max_resp_len, has_f1


print(f"{'Cell':<25} {'Source':<8} {'Rows':>5} {'N':>4} {'EM%':>6} {'MaxResp':>8} {'F1?':>4}")
print("-" * 70)

for ds in DATASETS:
    for tier in TIERS:
        fname = f"{ds}_baseline_tier{tier}.csv"
        active = BASE / fname
        backup = BACKUP / fname
        
        # Check active
        a_rows, a_n, a_correct, a_max, a_f1 = count_complete(active)
        b_rows, b_n, b_correct, b_max, b_f1 = count_complete(backup)
        
        # Pick the one with more complete problems
        if a_n >= b_n and a_n > 0:
            src, rows, n, correct, mx, f1 = "active", a_rows, a_n, a_correct, a_max, a_f1
        elif b_n > 0:
            src, rows, n, correct, mx, f1 = "backup", b_rows, b_n, b_correct, b_max, b_f1
        else:
            src, rows, n, correct, mx, f1 = "MISSING", 0, 0, 0, 0, False
        
        em = round(correct / n * 100, 2) if n > 0 else 0
        cell = f"{ds}_t{tier}"
        trunc = "TRUNC" if mx <= 510 else f"{mx}"
        f1_str = "YES" if f1 else "no"
        print(f"{cell:<25} {src:<8} {rows:>5} {n:>4} {em:>5.1f}% {trunc:>8} {f1_str:>4}")
        
        # Also show other source if it exists
        if a_n > 0 and b_n > 0:
            other_src = "backup" if src == "active" else "active"
            other_n = b_n if src == "active" else a_n
            other_correct = b_correct if src == "active" else a_correct
            other_em = round(other_correct / other_n * 100, 2) if other_n > 0 else 0
            other_mx = b_max if src == "active" else a_max
            other_f1 = b_f1 if src == "active" else a_f1
            print(f"  {'(alt)':<22} {other_src:<8} {'':>5} {other_n:>4} {other_em:>5.1f}% {'TRUNC' if other_mx<=510 else str(other_mx):>8} {'YES' if other_f1 else 'no':>4}")
    print()
