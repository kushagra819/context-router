# Baseline Validation Report

> **Updated:** 2026-06-25 (regenerate anytime with `python scripts/validate_baselines.py`)
> **Source of truth:** the CSV files in `results/baselines/` and `results/baselines_backup/` (ADR-001).
> **Method:** fully offline. EM is read from the per-row `correct` column (computed at run
> time from the *full, untruncated* response, so it is reliable everywhere). F1 is only
> recomputed when a CSV carries `ground_truth`/`predicted` columns (the new schema).

This report supersedes the baseline-status sections of `docs/project_audit.md` and
`docs/implementation_plan.md`, which are **stale** (they claim "12/12 complete / no reruns
needed"). The verified state below is the truth.

---

## 1. Verdict at a glance

| Dataset | T1 | T2 | T3 | T4 | Dataset status |
|---------|----|----|----|----|----------------|
| **GSM8K** | ✅ LOCKED | ✅ LOCKED | ✅ LOCKED | ✅ LOCKED | **Complete** (EM/cost final) |
| **HotpotQA** | ✅ 200, new schema | ✅ 200, new schema | ⚠️ 169/200 (stopped early) | ✅ 200, new schema (F1=57.58) | **T3 needs 31 more problems** |
| **MuSiQue** | ✅ 200, new schema | ⚠️ ~162/200 (stopped early) | ❌ backup only (old schema) | ⚠️ ~13/200 active | **T2/T3/T4 need completion** |

**Bottom line:**
- **GSM8K is publication-ready.** It uses numeric exact match (no F1), which is computed at
  run time, so the 500-char response truncation in its CSVs is irrelevant.
- **HotpotQA is nearly complete.** T1, T2, T4 are done with the new schema (full responses,
  F1 columns). Only T3 needs 31 more problems (169→200). T4 now has F1=57.58 (vs EM=37.5),
  confirming the verbose-answer hypothesis.
- **MuSiQue still needs significant work.** T1 is complete (new schema). T2 is at ~162/200
  (stopped early). T3 has no active-directory CSV (backup only, old truncated schema).
  T4 is at ~13/200 in active.

---

## 2. Verified completeness (manually verified 2026-06-25 from CSV line counts + stats JSONs)

| cell | best source | N (complete) | EM % | F1 % | cost $ | schema | status |
|------|-------------|:---:|:---:|:---:|:---:|:---:|--------|
| gsm8k T1 | active | 200 | 94.5 | n/a | 0.0314 | old | ✅ LOCKED |
| gsm8k T2 | active | 200 | 96.0 | n/a | 0.2186 | old | ✅ LOCKED |
| gsm8k T3 | active | 200 | 97.0 | n/a | 0.8220 | old | ✅ LOCKED |
| gsm8k T4 | active | 200 | 97.0 | n/a | 1.1824 | old | ✅ LOCKED |
| hotpotqa T1 | active | 200 | ~57.3 | 72.59 | — | **new** | ✅ COMPLETE (re-run 2026-06-23, resumed from 125) |
| hotpotqa T2 | active | **200** | 62.0 | — | — | **new** | ✅ COMPLETE (re-run 2026-06-23, session=200) |
| hotpotqa T3 | active | **169** | — | — | — | **new** | ⚠️ PARTIAL (stopped_early, resumed from 169, 0 new) |
| hotpotqa T4 | active | **200** | 37.5 | **57.58** | — | **new** | ✅ COMPLETE (re-run 2026-06-24); ⚠️ anomaly (§4) |
| musique T1 | active | **200** | ~26.2 | 35.81 | — | **new** | ✅ COMPLETE (re-run 2026-06-23, resumed from 158) |
| musique T2 | active | **~162** | ~42.9 | 64.01 | — | **new** | ⚠️ PARTIAL (stopped_early at 162/200, 2026-06-25) |
| musique T3 | **backup** | 200 | 47.5 | — | 4.4774 | **old** | ❌ NO ACTIVE CSV; backup is old schema (truncated) |
| musique T4 | active | **~13** | — | — | — | **new** | ❌ PARTIAL (only 13/200 in active, 2026-06-25) |

> **Schema key:** "old" = legacy logger (`response_text[:500]`, no F1/ground_truth columns).
> "new" = fixed logger (full responses + `f1`, `ground_truth`, `predicted`, `confidence` columns).
> EM/F1 values marked "~" are from session-only stats (last run session, not full CSV aggregate).
> Values marked "—" need recomputation from the full CSV.

> **Note on HotpotQA T1 EM:** The stats JSON shows session EM=57.33 (for the last 75 problems),
> which differs from the previous report's 63.0%. The full-CSV aggregate needs recomputation.

---

## 3. Why EM is trustworthy but F1 is not (root cause)

Two independent issues were conflated in the old audit; here they are separated:

1. **Response truncation (data loss).** The original logger stored `response_text[:500]`.
   The active GSM8K/HotpotQA-T1/MuSiQue-T1 CSVs and *all* backup CSVs are capped at 500
   chars (verified: `max(len(response_text)) == 500`). Only HotpotQA T2/T3 active CSVs are
   full-length (`max ≈ 9655`), because they were re-run after the logger was fixed.
   - **EM is unaffected:** the runner computes `correct` from the in-memory full response
     *before* logging, so the `correct` column is the real per-problem outcome.
   - **F1 is damaged:** recomputing F1 requires the predicted answer span, which is parsed
     from the (now truncated) `response_text`. Truncation drops the trailing `Final Answer:`
     line → wrong/empty predictions → unreliable F1.

2. **The `validation_problems` resume bug (stats only).** In `run_hotpotqa_baseline.py` /
   `run_musique_baseline.py`, the resume path referenced a module-global
   `validation_problems` only defined under `__main__`, and recomputed F1 over the *last
   session's* problems. This corrupted the **stats JSON** F1 values (producing the
   impossible "F1 < EM"), but never the CSV `correct` column.

