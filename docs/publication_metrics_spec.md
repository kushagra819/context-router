# publication_metrics_spec.md -- Frozen Metric Set (PART 2 deliverable)

> Status: FROZEN (methodology freeze; results are placeholders)

> Related docs (do not duplicate; this file is the single frozen index of the metric set):
> [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) (canonical formulas + code),
> [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md) (claim->evidence contract),
> [06_EVALUATION_PROTOCOL.md](06_EVALUATION_PROTOCOL.md), [04_BASELINE_PROTOCOL.md](04_BASELINE_PROTOCOL.md),
> [03_MODEL_MATRIX.md](03_MODEL_MATRIX.md), [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md),
> [07_RISK_REGISTER.md](07_RISK_REGISTER.md), [14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md),
> [15_FIGURE_PLAN.md](15_FIGURE_PLAN.md), [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md),
> [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md), [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md).

This document FREEZES the final metric set for the paper. It is the authoritative bridge between
the logged CSV columns, the implemented code in `src/evaluation/`, and the publication
tables/figures/claims. It does NOT introduce code. Every entry is honestly tagged either
`IMPLEMENTED` (a function exists in `routing_metrics.py` / `metrics.py`) or `SPEC-ONLY`
(computable at analysis time from logged columns with NO code/router change).

---

## 0. Conventions, data source, and references

A run evaluates `N` problems per (dataset, router). For problem `i`: `correct_i in {0,1}`
(exact match), `f1_i in [0,1]` (token-F1), `cost_i` = summed hypothetical USD over its agent
calls, `tok_i` = total tokens, `lat_i` = summed latency (s).

`N = 200` per (dataset, router) at freeze; the final paper may raise `N` to 500 (RISK R4).

REFERENCE pipeline for all savings / retention / WCG numbers = the all-Tier-4 pipeline
(`fixed_t4`): quality ceiling and cost reference (`aggregate.REFERENCE_TIER`).

DATASETS: GSM8K (numeric EM only, no F1), HotpotQA (EM + token-F1), MuSiQue (EM + token-F1).

ROUTERS (15, `get_router` names): oracle, random, fixed_t1, fixed_t2, fixed_t3, fixed_t4,
fixed_mixed, complexity, cascade, adaptive, learned, adaptive_no_complexity, adaptive_no_role,
adaptive_no_confidence, adaptive_no_budget.

### Logged CSV columns (per agent call; available for ALL analysis without re-running)

```
timestamp, experiment_id, problem_id, dataset, agent_role, tier, model_name, router_type,
input_tokens, output_tokens, latency_s, cost_usd, correct, f1, ground_truth, predicted,
confidence, routing_reason, escalated_from, response_text
```

Granularity note: the log is PER AGENT CALL (Analyzer / Solver / Verifier rows for one
`problem_id`). Per-problem aggregation rules used throughout:
- `cost_i` = SUM of `cost_usd` over the problem's agent rows.
- `tok_i`  = SUM of (`input_tokens` + `output_tokens`) over the problem's agent rows.
- `lat_i`  = SUM of `latency_s` over the problem's agent rows.
- `correct_i` / `f1_i` = the `correct` / `f1` of the VERIFIER row (the agent that emits the
  final answer). The router's "representative tier" for a problem = the `tier` of that verifier row.
- `escalated` (a derived per-call boolean) = `escalated_from` is non-empty / not null.

### Verified-offline anchor numbers (REAL; everything else is a placeholder)

These come from `scripts/validate_baselines.py` + `simulate_routing.py` and are labelled
"verified offline" wherever cited. GSM8K baselines are LOCKED. ALL HotpotQA/MuSiQue F1 is
PENDING clean re-runs (legacy logger truncated `response_text` at 500 chars).

