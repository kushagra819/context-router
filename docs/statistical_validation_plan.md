# Statistical Validation Plan

> Status: FROZEN (methodology freeze; results are placeholders)
> Related docs (do not duplicate): [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) (metric definitions, code map),
> [06_EVALUATION_PROTOCOL.md](06_EVALUATION_PROTOCOL.md) (metrics + cost model), [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md) (C1-C8 evidence contract),
> [04_BASELINE_PROTOCOL.md](04_BASELINE_PROTOCOL.md), [07_RISK_REGISTER.md](07_RISK_REGISTER.md), [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md),
> [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md), [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md).

This is the PART 3 deliverable. It is the single authority for how every reported number is
validated. The governing rule of the freeze:

> **RULE: No result enters the paper without a validation strategy defined in this document.**
> A number is publishable only if (a) it has a CI method here, (b) it has a hypothesis test
> here when it is used to support a claim (C1-C8), and (c) its multiple-comparison handling is
> covered by Section 6.

This is a methodology freeze. Nothing here requires changing the router or any scoring code.
Two functions already exist in [`src/evaluation/routing_metrics.py`](../src/evaluation/routing_metrics.py)
and are the workhorses: `bootstrap_ci` and `paired_bootstrap_pvalue`. Every other test named
here (McNemar, Wilcoxon signed-rank, permutation) is **spec-only / analysis-time**: it is run
once, on the frozen per-problem CSVs, with `scipy` in an analysis notebook. No spec-only test
requires new router code, a re-run, or a code feature. All per-problem inputs are reconstructed
from the LOGGED CSV COLUMNS (see [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md)).

---

## 1. Scope, data unit, and pairing

- **Unit of analysis:** the *problem* (`problem_id`), not the agent call. A pipeline run on one
  problem produces one outcome record: `correct in {0,1}`, `f1 in [0,1]`, summed `cost_usd`,
  summed `latency_s`, total tokens. Per-call rows are aggregated to per-problem before any test.
  (Exception: Escalation Rate and tier distribution are per-call by definition; their CIs treat
  the agent call as the unit -- see Section 4, SECONDARY.)
- **Pairing is the central design fact.** Every router and every baseline is evaluated on the
  **same N problems** in the same dataset. Therefore *all* router-vs-baseline and
  router-vs-router comparisons are **paired**: comparator outcomes are aligned by `problem_id`.
  Paired tests are strictly more powerful here and are mandatory; unpaired tests are used only
  when an aligned pairing genuinely does not exist (Section 5).
- **Datasets** (N=200 each, see [02_DATASET_SPECS.md](02_DATASET_SPECS.md)): GSM8K (EM only,
  numeric; F1 collapses to EM), HotpotQA (EM + token-F1), MuSiQue (EM + token-F1). Tests are run
  **per dataset**; cross-dataset claims (C7) are read off the three per-dataset result sets, not
  pooled (datasets differ in difficulty and answer type).
- **Routers under test (15):** reference {oracle, random, fixed_t1, fixed_t2, fixed_t3,
  fixed_t4, fixed_mixed}; proposed {complexity, cascade, adaptive, learned}; ablations
  {adaptive_no_complexity, adaptive_no_role, adaptive_no_confidence, adaptive_no_budget}.
- **EM/F1 honesty (C8):** the Tier-4 EM anomaly on multi-hop (T4 EM below weaker tiers; see
  [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) anomaly note) means **every
  EM result is reported with its F1 counterpart** and every EM-based hypothesis test is
  duplicated on F1. A claim is supported only if EM and F1 agree in sign; a disagreement is
  reported, not hidden.

---

## 2. Confidence interval method (every metric gets a CI)

**Default for all mean-type metrics: percentile bootstrap 95% CI**, implemented in
`bootstrap_ci(values, n_boot=10000, alpha=0.05, seed=42)`.

- **Resampling unit:** the per-problem vector. For EM, `values` = per-problem 0/1 EM flags. For
  F1, `values` = per-problem F1 in [0,1]. For cost/latency/tokens, `values` = per-problem
  summed quantity. The bootstrap resamples N problems with replacement, recomputes the mean,
  repeats `n_boot` times, and reports the [2.5, 97.5] percentiles.
- **Determinism:** `seed=42`, `n_boot=10000` fixed for every CI in the paper so any number is
  exactly reproducible. (`paired_bootstrap_pvalue` uses the same defaults.)
