# Paper Tables Template (Canonical T1-T7)

> Status: FROZEN (methodology freeze; results are placeholders)
> Related docs: [14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md), [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md),
> [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md), [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md),
> [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md), [15_FIGURE_PLAN.md](15_FIGURE_PLAN.md),
> [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md), [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md).

This file is the PART 5 deliverable: the seven canonical paper tables (T1-T7) as markdown
templates with real column headers and PLACEHOLDER cells. Every results number is a placeholder
([X.X], [X.XXX], TBD-after-run). The only REAL numbers anywhere in this doc are explicitly
labelled "verified offline" and reproduce values from [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md)
(GSM8K baselines LOCKED; all multi-hop F1 PENDING clean re-run). Do not insert any other live
numbers until the home-machine runs land and `aggregate_results.py` rebuilds
`results/master_results.{json,csv,md}`.

---

## Conventions (apply to all tables)

- N = 200 problems per (dataset, router) cell unless noted. Datasets: GSM8K (1-hop, numeric EM,
  no F1), HotpotQA (2-hop, EM + token-F1), MuSiQue (2-4 hop, EM + token-F1).
- Routers use the exact `get_router` names. The 15-router catalogue (grouped) is:
  - Reference / anchors: `oracle` (ceiling), `random` (floor), `fixed_t1`, `fixed_t2`,
    `fixed_t3`, `fixed_t4` (= the single-tier baselines), `fixed_mixed`.
  - Proposed (context-aware): `complexity`, `cascade`, `adaptive`, `learned`.
  - Ablations of `adaptive`: `adaptive_no_complexity`, `adaptive_no_role`,
    `adaptive_no_confidence`, `adaptive_no_budget`.
- Reference for cost/quality comparisons = the all-Tier-4 pipeline (`fixed_t4`):
  cost reference and quality ceiling (`aggregate.REFERENCE_TIER`; see
  [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) C/D).
- Cost is HYPOTHETICAL USD from published price ratios (T1 0.03/0.06, T2 0.59/0.79,
  T3 2.66/2.66, T4 2.00/8.00 per 1M in/out; [03_MODEL_MATRIX.md](03_MODEL_MATRIX.md), RISK R10).
  Report ratios (savings x), not absolute USD claims.
- Cost-per-task is the per-problem summed cost over the three agent calls (Analyzer, Solver,
  Verifier), not a single call.
- ALWAYS report EM AND F1 (claim C8). KNOWN ANOMALY: Tier-4 EM is lower than weaker tiers on
  multi-hop (EM brittleness to verbose frontier answers); F1 contextualizes it. QRR can exceed
  100% on multi-hop for the same reason ([13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) D).
- CI: percentile bootstrap 95% CI on EM/F1 means (`routing_metrics.bootstrap_ci`); reported as
  +/-CI half-width in points. N=200 gives EM 95% CI of roughly +/-7 pts at 50%, +/-3.4 pts at 90%.
- Significance markers (paired bootstrap vs the stated reference, `routing_metrics.paired_bootstrap_pvalue`):
  `*` p<0.05, `**` p<0.01, `***` p<0.001, `n.s.` not significant. The reference router for each
  test is stated in the table caption.
- "spec-only / analysis-time" = computable from the logged CSV columns at analysis time WITHOUT
  any code or router change (no implemented function yet); flagged inline where used.
- Source after live runs: `results/master_results.{json,csv,md}` via `aggregate_results.py`
  (data flow in [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) F). Commands in
  [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md).

---

## T1 - Main Benchmark Results

**Caption (draft).** Main benchmark results across the three datasets (N=200 each). For each
dataset we report Exact Match (EM) and token-F1 (GSM8K is numeric: F1 collapses to EM, shown as
"-"), per-task hypothetical cost (USD), and the bootstrap 95% CI half-width (+/-, points) on the
primary quality metric (EM for GSM8K, F1 for multi-hop). Rows are grouped: reference anchors,
single-tier baselines, proposed context-aware routers, and the learned router. Significance
markers compare each router's primary quality metric against the all-Tier-4 baseline (`fixed_t4`)
via paired bootstrap on the same problems. The Tier-4 EM anomaly on multi-hop (see C8) is why F1
is reported alongside EM. Verified-offline GSM8K baseline cells are noted; all other cells are
placeholders pending live routed runs.

**Supports claim(s): C2, C3, C6, C7, C8.**