| Quantity (verified offline) | Value |
|---|---|
| GSM8K EM by tier T1/T2/T3/T4 | 94.5 / 96.0 / 97.0 / 97.0 |
| GSM8K cost(200) by tier T1/T2/T3/T4 (USD) | 0.031 / 0.219 / 0.822 / 1.182 |
| GSM8K oracle (sim) | 98.5% EM @ $0.0485 |
| HotpotQA EM T1/T2/T3/T4 | 63.0 / 65.25 / 54.17 / 37.5 |
| MuSiQue EM T1/T2/T3/T4 | 31.5 / 55.0 / 47.5 / 25.6 |

KNOWN ANOMALY (C8): Tier-4 EM is LOWER than weaker tiers on multi-hop (EM brittleness to
verbose frontier answers). Consequence: ALWAYS report F1 alongside EM; QRR_EM can exceed 100%
(report F1-based QRR too). See [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) §4.

---

## 1. Frozen metric set at a glance

| Tier | Metric | Status | Code / Spec |
|---|---|---|---|
| PRIMARY | EM / Accuracy | IMPLEMENTED | `routing_metrics.exact_match`, `metrics.*_check_correct` |
| PRIMARY | Token-F1 | IMPLEMENTED | `routing_metrics.mean_f1`, `metrics.hotpotqa_compute_f1` |
| PRIMARY | Cost-per-task | IMPLEMENTED | `routing_metrics.cost_per_task` |
| PRIMARY | Cost Reduction Factor | IMPLEMENTED | `routing_metrics.cost_reduction_factor` |
| PRIMARY | Cost Savings % | IMPLEMENTED | `routing_metrics.cost_savings_pct` |
| PRIMARY | Quality Retention Rate (QRR) | IMPLEMENTED | `routing_metrics.quality_retention_pct` |
| PRIMARY | Workflow Context Gain (WCG) [HEADLINE] | IMPLEMENTED | `routing_metrics.workflow_context_gain` |
| PRIMARY | Pareto position | SPEC-ONLY | analysis-time from (cost,quality) |
| SECONDARY | Latency | IMPLEMENTED (agg) | `aggregate` from `latency_s` |
| SECONDARY | Throughput | IMPLEMENTED | `routing_metrics.throughput_per_min` |
| SECONDARY | Token Efficiency | IMPLEMENTED | `routing_metrics.token_efficiency` |
| SECONDARY | Routing Accuracy | IMPLEMENTED | `routing_metrics.routing_accuracy` |
| SECONDARY | Escalation Rate | IMPLEMENTED | `routing_metrics.escalation_rate` |
| SECONDARY | Tier distribution | SPEC-ONLY | analysis-time histogram of `tier` |
| DIAGNOSTIC | Over-Provision Rate | IMPLEMENTED | `routing_metrics.over_provision_rate` |
| DIAGNOSTIC | Under-Provision Rate | IMPLEMENTED | `routing_metrics.under_provision_rate` |
| DIAGNOSTIC | Budget Violations | SPEC-ONLY | `cost_spent` vs budget on budget runs |
| DIAGNOSTIC | Win Rate | SPEC-ONLY | paired per-problem correct/f1 |
| DIAGNOSTIC | Utility Score | SPEC-ONLY | quality - lambda*cost (lambda frozen) |
| DIAGNOSTIC | Pareto Dominance | SPEC-ONLY | from (cost,quality) points |
| DIAGNOSTIC | Confidence Calibration Error / ECE | SPEC-ONLY | `confidence` vs `correct` |
| STATS | Bootstrap 95% CI | IMPLEMENTED | `routing_metrics.bootstrap_ci` |
| STATS | Paired bootstrap p-value | IMPLEMENTED | `routing_metrics.paired_bootstrap_pvalue` |

Of the 21 substantive metrics, 14 are IMPLEMENTED (a function exists in `routing_metrics.py`
/ `metrics.py`, or an aggregation in `aggregate.py`) and 7 are SPEC-ONLY (Pareto position,
Pareto Dominance, Tier distribution, Budget Violations, Win Rate, Utility Score, ECE). All 7
spec-only metrics are derivable from the frozen logged columns with no code or router change.

---

## 2. PRIMARY metrics

These carry the headline scientific claims and populate the main result tables/figures.

### 2.1 EM / Accuracy