- **Derived/ratio metrics** (Cost Reduction Factor, Cost Savings %, Quality Retention %, WCG):
  these are functions of two means on the **same** problems, so the CI is computed by **paired
  bootstrap of the ratio/difference** -- on each of the `n_boot` iterations, resample the shared
  problem index once, recompute both numerator and denominator on that resample, then the
  derived statistic; take percentiles of the resulting distribution. This propagates the
  correlation between numerator and denominator (they share problems) and is tighter and more
  honest than dividing two independent CIs. Mechanically this is the resampling loop in
  `paired_bootstrap_pvalue` reused at analysis time to emit a CI (spec-only assembly; no code
  change -- the primitive resampling already exists).
- **Proportions sanity check:** for EM (a proportion), the bootstrap CI is cross-checked once
  against the Wilson score interval; they should agree to within rounding at N=200. The
  bootstrap CI is what is reported.
- **Reporting form:** every headline number is written as `point [lo, hi]`, e.g.
  `EM = 64.5 [57.8, 71.0]`. CIs are in the same units as the point (percentage points for
  EM/F1/retention, USD for cost, seconds for latency).

---

## 3. Bootstrap strategy (paired vs unpaired)

| Aspect | Specification |
|--------|---------------|
| n_boot | 10000 (fixed, all CIs and bootstrap p-values) |
| seed | 42 (fixed, all bootstrap procedures) |
| alpha | 0.05 (95% CI; two-sided tests) |
| Per-problem resample of EM | resample the 0/1 EM flag vector (paired: same resample index for both systems) |
| Per-problem resample of F1 | resample the per-problem F1 vector in [0,1] |
| Per-problem resample of cost/latency | resample the per-problem summed cost (USD) / latency (s) |
| CI procedure | percentile bootstrap, `bootstrap_ci` |
| Paired p-value procedure | `paired_bootstrap_pvalue` on aligned per-problem diffs |

- **Paired bootstrap (the default for differences).** Use whenever two systems are compared on
  the **same problems** and the statistic is a **mean difference** (EM diff, F1 diff, cost diff,
  WCG, retention gap). One resample index of size N is drawn per iteration and applied to
  *both* systems, preserving pairing. `paired_bootstrap_pvalue` implements the two-sided test of
  H0: mean(a) == mean(b) by centering the per-problem diffs at zero and counting how often the
  resampled mean diff is at least as extreme as observed. This is the primary engine for C3, C4,
  C6.
- **Unpaired bootstrap (rare).** Only for quantities with no per-problem pairing -- e.g.
  comparing learned-router *held-out classifier accuracy* against a chance baseline computed on
  a different index. Resample each group independently. Flagged explicitly wherever used; it is
  not used for any headline metric.

---

## 4. Per-metric validation table (CI method + test per metric)

CI = percentile bootstrap via `bootstrap_ci` unless noted. "Primary test" is the hypothesis
test used when the metric backs a claim. "Spec-only" = `scipy` at analysis time, no router
change. Metric tiers follow [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md).

### PRIMARY metrics

| Metric | Resample unit | CI method | Primary hypothesis test | Status |
|--------|---------------|-----------|--------------------------|--------|
| EM / Accuracy | per-problem 0/1 | bootstrap_ci | **McNemar** (paired binary, router vs baseline, same problems) + paired bootstrap as corroboration | McNemar spec-only; bootstrap implemented |
| Token-F1 | per-problem F1 | bootstrap_ci | **Wilcoxon signed-rank** (paired, non-normal) + paired bootstrap | Wilcoxon spec-only; bootstrap implemented |
| Cost per task | per-problem cost | bootstrap_ci | **Wilcoxon signed-rank** (paired, right-skewed cost) | spec-only / bootstrap implemented |
| Cost Reduction Factor (x) | paired (router, T4) | paired-bootstrap CI of ratio | paired bootstrap (ratio) | implemented |
| Cost Savings % vs T4 | paired (router, T4) | paired-bootstrap CI of ratio | paired bootstrap | implemented |
| Quality Retention % vs T4 | paired (router, T4) | paired-bootstrap CI of ratio | paired bootstrap (H0: retention == 100%) | implemented |
| **Workflow Context Gain (HEADLINE)** | paired (workflow-aware, complexity), matched cost | paired-bootstrap CI of difference | **paired bootstrap** (`paired_bootstrap_pvalue`) on EM; **Wilcoxon** on F1 | bootstrap implemented; Wilcoxon spec-only |
| Pareto position | per-problem (cost, quality) | bootstrap_ci on each axis | **Pareto Dominance** check (spec-only, Section 7) | spec-only |