Columns: Router | GSM8K EM (%) | GSM8K F1 | GSM8K cost/task ($) | GSM8K +/-CI |
HotpotQA EM (%) | HotpotQA F1 (%) | HotpotQA cost/task ($) | HotpotQA +/-CI |
MuSiQue EM (%) | MuSiQue F1 (%) | MuSiQue cost/task ($) | MuSiQue +/-CI

| Router | G EM (%) | G F1 | G $/task | G +/-CI | H EM (%) | H F1 (%) | H $/task | H +/-CI | M EM (%) | M F1 (%) | M $/task | M +/-CI |
|--------|:--------:|:----:|:--------:|:-------:|:--------:|:--------:|:--------:|:-------:|:--------:|:--------:|:--------:|:-------:|
| oracle | [X.X] | - | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] |
| random | [X.X] | - | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] |
| fixed_t1 | 94.5 | - | 0.000157 | [X.X] | 63.0 | TBD | [X.XXXX] | [X.X] | 31.5 | TBD | [X.XXXX] | [X.X] |
| fixed_t2 | 96.0 | - | 0.001093 | [X.X] | 65.25 | TBD | [X.XXXX] | [X.X] | 55.0 | TBD | [X.XXXX] | [X.X] |
| fixed_t3 | 97.0 | - | 0.004110 | [X.X] | 54.17 | TBD | [X.XXXX] | [X.X] | 47.5 | TBD | [X.XXXX] | [X.X] |
| fixed_t4 | 97.0 | - | 0.005912 | [X.X] | 37.5 | TBD | [X.XXXX] | [X.X] | 25.6 | TBD | [X.XXXX] | [X.X] |
| fixed_mixed | [X.X] | - | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] |
| complexity | [X.X] | - | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] |
| cascade | [X.X] | - | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] |
| adaptive | [X.X] | - | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] |
| learned | [X.X] | - | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] | [X.X] | [X.X] | [X.XXXX] | [X.X] |

Notes:
- Verified offline (LOCKED, GSM8K baselines): EM and cost/task for `fixed_t1..fixed_t4`
  (94.5/96.0/97.0/97.0 EM; cost/task = total/200 from $0.0314/0.2186/0.8220/1.1824).
- Multi-hop EM (reliable today, but on inconsistent N): HotpotQA EM `fixed_t1`=63.0 (200),
  `fixed_t2`=65.25 (clean partial 118/200), `fixed_t3`=54.17 (clean partial 48/200),
  `fixed_t4`=37.5 (truncated backup 200, anomaly); MuSiQue EM `fixed_t1`=31.5 (200),
  `fixed_t2`=55.0 (backup 200), `fixed_t3`=47.5 (backup 200), `fixed_t4`=25.6 (backup, **N=199**,
  one problem missing). These EM values are shown for orientation only; they come from mixed
  sources/N (some truncated backups) and are NOT verified-offline LOCKED like GSM8K.
- Multi-hop cost/task cells are left as `[X.XXXX]` placeholders: per the freeze rule, only the
  verified-offline GSM8K costs may be concrete. Earlier provisional values were dropped because
  they were back-derived from mixed N (e.g. HotpotQA T2 from the clean-118 total vs T3 from the
  backup-200 total) and would not be comparable.
- ALL multi-hop F1 = TBD (legacy logger truncated responses at 500 chars; pending the clean N=200
  re-run, [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md) / [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md)).
- Significance (`*`) markers are added only after live CIs land (paired bootstrap / McNemar vs
  `fixed_t4`, see [statistical_validation_plan.md](statistical_validation_plan.md)); none are shown now.
- Companion figure: F3 Cost-vs-Quality / Pareto Frontier (`fig4_pareto_<dataset>`).

---

## T2 - Cost Analysis

**Caption (draft).** Cost analysis against the all-Tier-4 reference pipeline (`fixed_t4`).
Cost/task is per-problem hypothetical USD; Cost Reduction Factor = cost(`fixed_t4`)/cost(router)
(`routing_metrics.cost_reduction_factor`); Savings % = (1 - cost(router)/cost(`fixed_t4`))*100
(`routing_metrics.cost_savings_pct`); Cost-per-Correct = total cost / number of correct answers
(spec-only / analysis-time: derivable from logged `cost_usd` and `correct`). Reported per dataset.
Cost is hypothetical (RISK R10); we emphasize ratios over absolute USD. `fixed_t4` is the
reference (reduction 1.0x, savings 0%). Significance markers compare router cost-per-correct
against `fixed_t4` via paired bootstrap.