- Formula: `EM = (1/N) * sum_i correct_i`.
- Interpretation: fraction of problems answered exactly correctly. The primary quality axis.
- Why reviewers care: standard, comparable, unambiguous task-success measure; required for any
  QA/reasoning benchmark to be taken seriously.
- How computed: per-problem `correct` (verifier row) -> mean over the N problems for each
  (dataset, router). GSM8K uses numeric equality `|a-b| < 1e-6`; HotpotQA/MuSiQue use
  normalized string equality.
- Code location: IMPLEMENTED. Aggregate `routing_metrics.exact_match(correct_flags)`;
  per-problem scorers `metrics.gsm8k_check_correct`, `metrics.hotpotqa_check_correct`
  (`metrics.musique_check_correct` aliases HotpotQA), `metrics.normalize_answer`.
- Publication usage: Table T1 (Main Benchmark Results), Table T7 (Cross-Dataset
  Generalization); inputs to QRR/WCG/Pareto. Supports C2, C3, C6, C7, C8.

### 2.2 Token-F1

- Formula: `F1 = 2*P*R/(P+R)`, `P = overlap/len(pred)`, `R = overlap/len(gold)` over
  bag-of-tokens on normalized text; reported as macro mean `(1/N) sum_i f1_i`.
- Interpretation: partial-credit overlap between predicted and gold answer; robust to verbose
  or differently-phrased correct answers that EM marks wrong.
- Why reviewers care: F1 is the honesty companion to EM. With the documented Tier-4 EM anomaly
  (verbose frontier answers fail brittle EM), F1 prevents a misleading ranking. `F1 >= EM`
  always; `F1 < EM` would signal a bug.
- How computed: per-problem `f1` (verifier row) -> macro mean per (dataset, router). GSM8K F1
  collapses to EM (numeric), so F1 is reported for HotpotQA and MuSiQue only.
- Code location: IMPLEMENTED. Aggregate `routing_metrics.mean_f1(f1_scores)`; per-problem
  `metrics.hotpotqa_compute_f1` (`metrics.musique_compute_f1` aliases it).
- Publication usage: Table T1, Table T5 (Error Analysis), Table T7; F1-based QRR and WCG.
  Directly serves C8 (report EM AND F1) and de-risks C7. Status: PENDING clean re-runs for all
  multi-hop F1 (legacy 500-char truncation).

### 2.3 Cost-per-task

- Formula: `cost_per_task = (sum_i cost_i) / N`.
- Interpretation: average hypothetical USD per problem; the primary cost axis.
- Why reviewers care: the whole premise is cost-quality trade-off; a single comparable scalar
  per router. (Costs are hypothetical $/1M token prices; see C8 honesty caveat and R-cost.)
- How computed: sum `cost_usd` across all agent rows of a problem -> `cost_i`; sum over
  problems / N. Prices per tier from `MODEL_CONFIG` / [03_MODEL_MATRIX.md](03_MODEL_MATRIX.md);
  per-call cost is `metrics.calculate_cost(input_tokens, output_tokens, tier)`.
- Code location: IMPLEMENTED. `routing_metrics.cost_per_task(total_cost, n)`; per-call
  `metrics.calculate_cost`.
- Publication usage: Table T2 (Cost Analysis), x-axis of Figure F3 (Pareto). Supports C2, C3, C6.

### 2.4 Cost Reduction Factor (CRF)

- Formula: `CRF = cost(all-Tier-4) / cost(router)` (a multiplier, "x cheaper").
- Interpretation: how many times cheaper the router is than the all-Tier-4 ceiling.
- Why reviewers care: an intuitive "Nx cheaper at comparable quality" headline that anchors the
  practical value of routing.
- How computed: reference cost = total `fixed_t4` cost on the same dataset; router cost = total
  router cost; ratio.
- Code location: IMPLEMENTED. `routing_metrics.cost_reduction_factor(reference_cost, router_cost)`.
- Publication usage: Table T2; abstract/results headline. Supports C3 (paired with QRR).

### 2.5 Cost Savings %