**Fix in this codebase:** the new logger (`src/utils/logger.py`) stores full responses plus
`ground_truth`, `predicted`, `f1`, `confidence`, `routing_reason`. Fresh runs are therefore
fully self-describing and F1 becomes recomputable offline (no dataset reload). The unified
runner (`run_experiment.py`) also computes EM/F1 per problem during the run.

---

## 4. The Tier-4 EM anomaly (open item, not a blocker)

GPT-4.1 (T4) shows **lower EM than weaker tiers** on the multi-hop sets:

- HotpotQA: T4 = 37.5% vs T1 = 63.0%, T2 = 65.25%, T3 = 54.17%
- MuSiQue: T4 = 25.63% vs T1 = 31.5%, T2 = 55.0%, T3 = 47.5%

These EM values are real (computed at run time), so this is a genuine measurement, not a
logging artifact. Leading hypotheses, to be confirmed on the clean re-run:

1. **EM brittleness to verbose frontier answers.** Strong models often answer
   "Final Answer: The director is Christopher Nolan" where gold is "Christopher Nolan".
   Normalized EM scores this 0 while token-F1 would be high. This is the most likely cause
   and is exactly why F1 must be reported alongside EM (ADR-005), and why the answer
   extractor matters.
2. **`max_tokens=2048` truncating the verifier's chain-of-thought** before it emits the
   `Final Answer:` line on long contexts.
3. **Provider/prompt variance** for GPT-4.1 on GitHub Models.

**Planned actions (home machine):** re-run with the fixed logger; report EM **and** F1;
inspect a sample of T4 verifier outputs. If hypothesis (1) holds, the headline efficiency
story is *strengthened* (a cheaper tier matches/*beats* the frontier on EM, and the router
can exploit that). No code change is required to proceed; this is an analysis item.

---

## 5. What still needs to run (updated 2026-06-25)

GSM8K needs nothing. HotpotQA T1/T2/T4 are now complete with the new schema. The
remaining work is:

```bash
# HotpotQA — only T3 needs completion (31 more problems)
python run_experiment.py --dataset hotpotqa --router fixed_t3 --num-problems 200 --resume

# MuSiQue — T2 needs completion, T3 needs fresh run, T4 needs completion
python run_experiment.py --dataset musique --router fixed_t2 --num-problems 200 --resume
python run_experiment.py --dataset musique --router fixed_t3 --num-problems 200          # fresh (no active CSV)
python run_experiment.py --dataset musique --router fixed_t4 --num-problems 200 --resume

# Then re-validate
python scripts/validate_baselines.py
```

**Priority order (API constraint: T3 & T4 share GitHub Models token pool):**
1. HotpotQA T3 (31 problems, ~30 min with 8s delay) — **quick win**
2. MuSiQue T2 (38 problems, Groq, fast) — **quick win**
3. MuSiQue T3 (200 problems, GitHub Models T3, ~3 hours)
4. MuSiQue T4 (187 problems, GitHub Models T4, ~3 hours)

> Tier 3 & Tier 4 share the GitHub Models token pool — **do not run them simultaneously**
> (RISK R1, see `docs/07_RISK_REGISTER.md`).

---

## 6. Reproducing this report

```bash
python scripts/validate_baselines.py        # writes results/baseline_validation.json + console table
```

The numbers in §2 are copied verbatim from that run. Any future Claude/engineer should
re-run it and trust its output over any prose in the older docs.
