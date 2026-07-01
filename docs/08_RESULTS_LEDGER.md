# Results Ledger

> **Source of Truth:** CSV files in `results/baselines/` (regenerate status with
> `python scripts/validate_baselines.py`; authoritative completeness in
> [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md)).
> **Backup (truncated logs):** `results/baselines_backup/`
> **Last Updated:** 2026-06-22
> **Status:** GSM8K **LOCKED** (EM/cost final; no F1 needed). HotpotQA/MuSiQue: **EM reliable
> everywhere, F1 pending clean re-run** (all multi-hop CSVs are either truncated or partial).
> Router results: pending live runs (offline estimates in `results/routing_sim/`).

---

## 1. GSM8K Baselines — LOCKED ✅

Recomputed from CSVs. All 4 tiers have 200 unique problems. Metrics are final.

| Tier | Model | Accuracy | Total Cost | Avg Cost/Prob | Total Tokens | Avg Latency |
|:----:|-------|:--------:|:----------:|:-------------:|:------------:|:-----------:|
| 1 | Gemma 4 E4B | **94.5%** (189/200) | $0.0314 | $0.000157 | 627,338 | 98.3s |
| 2 | Llama 3.3 70B | **96.0%** (192/200) | $0.2186 | $0.001093 | 322,765 | 3.3s |
| 3 | Llama 3.1 405B | **97.0%** (194/200) | $0.8220 | $0.004110 | 309,608 | 54.3s |
| 4 | GPT-4.1 | **97.0%** (194/200) | $1.1824 | $0.005912 | 264,247 | 12.1s |

**Key Observation:** Tier 3 and Tier 4 tie at 97.0% accuracy, but Tier 2 (96.0%) is nearly as good at ~4× less cost. Tier 1 local model achieves 94.5% — remarkably competitive.

---

## 2. HotpotQA Baselines — RE-RUNNING 🔄

### Tier 1 — EM LOCKED ✅ / F1 pending (active CSV, but response truncated)

| Metric | Value |
|--------|:-----:|
| EM | **63.0%** (126/200) — reliable |
| F1 | pending (active T1 CSV is capped at 500 chars; re-run for clean F1) |
| Cost | $0.0594 |
| Avg Latency | 78.7s |

### Tiers 2-4 — EM reliable, F1 pending

| Tier | Model | EM (valid) | source / N | Cost | Notes |
|:----:|-------|:----------:|:----------:|:----:|-------|
| 2 | Llama 3.3 70B | **65.25%** (77/118) | active **partial** 118/200 | $0.4533 | clean/untruncated; `--resume` to finish |
| 2 | Llama 3.3 70B | 63.0% (126/200) | backup 200 (truncated) | $0.767 | older full run, F1 unusable |
| 3 | Llama 3.1 405B | **54.17%** (26/48) | active **partial** 48/200 | $0.7759 | clean; `--resume` to finish |
| 3 | Llama 3.1 405B | 57.0% (114/200) | backup 200 (truncated) | $3.102 | older full run |
| 4 | GPT-4.1 | **37.5%** (75/200) | backup 200 (truncated) | $3.787 | ⚠️ anomaly (§4 of validation report) |

> [!WARNING]
> **HotpotQA T4 (37.5% EM) needs investigation.** GPT-4.1 should outperform Gemma 4B (63%) on multi-hop QA. The re-run will clarify whether this is a real result or an artifact.

---

## 3. MuSiQue Baselines — RE-RUNNING 🔄

### Tier 1 — LOCKED ✅ (from `baselines/`)

| Metric | Value |
|--------|:-----:|
| EM | **31.5%** (63/200) |
| F1 | 31.9% (conservative — old logger truncation) |
| Cost | $0.0737 |
| Avg Latency | 103.9s |

### Tiers 2-4 — AWAITING RE-RUN COMPLETION

**Old values from backup CSVs (EM valid, F1 unreliable):**

| Tier | Model | EM (valid) | F1 (lower bound) | Cost | N |
|:----:|-------|:----------:|:--:|:----:|:---:|
| 2 | Llama 3.3 70B | **55.0%** (110/200) | ~55.0% | $1.065 | 200 |
| 3 | Llama 3.1 405B | **47.5%** (95/200) | ~50.9% | $4.477 | 200 |
| 4 | GPT-4.1 | **25.6%** (51/199) | ~29.4% | $4.513 | 199 |

> [!WARNING]
> **MuSiQue T4 (25.6% EM) is also suspiciously low.** Same concern as HotpotQA T4. Re-run will clarify. Also missing 1 problem (199/200).

---

## 4. Cross-Dataset Comparison

### Accuracy/EM by Tier and Dataset

| Tier | GSM8K | HotpotQA | MuSiQue |
|:----:|:-----:|:--------:|:-------:|
| 1 (4B) | 94.5% | 63.0% | 31.5% |
| 2 (70B) | 96.0% | 63.0%* | 55.0%* |
| 3 (405B) | 97.0% | 57.0%* | 47.5%* |
| 4 (GPT-4.1) | 97.0% | 37.5%*⚠️ | 25.6%*⚠️ |

*\* Pending re-run verification*

### Cost by Tier and Dataset

| Tier | GSM8K | HotpotQA | MuSiQue |
|:----:|:-----:|:--------:|:-------:|
| 1 | $0.031 | $0.059 | $0.074 |
| 2 | $0.219 | $0.767* | $1.065* |
| 3 | $0.822 | $3.102* | $4.477* |
| 4 | $1.182 | $3.787* | $4.513* |

---

## 5. File Index

### Active Baselines (`results/baselines/`)
| File | Status |
|------|:------:|
| `gsm8k_baseline_tier{1,2,3,4}.csv` | ✅ LOCKED (EM/cost; response_text truncated but irrelevant for numeric EM) |
| `hotpotqa_baseline_tier1.csv` | EM ✅ / F1 pending (truncated) |
| `hotpotqa_baseline_tier2.csv` | 🔄 Partial 118/200 (clean) |
| `hotpotqa_baseline_tier3.csv` | 🔄 Partial 48/200 (clean) |
| `musique_baseline_tier1.csv` | EM ✅ / F1 pending (truncated) |

### Backup Baselines (`results/baselines_backup/`)
| File | Status |
|------|:------:|
| `hotpotqa_baseline_tier{2,3,4}.*` | ⚠️ Old truncated logs (EM ok, F1 unusable) |
| `musique_baseline_tier{2,3,4}.*` | ⚠️ Old truncated logs (EM ok, F1 unusable) |

---

## 6. Update Protocol

When new baseline/routing CSVs arrive:
1. `python scripts/validate_baselines.py` — completeness + EM (+ F1 if columns present)
2. `python scripts/recompute_metrics_from_dataset.py` — backfill F1 for any legacy CSV (loads HF datasets)
3. `python aggregate_results.py` — rebuild `results/master_results.*`
4. Update this ledger; mark each cell LOCKED only when N=200 **and** F1 is computed (multi-hop)
5. Archive/delete superseded backup files