- Formula: `cost_savings_pct = (1 - cost(router)/cost(all-Tier-4)) * 100`.
- Interpretation: percent of the all-Tier-4 spend avoided. Positive = cheaper than reference.
- Why reviewers care: complements CRF in the units (percent) reviewers expect for savings.
- How computed: same inputs as CRF, reported as a percentage.
- Code location: IMPLEMENTED. `routing_metrics.cost_savings_pct(reference_cost, router_cost)`.
- Publication usage: Table T2 (`cost_savings_pct_vs_t4`). Supports C3.

### 2.6 Quality Retention Rate (QRR)

- Formula: `QRR = quality(router) / quality(all-Tier-4) * 100` (computed for EM and for F1).
- Interpretation: how much of the all-Tier-4 quality the router keeps; 100% = matches ceiling.
- Why reviewers care: the quality half of the trade-off claim. "Keeps X% of ceiling quality at
  Nx lower cost" is the core selling sentence; pairing CRF with QRR forbids cherry-picking one axis.
- How computed: router EM (or F1) / `fixed_t4` EM (or F1) on the same dataset, x100.
- Code location: IMPLEMENTED. `routing_metrics.quality_retention_pct(router_quality, reference_quality)`.
- Publication usage: Table T1/T2 (`quality_retention_pct_vs_t4`), Figure F3. Supports C3.
- Honesty note: QRR_EM may exceed 100% on HotpotQA/MuSiQue because Tier-4 EM is anomalously
  low; ALWAYS report F1-based QRR alongside (C8).

### 2.7 Workflow Context Gain (WCG) [HEADLINE]

- Formula: `WCG = quality(workflow-aware router) - quality(best context-free router)` evaluated
  AT MATCHED (<=) COST. Reported in quality points (x100) for EM and F1.
- Interpretation: the quality advantage attributable specifically to workflow-only signals
  (agent role, upstream confidence, workflow stage) over pure query-difficulty routing.
- Why reviewers care: this is the paper's novel contribution made measurable. A positive WCG is
  direct evidence that workflow context -- not just difficulty -- drives the gains, isolating
  our design point from query-level routing (RouteLLM/FrugalGPT/AutoMix-style).
- How computed (analysis-time protocol around the implemented function): workflow-aware router =
  `cascade` or `adaptive`; best context-free comparator = `complexity` (fallbacks `random` /
  `fixed_mixed`), constrained to spend no more (matched <= cost). The caller selects the
  matched-cost comparator; the function returns the delta. Significance via paired bootstrap.
- Code location: IMPLEMENTED. `routing_metrics.workflow_context_gain(workflow_aware_quality,
  best_context_free_quality)`; significance `routing_metrics.paired_bootstrap_pvalue`. The
  matched-cost SELECTION of comparators is analysis-time (no code change).
- Publication usage: Figure F3 (matched-cost markers), headline row of results; primary
  evidence for C4 (the key claim). Also referenced by C1.

### 2.8 Pareto position

- Formula: a router's point `(cost_per_task, quality)` and whether it lies on the
  cost-quality Pareto frontier of the router set (non-dominated points).
- Interpretation: where each router sits on the achievable cost-quality frontier; the visual
  summary of the entire trade-off.
- Why reviewers care: the single figure that communicates the whole result; reviewers expect a
  Pareto/frontier plot for any efficiency claim.
- How computed: plot all routers as `(cost_per_task, EM-or-F1)`; the frontier is the upper-left
  envelope. Inputs are already-implemented `cost_per_task` and EM/F1.
- Code location: SPEC-ONLY: analysis-time, computed from the implemented `cost_per_task` and
  `exact_match`/`mean_f1` outputs; plotted by `src/visualization/figures.py` (`fig4_pareto_<ds>`).
  No new metric code.
- Publication usage: Figure F3 (Cost-vs-Quality / Pareto Frontier), per dataset. Supports
  C2, C3, C6, C7.

---

## 3. SECONDARY metrics

Support the headline story: operational cost, routing-decision quality, and behavior.

### 3.1 Latency