**Supports claim(s): C2, C3, C7, C8.**

Columns: Router | Dataset | Cost/task ($) | Cost Reduction (x) | Savings (%) | Cost/Correct ($)

| Router | Dataset | Cost/task ($) | Reduction (x) | Savings (%) | Cost/Correct ($) |
|--------|---------|:-------------:|:-------------:|:-----------:|:----------------:|
| oracle | GSM8K | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| oracle | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| oracle | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t1 | GSM8K | 0.000157 | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t1 | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t1 | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t2 | GSM8K | 0.001093 | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t2 | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t2 | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t3 | GSM8K | 0.004110 | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t3 | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t3 | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_t4 (ref) | GSM8K | 0.005912 | 1.0 | 0.0 | [X.XXXX] |
| fixed_t4 (ref) | HotpotQA | [X.XXXX] | 1.0 | 0.0 | [X.XXXX] |
| fixed_t4 (ref) | MuSiQue | [X.XXXX] | 1.0 | 0.0 | [X.XXXX] |
| fixed_mixed | GSM8K | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_mixed | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| fixed_mixed | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| complexity | GSM8K | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| complexity | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| complexity | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| cascade | GSM8K | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| cascade | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| cascade | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| adaptive | GSM8K | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| adaptive | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| adaptive | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| learned | GSM8K | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| learned | HotpotQA | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |
| learned | MuSiQue | [X.XXXX] | [XX.X] | [XX.X] | [X.XXXX] |

Notes:
- Verified offline: GSM8K `fixed_t*` cost/task (LOCKED). Verified offline (sim): oracle GSM8K
  total $0.0485/200 -> cost/task 0.000243 (placeholder kept as [X.XXXX] pending live confirmation).
- Cost-per-Correct is spec-only / analysis-time (no dedicated function; compute as
  sum(`cost_usd`)/sum(`correct`) per (router,dataset) from the routed CSVs).
- Ablation rows (`adaptive_no_*`) are reported in T4 at matched budget; omitted here to keep T2
  focused on the headline cost story.
- Companion figure: F3 Cost-vs-Quality / Pareto Frontier (`fig4_pareto_<dataset>`).

---

## T3 - Latency Analysis

**Caption (draft).** Latency and throughput per router and dataset. Latency = mean per-problem
summed agent latency in seconds (`aggregate`); Throughput = N / (sum latency / 60) problems/min,
using sum-of-latency as a wall-clock proxy (`routing_metrics.throughput_per_min`); Token
Efficiency = correct answers per 1M tokens (`routing_metrics.token_efficiency`). Latency is
hardware/provider dependent (Ollama-local T1, Groq T2, GitHub Models T3/T4 sharing one token
pool, RISK R1) and is a SECONDARY metric; it is reported for completeness, not as a primary claim.

**Supports claim(s): C3, C7 (secondary support); C8 (honest reporting).**

Columns: Router | Dataset | Latency (s/task) | Throughput (probs/min) | Token Efficiency (correct/1M tok)

| Router | Dataset | Latency (s/task) | Throughput (probs/min) | Token Eff (correct/1M) |
|--------|---------|:----------------:|:----------------------:|:----------------------:|
| oracle | GSM8K | [XX.X] | [X.X] | [XX.X] |
| oracle | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| oracle | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| fixed_t1 | GSM8K | 98.3 | [X.X] | [XX.X] |
| fixed_t1 | HotpotQA | 78.7 | [X.X] | [XX.X] |
| fixed_t1 | MuSiQue | 103.9 | [X.X] | [XX.X] |
| fixed_t2 | GSM8K | 3.3 | [X.X] | [XX.X] |
| fixed_t2 | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| fixed_t2 | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| fixed_t3 | GSM8K | 54.3 | [X.X] | [XX.X] |
| fixed_t3 | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| fixed_t3 | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| fixed_t4 | GSM8K | 12.1 | [X.X] | [XX.X] |
| fixed_t4 | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| fixed_t4 | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| fixed_mixed | GSM8K | [XX.X] | [X.X] | [XX.X] |
| fixed_mixed | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| fixed_mixed | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| complexity | GSM8K | [XX.X] | [X.X] | [XX.X] |
| complexity | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| complexity | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| cascade | GSM8K | [XX.X] | [X.X] | [XX.X] |
| cascade | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| cascade | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| adaptive | GSM8K | [XX.X] | [X.X] | [XX.X] |
| adaptive | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| adaptive | MuSiQue | [XX.X] | [X.X] | [XX.X] |
| learned | GSM8K | [XX.X] | [X.X] | [XX.X] |
| learned | HotpotQA | [XX.X] | [X.X] | [XX.X] |
| learned | MuSiQue | [XX.X] | [X.X] | [XX.X] |

