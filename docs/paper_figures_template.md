> Status: FROZEN (methodology freeze; results are placeholders)
> Companion to existing freeze docs: see 15_FIGURE_PLAN.md (canonical figure list + code),
> 17_RESEARCH_CLAIMS.md (claims C1-C8 + evidence), 13_METRICS_AND_FORMULAS.md (metric defs),
> 14_PAPER_OUTLINE.md, 08_RESULTS_LEDGER.md, 16_EXPERIMENT_MANIFEST.md, BASELINE_VALIDATION_REPORT.md.
> This file is the PART 6 deliverable: the per-figure publication spec. It does NOT introduce
> new code. Generating functions referenced below already exist in src/visualization/figures.py.

# Paper Figures Template (Publication-Readiness Spec)

This document specifies, for every canonical figure, the exact data source, required metrics,
plot type, expected insight, generating code, and the claim (Cxx) and table (Txx) it pairs
with. It distinguishes SCHEMATIC figures (drawn from code, no experiment data) from DATA-DRIVEN
figures (read from `results/master_results.{json,csv,md}`, live from `aggregate_results.py`, or
offline fallback `results/routing_sim/*.json` from `simulate_routing.py`).

No fabricated data. Result numbers are placeholders `[X.X]` or `TBD-after-run`. The only real
numbers cited are explicitly labelled "verified offline" (from `scripts/validate_baselines.py`
+ `simulate_routing.py`); GSM8K baselines are LOCKED, all HotpotQA/MuSiQue F1 is PENDING clean
re-runs (legacy logger truncated responses at 500 chars).

---

## 0. Conventions used by every figure

- Datasets (each N=200): GSM8K (1-hop, EM only), HotpotQA (2-hop, EM+F1), MuSiQue (2-4 hop, EM+F1).
  Data figures are produced PER dataset: stem `<fig>_<dataset>` (e.g. `fig4_pareto_gsm8k`).
- Tier colors are fixed across all figures (`TIER_COLORS`): T1 red `#e74c3c`, T2 orange
  `#e67e22`, T3 blue `#3498db`, T4 green `#2ecc71`. Tier labels (`TIER_LABELS`):
  T1 Gemma 4B, T2 Llama 70B, T3 Llama 405B, T4 GPT-4.1.
- Reference for all savings/retention = the all-Tier-4 pipeline (`aggregate.REFERENCE_TIER`):
  quality ceiling and cost reference.
- Router marker convention in Pareto (`fig_pareto`): oracle = star, routers = circle (purple
  `#8e44ad`), baselines/fixed_t* = square (slate `#34495e`).
- ALWAYS report F1 alongside EM on multi-hop. KNOWN ANOMALY: Tier-4 EM is LOWER than weaker
  tiers on multi-hop (EM brittleness to verbose frontier answers) -> any EM-only multi-hop
  figure MUST be paired with the F1 variant or carry the anomaly caption (C8).
- Output: 200 DPI PNG (slides) for all; vector PDF for the four schematic/vector figures
  (F1/F2/F3 schematics + F3-Pareto). Regenerate: `python make_figures.py` after
  `aggregate_results.py`.
- Hypothetical-cost assumption (all models free in practice; $/1M are scenario prices, T3/T4
  share one token pool = RISK R1) must appear in the cost-axis caption (C8).

Canonical figure IDs map to existing code stems as follows. NOTE the two numbering systems
deliberately coexist: the SHARED canonical IDs (F1..F7, used in the paper body) vs the legacy
code stems `fig1..fig7` in `src/visualization/figures.py`. The crosswalk is authoritative:

| Canonical (paper) | Title | Code stem(s) | Function | Kind |
|-------------------|-------|--------------|----------|------|
| F1 | System Architecture | `fig1_architecture` | `fig_architecture` | schematic |
| F2 | Routing Decision Flow | `fig3_router_decision_flow` (+ `fig2_workflow` context) | `fig_router_decision_flow` (+ `fig_workflow`) | schematic |
| F3 | Cost-vs-Quality / Pareto Frontier [HEADLINE] | `fig4_pareto_<ds>` | `fig_pareto` | data |
| F4 | Ablation Results | `fig6_ablation_<ds>` | `fig_ablation` | data |
| F5 | Escalation Distribution | `fig7_escalation_<ds>` | `fig_escalation` | data |
| F6 | Routing Frequency / Model Utilization | `fig5_utilization_<ds>` | `fig_model_utilization` | data |
| F7 | Failure Categories | (spec-only, analysis-time plot) | none yet | data |
| F8 (supp.) | Confidence Calibration / ECE | (spec-only, analysis-time plot) | none yet | data |
| F9 (supp.) | Budget Sweep / Budget Violations | (spec-only, analysis-time plot) | none yet | data |