- Formula: `latency = (1/N) sum_i lat_i`, `lat_i = sum of latency_s over the problem's agent rows`.
- Interpretation: average wall-time proxy per problem (seconds).
- Why reviewers care: routing to cheaper tiers must not silently destroy responsiveness;
  reviewers ask "what does it cost in latency?".
- How computed: sum `latency_s` per problem -> mean over N. Caveat: this is a sum-of-call proxy,
  not measured end-to-end wall clock (sequential agents).
- Code location: IMPLEMENTED (aggregation): `aggregate` sums `latency_s`. No dedicated formula
  function; throughput below wraps the same input.
- Publication usage: Table T3 (Latency Analysis). Supports C8 (full reporting).

### 3.2 Throughput

- Formula: `throughput = N / (sum_i lat_i / 60)` (problems/min).
- Interpretation: problems completed per minute, using summed latency as a wall-clock proxy.
- Why reviewers care: operational framing of latency; ties cost savings to deployment capacity.
- How computed: total latency (s) across all problems -> N / (total/60).
- Code location: IMPLEMENTED. `routing_metrics.throughput_per_min(n, total_latency_s)`.
- Publication usage: Table T3. Supports C8.

### 3.3 Token Efficiency

- Formula: `token_efficiency = correct_count / (sum_i tok_i / 1e6)` (correct answers per 1M tokens).
- Interpretation: quality produced per unit of token spend; a cost proxy independent of price
  assumptions.
- Why reviewers care: prices are hypothetical (C8); token efficiency is a price-free efficiency
  measure that survives a reviewer disputing the $/1M numbers.
- How computed: count correct (verifier rows) / (total tokens / 1e6) per (dataset, router).
- Code location: IMPLEMENTED. `routing_metrics.token_efficiency(correct_count, total_tokens)`.
- Publication usage: Table T2 (secondary column). Supports C3, C8.

### 3.4 Routing Accuracy

