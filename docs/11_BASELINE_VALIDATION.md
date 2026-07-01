# Baseline Validation Report

> **Date:** 2026-06-22
> **Method:** Direct CSV file inspection
> **Tool:** `scripts/verify_baseline_integrity.py`

---

## 1. CSV Inventory

### Active (`results/baselines/`)

| File | Size | Rows | Unique Problems | Complete? |
|------|:----:|:----:|:---------------:|:---------:|
| `gsm8k_baseline_tier1.csv` | 389 KB | 627 | **200** | ✅ |
| `gsm8k_baseline_tier2.csv` | 379 KB | 600 | **200** | ✅ |
| `gsm8k_baseline_tier3.csv` | 383 KB | 600 | **200** | ✅ |
| `gsm8k_baseline_tier4.csv` | 364 KB | 600 | **200** | ✅ |
| `hotpotqa_baseline_tier1.csv` | 380 KB | 600 | **200** | ✅ |
| `hotpotqa_baseline_tier2.csv` | 448 KB | 304 | **~101** | ❌ Partial re-run |
| `musique_baseline_tier1.csv` | 360 KB | 600 | **200** | ✅ |

### Backup (`results/baselines_backup/`) — Old truncated-log versions

| File | Size | Rows | Unique Problems | EM Valid? | F1 Valid? |
|------|:----:|:----:|:---------------:|:---------:|:---------:|
| `hotpotqa_baseline_tier2.csv` | 388 KB | 601 | **200** | ✅ | ❌ Truncated |
| `hotpotqa_baseline_tier3.csv` | 384 KB | 600 | **200** | ✅ | ❌ Truncated |
| `hotpotqa_baseline_tier4.csv` | 383 KB | 600 | **200** | ✅ | ❌ Truncated |
| `musique_baseline_tier2.csv` | 386 KB | 600 | **200** | ✅ | ❌ Truncated |
| `musique_baseline_tier3.csv` | 383 KB | 600 | **200** | ✅ | ❌ Truncated |
| `musique_baseline_tier4.csv` | 378 KB | 597 | **199** | ✅ | ❌ Truncated |

---

## 2. Truncation Bug Explanation

### Root Cause
The `ExperimentLogger.log_call()` in `src/utils/logger.py` contained:
```python
"response_text": response_text.replace("\n", " ")[:500]
```
The `[:500]` truncation destroyed verifier responses, which typically exceed 500 characters. The `Final Answer:` pattern — which appears at the END of verifier output — was cut off.

### Fix Applied
Removed the `[:500]` slice. Now logs full response text:
```python
"response_text": response_text.replace("\n", " ")
```

### Impact
- **EM (Exact Match):** UNAFFECTED — EM was computed at runtime before logging
- **F1 Score:** AFFECTED — F1 requires extracting the predicted answer from `response_text` in the CSV. With truncated text, answer extraction fails or returns incomplete text, yielding artificially low F1.
- **Symptom:** Stats JSONs showed F1 < EM, which is mathematically impossible (F1 ≥ EM by definition).

---

## 3. Stats JSON Anomalies

### GSM8K — All Clean ✅
All 4 stats JSONs have `"note": "Recomputed from CSV..."` → already recomputed from CSVs.

### HotpotQA Tier 1 — Clean with caveat
```json
"avg_f1": 64.41,
"note_f1": "F1 calculated from CSV is a conservative lower bound because verifier responses are truncated in the CSV."
```
This Tier 1 was run without resume (no truncation bug in the runner itself), but the logger still truncated. F1=64.4% vs EM=63.0% is plausible (F1 > EM ✅).

### HotpotQA Tier 2 (backup)
```json
"accuracy": 63.0, "avg_f1": 63.0
```
F1 = EM exactly → suspicious (F1 should be ≥ EM but typically higher). Likely truncation artifact making F1 collapse to EM.

### HotpotQA Tier 2 (active re-run)
```json
"total_problems": 101, "accuracy": 64.36, "avg_f1": 77.9
```
Only 101 problems complete. F1=77.9% > EM=64.4% ✅ — consistent, no truncation.

### Backup F1 < EM violations
| Experiment | EM | F1 | Violation? |
|-----------|:---:|:---:|:---------:|
| HotpotQA T2 backup | 63.0% | 63.0% | ⚠️ Suspicious (equals) |
| HotpotQA T3 backup | 57.0% | 60.6% | ✅ OK |
| HotpotQA T4 backup | 37.5% | 40.1% | ✅ OK |
| MuSiQue T2 backup | 55.0% | 55.0% | ⚠️ Suspicious (equals) |
| MuSiQue T3 backup | 47.5% | 50.9% | ✅ OK |
| MuSiQue T4 backup | 25.6% | 29.4% | ✅ OK |

The original audit flagged F1 < EM from raw JSON stats. The recomputed backup stats show F1 ≥ EM, but the values are "conservative lower bounds" — likely depressed by truncation.

---

## 4. Decision

**Action taken:** Re-run all 5 incomplete/truncated baselines with the fixed logger.

| Baseline | Action | Why |
|----------|--------|-----|
| HotpotQA T2 | Complete re-run (200 problems fresh) | Only 101 done |
| HotpotQA T3 | Fresh re-run | Truncated F1 in backup |
| HotpotQA T4 | Fresh re-run | Truncated F1 + suspiciously low EM |
| MuSiQue T2 | Fresh re-run | Truncated F1 in backup |
| MuSiQue T3 | Fresh re-run | Truncated F1 in backup |
| MuSiQue T4 | Fresh re-run | Truncated F1 + missing 1 problem |

**Commands to run at HOME:**
```bash
python run_hotpotqa_baseline.py --tier 2 --num-problems 200
python run_hotpotqa_baseline.py --tier 3 --num-problems 200
python run_hotpotqa_baseline.py --tier 4 --num-problems 200
python run_musique_baseline.py --tier 2 --num-problems 200
python run_musique_baseline.py --tier 3 --num-problems 200
python run_musique_baseline.py --tier 4 --num-problems 200
```

> **Note:** Do NOT use `--resume` flag. Start fresh so the new CSVs have clean, untruncated logs.
> **Important:** Move or rename the old partial `hotpotqa_baseline_tier2.csv` in `baselines/` before starting.

---

## 5. Post Re-run Protocol

1. Verify each new CSV has 200 unique problems (600 rows for 3-agent pipeline)
2. Verify verifier `response_text` contains "Final Answer:" pattern
3. Run `scripts/recompute_and_update_metrics.py` to generate new stats JSONs
4. Update `08_RESULTS_LEDGER.md` with final numbers
5. Mark each baseline as LOCKED in project state
6. Archive `baselines_backup/` (can be deleted once new runs are verified)