`fig2_workflow` (`fig_workflow`) is retained as a schematic companion to F2; it is not a
separate canonical paper figure but is available for the methods section and slides.

---

## F1 - System Architecture  [SCHEMATIC]

- Purpose: show the end-to-end design point -- problem -> signal extractor -> router (selects a
  tier PER agent) -> tier decision; the Analyzer -> Solver -> Verifier pipeline below; that the
  router selects a tier independently for each agent call. Establishes novelty (per-agent, not
  per-query routing).
- Data source: none (schematic, drawn from code).
- Metrics required: none.
- Plot type: boxes-and-arrows block diagram (top: problem/signals/router/decision; bottom:
  4 tier boxes color-coded; pipeline row).
- Expected insight: the contribution is structural -- routing happens inside a fixed pipeline,
  one decision per agent, using signals (role, upstream confidence, stage) unavailable to
  single-agent / query-level routers.
- Generating code: existing `fig_architecture()` -> `fig1_architecture.png/.pdf`.
- Schematic vs data-driven: SCHEMATIC (renders today, no data).
- Pairs with: claim C1 (per-agent routing feasible & novel). Table pairing: none direct;
  conceptually anchors T6 (Router Comparison). Cross-ref 01_RESEARCH_GAP.md,
  12_RESEARCH_CONTRIBUTION.md, ROUTER_FINAL_SPEC.md.

## F2 - Routing Decision Flow  [SCHEMATIC]

- Purpose: show the per-call decision logic of the `adaptive` router: complexity floor ->
  upstream-confidence check -> role base tier -> confidence escalate/de-escalate -> budget cap
  clamp. Companion schematic `fig2_workflow` shows that upstream output + confidence feed the
  next agent's routing decision.
- Data source: none (schematic, drawn from code).
- Metrics required: none.
- Plot type: flowchart (decision nodes + branch labels yes/high/low) for F2;
  3-box linear pipeline for the `fig2_workflow` companion.
- Expected insight: the router is a transparent, inspectable policy, not a black box; the exact
  signal-combination order is what the ablations (F4) probe.
- Generating code: existing `fig_router_decision_flow()` -> `fig3_router_decision_flow.png/.pdf`;
  companion `fig_workflow()` -> `fig2_workflow.png/.pdf`.
- Schematic vs data-driven: SCHEMATIC (renders today, no data).
- Pairs with: claims C1, C5 (each signal in this flow is later ablated). Table pairing: T4
  (Ablation Study) -- the flow defines what `adaptive_no_*` removes. Cross-ref 05_ROUTER_SPEC.md,
  ROUTER_FINAL_SPEC.md.

## F3 - Cost-vs-Quality / Pareto Frontier  [DATA]  *** HEADLINE FIGURE ***

- Purpose: THE headline figure. Plot every router and baseline as a point in
  (cost-per-task, quality) space and draw the Pareto frontier; show that workflow-aware routers
  (`adaptive`, `cascade`) sit on the upper-left frontier -- near-ceiling quality at a fraction
  of all-Tier-4 cost -- and that the `oracle` star marks the achievable headroom.
- Data source: `results/master_results.json` rows filtered by `dataset`; each row needs `em`
  (and `f1` for the multi-hop variant), `cost_per_task`, `label`, `n`. Live from
  `aggregate_results.py`; offline fallback `results/routing_sim/*.json` from `simulate_routing.py`.
- Metrics required (PRIMARY): EM/Accuracy and Token-F1 (y-axis; produce both an EM panel and an
  F1 panel for HotpotQA/MuSiQue), Cost per Task (x-axis, log scale), and derived overlays:
  Cost Reduction Factor / Cost Savings %, Quality Retention Rate, Workflow Context Gain
  (matched-cost markers), Pareto position. Spec-only diagnostics that may annotate it: Pareto
  Dominance, Utility Score iso-utility line (lambda frozen at analysis time).
- Plot type: scatter (one marker per router) + dashed step-line Pareto frontier (max quality at
  <= cost), log x-axis. Markers: oracle=star, routers=circle, baselines=square. Annotated labels.