### SECONDARY metrics

| Metric | Resample unit | CI method | Primary hypothesis test | Status |
|--------|---------------|-----------|--------------------------|--------|
| Latency (per problem) | per-problem latency | bootstrap_ci | **Wilcoxon signed-rank** (paired, non-normal) | spec-only |
| Throughput (prob/min) | per-problem latency | bootstrap_ci (transform of latency) | Wilcoxon on underlying latency | spec-only |
| Token Efficiency | per-problem (correct, tokens) | bootstrap_ci of ratio | paired bootstrap (ratio) | implemented (assembly) |
| Routing Accuracy | per-problem agree/disagree vs oracle tier | bootstrap_ci | **McNemar** (paired binary agreement, router vs router) | McNemar spec-only |
| Escalation Rate | per **agent call** 0/1 | bootstrap_ci (call as unit) | descriptive; **permutation** if compared | permutation spec-only |
| Tier distribution | per-call tier counts | n/a (report shares) | **chi-square / permutation** on tier-share difference | spec-only |

### DIAGNOSTIC metrics

| Metric | Resample unit | CI method | Primary hypothesis test | Status |
|--------|---------------|-----------|--------------------------|--------|
| Over-Provision Rate | per-problem 0/1 (chosen > oracle) | bootstrap_ci | McNemar (paired) if compared | spec-only |
| Under-Provision Rate | per-problem 0/1 (solvable but wrong) | bootstrap_ci | McNemar (paired) if compared | spec-only |
| Budget Violations (spec-only) | per-problem 0/1 (cost > budget) on budget runs | bootstrap_ci | McNemar (paired) | spec-only / analysis-time |
| Win Rate (spec-only) | per-problem paired win/loss/tie on correct or F1 | bootstrap_ci on win share | **McNemar** (binary win/loss, ties dropped) | spec-only / analysis-time |
| Utility Score (spec-only) | per-problem (quality - lambda*cost) | bootstrap_ci | **Wilcoxon signed-rank** (paired) | spec-only / analysis-time |
| Pareto Dominance (spec-only) | (cost, quality) point set | n/a | **dominance + permutation** on the frontier gap | spec-only / analysis-time |
| Confidence Calibration Error / ECE (spec-only) | per-call (confidence, correct) | bootstrap_ci over bins | descriptive; bootstrap CI on ECE | spec-only / analysis-time |

**Spec-only computability note.** Every spec-only metric above is computable from the LOGGED
CSV COLUMNS with no re-run: Win Rate from paired `correct`/`f1`; Utility Score from `correct`/`f1`
and `cost_usd` with a frozen lambda (see Section 9); Pareto Dominance from per-router
(`cost_usd` mean, quality) points; Budget Violations from `cost_usd` vs the run's cost budget on
budget-capped runs; ECE from `confidence` vs `correct` binned over agent calls.

---

## 5. Hypothesis test catalogue: when to use which

The test must match the data type. Mapping:

| Data type / situation | Test | When to use | Implementation |
|-----------------------|------|-------------|----------------|
| Mean **difference** of any paired per-problem quantity | **Paired bootstrap** | EM/F1/cost/latency mean diffs, WCG, retention vs 100%; the general-purpose engine | `paired_bootstrap_pvalue` (IMPLEMENTED) |
| Paired **binary** outcomes (EM 0/1), router vs baseline on same problems | **McNemar's test** | Headline EM comparisons; exact test on discordant pairs (b, c) | spec-only (`scipy.stats` / `statsmodels` at analysis time) |
| Paired **continuous, non-normal** (F1, cost, latency, utility) | **Wilcoxon signed-rank** | F1/cost/latency/utility comparisons where the diff distribution is skewed/zero-inflated | spec-only (`scipy.stats.wilcoxon`) |
| General paired/unpaired, distribution-free, exact-ish | **Permutation test** | Escalation rate, tier-share, ECE, or as a robustness cross-check for any of the above | spec-only (`scipy` / numpy at analysis time) |

Decision rule:

1. **Binary outcome, paired (same problems)** -> **McNemar** (e.g. router EM vs `fixed_t4` EM,
   router EM vs `complexity` EM). McNemar is the correct test for two correlated proportions;
   it conditions on the discordant pairs only.
2. **Continuous/ordinal, paired, non-normal** -> **Wilcoxon signed-rank** (F1, cost per task,
   latency, Utility Score). Cost and latency are right-skewed; F1 is bounded and lumpy -- normal
   t-tests are inappropriate.
