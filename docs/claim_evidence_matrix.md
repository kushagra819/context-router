# Claim-Evidence Matrix

> Status: FROZEN (methodology freeze; results are placeholders).
> Related freeze docs: [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md),
> [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md),
> [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md), [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md),
> [14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md), [15_FIGURE_PLAN.md](15_FIGURE_PLAN.md),
> [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md), [07_RISK_REGISTER.md](07_RISK_REGISTER.md),
> [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md).
> This document is the single source of truth that binds every scientific claim (C1..C8 and
> sub-claims) to the exact experiment, metric, statistical test, figure, and table that must
> exist before the claim may be written. All result numbers are PLACEHOLDERS ([X.X] / TBD-after-run)
> except those explicitly labelled "verified offline".

---

## 0. Canonical id sets (authoritative for cross-doc consistency)

These ids are reused verbatim in every freeze doc. Do not invent new ids.

Routers (15, `get_router` names):
- Reference / anchors: `oracle` (ceiling), `random` (floor), `fixed_t1`, `fixed_t2`,
  `fixed_t3`, `fixed_t4` (= the baselines), `fixed_mixed`.
- Proposed (context-aware): `complexity`, `cascade`, `adaptive`, `learned`.
- Ablations of `adaptive`: `adaptive_no_complexity`, `adaptive_no_role`,
  `adaptive_no_confidence`, `adaptive_no_budget`.

Datasets (N=200 each): GSM8K (test, EM only), HotpotQA (validation/distractor, EM + token-F1),
MuSiQue (validation/answerable, EM + token-F1). Difficulty gradient 1-hop -> 2-hop -> 2-4 hop.

Metric tiers (groupings from [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md)):
- PRIMARY: EM/Accuracy, Token-F1, Cost-per-task, Cost Reduction Factor / Cost Savings %,
  Quality Retention Rate (QRR), Workflow Context Gain (WCG, headline), Pareto position.
- SECONDARY: Latency, Throughput, Token Efficiency, Routing Accuracy, Escalation Rate,
  Tier distribution.
- DIAGNOSTIC: Over-Provision Rate, Under-Provision Rate, Budget Violations (spec-only),
  Win Rate (spec-only), Utility Score (spec-only), Pareto Dominance (spec-only),
  Confidence Calibration Error / ECE (spec-only).

"spec-only / analysis-time" = computable from the logged CSV columns at analysis time with NO
code change and NO router re-run; not yet a named function in `routing_metrics.py`.

Statistical tests (implemented): percentile bootstrap 95% CI (`routing_metrics.bootstrap_ci`);
paired bootstrap p-value on the same problems (`routing_metrics.paired_bootstrap_pvalue`).

Tables (canonical):
- T1 Main Benchmark Results
- T2 Cost Analysis
- T3 Latency Analysis
- T4 Ablation Study
- T5 Error Analysis
- T6 Router Comparison
- T7 Cross-Dataset Generalization