- Expected insight (what a referee should conclude): the proposed routers Pareto-dominate (or
  match the frontier of) the fixed-tier baselines -- they achieve [X.X]% Quality Retention vs
  all-Tier-4 (C3) at a [X.X]x Cost Reduction Factor; the oracle star shows large exploitable
  headroom (C2); and at MATCHED cost, `adaptive`/`cascade` sit ABOVE `complexity`, i.e. a
  positive Workflow Context Gain (C4, the key claim). Verified offline (GSM8K) anchor points the
  referee can already trust: oracle 98.5% EM @ $0.0485/200 vs Tier-4 97.0% EM @ $1.18 vs Tier-1
  94.5% EM @ $0.031 -- oracle beats every single tier at ~1.5x Tier-1 cost.
- Generating code: existing `fig_pareto(rows, dataset)` -> `fig4_pareto_<dataset>.png/.pdf`.
  (F1-on-y variant is the same function fed F1 rows at analysis time; spec-only relabel,
  no code change.)
- Schematic vs data-driven: DATA-DRIVEN. GSM8K version generated today from baselines + sim
  oracle; HotpotQA/MuSiQue Pareto PENDING clean baselines (`TBD-after-run`).
- Pairs with: claims C2 (oracle gap), C3 (retention@cost), C4 (WCG via matched-cost markers),
  C6 (learned router point), C7 (one panel per dataset). Tables: T1 (Main Benchmark Results),
  T2 (Cost Analysis), T6 (Router Comparison), T7 (Cross-Dataset Generalization).

## F4 - Ablation Results  [DATA]

- Purpose: quantify each workflow signal's contribution by comparing `adaptive` against
  `adaptive_no_complexity`, `adaptive_no_role`, `adaptive_no_confidence`, `adaptive_no_budget`
  (with `cascade`/`complexity` as reference bars).
- Data source: `results/master_results.json` rows where `label` is an ablation variant or in
  {`adaptive`, `cascade`, `complexity`}; needs `em` (and `f1` for multi-hop), `cost_per_task`.
- Metrics required (PRIMARY): EM/Accuracy and Token-F1 at fixed/matched budget; secondary
  Cost per Task per variant to confirm the comparison is at comparable spend.
- Plot type: bar chart, EM (%) per variant (sorted), grid on y; produce an F1 companion bar for
  multi-hop.
- Expected insight: removing any single signal (role / confidence / complexity / budget) lowers
  quality at fixed budget -> each signal contributes; the full `adaptive` is best or tied-best.
  Placeholder: `adaptive` [X.X] EM vs largest drop `adaptive_no_[signal]` [X.X] EM.
- Generating code: existing `fig_ablation(rows, dataset)` -> `fig6_ablation_<dataset>.png`.
- Schematic vs data-driven: DATA-DRIVEN. PENDING ablation runs (`TBD-after-run`); router
  variants implemented and unit-tested.
- Pairs with: claim C5 (each signal contributes). Table: T4 (Ablation Study).

## F5 - Escalation Distribution  [DATA]

- Purpose: show the confidence-driven escalation behaviour -- fraction of agent calls where a
  routed router escalated above its base tier -- across `cascade`, `adaptive`, and ablations.
- Data source: `results/master_results.json` rows with `escalation_rate` not null and not a
  baseline; underlying signal is the per-call `escalated_from` / `decision.escalated` logged
  column.
- Metrics required (SECONDARY): Escalation Rate (% of agent calls). Optional overlay: Tier
  distribution context (links to F6).
- Plot type: bar chart, escalation rate (%) per routed router; grid on y.
- Expected insight: escalation is selective (concentrated where upstream confidence is low),
  rising with dataset difficulty (GSM8K < HotpotQA < MuSiQue), explaining HOW the router spends
  budget where it pays off. Placeholder: `cascade` [X.X]%, `adaptive` [X.X]%.
- Generating code: existing `fig_escalation(rows, dataset)` -> `fig7_escalation_<dataset>.png`.
- Schematic vs data-driven: DATA-DRIVEN. PENDING routed runs (`TBD-after-run`).
- Pairs with: claims C4, C5 (escalation is the confidence signal in action). Tables: T6 (Router
  Comparison), T4 (Ablation Study).

## F6 - Routing Frequency / Model Utilization  [DATA]

- Purpose: show, per router, the distribution of problems across tiers (which models actually
  get used) -- the mechanism behind the cost savings.
- Data source: `results/master_results.json` rows with `tier_distribution` (counts by verifier
  tier t1..t4 per router); derived from logged `tier` column at the verifier stage.