3. **Mean difference, want a CI-consistent p** -> **paired bootstrap** (`paired_bootstrap_pvalue`).
   Reported alongside McNemar/Wilcoxon so the p-value and the bootstrap CI come from the same
   resampling logic (they will agree; divergence is a flag to investigate).
4. **No clean pairing or a non-standard statistic** -> **permutation test** (tier-share
   differences, ECE differences, escalation-rate differences).

Every headline EM comparison reports **both** McNemar (exact, paired-binary-correct) **and**
paired bootstrap; every F1/cost/latency comparison reports **both** Wilcoxon and paired
bootstrap. Agreement across methods is the robustness bar (C8).

---

## 6. Multiple-comparison correction

The router family is large (15 routers), so uncorrected per-comparison p-values would inflate
the family-wise error rate.

- **Correction:** **Holm-Bonferroni** across the **router family** within a (dataset, metric)
  comparison set. Holm is uniformly more powerful than plain Bonferroni and controls FWER under
  arbitrary dependence -- appropriate because router outcomes on shared problems are correlated.
- **Comparison families (each corrected independently):**
  - **Family A (proposed vs ceiling/baselines):** {complexity, cascade, adaptive, learned} vs
    {fixed_t4, fixed_mixed, random} -- supports C3, C6.
  - **Family B (workflow vs difficulty, the headline):** {cascade, adaptive} vs {complexity}
    at matched cost -- supports C4 (WCG). Small family; the PRIMARY hypothesis (Section 8) is
    the protected member.
  - **Family C (ablations):** {adaptive_no_complexity, adaptive_no_role, adaptive_no_confidence,
    adaptive_no_budget} vs {adaptive} -- supports C5.
- **Procedure:** within a family, order the m p-values ascending p(1)..p(m); reject H0(k) while
  p(k) <= alpha / (m - k + 1). Report both the raw p and the Holm-adjusted p.
- **EM and F1** are treated as one logical test per comparison (the claim needs both); we do not
  double-count them as separate hypotheses, but both must clear the bar.
- **Cross-dataset (C7)** is not pooled into one family; each dataset is its own family. A
  generalization claim requires the effect to hold (same sign, significant after Holm) in the
  pre-specified primary dataset and to be directionally consistent in the other two.

---

## 7. Significance reporting standard

Every comparison that supports a claim is reported as the triple **(effect size, CI, p)**:

- **Effect size + CI:** the point difference and its 95% paired-bootstrap CI in natural units
  (EM/F1 points, USD, seconds). The CI is primary; a result whose CI excludes the null is the
  main evidence.
- **p-value:** the matched test from Section 5, at **alpha = 0.05**, two-sided, with the
  **Holm-adjusted** p where a family applies (Section 6).
- **Decision:** "significant" requires CI excluding the null AND Holm-adjusted p < 0.05 from the
  data-type-matched test. EM and F1 must agree in sign (C8).
- **Pareto Dominance (spec-only):** router A dominates B if A is no worse on both cost and
  quality and strictly better on at least one, with the quality CI accounting for sampling; a
  frontier-gap permutation test reports whether A's dominance is beyond chance.
- **Format example:** `WCG(adaptive vs complexity, matched cost) = +4.2 EM pts [+1.1, +7.3],
  McNemar p=0.012, Holm-adj p=0.024; F1 +3.8 [+0.9, +6.6], Wilcoxon p=0.018.`

---

## 8. Pre-registration of the PRIMARY hypothesis

Pre-registered before the live runs (this freeze is the registration; see C4 in
[17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md)):

- **PRIMARY hypothesis (one-sided, the headline):**
  **H1: Workflow Context Gain > 0** -- the workflow-aware router (`adaptive`, with `cascade` as
  the confirmatory secondary) achieves higher quality than the best difficulty-only router
  (`complexity`) **at matched (<=) cost**, on the pre-specified primary dataset.
  Null: **H0: WCG = 0**.
- **Primary endpoint:** WCG on **EM**, with **F1** as the co-primary (both must be > 0; sign
  agreement required by C8).
- **Primary dataset:** HotpotQA (2-hop; the cleanest multi-hop case once F1 re-runs land). MuSiQue
  and GSM8K are secondary/confirmatory for generalization (C7).
- **Primary test:** paired bootstrap (`paired_bootstrap_pvalue`, EM) + Wilcoxon signed-rank
  (F1), one-sided at alpha = 0.05; the comparison is the protected member of Family B and is
  reported with its Holm-adjusted p.