- Formula: fraction of SOLVABLE problems where `representative_tier == oracle_tier`.
- Interpretation: how often the router picks exactly the cheapest tier that would solve the
  problem (the oracle's choice).
- Why reviewers care: separates "router decision quality" from "model ceiling"; shows the
  router is making the RIGHT choices, not just riding strong base models.
- How computed: oracle tier per problem from per-tier baseline correctness
  (`routing_metrics.oracle_tier`); representative tier = verifier-row `tier`; problems with
  `oracle = None` excluded.
- Code location: IMPLEMENTED. `routing_metrics.routing_accuracy(chosen_tiers, oracle_tiers)`;
  helper `routing_metrics.oracle_tier`.
- Publication usage: Table T6 (Router Comparison). Supports C6.

### 3.5 Escalation Rate

- Formula: `escalation_rate = (1/M) sum over agent CALLS of escalated`, `M = number of calls`.
- Interpretation: fraction of agent calls where the router moved above its base tier (the
  cascade/confidence mechanism firing).
- Why reviewers care: makes the routing MECHANISM observable -- shows confidence-driven
  escalation is actually used, not vestigial.
- How computed: per-call `escalated` derived from `escalated_from` non-empty; mean over calls.
- Code location: IMPLEMENTED. `routing_metrics.escalation_rate(escalated_flags)`.
- Publication usage: Figure F5 (Escalation Distribution; `fig7_escalation_<ds>`), Table T6.
  Supports C4, C5 (confidence-signal behavior).

### 3.6 Tier distribution

- Formula: histogram of representative (or per-call) `tier` over T1..T4 for each router.
- Interpretation: how the router spreads load across tiers; explains WHERE savings come from.
- Why reviewers care: a transparency/sanity check -- e.g. shows `fixed_*` are degenerate, and
  that `adaptive` actually mixes tiers rather than collapsing to one.
- How computed: count `tier` values (verifier rows for representative; all rows for utilization)
  per (dataset, router); normalize.
- Code location: SPEC-ONLY: analysis-time histogram of the logged `tier` column; plotted by
  `figures.py` (`fig5_utilization_<ds>`). No metric-function change.
- Publication usage: Figure F6 (Routing Frequency / Model Utilization). Supports C3, C5.

---

## 4. DIAGNOSTIC metrics

Error-analysis and calibration measures; deepen the analysis, not headline numbers.

### 4.1 Over-Provision Rate

- Formula: fraction of SOLVABLE problems with `representative_tier > oracle_tier`.
- Interpretation: how often the router paid for more capability than needed (wasted cost).
- Why reviewers care: explains the cost side of routing errors; localizes where savings leak.
- How computed: per-problem chosen vs oracle tier; count chosen>oracle / solvable.
- Code location: IMPLEMENTED. `routing_metrics.over_provision_rate(chosen_tiers, oracle_tiers)`.
- Publication usage: Table T5 (Error Analysis). Supports C5 (budget/role ablations), C8.

### 4.2 Under-Provision Rate

- Formula: fraction of SOLVABLE problems the router got WRONG (winnable but under-powered).
- Interpretation: how often the router was too cheap and lost a winnable problem (the quality
  side of routing errors).
- Why reviewers care: the failure mode that hurts quality; pairs with over-provision to
  characterize the router's bias.
- How computed: among solvable problems (`oracle != None`), count `not correct_i` / solvable.
- Code location: IMPLEMENTED.
  `routing_metrics.under_provision_rate(chosen_tiers, oracle_tiers, correct_flags)`.
- Publication usage: Table T5. Supports C5, C8.

### 4.3 Budget Violations

- Formula: `budget_violation_rate = (1/R) sum over budget runs of [cost_spent > cost_budget]`,
  where `cost_spent = sum_i cost_i` for the run and `cost_budget` is the configured cap.
- Interpretation: how often a budget-capped router exceeds its cost cap (cap enforcement check).
- Why reviewers care: the budget signal is one of the ablated components (C5); reviewers want
  evidence the cap is actually honored, not nominal.
- How computed: SPEC-ONLY / analysis-time. On budget runs, compare run-total `cost_usd`
  (summed) against the run's configured budget. The cap value is a RUN CONFIG input recorded
  with the experiment (e.g. `experiment_id` / manifest, see
  [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md)); the spend is from logged `cost_usd`.
- Code location: SPEC-ONLY: analysis-time, computed from `cost_usd` (summed per run) vs the
  configured budget; no code change. Not a function in `routing_metrics.py`.
- Publication usage: Table T4 (Ablation Study) -- `adaptive` vs `adaptive_no_budget`. Supports C5.

### 4.4 Win Rate

- Formula: on the SAME problems, `win_rate(A vs B) = mean_i [ q(A_i) > q(B_i) ]` with ties
  optionally split; `q` = `correct` (or `f1`). Report wins / losses / ties.
- Interpretation: head-to-head problem-level dominance of one router over another, paired.
- Why reviewers care: a paired, distribution-aware complement to mean EM gaps; harder to dismiss
  than an aggregate difference and intuitive for a "which is better" verdict.
- How computed: SPEC-ONLY / analysis-time. Join two routers' rows on `problem_id` (same
  dataset), compare per-problem `correct`/`f1`, tally. Significance via the IMPLEMENTED
  `routing_metrics.paired_bootstrap_pvalue` on the per-problem outcome vectors.
- Code location: SPEC-ONLY: analysis-time, computed from `problem_id` + `correct`/`f1`; no new
  metric function (reuses `paired_bootstrap_pvalue` for the p-value).
- Publication usage: Table T6 (Router Comparison). Supports C4, C6.

### 4.5 Utility Score

- Formula: `utility = quality - lambda * cost`, with quality = EM (or F1) fraction and cost =
  `cost_per_task`. FROZEN lambda for the paper: `lambda = 1.0` per USD-per-task (quality
  fraction units), i.e. one quality point (0.01) trades against $0.01/task. Report a small
  sensitivity sweep (lambda in {0.5, 1.0, 2.0}) for robustness.
- Interpretation: a single scalar collapsing the trade-off under an explicit, fixed price on
  quality vs cost; useful for ranking routers when a frontier plot is ambiguous.