Notes:
- Verified offline (avg latency, baselines from ledger): GSM8K T1/T2/T3/T4 = 98.3/3.3/54.3/12.1s;
  HotpotQA T1 = 78.7s; MuSiQue T1 = 103.9s. Latency is per-tier provider-bound and NOT a fair
  cross-provider comparison (R1); flag in the paper.
- Throughput and Token Efficiency cells require routed CSVs (sum `latency_s`, `input_tokens`,
  `output_tokens`, `correct`) and are placeholders.

---

## T4 - Ablation Study (matched budget)

**Caption (draft).** Ablation of the `adaptive` router's signal families at MATCHED budget:
each `adaptive_no_*` variant removes one signal family (complexity / role / confidence / budget)
while holding the cost budget fixed so quality differences isolate that signal's contribution.
We report EM, F1 (multi-hop), and cost/task per dataset; Delta EM is relative to full `adaptive`.
A negative Delta EM indicates the removed signal was contributing. Significance markers compare
each variant against full `adaptive` via paired bootstrap on the same problems. Companion figure:
F4 Ablation Results (`fig6_ablation_<dataset>`).

**Supports claim(s): C5 (primary), C4 (workflow-signal value), C8.**

Columns: Variant | Dataset | EM (%) | F1 (%) | Cost/task ($) | Delta EM vs adaptive (pts) | Sig.

| Variant | Dataset | EM (%) | F1 (%) | Cost/task ($) | Delta EM (pts) | Sig. |
|---------|---------|:------:|:------:|:-------------:|:--------------:|:----:|
| adaptive (full) | GSM8K | [X.X] | - | [X.XXXX] | 0.0 | ref |
| adaptive (full) | HotpotQA | [X.X] | [X.X] | [X.XXXX] | 0.0 | ref |
| adaptive (full) | MuSiQue | [X.X] | [X.X] | [X.XXXX] | 0.0 | ref |
| adaptive_no_complexity | GSM8K | [X.X] | - | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_complexity | HotpotQA | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_complexity | MuSiQue | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_role | GSM8K | [X.X] | - | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_role | HotpotQA | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_role | MuSiQue | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_confidence | GSM8K | [X.X] | - | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_confidence | HotpotQA | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_confidence | MuSiQue | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_budget | GSM8K | [X.X] | - | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_budget | HotpotQA | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |
| adaptive_no_budget | MuSiQue | [X.X] | [X.X] | [X.XXXX] | [-X.X] | [*] |

Notes:
- "Matched budget" means the same `cost_budget` is passed to all variants so cost is comparable;
  any residual cost difference is reported in the Cost/task column for transparency.
- Sig. column placeholders ([*]) become `*`/`**`/`***`/`n.s.` after paired bootstrap vs `adaptive`.
- All cells pending §D ablation runs ([16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md)).

---

## T5 - Error Analysis (failure categories x router)

**Caption (draft).** Distribution of failure categories per router, aggregated across datasets
(or reported per dataset in the appendix). Each cell is the percentage of that router's INCORRECT
problems falling in the category (columns sum to ~100% per router, modulo multi-label). Categories
are derived at analysis time from the logged columns (`correct`, `f1`, `predicted`,
`ground_truth`, `routing_reason`, `escalated_from`, `tier`) and are spec-only / analysis-time
(no implemented categorizer; manual + rule-based coding). Companion figure: F7 Failure Categories
(`fig7_*` family / dedicated panel). Reporting failure modes supports the honesty claim C8.

**Supports claim(s): C5, C8; context for C3/C4.**

Failure categories (columns):
- Under-provision: winnable problem (oracle tier exists) routed below the needed tier.
- Over-provision wasted: correct but routed above oracle tier (cost waste, not an error; tracked
  separately for cost story, shown for completeness).
- EM-only miss (F1>0.5): substantively correct answer that fails strict EM (the Tier-4 anomaly
  class; multi-hop).