- Metrics required (SECONDARY): Tier distribution (stacked counts/shares); pairs with Cost per
  Task and Routing Accuracy / Over-Provision / Under-Provision diagnostics.
- Plot type: stacked bar chart (one bar per router, tier-colored segments T1..T4).
- Expected insight: proposed routers concentrate mass on cheap tiers (T1/T2) and reserve
  T3/T4 for hard cases -> the cost reduction in F3 is explained by utilization, not by quality
  loss. Contrast with fixed_t4 (all green) and random (uniform). Placeholder shares
  `TBD-after-run`.
- Generating code: existing `fig_model_utilization(rows, dataset)` ->
  `fig5_utilization_<dataset>.png`.
- Schematic vs data-driven: DATA-DRIVEN. GSM8K generated today from baselines;
  HotpotQA/MuSiQue PENDING (`TBD-after-run`).
- Pairs with: claims C3 (mechanism of savings), C6 (learned vs hand-built utilization),
  C7 (per dataset). Tables: T2 (Cost Analysis), T6 (Router Comparison).

## F7 - Failure Categories  [DATA, SPEC-ONLY]

- Purpose: error analysis -- categorize incorrect answers (e.g. under-provision miss,
  over-provision-but-still-wrong, EM-anomaly false-negative where F1 is high, parse/format
  failure) to explain WHERE routing errors come from.
- Data source: logged per-call CSV columns at analysis time (NO rerun): `correct`, `f1`,
  `tier`, `router_type`, `ground_truth`, `predicted`, `response_text`, `escalated_from`. Cross
  with `oracle_tier` to label under- vs over-provision. The Tier-4-EM-anomaly bucket is detected
  by `correct==0 & f1` high.
- Metrics required (DIAGNOSTIC): Under-Provision Rate, Over-Provision Rate, EM-vs-F1 disagreement
  count (anomaly bucket), category shares.
- Plot type: grouped/stacked bar (category counts per router) or horizontal bar of category
  shares. Schematic-of-categories optional.
- Expected insight: a large share of multi-hop "failures" are EM-brittleness false-negatives
  (high F1, EM=0), motivating reporting F1 alongside EM (C8); genuine routing errors split into
  under-provision (winnable but under-powered) vs noise.
- Generating code: spec-only, analysis-time plot (no existing function; build from CSV at
  analysis time, no code/router change).
- Schematic vs data-driven: DATA-DRIVEN but currently SPEC-ONLY (no generator function yet).
- Pairs with: claims C8 (anomaly + honesty), C5 (under-provision diagnostics). Table: T5 (Error
  Analysis). Cross-ref BASELINE_VALIDATION_REPORT.md §4, 07_RISK_REGISTER.md.

## F8 (supplementary) - Confidence Calibration / ECE  [DATA, SPEC-ONLY]

- Purpose: validate the confidence signal the router escalates on -- is logged `confidence`
  predictive of `correct`? Reliability diagram + Expected Calibration Error.
- Data source: logged columns `confidence` and `correct` (per agent call), at analysis time
  (NO rerun). Bin by confidence, compute accuracy per bin.
- Metrics required (DIAGNOSTIC, spec-only): Confidence Calibration Error / ECE (confidence vs
  correct); per-bin accuracy.
- Plot type: reliability diagram (binned confidence x-axis vs empirical accuracy y-axis, with
  the y=x perfect-calibration diagonal); ECE as a number/annotation.
- Expected insight: if confidence is reasonably calibrated, escalation decisions are justified;
  ECE quantifies the residual gap. Placeholder ECE `TBD-after-run`.
- Generating code: spec-only, analysis-time plot (no existing function; ECE is spec-only /
  analysis-time per the metric inventory, computable from logged columns with no code change).
- Schematic vs data-driven: DATA-DRIVEN but currently SPEC-ONLY.
- Pairs with: claims C4/C5 (justifies the confidence signal), C8 (honest reporting). Tables: T4,
  T6 (supporting). Cross-ref 13_METRICS_AND_FORMULAS.md.

## F9 (supplementary) - Budget Sweep / Budget Violations  [DATA, SPEC-ONLY]

- Purpose: show how `adaptive` quality responds to the budget cap (sweep) and whether the budget
  signal is honoured (cost_spent vs cost_budget on budget runs).
- Data source: budget-run logged CSVs at analysis time -- per-run total `cost_usd` vs the
  configured budget; quality (EM/F1) per budget level. NO rerun beyond the planned budget runs.