- Why reviewers care: gives a defensible single-number ranking AND, via the sweep, shows the
  ranking is not an artifact of one lambda choice.
- How computed: SPEC-ONLY / analysis-time from already-aggregated EM/F1 and `cost_per_task`.
- Code location: SPEC-ONLY: analysis-time, computed from columns/aggregates EM, F1, `cost_usd`;
  no code change. (lambda frozen here so the number is reproducible.)
- Publication usage: Table T6 (auxiliary ranking column); referenced in discussion. Supports
  C3, C6.

### 4.6 Pareto Dominance

- Formula: router A dominates B iff `cost(A) <= cost(B)` AND `quality(A) >= quality(B)` with at
  least one strict; report each router's dominated/dominating set and frontier membership.
- Interpretation: rigorous, lambda-free statement of "strictly better on both axes"; the formal
  backbone of the Pareto figure.
- Why reviewers care: a dominance claim needs no weighting assumption, so it is the most
  defensible form of "our router is better"; reviewers trust it more than a single utility number.
- How computed: SPEC-ONLY / analysis-time over the set of `(cost_per_task, quality)` points.
- Code location: SPEC-ONLY: analysis-time, computed from `cost_per_task` and `exact_match`/
  `mean_f1` outputs; no new code. Visualized via `fig4_pareto_<ds>` in `figures.py`.
- Publication usage: Figure F3 + accompanying text. Supports C2, C3, C6, C7.

### 4.7 Confidence Calibration Error / ECE

- Formula: bin agent calls into `K` equal-width confidence bins (freeze `K = 10`); per bin `b`
  with `n_b` calls: `acc_b = mean(correct)`, `conf_b = mean(confidence)`;
  `ECE = sum_b (n_b/M) * |acc_b - conf_b|`, `M = total calls`.
- Interpretation: how well the upstream `confidence` signal matches realized correctness;
  low ECE = trustworthy confidence.
- Why reviewers care: the cascade/adaptive escalation logic CONSUMES confidence; ECE shows that
  signal is meaningful, justifying confidence-driven routing (and contextualizing the
  `adaptive_no_confidence` ablation).
- How computed: SPEC-ONLY / analysis-time from logged `confidence` and `correct` over agent
  calls (typically the analyzer/solver whose confidence feeds escalation). Freeze K=10,
  equal-width bins, for reproducibility.
- Code location: SPEC-ONLY: analysis-time, computed from columns `confidence`, `correct`; no
  code change. Not a function in `routing_metrics.py`.
- Publication usage: Table T5 (Error Analysis) / discussion of the confidence signal. Supports
  C5, C8.

---

## 5. Statistical-validity tooling (applies to every headline number)

| Tool | Use | Status / Code |
|---|---|---|
| Percentile bootstrap 95% CI | CI on EM/F1 means (per-problem 0/1 or F1 resampled) | IMPLEMENTED `routing_metrics.bootstrap_ci` |
| Paired bootstrap p-value | router-vs-baseline / WCG significance on the SAME problems | IMPLEMENTED `routing_metrics.paired_bootstrap_pvalue` |

`N=200` gives EM 95% CIs of roughly +/-7 pts at 50% (+/-3.4 pts at 90%). Report CIs on every
headline number and paired p-values for router-vs-T4 and WCG comparisons. Both functions are
deterministic given `seed` (default 42, `n_boot=10000`). Serves C8 throughout.

---

## 6. Metric selection rationale

- Why EM AND F1 (both): EM is the standard, comparable success measure, but it is brittle to
  verbose / differently-phrased answers -- exactly the failure behind the verified Tier-4
  multi-hop anomaly (Tier-4 EM below weaker tiers). F1 gives partial credit and a stable
  ranking. Reporting both is the honesty contract (C8) and prevents a misleading conclusion; on
  GSM8K F1 collapses to EM so only EM is reported there.