- **Matched-cost rule (frozen):** the workflow-aware router must spend <= the comparator's cost
  per task (Section §D of [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md)); if it spends
  more, WCG is not claimed. Comparator is `complexity` (primary) with `fixed_mixed`/`random` as
  reported alternates.
- **All other hypotheses (C2, C3, C5, C6, C7) are secondary/confirmatory** and corrected within
  their families. Anything not listed here is exploratory and labelled as such in the paper.

---

## 9. Frozen analysis parameters

These are fixed now and may not change after results land (changing them post-hoc is p-hacking):

- `n_boot = 10000`, `seed = 42`, `alpha = 0.05`, two-sided unless a hypothesis is registered
  one-sided (Section 8).
- **Utility Score lambda (frozen):** Utility = quality - lambda * cost, with **lambda chosen so
  that one EM/F1 point trades against a fixed USD amount**; the exact value is frozen in the
  analysis notebook header before any Utility number is reported and is reported in the paper.
  (Sensitivity to lambda is shown as a one-line robustness curve, not used to pick a winner.)
- **ECE binning (frozen):** 10 equal-width confidence bins over `confidence in [0,1]`; ECE is the
  weighted mean |accuracy - confidence| per bin, with a bootstrap CI over bins.
- **Reference for savings/retention:** the all-Tier-4 pipeline (`fixed_t4`), per
  [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) §C-D.

---

## 10. Sample size

- **Current phase (N = 200 per condition per dataset).** Adequate for large effects. At a 50% EM
  base rate the percentile-bootstrap 95% CI half-width is **approximately +-7 points** (matches
  [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) §E: ~+-7 pts at 50%, ~+-3.4 pts at
  90%). Implication: only EM differences of roughly **>= 8-10 points** are reliably detectable
  per dataset at N=200; smaller true effects may be non-significant from underpowering, not
  absence. This is stated wherever a near-null result appears.
- **Paired power advantage.** Because comparisons are paired (Section 1), the relevant variance
  is of the *per-problem difference*, which is much smaller than the marginal variance when
  router and baseline are correlated. McNemar/Wilcoxon/paired-bootstrap therefore detect
  meaningfully smaller differences than the +-7 pt marginal CI suggests -- the marginal CI bounds
  the *level* estimate, the paired test bounds the *difference*.
- **Final paper (N = 500, RISK R4).** Raising N to 500 shrinks the marginal EM CI half-width to
  **approximately +-4.4 points at 50%** (scales as ~1/sqrt(N)), making sub-5-point effects and
  the ablation deltas (C5) detectable. The methodology here is unchanged at N=500; only N moves.
  N=500 is the target for the headline WCG (C4) and the ablation family (C5).
- **Coverage caveat:** GSM8K baselines are LOCKED (verified offline); ALL HotpotQA/MuSiQue F1 is
  PENDING clean re-runs (legacy logger truncated responses at 500 chars). F1-based CIs/tests on
  multi-hop are computed only on the clean re-run CSVs.

---

## 11. Implemented vs spec-only (freeze boundary)

| Procedure | State | Where |
|-----------|-------|-------|
| `bootstrap_ci` (percentile 95% CI) | **IMPLEMENTED** | `src/evaluation/routing_metrics.py` |
| `paired_bootstrap_pvalue` (paired bootstrap, two-sided) | **IMPLEMENTED** | `src/evaluation/routing_metrics.py` |
| Paired-bootstrap CI for ratio/derived metrics (CRF, savings, retention, WCG) | implemented primitives, **assembled at analysis time** | reuse of the two functions above; no code change |
| McNemar's test (paired binary EM) | **spec-only / analysis-time** | `scipy`/`statsmodels` in analysis notebook |
| Wilcoxon signed-rank (paired F1/cost/latency/utility) | **spec-only / analysis-time** | `scipy.stats.wilcoxon` |
| Permutation test (escalation/tier-share/ECE/general) | **spec-only / analysis-time** | `scipy`/numpy in analysis notebook |
| Holm-Bonferroni correction | **spec-only / analysis-time** | `statsmodels.stats.multitest` |
| Win Rate / Utility / Pareto Dominance / Budget Violations / ECE metric values | **spec-only / analysis-time** | computed from LOGGED CSV COLUMNS |

No spec-only item changes the router, adds a code feature, or requires a re-run; all consume the
frozen per-problem CSVs. This document is the validation contract for [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md):
results numbers there remain PLACEHOLDERS ([X.X] / TBD-after-run) except the VERIFIED-OFFLINE
GSM8K baselines and oracle, which carry that explicit label.