- Cascade/escalation failure: escalated (`escalated_from` set) yet still incorrect.
- Unsolvable: no tier solved it in baselines (model-ceiling, not a routing error).
- Other/format: parsing, refusal, empty, or formatting failure.

Columns: Router | Under-provision (%) | EM-only miss F1>0.5 (%) | Cascade-fail (%) | Unsolvable (%) | Other/format (%)

| Router | Under-prov (%) | EM-only miss (%) | Cascade-fail (%) | Unsolvable (%) | Other/format (%) |
|--------|:--------------:|:----------------:|:----------------:|:--------------:|:----------------:|
| oracle | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| random | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| fixed_t1 | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| fixed_t2 | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| fixed_t3 | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| fixed_t4 | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| fixed_mixed | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| complexity | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| cascade | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| adaptive | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| learned | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| adaptive_no_complexity | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| adaptive_no_role | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| adaptive_no_confidence | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |
| adaptive_no_budget | [X.X] | [X.X] | [X.X] | [X.X] | [X.X] |

Notes:
- Spec-only / analysis-time: the categorizer is a planned analysis script over the logged CSVs;
  no code change to the router/pipeline is required. Cascade-fail uses `escalated_from`.
- "Cascade-fail" is N/A (report "-") for routers that never escalate (`oracle`, `random`,
  `fixed_*`, `complexity`, `adaptive_no_confidence`); the cascade signal is only present in
  `cascade` and confidence-using `adaptive` variants.
- The EM-only-miss column is the quantitative form of the Tier-4 EM anomaly (C8); expect it
  highest for high-tier-heavy routers on multi-hop.

---

## T6 - Router Comparison (all 15 routers)

**Caption (draft).** Headline comparison of all 15 routers on a single representative dataset
(default: MuSiQue, the hardest; replicate per dataset in the appendix). For each router we report
EM, F1, cost/task, Cost Reduction Factor vs `fixed_t4`, Quality Retention Rate vs `fixed_t4`
(EM-based; F1-based in parentheses), Routing Accuracy (fraction of solvable problems where the
verifier tier equals the oracle tier, `routing_metrics.routing_accuracy`), and Escalation Rate
(fraction of agent calls escalated above base, `routing_metrics.escalation_rate`). Routing
Accuracy and Escalation Rate are "-" for `oracle` (definitionally 100% / 0) and `fixed_*`
(no escalation) where not meaningful. Significance markers compare router EM against `random`
(floor) via paired bootstrap. This is the omnibus table the Pareto figure (F3) visualizes.

**Supports claim(s): C2, C3, C4, C6, C8.**

Columns: Router | EM (%) | F1 (%) | Cost/task ($) | Cost Reduction (x) | QRR EM% (F1%) | Routing Acc (%) | Escalation Rate (%) | Sig. vs random

| Router | EM (%) | F1 (%) | Cost/task ($) | Reduction (x) | QRR EM% (F1%) | Routing Acc (%) | Escal. Rate (%) | Sig. |
|--------|:------:|:------:|:-------------:|:-------------:|:-------------:|:---------------:|:---------------:|:----:|
| oracle | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | 100.0 | 0.0 | [*] |
| random | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | [X.X] | ref |
| fixed_t1 | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | - | [*] |
| fixed_t2 | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | - | [*] |
| fixed_t3 | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | - | [*] |
| fixed_t4 | [X.X] | [X.X] | [X.XXXX] | 1.0 | 100.0 (100.0) | [X.X] | - | [*] |
| fixed_mixed | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | - | [*] |
| complexity | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | - | [*] |
| cascade | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | [X.X] | [*] |
| adaptive | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | [X.X] | [*] |
| learned | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | - | [*] |
| adaptive_no_complexity | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | [X.X] | [*] |
| adaptive_no_role | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | [X.X] | [*] |
| adaptive_no_confidence | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | - | [*] |
| adaptive_no_budget | [X.X] | [X.X] | [X.XXXX] | [XX.X] | [XXX.X] ([XXX.X]) | [X.X] | [X.X] | [*] |

Notes:
- QRR can exceed 100% on multi-hop because `fixed_t4` EM is anomalously low (C8); report both
  EM-based and F1-based QRR (F1 in parentheses).
- Escalation Rate is "-" for routers without a confidence cascade
  (`fixed_*`, `complexity`, `learned`, `adaptive_no_confidence`); set only when `escalated_from`
  can be populated (`cascade`, `adaptive`, `adaptive_no_role/complexity/budget`).