- Why ratios, not absolute cost (CRF / Cost Savings % / QRR / Token Efficiency): the $/1M
  prices are HYPOTHETICAL (models run free locally / on free tiers; T3 and T4 also share one
  token pool, RISK R1). Absolute USD would imply false precision and would not survive a
  reviewer disputing the price table. Ratios against the fixed all-Tier-4 reference are
  invariant to a global price re-scaling and to swapping the price source, so the trade-off
  claim (C3) is robust. Token Efficiency adds a fully price-free efficiency axis as a backstop.
- Why WCG is the single headline: CRF/QRR show routing helps, but a query-level router could
  show the same. WCG, at MATCHED cost, isolates the value of the workflow-only signals (role,
  upstream confidence, stage) versus difficulty-only routing -- the actual novelty (C1, C4).
  This is why the comparator is fixed to `complexity` (difficulty-only) at <= cost.
- Why a per-problem ORACLE underpins the routing-quality metrics: Routing Accuracy / Over- /
  Under-Provision measure DECISION quality independent of model ceiling, answering "is the
  router choosing well?" rather than "are the base models strong?" -- the question reviewers ask
  to credit the router rather than the backbone (C6).
- Why three groups (PRIMARY / SECONDARY / DIAGNOSTIC): PRIMARY carries the claims and the main
  tables/figures; SECONDARY proves the gains do not come at a hidden operational cost (latency /
  throughput) and that the mechanism behaves (escalation, tier mix); DIAGNOSTIC supports error
  analysis and signal-validity (calibration, win rate, budget enforcement) without inflating the
  headline metric count.
- Honest implemented-vs-spec split: 11 metrics are IMPLEMENTED and frozen in code; 7 are
  SPEC-ONLY but computable at analysis time from the frozen logged columns with NO code or
  router change. Marking them SPEC-ONLY (rather than implementing now) preserves the freeze
  while keeping the analyses available. lambda (Utility) and K (ECE) are frozen here so the
  spec-only numbers are reproducible.

---

## 7. Metric -> claim -> table/figure traceability

| Metric | Group | Claims | Tables | Figures |
|---|---|---|---|---|
| EM / Accuracy | PRIMARY | C2,C3,C6,C7,C8 | T1,T5,T7 | F3 |
| Token-F1 | PRIMARY | C7,C8 | T1,T5,T7 | F3 |
| Cost-per-task | PRIMARY | C2,C3,C6 | T2 | F3 |
| Cost Reduction Factor | PRIMARY | C3 | T2 | -- |
| Cost Savings % | PRIMARY | C3 | T2 | -- |
| Quality Retention (QRR) | PRIMARY | C3 | T1,T2 | F3 |
| Workflow Context Gain | PRIMARY (HEADLINE) | C1,C4 | T6 | F3 |
| Pareto position | PRIMARY | C2,C3,C6,C7 | -- | F3 |
| Latency | SECONDARY | C8 | T3 | -- |
| Throughput | SECONDARY | C8 | T3 | -- |
| Token Efficiency | SECONDARY | C3,C8 | T2 | -- |
| Routing Accuracy | SECONDARY | C6 | T6 | -- |
| Escalation Rate | SECONDARY | C4,C5 | T6 | F5 |
| Tier distribution | SECONDARY | C1,C3,C5 | -- | F6 |
| Over-Provision Rate | DIAGNOSTIC | C5,C8 | T5 | -- |
| Under-Provision Rate | DIAGNOSTIC | C5,C8 | T5 | -- |
| Budget Violations | DIAGNOSTIC (spec-only) | C5 | T4 | -- |
| Win Rate | DIAGNOSTIC (spec-only) | C4,C6 | T6 | -- |
| Utility Score | DIAGNOSTIC (spec-only) | C3,C6 | T6 | -- |
| Pareto Dominance | DIAGNOSTIC (spec-only) | C2,C3,C6,C7 | -- | F3 |
| Confidence Calibration Error / ECE | DIAGNOSTIC (spec-only) | C5,C8 | T5 | -- |

All result cells populated by these metrics are PLACEHOLDERS ([X.X] / TBD-after-run) at this
freeze, except the verified-offline anchors in Section 0, which are explicitly labelled.