- Metrics required (PRIMARY x DIAGNOSTIC, spec-only): cost-quality curve over budgets; Budget
  Violations (cost_spent vs cost_budget). Pairs with Cost Savings % and Quality Retention.
- Plot type: line/curve of quality vs budget (with the unconstrained `adaptive` and `fixed_t4`
  reference lines); secondary bar/marker for any violation magnitude.
- Expected insight: the budget cap trades cost for quality monotonically and is respected
  (violations ~0), confirming the budget signal (the `adaptive_no_budget` ablation in F4 is the
  counterfactual). Placeholders `TBD-after-run`.
- Generating code: spec-only, analysis-time plot (no existing function; Budget Violations is
  spec-only / analysis-time, computable from logged columns with no code change).
- Schematic vs data-driven: DATA-DRIVEN but currently SPEC-ONLY.
- Pairs with: claims C5 (budget signal contributes), C3 (cost control). Tables: T2 (Cost
  Analysis), T4 (Ablation Study). Cross-ref 16_EXPERIMENT_MANIFEST.md, 07_RISK_REGISTER.md.

---

## Headline figure statement

The headline figure is **F3 - Cost-vs-Quality Pareto Frontier** (`fig4_pareto_<dataset>`,
`fig_pareto`). A referee should be able to conclude, from F3 alone:

1. There is large exploitable headroom between tiers -- the `oracle` star reaches near-ceiling
   quality at near-floor cost (C2; verified offline on GSM8K: 98.5% EM @ $0.0485/200).
2. The proposed workflow-aware routers (`adaptive`, `cascade`) lie on the upper-left Pareto
   frontier: they retain [X.X]% of all-Tier-4 quality (C3) while cutting cost by a factor of
   [X.X]x (Cost Reduction Factor), and they Pareto-dominate the fixed-tier baselines.
3. AT MATCHED COST, the workflow-aware routers sit ABOVE the difficulty-only `complexity`
   router -- a positive Workflow Context Gain (C4, the key scientific claim) -- showing the gains
   come from workflow context (role, upstream confidence, stage), not difficulty alone.
4. The pattern repeats across GSM8K -> HotpotQA -> MuSiQue (one panel per dataset, C7), with EM
   AND F1 panels on multi-hop so the Tier-4 EM anomaly cannot mislead (C8).

---

## Figure -> Claim -> Table crosswalk (summary)

| Canonical fig | Code stem | Kind | Claims | Tables |
|---------------|-----------|------|--------|--------|
| F1 Architecture | fig1_architecture | schematic | C1 | (T6 anchor) |
| F2 Decision Flow | fig3_router_decision_flow (+ fig2_workflow) | schematic | C1, C5 | T4 |
| F3 Pareto [HEADLINE] | fig4_pareto_<ds> | data | C2, C3, C4, C6, C7 | T1, T2, T6, T7 |
| F4 Ablation | fig6_ablation_<ds> | data | C5 | T4 |
| F5 Escalation | fig7_escalation_<ds> | data | C4, C5 | T4, T6 |
| F6 Utilization | fig5_utilization_<ds> | data | C3, C6, C7 | T2, T6 |
| F7 Failure Categories | spec-only | data (spec-only) | C5, C8 | T5 |
| F8 Calibration/ECE | spec-only | data (spec-only) | C4, C5, C8 | T4, T6 |
| F9 Budget Sweep/Violations | spec-only | data (spec-only) | C3, C5 | T2, T4 |

---

## Generation status (freeze snapshot)

| Figure | Generator exists | Generated today | Pending |
|--------|------------------|-----------------|---------|
| F1, F2 (+fig2_workflow) | yes | yes (PNG+PDF) | none |
| F3 Pareto | yes | GSM8K only (baselines + sim oracle) | HotpotQA/MuSiQue baselines |
| F6 Utilization | yes | GSM8K only | HotpotQA/MuSiQue |
| F4 Ablation | yes | no | ablation routed runs |
| F5 Escalation | yes | no | routed runs |
| F7 Failure | no (spec-only, analysis-time) | no | analysis-time script post-run |
| F8 Calibration | no (spec-only, analysis-time) | no | analysis-time script post-run |
| F9 Budget | no (spec-only, analysis-time) | no | budget runs + analysis-time script |

Regenerate data figures: `python aggregate_results.py` then `python make_figures.py`.
Offline preview without live runs: `python simulate_routing.py`. See 16_EXPERIMENT_MANIFEST.md.