- Routing Accuracy / Over-/Under-Provision use the VERIFIER tier as the representative tier and
  exclude unsolvable problems ([13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) B).
- Optional DIAGNOSTIC appendix columns (spec-only / analysis-time, omit from main table to save
  width): Over-Provision Rate, Under-Provision Rate, Win Rate (paired correct/F1 vs reference),
  Utility Score (= quality - lambda*cost; FREEZE lambda, state value), Confidence Calibration
  Error / ECE (confidence vs correct), Budget Violations (cost_spent vs cost_budget on budget runs).

---

## T7 - Cross-Dataset Generalization

**Caption (draft).** Cross-dataset generalization of cost-quality benefit along the difficulty
gradient GSM8K (1-hop) -> HotpotQA (2-hop) -> MuSiQue (2-4 hop). For each router x dataset we
report the two headline quantities together: Cost Savings % vs `fixed_t4` and Quality Retention
Rate vs `fixed_t4` (EM-based; the paired (savings%, QRR%) is the generalization signal). A router
generalizes if it holds high QRR at high savings across all three datasets. Workflow Context Gain
(WCG, EM pts) of `adaptive`/`cascade` vs the best context-free router (`complexity`) at matched
cost is shown in the dedicated WCG sub-rows; positive WCG across datasets is the headline C4
evidence. Significance markers on WCG use paired bootstrap vs `complexity` at matched cost.
The WCG test is the pre-registered PRIMARY hypothesis and is **one-sided** (H1: WCG > 0) per
[statistical_validation_plan.md](statistical_validation_plan.md) Section 8; all other comparisons
in these tables are two-sided.

**Supports claim(s): C7 (primary), C3, C4 (WCG sub-rows), C8.**

Columns: Router | GSM8K Savings% / QRR% | HotpotQA Savings% / QRR% | MuSiQue Savings% / QRR%

| Router | GSM8K Save% / QRR% | HotpotQA Save% / QRR% | MuSiQue Save% / QRR% |
|--------|:------------------:|:---------------------:|:--------------------:|
| oracle | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| random | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| fixed_t1 | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| fixed_t2 | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| fixed_t3 | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| fixed_t4 (ref) | 0.0 / 100.0 | 0.0 / 100.0 | 0.0 / 100.0 |
| fixed_mixed | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| complexity | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| cascade | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| adaptive | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |
| learned | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] | [XX.X] / [XXX.X] |

WCG sub-rows (Workflow Context Gain, EM pts, vs `complexity` at matched cost; headline C4):

| Comparison | GSM8K WCG (pts) | HotpotQA WCG (pts) | MuSiQue WCG (pts) |
|------------|:---------------:|:------------------:|:-----------------:|
| cascade - complexity | [+X.X] [*] | [+X.X] [*] | [+X.X] [*] |
| adaptive - complexity | [+X.X] [*] | [+X.X] [*] | [+X.X] [*] |

Notes:
- WCG uses EM by default; report an F1-based WCG row in the appendix (multi-hop), since the Tier-4
  EM anomaly motivates F1 corroboration (C8).
- Difficulty gradient framing: expect the benefit of workflow context to grow from GSM8K
  (near-ceiling, little headroom; RISK R6) toward MuSiQue (most headroom). State this hypothesis
  in Discussion ([14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md) section 8).
- Companion figure: F3 Pareto per dataset (`fig4_pareto_<dataset>`) shows the same data
  geometrically.

---

## Significance / placeholder legend (applies to every table)

- `*` p<0.05, `**` p<0.01, `***` p<0.001 (paired bootstrap vs the reference stated in the caption).
- `n.s.` not significant; `ref` reference row (no test); `-` not applicable for that router.
- `[X.X]`, `[X.XX]`, `[X.XXX]`, `[X.XXXX]`, `[XX.X]`, `[XXX.X]`, `[+X.X]`, `[-X.X]`, `[*]`, `TBD`
  are PLACEHOLDERS to be filled from `results/master_results.{json,csv,md}`
  (`aggregate_results.py`) plus the analysis-time scripts for spec-only metrics.
- The only non-placeholder numbers above are the cells explicitly labelled "verified offline"
  (GSM8K baselines LOCKED; multi-hop EM reliable; multi-hop F1 = TBD), reproduced from
  [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md). Do not edit those without re-running
  `scripts/validate_baselines.py`.