Figures (canonical, this doc's authoritative F-ids):
- F1 System Architecture
- F2 Routing Decision Flow
- F3 Cost-vs-Quality / Pareto Frontier (headline)
- F4 Ablation Results
- F5 Escalation Distribution
- F6 Routing Frequency / Model Utilization
- F7 Failure Categories

Figure-id mapping to code stems in `src/visualization/figures.py` (so freeze docs and code
line up; [15_FIGURE_PLAN.md](15_FIGURE_PLAN.md) lists stems in render order):

| Canonical | Code stem (`figures.py`) |
|-----------|--------------------------|
| F1 System Architecture | `fig1_architecture` |
| F2 Routing Decision Flow | `fig3_router_decision_flow` (+ `fig2_workflow` companion schematic) |
| F3 Pareto Frontier | `fig4_pareto_<dataset>` |
| F4 Ablation Results | `fig6_ablation_<dataset>` |
| F5 Escalation Distribution | `fig7_escalation_<dataset>` |
| F6 Routing Frequency / Utilization | `fig5_utilization_<dataset>` |
| F7 Failure Categories | (Error Analysis render; from logged `correct`/`f1`/`predicted` columns) |

---

## 1. The rule: NO CLAIM WITHOUT EVIDENCE

A claim may appear in the paper, slides, abstract, or any external artifact only when every
cell of its row in the master matrix below is satisfied: the required experiment(s) have been
run live (or are explicitly the verified-offline numbers), the required metric(s) are computed
from the logged CSV columns, the required statistical test (bootstrap 95% CI on every headline
number; paired bootstrap p-value for every router-vs-baseline and WCG comparison) is reported,
and the required figure (Fxx) and table (Txx) exist and are checked into `results/`. No claim is
made from a single point estimate without its CI, no comparative claim is made without its paired
test, and no claim extends beyond the datasets actually evaluated. Until a row is fully green its
claim text remains gated; placeholder rows hold the contract but produce no prose. This rule is
the contract between [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md) (what is run),
[13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) (how it is measured), and
[14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md) (what is written).

---

## 2. Master claim-evidence matrix

Columns: Claim | Required Experiment(s) (router(s) x dataset(s)) | Required Metric(s) |
Required Statistical Test | Required Figure | Required Table.

### C1 - Per-agent routing is feasible and novel vs query-level routing

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C1 Per-agent routing inside a fixed multi-agent pipeline (Analyzer->Solver->Verifier) is a feasible and novel design point distinct from per-query routing. | Existence proof: any routed run executes a per-call tier decision, e.g. `adaptive` x {GSM8K, HotpotQA, MuSiQue}; interface in `src/router/base_router.py`. No new number required beyond demonstrating per-call decisions are logged (`agent_role`, `tier`, `routing_reason`, `escalated_from` columns). | Qualitative: per-call tier assignment exists and differs by `agent_role` (Tier distribution by role). Related-work positioning matrix (per-agent? role? confidence? stage? budget?). | None (feasibility/novelty claim; positioning, not a statistical comparison). | F1 System Architecture; F2 Routing Decision Flow. | Related-work feature matrix (E8 in [14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md) Sec 2); T6 Router Comparison (shows per-call routers exist). |

### C2 - Large oracle headroom exists between tiers

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C2 A per-problem oracle reaches near-ceiling quality at near-floor cost, so routing has room to cut cost without losing quality. | `oracle` vs `fixed_t1..fixed_t4` x {GSM8K, HotpotQA, MuSiQue}. (GSM8K verified offline; multi-hop pending.) | EM/Accuracy and Token-F1 (oracle and each tier); Cost-per-task; Pareto position of `oracle`. | Bootstrap 95% CI on oracle EM and on each tier EM. | F3 Cost-vs-Quality / Pareto Frontier (oracle marker dominates all single tiers). | T1 Main Benchmark Results (`oracle` row); T2 Cost Analysis. |

Verified offline (GSM8K, from `scripts/validate_baselines.py` + `simulate_routing.py`):
oracle 98.5% EM @ $0.0485/200 vs `fixed_t4` 97.0% @ $1.182 and `fixed_t1` 94.5% @ $0.031;
oracle beats every single tier at ~1.5x Tier-1 cost. HotpotQA/MuSiQue oracle = TBD-after-run.

### C3 - Context-aware routing preserves quality while cutting cost

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C3 `cascade`/`adaptive` achieve high Quality Retention vs the all-Tier-4 ceiling at a large Cost Reduction Factor. | `cascade`, `adaptive` vs `fixed_t4` (reference) x {GSM8K, HotpotQA, MuSiQue}. | Quality Retention Rate (EM and F1) vs `fixed_t4`; Cost Reduction Factor (x); Cost Savings %; Cost-per-task; Pareto position. Secondary: Tier distribution, Escalation Rate. | Bootstrap 95% CI on QRR (EM and F1); paired bootstrap p-value for cascade/adaptive EM-and-F1 vs `fixed_t4`. | F3 Pareto Frontier (cascade/adaptive points up-left of T4). | T1 Main Benchmark Results; T2 Cost Analysis (`cost_savings_pct_vs_t4`, `quality_retention_pct_vs_t4`). |

Sub-claim C3a "adaptive routing reduces inference cost": `adaptive` (and `cascade`) vs
`fixed_t4` x all datasets; Cost Reduction Factor (x) and Cost Savings %; paired bootstrap
p-value on cost vs `fixed_t4`; F3; T2.

### C4 - [HEADLINE] Workflow context beats difficulty-only routing

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C4 Workflow Context Gain > 0: `adaptive`/`cascade` beat the best context-free (difficulty-only) router `complexity` at matched (<=) cost. | `adaptive` and `cascade` vs `complexity` x {GSM8K, HotpotQA, MuSiQue}, constrained to matched (<=) cost. Reference also vs `random`/`fixed_mixed`. | Workflow Context Gain (EM and F1) = quality(workflow-aware) - quality(best context-free at <= cost); supporting EM/F1, Cost-per-task to demonstrate matched cost. | Paired bootstrap p-value on WCG (same problems, EM and F1) plus bootstrap 95% CI on WCG. | F3 Pareto Frontier with matched-cost markers (adaptive/cascade above complexity at equal x). | T1 Main Benchmark Results; T6 Router Comparison (WCG derived column). |

Sub-claim C4a "multi-factor beats complexity-only": same as C4; the workflow-aware routers
(`adaptive`/`cascade`, which add role + upstream confidence + budget) must beat `complexity`
(difficulty-only) at matched cost; WCG > 0 with paired p < 0.05; F3; T6.

> **Test directionality:** the C4 WCG test is the pre-registered PRIMARY hypothesis and is
> **one-sided** (H1: WCG > 0), per [statistical_validation_plan.md](statistical_validation_plan.md)
> Section 8. ALL other comparisons in this matrix are **two-sided**.

### C5 - Each routing signal contributes (ablation)

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C5 Removing any one signal family (role / confidence / complexity / budget) degrades quality at fixed budget. | `adaptive` vs each of `adaptive_no_role`, `adaptive_no_confidence`, `adaptive_no_complexity`, `adaptive_no_budget` x {GSM8K, HotpotQA, MuSiQue}, at fixed/matched budget. | EM and F1 delta (full vs each ablation); Cost-per-task (to confirm fixed budget). Diagnostic: Over-Provision Rate, Under-Provision Rate, Budget Violations (spec-only, on `adaptive_no_budget`). | Paired bootstrap p-value for `adaptive` vs each `adaptive_no_*` (same problems); bootstrap 95% CI on each delta. | F4 Ablation Results (EM of `adaptive` vs `adaptive_no_*`). | T4 Ablation Study. |

Sub-claims, one per signal (each its own paired test in T4 / F4):
- C5-role: `adaptive` vs `adaptive_no_role`.
- C5-confidence: `adaptive` vs `adaptive_no_confidence`.
- C5-complexity: `adaptive` vs `adaptive_no_complexity`.
- C5-budget: `adaptive` vs `adaptive_no_budget` (also Budget Violations, spec-only).

### C6 - Learned routing approximates the oracle and beats random and rule-based at matched cost

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C6 A DecisionTree (`learned`) trained on oracle labels routes better than `random` and approaches/beats rule-based routers at matched cost. | `learned` vs `random`, vs `complexity`/`cascade`/`adaptive`, vs `oracle` (gap), x {GSM8K, HotpotQA, MuSiQue}. Trained via `train_router.py` on oracle labels. | EM and F1 at matched cost; Routing Accuracy vs oracle; gap-to-oracle; Cost-per-task; learned-router held-out test accuracy. | Paired bootstrap p-value for `learned` vs `random` and `learned` vs `complexity` (same problems, EM and F1); bootstrap 95% CI on `learned` EM/F1. | F3 Pareto Frontier (learned point vs random/rule-based/oracle); F6 Routing Frequency / Utilization. | T1 Main Benchmark Results (`learned` row); T6 Router Comparison. |

Sub-claim C6a "learned beats rule-based": `learned` vs `complexity` (and vs `cascade`) at
matched cost; EM/F1 with paired bootstrap p-value; F3; T6. (State honestly if learned only
matches, does not beat, rule-based; do not overclaim.)

### C7 - Results generalize across difficulty

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C7 The cost-quality benefit holds on GSM8K (1-hop), HotpotQA (2-hop), MuSiQue (2-4 hop). | All proposed routers (`complexity`, `cascade`, `adaptive`, `learned`) and references across all three datasets. | Cost Savings %, Quality Retention Rate, WCG reported per dataset; consistent direction/magnitude across the difficulty gradient. | Bootstrap 95% CI per dataset on each headline; paired bootstrap p-values per dataset. | F3 Pareto Frontier rendered per dataset (x3). | T7 Cross-Dataset Generalization; T1 (per-dataset rows). |

### C8 - Robustness / honesty

| Claim | Required Experiment(s) | Required Metric(s) | Required Statistical Test | Required Figure | Required Table |
|-------|------------------------|--------------------|---------------------------|-----------------|----------------|
| C8 We report EM AND F1, confidence intervals on every headline, and explicitly flag the Tier-4 EM anomaly and the hypothetical-cost assumption. | All routers x {GSM8K, HotpotQA, MuSiQue}: every headline carries both EM and F1 (F1 omitted only for GSM8K, where F1 collapses to EM) and a CI; anomaly documented from `fixed_t4` multi-hop EM. | EM and Token-F1 side by side; bootstrap 95% CIs; documented Tier-4 EM-vs-F1 discrepancy; cost reported as ratios with stated hypothetical-price assumption. Diagnostic: Confidence Calibration Error / ECE (spec-only) where confidence is reported. | Bootstrap 95% CI on every headline EM and F1 (the honesty deliverable itself). | F7 Failure Categories (error analysis). | T5 Error Analysis; T1 (EM and F1 columns + CIs). |

Anomaly to flag (verified offline): on multi-hop, `fixed_t4` EM is LOWER than weaker tiers
(HotpotQA EM T1=63.0, T2=65.25, T3=54.17, T4=37.5; MuSiQue EM T1=31.5, T2=55.0, T3=47.5,
T4=25.6) -> likely EM brittleness to verbose frontier answers -> ALWAYS report F1 alongside EM
(QRR > 100% can result; see [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) Sec 4,
[07_RISK_REGISTER.md](07_RISK_REGISTER.md) R1/R10). Hypothetical-cost assumption: report cost
ratios only, never absolute USD as a deployment cost (R10).

---

## 3. Reverse-coverage check (every table / figure serves a claim; nothing orphaned)

### Tables

| Table | Title | Serves claim(s) | Orphan? |
|-------|-------|-----------------|---------|
| T1 | Main Benchmark Results (EM, F1, cost, savings x, QRR per router x dataset, with CIs) | C2, C3, C6, C7, C8 | No |
| T2 | Cost Analysis (cost-per-task, Cost Reduction Factor, Cost Savings %) | C2, C3 (C3a) | No |
| T3 | Latency Analysis (latency, throughput, token efficiency) | Secondary support for C3/C7 (efficiency framing); no standalone claim | Allowed (secondary; cited in Results Sec 7.5) |
| T4 | Ablation Study (`adaptive` vs `adaptive_no_*`) | C5 (and sub-claims C5-role/confidence/complexity/budget) | No |
| T5 | Error Analysis | C8 | No |
| T6 | Router Comparison (incl. WCG derived column, learned vs rule-based) | C1, C4 (C4a), C6 (C6a) | No |
| T7 | Cross-Dataset Generalization | C7 | No |

### Figures

| Figure | Title | Code stem | Serves claim(s) | Orphan? |
|--------|-------|-----------|-----------------|---------|
| F1 | System Architecture | `fig1_architecture` | C1 | No |
| F2 | Routing Decision Flow | `fig3_router_decision_flow` (+ `fig2_workflow`) | C1 | No |
| F3 | Cost-vs-Quality / Pareto Frontier (headline) | `fig4_pareto_<dataset>` | C2, C3, C4 (matched-cost markers), C6, C7 | No |
| F4 | Ablation Results | `fig6_ablation_<dataset>` | C5 | No |
| F5 | Escalation Distribution | `fig7_escalation_<dataset>` | C3, C5 (confidence cascade behaviour) | No |
| F6 | Routing Frequency / Model Utilization | `fig5_utilization_<dataset>` | C6, supporting C3/C5 (tier distribution) | No |
| F7 | Failure Categories | error-analysis render | C8 | No |

T3 (Latency) is intentionally a secondary table: it supports the efficiency narrative for C3/C7
but does not back a standalone scientific claim; it is retained, not orphaned, and is cited in
Results Sec 7.5 of [14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md). Every other table and figure maps
to at least one C-claim. No claim lacks a figure and a table; no figure or table lacks a claim.

### Spec-only diagnostics (analysis-time, no code change) and where they land

| Diagnostic (spec-only) | Computed from logged columns | Lands in | Serves |
|------------------------|------------------------------|----------|--------|
| Win Rate | paired `correct`/`f1` | T6 | C4/C6 support |
| Utility Score (quality - lambda*cost; freeze lambda) | `correct`/`f1`, `cost_usd` | T2/T6 | C3/C4 support |
| Pareto Dominance | (`cost_usd`, `correct`/`f1`) points | F3 | C2/C3 support |
| Budget Violations | `cost_usd` vs cost budget on budget runs | T4 | C5-budget |
| Confidence Calibration Error / ECE | `confidence` vs `correct` | T5 | C8 |

---

## 4. Claims we will NOT make (out of scope; pre-empts overclaiming)

- No claim of real-world dollar savings or deployment cost. Costs are hypothetical published
  prices; we report ratios only (R10). All models are free in practice.
- No claim of statistical superiority without a paired bootstrap p-value on the same problems;
  no headline without a bootstrap 95% CI. N=200 gives EM 95% CIs of ~+/-7 pts at 50%.
- No claim that `learned` beats the `oracle` (oracle is the per-problem upper bound by
  construction). We claim only "approaches oracle".
- No claim of generalization beyond the three evaluated datasets, beyond the single
  Analyzer->Solver->Verifier pipeline shape, or beyond N=200 (final N may rise to 500, R4).
- No causal claim that a single signal is "most important" beyond what the ablation magnitudes
  in T4/F4 support; we report per-signal deltas, not a global importance ordering.
- No claim that `confidence` is calibrated; it is a lexical heuristic (`extract_confidence`).
  Any ECE we report is descriptive, not a calibration guarantee.
- No EM-only multi-hop claim: on HotpotQA/MuSiQue we never report EM without F1, given the
  documented Tier-4 EM anomaly.
- No claim derived solely from `simulate_routing.py` estimates as if they were live results;
  offline numbers are labelled "verified offline" (exact for single-tier and oracle) or are
  estimates (mixed/random) and are clearly distinguished from live routed runs.
- No latency/throughput claim as a hardware benchmark; latency is a logged proxy
  (sum-of-latency as wall-clock proxy), reported as a secondary metric only.
- No claim of novelty for query-level routing; novelty is strictly the per-agent, workflow-signal
  design point (C1), positioned against RouteLLM/FrugalGPT/AutoMix/MasRouter.

---

## 5. Gate summary

A claim ships only when its matrix row is fully green: experiment run (or verified-offline and
labelled), metric computed, statistical test reported, figure and table present. The reverse-
coverage check guarantees no orphan artifacts. The out-of-scope list bounds the claims so the
paper states exactly what the evidence supports and nothing more. Cross-reference
[17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md) for per-claim status flags and
[16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md) for the exact commands that turn each row
green.
