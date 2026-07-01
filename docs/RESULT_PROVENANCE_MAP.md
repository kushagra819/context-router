# Result Provenance Map

> Status: FROZEN (provenance map)

> Purpose: a complete, end-to-end RESULT PROVENANCE MAP so every scientific statement
> (claims C1..C8) is traceable from the experiment command -> raw CSV logs (+ exact columns) ->
> aggregation script -> metric function -> statistical test -> figure -> table -> paper section.
> Every link below names a file or function that EXISTS in the repository. Where a link cannot
> yet be made live, it is marked `PENDING` with the reason. ASCII-only. Results are PLACEHOLDERS.

> This document does NOT duplicate the freeze docs it binds together. It cross-references:
> [claim_evidence_matrix.md](claim_evidence_matrix.md) (claim -> evidence contract),
> [publication_metrics_spec.md](publication_metrics_spec.md) (frozen metric set),
> [statistical_validation_plan.md](statistical_validation_plan.md) (tests + Section 8 pre-reg),
> [paper_tables_template.md](paper_tables_template.md) (T1-T7),
> [paper_figures_template.md](paper_figures_template.md) (F1-F7),
> [publishable_paper_skeleton.md](publishable_paper_skeleton.md) (paper sections),
> [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md) (canonical claims C1-C8),
> [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md) / [experiment_execution_plan.md](experiment_execution_plan.md) (commands),
> [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) (verified-offline anchors).

---

## 0. Verified repository facts (the only names used below)

Everything in the chains is one of these real artifacts. No invented names.

ENTRY-POINT SCRIPTS (repo root):
- `run_experiment.py`           -- runs one (dataset x router) experiment.
- `aggregate_results.py`        -- CLI wrapper; calls `src/evaluation/aggregate.py`.
- `simulate_routing.py`         -- CLI wrapper; calls `src/evaluation/simulate.py`.
- `make_figures.py`             -- CLI wrapper; calls `src/visualization/figures.py`.
- `train_router.py`             -- trains the `learned` router (uses `src/router/training_data.py`).

LIBRARY MODULES:
- `src/pipeline/experiment.py`        -- `run_experiment(...)`; writes the CSV (paths below).
- `src/evaluation/aggregate.py`       -- `build_master(...)`, `write_outputs(...)`,
                                         `summarize_experiment(...)`, `oracle_tiers_for(...)`,
                                         constants `TIERS=(1,2,3,4)`, `REFERENCE_TIER=4`.
- `src/evaluation/simulate.py`        -- offline estimates (`simulate`, `CONTENT_FREE`,
                                         `NEEDS_QUESTION`, `NOT_SIMULABLE`).
- `src/evaluation/routing_metrics.py` -- all IMPLEMENTED metric functions (verified present:
                                         exact_match L28, mean_f1 L33, oracle_tier L41,
                                         routing_accuracy L49, over_provision_rate L61,
                                         under_provision_rate L73, escalation_rate L89,
                                         cost_per_task L97, cost_reduction_factor L101,
                                         cost_savings_pct L106, throughput_per_min L111,
                                         token_efficiency L116, quality_retention_pct L124,
                                         workflow_context_gain L129, bootstrap_ci L145,
                                         paired_bootstrap_pvalue L170).
- `src/evaluation/metrics.py`         -- per-problem scorers (gsm8k/hotpotqa/musique check + f1,
                                         normalize_answer, calculate_cost).
- `src/evaluation/csv_io.py`          -- `per_problem_records(path)` (CSV -> per-problem dict).
- `src/visualization/figures.py`      -- figure generators (stems below).
- `scripts/validate_baselines.py`     -- offline completeness/EM/F1 validation of baseline CSVs.

EXACT OUTPUT PATHS (from `src/pipeline/experiment.py` lines 7-8, 44-48, 71):
- baseline run  ->  `results/baselines/{dataset}_baseline_tier{N}.csv`
- routed run    ->  `results/routing/{dataset}_{router}.csv`
- aggregation   ->  `results/master_results.{json,csv,md}`  (`write_outputs`, aggregate.py L158-186)
- simulation    ->  `results/routing_sim/{dataset}_sim.json` + `simulation_table.md`
- figures       ->  `results/figures/<stem>.png` (+ `.pdf` for schematics/Pareto)
- backups       ->  `results/baselines_backup/{dataset}_baseline_tier{N}.csv` (oracle fallback,
                    aggregate.py L83-91, L117-119)

`run_experiment.py` CLI (verified L38-46): `--dataset {gsm8k,hotpotqa,musique}` (required),
`--router <name>` (required, from `list_routers()`), `--num-problems` (default 200),
`--resume`, `--mock`, `--cost-budget` (default inf; per-problem USD cap for budget-aware routers).
NOTE: there is no `--tier` flag; a baseline is produced by choosing `--router fixed_tN`.

LOGGED CSV COLUMNS (per agent call; identical for baseline and routed CSVs):
`timestamp, experiment_id, problem_id, dataset, agent_role, tier, model_name, router_type,
input_tokens, output_tokens, latency_s, cost_usd, correct, f1, ground_truth, predicted,
confidence, routing_reason, escalated_from, response_text`.

Per-problem aggregation (publication_metrics_spec.md Sec 0; csv_io + aggregate.py):
`correct_i`/`f1_i` = VERIFIER row's `correct`/`f1`; `cost_i`/`tok_i`/`lat_i` = SUM over the
problem's agent rows; representative tier = verifier-row `tier`; `escalated` = `escalated_from`
non-empty.

FIGURE STEM CROSSWALK (canonical F-id -> code stem in `figures.py`; verified function names):
| Canonical | Function (`figures.py`)       | Output stem                  |
|-----------|-------------------------------|------------------------------|
| F1        | `fig_architecture`            | `fig1_architecture`          |
| F2        | `fig_router_decision_flow`    | `fig3_router_decision_flow`  |
| F2 (comp) | `fig_workflow`                | `fig2_workflow`              |
| F3        | `fig_pareto`                  | `fig4_pareto_<dataset>`      |
| F4        | `fig_ablation`                | `fig6_ablation_<dataset>`    |
| F5        | `fig_escalation`              | `fig7_escalation_<dataset>`  |
| F6        | `fig_model_utilization`       | `fig5_utilization_<dataset>` |
| F7        | (spec-only; no generator yet) | analysis-time plot           |

> NOTE: the canonical figure ids (F1..F7) used across the freeze docs DELIBERATELY do not
> match the code output stem numbers (`fig1..fig7`). The mapping is intentional (e.g. F4 ->
> `fig6_ablation`, F5 -> `fig7_escalation`, F6 -> `fig5_utilization`); always resolve by the
> Function/Output-stem columns above, never by assuming `figN == FN`.

DATASETS (N=200 each): gsm8k (1-hop, EM only), hotpotqa (2-hop, EM+F1), musique (2-4 hop, EM+F1).
15 ROUTERS (`list_routers()`/`get_router`): oracle, random, fixed_t1, fixed_t2, fixed_t3,
fixed_t4, fixed_mixed, complexity, cascade, adaptive, learned, adaptive_no_complexity,
adaptive_no_role, adaptive_no_confidence, adaptive_no_budget.

CSV STATE AT FREEZE (verified on disk):
- PRESENT, LOCKED: `results/baselines/gsm8k_baseline_tier{1,2,3,4}.csv`.
- PRESENT (mixed N / sources): `results/baselines/hotpotqa_baseline_tier{1,2,3}.csv`,
  `results/baselines/musique_baseline_tier1.csv`,
  `results/baselines_backup/hotpotqa_baseline_tier{2,3,4}.csv`,
  `results/baselines_backup/musique_baseline_tier{2,3,4}.csv`.
- ABSENT: `results/routing/*.csv` (NO live routed runs yet) -> all router rows PENDING.
- F1 columns on multi-hop = TBD (legacy logger truncated `response_text` at 500 chars).

---

## 1. Data lineage diagram (CSV -> master_results -> figures/tables -> paper)

```
  LIVE EXPERIMENT                          OFFLINE ESTIMATE (no API)
  ---------------                          -------------------------
  run_experiment.py                        simulate_routing.py
    --dataset D --router R                    --dataset D
        |                                          |
        v   src/pipeline/experiment.py            v   src/evaluation/simulate.py
   one CSV, per-agent-call rows           results/routing_sim/D_sim.json
   (20 logged columns)                    (preview only; NEVER a live claim)
        |                                          |
        |  fixed_tN -> results/baselines/D_baseline_tierN.csv
        |  other    -> results/routing/D_R.csv
        |
        |   (validation gate)
        +--> scripts/validate_baselines.py  --> completeness / EM / F1 / N check
        |                                       (BASELINE_VALIDATION_REPORT.md)
        v
   aggregate_results.py  ->  src/evaluation/aggregate.py
        build_master(): per_problem_records() (csv_io)
                        summarize_experiment() per (dataset,router)
                        oracle_tiers_for() from per-tier baseline correctness
                        metrics via src/evaluation/routing_metrics.py
        write_outputs():
        +--------------------------+--------------------------+
        v                          v                          v
  results/master_results.json  results/master_results.csv  results/master_results.md
   (full metrics, +CI flags)    (flat table for figures)    (human-readable)
        |
        v   make_figures.py -> src/visualization/figures.py (reads master_results rows)
   results/figures/<stem>.png/.pdf
        |
        |   analysis-time (notebook): bootstrap_ci, paired_bootstrap_pvalue (routing_metrics),
        |   + spec-only tests (McNemar/Wilcoxon/permutation/Holm, statistical_validation_plan.md)
        |   + spec-only metrics (Pareto, Win Rate, Utility, ECE, Budget Violations)
        v
   PAPER TABLES T1-T7 (paper_tables_template.md)  +  FIGURES F1-F7 (paper_figures_template.md)
        |
        v
   PAPER SECTIONS (publishable_paper_skeleton.md Sec 6.x) -> CLAIMS C1..C8
```

Single source of truth: the CSVs in `results/baselines/` + `results/routing/`. Everything
downstream is regenerable by `python aggregate_results.py && python make_figures.py`.

---

## 2. Per-claim provenance blocks (C1..C8)

Each block: Claim -> Experiment(+command) -> Raw Logs(+columns) -> Aggregation -> Metric
-> Statistical Test -> Figure -> Table -> Paper Section, plus one-command reproduction and notes.

Legend: [LOCKED] verified-offline GSM8K; [EM-OK] multi-hop EM reliable but mixed N/source;
[PENDING] cannot be made live yet (reason stated). "spec-only" = computable from logged columns
at analysis time, no code change.

---

### C1 -- Per-agent routing is feasible and novel

- CLAIM: Per-agent tier routing inside a fixed Analyzer->Solver->Verifier pipeline is a feasible,
  novel design point (distinct from per-query routing). Existence/positioning claim, not a stat
  comparison.
- EXPERIMENT (router x dataset): any routed run that logs a per-call tier decision, e.g.
  `adaptive` x {gsm8k, hotpotqa, musique}. Interface: `src/router/base_router.py`.
  - COMMAND: `python run_experiment.py --dataset gsm8k --router adaptive --num-problems 200`
- RAW LOGS: `results/routing/gsm8k_adaptive.csv` (and hotpotqa/musique). [PENDING] -- no
  `results/routing/*.csv` exist yet.
  - COLUMNS USED: `agent_role`, `tier`, `routing_reason`, `escalated_from` (proves a per-call,
    role-dependent decision is logged).
- AGGREGATION: `src/evaluation/aggregate.py` `summarize_experiment` -> `tier_distribution`
  (verifier-tier histogram, L43-44) shows tier varies; full `build_master`.
- METRIC: spec-only (qualitative tier-distribution-by-role; no headline number). No
  `routing_metrics.py` function required for feasibility.
- STATISTICAL TEST: none (feasibility/novelty positioning; claim_evidence_matrix.md C1).
- FIGURE: F1 `fig_architecture` (`fig1_architecture`); F2 `fig_router_decision_flow`
  (`fig3_router_decision_flow`) + companion `fig_workflow` (`fig2_workflow`). SCHEMATIC --
  render today, no data: `python make_figures.py`.
- TABLE: T6 Router Comparison (shows per-call routers exist); related-work feature matrix.
- PAPER SECTION: publishable_paper_skeleton.md Sec 2 (Introduction) + Sec 4.1-4.3 (Methodology:
  pipeline + routing signals); positioning in Sec 3 (Related Work).
- ONE-COMMAND REPRO (figures available now): `python make_figures.py` (F1/F2 schematics).
- NOTES: The ONLY part of C1 that is PENDING is the live `results/routing/*.csv` existence proof;
  the schematic figures and the architectural argument are available today.

---

### C2 -- Large oracle headroom exists between tiers

- CLAIM: A per-problem `oracle` reaches near-ceiling quality at near-floor cost -> room to cut
  cost without losing quality.
- EXPERIMENT: `oracle` vs `fixed_t1..fixed_t4` x {gsm8k, hotpotqa, musique}. `oracle` is derived
  offline from per-tier baseline correctness (`aggregate.oracle_tiers_for` ->
  `routing_metrics.oracle_tier`); the four baselines are live runs.
  - COMMANDS (baselines):
    `python run_experiment.py --dataset gsm8k --router fixed_t1 --num-problems 200`
    (repeat for `fixed_t2`, `fixed_t3`, `fixed_t4`, and per dataset).
  - COMMAND (oracle estimate preview): `python simulate_routing.py --dataset gsm8k`.
- RAW LOGS: `results/baselines/gsm8k_baseline_tier{1,2,3,4}.csv` [LOCKED];
  `results/baselines/hotpotqa_baseline_tier{1,2,3}.csv` + `results/baselines_backup/hotpotqa_baseline_tier4.csv` [EM-OK, mixed];
  `results/baselines/musique_baseline_tier1.csv` + `results/baselines_backup/musique_baseline_tier{2,3,4}.csv` [EM-OK, mixed; T4 N=199].
  - COLUMNS USED: `problem_id`, `tier`, `correct`, `f1` (verifier row), `cost_usd`,
    `input_tokens`, `output_tokens`.
- AGGREGATION: `aggregate.py` `oracle_tiers_for` (builds oracle tier per problem from the four
  baseline CSVs, with `baselines_backup` fallback) + `summarize_experiment`/`build_master`.
- METRIC: `routing_metrics.exact_match` (EM), `routing_metrics.mean_f1` (F1),
  `routing_metrics.cost_per_task`; Pareto position = spec-only.
- STATISTICAL TEST: `routing_metrics.bootstrap_ci` (95% CI on oracle EM and each tier EM);
  EM comparison test = McNemar (spec-only, statistical_validation_plan.md Sec 4) + paired
  bootstrap corroboration.
- FIGURE: F3 `fig_pareto` (`fig4_pareto_<dataset>`) -- oracle star dominates single tiers.
- TABLE: T1 Main Benchmark Results (`oracle` row) + T2 Cost Analysis.
- PAPER SECTION: publishable_paper_skeleton.md Sec 6.2 (Oracle headroom (C2)); anchors in
  Sec 6.8 (verified-offline GSM8K).
- ONE-COMMAND REPRO (GSM8K, available now): `python aggregate_results.py --datasets gsm8k`
  then `python make_figures.py` (renders `fig4_pareto_gsm8k`).
- VERIFIED OFFLINE (GSM8K, LOCKED): oracle 98.5% EM @ $0.0485/200 vs fixed_t4 97.0% @ $1.182 vs
  fixed_t1 94.5% @ $0.031 (oracle beats every single tier at ~1.5x Tier-1 cost).
- NOTES: HotpotQA/MuSiQue oracle EM = TBD (mixed-N baselines); oracle F1 = [PENDING] (multi-hop
  F1 raw logs not yet regenerated; legacy 500-char truncation).

---

### C3 -- Context-aware routing preserves quality while cutting cost

- CLAIM: `cascade`/`adaptive` achieve high Quality Retention vs the all-Tier-4 ceiling at a large
  Cost Reduction Factor.
- EXPERIMENT: `cascade`, `adaptive` vs `fixed_t4` (reference) x {gsm8k, hotpotqa, musique}.
  - COMMANDS:
    `python run_experiment.py --dataset gsm8k --router cascade --num-problems 200`
    `python run_experiment.py --dataset gsm8k --router adaptive --num-problems 200`
    (reference `fixed_t4` per C2; repeat per dataset).
- RAW LOGS: `results/routing/{gsm8k,hotpotqa,musique}_cascade.csv`,
  `results/routing/{gsm8k,hotpotqa,musique}_adaptive.csv` [PENDING -- not yet produced];
  reference `results/baselines/{dataset}_baseline_tier4.csv` (GSM8K [LOCKED], multi-hop in
  `baselines_backup`).
  - COLUMNS USED: `correct`, `f1` (verifier), `cost_usd`, `tier`, `escalated_from`,
    `input_tokens`, `output_tokens`, `problem_id`.
- AGGREGATION: `aggregate.py` `build_master` derived-metric block (L129-146) computes
  `cost_savings_pct_vs_t4`, `cost_reduction_factor_vs_t4`, `quality_retention_pct_vs_t4`,
  `f1_retention_pct_vs_t4`, all against `REFERENCE_TIER=4`.
- METRIC: `routing_metrics.quality_retention_pct` (QRR, EM and F1),
  `routing_metrics.cost_reduction_factor`, `routing_metrics.cost_savings_pct`,
  `routing_metrics.cost_per_task`; secondary `routing_metrics.escalation_rate`; Pareto = spec-only.
- STATISTICAL TEST: `routing_metrics.bootstrap_ci` (CI on QRR EM and F1);
  `routing_metrics.paired_bootstrap_pvalue` (cascade/adaptive vs fixed_t4, EM and F1, same
  problems); plus McNemar (EM) / Wilcoxon (F1, cost) spec-only (stat plan Sec 4).
- FIGURE: F3 `fig_pareto` (`fig4_pareto_<dataset>`) -- cascade/adaptive up-left of T4;
  supporting F6 `fig_model_utilization` (`fig5_utilization_<dataset>`) explains WHERE savings
  come from; F5 `fig_escalation` (`fig7_escalation_<dataset>`).
- TABLE: T1 Main Benchmark Results + T2 Cost Analysis (`cost_savings_pct_vs_t4`,
  `quality_retention_pct_vs_t4` columns).
- PAPER SECTION: publishable_paper_skeleton.md Sec 6.1 (Main benchmark, C3/C7) + Sec 6.3
  (Cost-quality Pareto, C3).
- ONE-COMMAND REPRO (after routed runs land): `python aggregate_results.py && python make_figures.py`.
- NOTES: Sub-claim C3a (adaptive reduces inference cost) uses the same CRF/Savings% +
  `paired_bootstrap_pvalue` on cost. QRR_EM can exceed 100% on multi-hop (Tier-4 EM anomaly) ->
  ALWAYS pair F1-based QRR (`f1_retention_pct_vs_t4`). All multi-hop F1 = [PENDING].

---

### C4 -- [HEADLINE] Workflow context beats difficulty-only routing

- CLAIM: Workflow Context Gain > 0 -- `adaptive`/`cascade` beat the best context-free
  (difficulty-only) router `complexity` at matched (<=) cost.
- EXPERIMENT: `adaptive` and `cascade` vs `complexity` x {gsm8k, hotpotqa, musique}, constrained
  to matched (<=) cost; references `random`/`fixed_mixed`.
  - COMMANDS:
    `python run_experiment.py --dataset musique --router adaptive --num-problems 200`
    `python run_experiment.py --dataset musique --router cascade --num-problems 200`
    `python run_experiment.py --dataset musique --router complexity --num-problems 200`
    (repeat per dataset; matched-cost selection is analysis-time).
- RAW LOGS: `results/routing/{dataset}_adaptive.csv`, `results/routing/{dataset}_cascade.csv`,
  `results/routing/{dataset}_complexity.csv` [PENDING -- not yet produced].
  - COLUMNS USED: `problem_id` (pairing), `correct`, `f1` (verifier), `cost_usd` (matched-cost
    constraint), `tier`.
- AGGREGATION: `aggregate.py` `build_master` (per-router EM/F1/cost_per_task); the matched-cost
  comparator SELECTION (workflow-aware vs `complexity` at <= cost) is analysis-time (no code
  change), then `routing_metrics.workflow_context_gain` returns the delta.
- METRIC: `routing_metrics.workflow_context_gain` (WCG = quality(workflow-aware) -
  quality(best context-free at <= cost), EM and F1) -- THE HEADLINE METRIC; inputs from
  `exact_match`/`mean_f1` + `cost_per_task`.
- STATISTICAL TEST: PRE-REGISTERED PRIMARY, ONE-SIDED (H1: WCG > 0), alpha=0.05
  (statistical_validation_plan.md Sec 8). `routing_metrics.paired_bootstrap_pvalue` on EM +
  Wilcoxon signed-rank on F1 (spec-only); paired-bootstrap CI of the difference; Holm-adjusted
  within Family B. (ALL other comparisons in this map are two-sided.)
- FIGURE: F3 `fig_pareto` (`fig4_pareto_<dataset>`) with matched-cost markers (adaptive/cascade
  ABOVE complexity at equal x); supporting F5 `fig_escalation` (confidence signal in action).
- TABLE: T6 Router Comparison (WCG-derived column, Win Rate) + T7 Cross-Dataset Generalization
  (WCG sub-rows: `cascade - complexity`, `adaptive - complexity` per dataset).
- PAPER SECTION: publishable_paper_skeleton.md Sec 6.4 (Workflow Context Gain -- headline (C4)).
- ONE-COMMAND REPRO: WCG point estimate after runs via `python aggregate_results.py`; the
  one-sided paired test + matched-cost selection is the analysis notebook
  (`routing_metrics.paired_bootstrap_pvalue`), no separate CLI.
- NOTES: Entire chain [PENDING] on routed CSVs. F1-based WCG additionally [PENDING] on multi-hop
  F1 regeneration. This is the paper's key claim: do NOT write prose until the routed runs land
  and the one-sided test reports.

---

### C5 -- Each routing signal contributes (ablation)

- CLAIM: Removing any one signal family (role / confidence / complexity / budget) degrades
  quality at fixed budget.
- EXPERIMENT: `adaptive` vs each of `adaptive_no_role`, `adaptive_no_confidence`,
  `adaptive_no_complexity`, `adaptive_no_budget` x {gsm8k, hotpotqa, musique}, matched budget.
  - COMMANDS (use `--cost-budget` to hold budget fixed across variants):
    `python run_experiment.py --dataset musique --router adaptive --num-problems 200 --cost-budget B`
    `python run_experiment.py --dataset musique --router adaptive_no_role --num-problems 200 --cost-budget B`
    `python run_experiment.py --dataset musique --router adaptive_no_confidence --num-problems 200 --cost-budget B`
    `python run_experiment.py --dataset musique --router adaptive_no_complexity --num-problems 200 --cost-budget B`
    `python run_experiment.py --dataset musique --router adaptive_no_budget --num-problems 200 --cost-budget B`
    (repeat per dataset; B = the frozen budget).
- RAW LOGS: `results/routing/{dataset}_adaptive.csv`,
  `results/routing/{dataset}_adaptive_no_role.csv`,
  `results/routing/{dataset}_adaptive_no_confidence.csv`,
  `results/routing/{dataset}_adaptive_no_complexity.csv`,
  `results/routing/{dataset}_adaptive_no_budget.csv` [PENDING -- not yet produced].
  - COLUMNS USED: `problem_id`, `correct`, `f1` (verifier), `cost_usd` (confirm fixed budget),
    `tier`, `escalated_from` (confidence variants); `cost_usd` vs budget (budget variant).
- AGGREGATION: `aggregate.py` `build_master` (per-variant EM/F1/cost_per_task; routing_accuracy,
  over_provision_rate, under_provision_rate when oracle present).
- METRIC: `routing_metrics.exact_match`, `routing_metrics.mean_f1` (delta full vs each ablation);
  `routing_metrics.cost_per_task`; diagnostics `routing_metrics.over_provision_rate`,
  `routing_metrics.under_provision_rate`; Budget Violations = spec-only (cost_usd vs
  `--cost-budget` on `adaptive_no_budget`).
- STATISTICAL TEST: `routing_metrics.paired_bootstrap_pvalue` (adaptive vs each `adaptive_no_*`,
  same problems) + `routing_metrics.bootstrap_ci` on each delta; McNemar (EM) per pair spec-only;
  Holm-Bonferroni across the 4-member ablation family (stat plan Sec 6).
- FIGURE: F4 `fig_ablation` (`fig6_ablation_<dataset>`); supporting F5 `fig_escalation`
  (confidence-cascade behaviour).
- TABLE: T4 Ablation Study (Delta EM vs adaptive, per variant per dataset).
- PAPER SECTION: publishable_paper_skeleton.md Sec 6.5 (Ablation (C5)); methods Sec 5.4.
- ONE-COMMAND REPRO (after ablation runs): `python aggregate_results.py && python make_figures.py`
  (renders `fig6_ablation_<dataset>`).
- NOTES: Per-signal sub-claims (C5-role/confidence/complexity/budget) each get their own paired
  test row in T4/F4. Whole chain [PENDING] on ablation routed runs. F1 deltas [PENDING] on
  multi-hop F1 regeneration.

---

### C6 -- Learned routing approximates oracle, beats random + rule-based

- CLAIM: A DecisionTree (`learned`) trained on oracle labels routes better than `random` and
  approaches/beats rule-based routers at matched cost (NEVER claims to beat the oracle).
- EXPERIMENT: train `learned` on oracle labels, then `learned` vs `random`, vs
  `complexity`/`cascade`/`adaptive`, vs `oracle` (gap) x {gsm8k, hotpotqa, musique}.
  - COMMANDS:
    `python train_router.py`  (uses `src/router/training_data.py`; produces the learned model)
    `python run_experiment.py --dataset gsm8k --router learned --num-problems 200`
    `python run_experiment.py --dataset gsm8k --router random --num-problems 200`
    (repeat per dataset; `complexity`/`cascade`/`adaptive` from C3/C4).
- RAW LOGS: `results/routing/{dataset}_learned.csv`, `results/routing/{dataset}_random.csv`
  [PENDING -- not yet produced].
  - COLUMNS USED: `problem_id`, `correct`, `f1` (verifier), `cost_usd`, `tier` (vs oracle tier
    for routing accuracy).
- AGGREGATION: `aggregate.py` `build_master` + `oracle_tiers_for` (gap-to-oracle and
  routing_accuracy use oracle tiers from the four baseline CSVs).
- METRIC: `routing_metrics.exact_match`, `routing_metrics.mean_f1`,
  `routing_metrics.cost_per_task`, `routing_metrics.routing_accuracy` (vs `oracle_tier`);
  gap-to-oracle = spec-only; Utility Score / Win Rate = spec-only.
- STATISTICAL TEST: `routing_metrics.paired_bootstrap_pvalue` (learned vs random; learned vs
  complexity, EM and F1) + `routing_metrics.bootstrap_ci` on learned EM/F1; McNemar/Wilcoxon
  spec-only.
- FIGURE: F3 `fig_pareto` (`fig4_pareto_<dataset>`) -- learned point vs random/rule-based/oracle;
  F6 `fig_model_utilization` (`fig5_utilization_<dataset>`) -- learned vs hand-built utilization.
- TABLE: T1 Main Benchmark Results (`learned` row) + T6 Router Comparison.
- PAPER SECTION: publishable_paper_skeleton.md Sec 6.6 (Learned router (C6)); methods Sec 5.5.
- ONE-COMMAND REPRO (after train + runs): `python train_router.py` then
  `python run_experiment.py --dataset gsm8k --router learned --num-problems 200` then
  `python aggregate_results.py && python make_figures.py`.
- NOTES: Sub-claim C6a (learned beats rule-based) -- state honestly if learned only MATCHES
  `complexity`; do not overclaim. Chain [PENDING] on routed CSVs. Offline preview only:
  `python simulate_routing.py --dataset gsm8k --with-questions --routers complexity learned`
  (NEVER cite sim numbers as live; claim_evidence_matrix.md Sec 4).

---

### C7 -- Results generalize across difficulty

- CLAIM: The cost-quality benefit holds on gsm8k (1-hop) -> hotpotqa (2-hop) -> musique (2-4 hop).
- EXPERIMENT: all proposed routers (`complexity`, `cascade`, `adaptive`, `learned`) + references
  across all three datasets.
  - COMMAND PATTERN (Cartesian product; see experiment_execution_plan.md /
    16_EXPERIMENT_MANIFEST.md): `python run_experiment.py --dataset <D> --router <R> --num-problems 200`
    for D in {gsm8k, hotpotqa, musique}, R in the proposed + reference set.
- RAW LOGS: `results/routing/{gsm8k,hotpotqa,musique}_{complexity,cascade,adaptive,learned}.csv`
  + the per-dataset baselines [PENDING for routed; baselines GSM8K LOCKED, multi-hop EM-OK].
  - COLUMNS USED: `correct`, `f1` (verifier), `cost_usd`, per dataset.
- AGGREGATION: `aggregate.py` `build_master(datasets=[gsm8k,hotpotqa,musique])` -- one master
  table spanning all three; derived savings/QRR per dataset.
- METRIC: `routing_metrics.cost_savings_pct`, `routing_metrics.quality_retention_pct`,
  `routing_metrics.workflow_context_gain` reported PER dataset (consistent direction/magnitude
  along the gradient).
- STATISTICAL TEST: `routing_metrics.bootstrap_ci` per dataset on each headline;
  `routing_metrics.paired_bootstrap_pvalue` per dataset; generalization requires same-sign +
  Holm-significant in each dataset (stat plan Sec 6 footnote).
- FIGURE: F3 `fig_pareto` rendered per dataset -- `fig4_pareto_gsm8k`, `fig4_pareto_hotpotqa`,
  `fig4_pareto_musique`.
- TABLE: T7 Cross-Dataset Generalization (Savings%/QRR% per dataset + WCG sub-rows) + T1
  (per-dataset rows).
- PAPER SECTION: publishable_paper_skeleton.md Sec 6.1 (Main benchmark, C3/C7); difficulty-gradient
  discussion Sec 7.
- ONE-COMMAND REPRO: `python aggregate_results.py` (defaults to all three datasets) then
  `python make_figures.py` (renders all three Pareto panels).
- NOTES: GSM8K Pareto/utilization renderable today from baselines + sim oracle; hotpotqa/musique
  panels [PENDING] clean baselines + routed runs. Multi-hop F1 [PENDING].

---

### C8 -- Robustness / honesty (EM+F1, CIs, T4 anomaly, hypothetical cost)

- CLAIM: We report EM AND F1, a CI on every headline, explicitly flag the Tier-4 EM anomaly, and
  state the hypothetical-cost assumption (ratios only, never absolute USD as deployment cost).
- EXPERIMENT: all routers x {gsm8k, hotpotqa, musique} -- every headline carries EM and F1
  (F1 omitted only for GSM8K, where it collapses to EM) and a CI. Anomaly documented from
  `fixed_t4` multi-hop EM. (Validation gate run offline.)
  - COMMAND (validation/anomaly evidence):
    `python scripts/validate_baselines.py`  (offline completeness / EM / F1 / N audit).
- RAW LOGS: every baseline + routed CSV; anomaly source =
  `results/baselines_backup/hotpotqa_baseline_tier4.csv` and
  `results/baselines_backup/musique_baseline_tier4.csv`.
  - COLUMNS USED: `correct`, `f1`, `predicted`, `ground_truth` (EM-vs-F1 disagreement bucket),
    `confidence` (ECE), `cost_usd` (ratios), `tier`, `escalated_from`, `response_text`
    (truncation-flagged).
- AGGREGATION: `aggregate.py` `build_master`/`write_outputs` (EM and F1 side by side, savings as
  ratios `cost_reduction_factor_vs_t4`); `scripts/validate_baselines.py` for the offline
  completeness/anomaly audit (BASELINE_VALIDATION_REPORT.md).
- METRIC: `routing_metrics.exact_match` + `routing_metrics.mean_f1` (paired EM/F1);
  ratios `cost_reduction_factor`/`cost_savings_pct`/`token_efficiency`; ECE = spec-only
  (`confidence` vs `correct`, K=10).
- STATISTICAL TEST: `routing_metrics.bootstrap_ci` on EVERY headline EM and F1 (the honesty
  deliverable itself); deterministic given seed=42, n_boot=10000 (stat plan Sec 9).
- FIGURE: F7 Failure Categories (spec-only, analysis-time plot; NO generator function in
  `figures.py` yet -- built from logged CSV columns at analysis time). The EM-anomaly bucket =
  `correct==0 & f1` high.
- TABLE: T5 Error Analysis + T1 (EM and F1 columns with +/-CI).
- PAPER SECTION: publishable_paper_skeleton.md Sec 6.7 (Secondary/diagnostic) + Sec 6.8
  (verified-offline GSM8K) + Sec 8 (Limitations) for the anomaly + hypothetical-cost caveat.
- ONE-COMMAND REPRO (anomaly audit, available now): `python scripts/validate_baselines.py`.
- VERIFIED OFFLINE ANOMALY: Tier-4 EM LOWER than weaker tiers on multi-hop --
  HotpotQA EM T1=63.0, T2=65.25, T3=54.17, T4=37.5; MuSiQue EM T1=31.5, T2=55.0, T3=47.5,
  T4=25.63 (T4 N=199). Consequence: report F1 alongside EM; QRR_EM may exceed 100%.
- NOTES: F7 has no generator yet (spec-only) and all multi-hop F1 = [PENDING] (legacy logger
  500-char truncation) -- so the F1-half of the honesty contract is gated on the clean re-run.

---

## 3. Master traceability table

Columns: Claim | Experiment (router x dataset) | Raw Logs (path + key columns) | Aggregation |
Metric (routing_metrics.py fn / spec-only) | Statistical Test | Figure (Fxx / stem) |
Table | Paper Section | Status.

| Claim | Experiment | Raw Logs (+columns) | Aggregation | Metric | Stat Test | Figure | Table | Paper Sec | Status |
|-------|-----------|---------------------|-------------|--------|-----------|--------|-------|-----------|--------|
| C1 | adaptive x {all} | results/routing/{ds}_adaptive.csv; agent_role,tier,routing_reason,escalated_from | aggregate.summarize_experiment (tier_distribution) | spec-only (tier-by-role) | none | F1 fig1_architecture; F2 fig3_router_decision_flow | T6 | Sec 2,4.1-4.3 | PENDING routed CSV; figs ready |
| C2 | oracle vs fixed_t1..t4 x {all} | results/baselines/{ds}_baseline_tier{1..4}.csv (+backup); problem_id,tier,correct,f1,cost_usd | aggregate.oracle_tiers_for + build_master | exact_match, mean_f1, cost_per_task; Pareto spec-only | bootstrap_ci; McNemar spec-only | F3 fig4_pareto_<ds> | T1,T2 | Sec 6.2,6.8 | GSM8K LOCKED; multi-hop EM-OK; F1 PENDING |
| C3 | cascade,adaptive vs fixed_t4 x {all} | results/routing/{ds}_{cascade,adaptive}.csv; correct,f1,cost_usd,tier,escalated_from | build_master derived block (L129-146) | quality_retention_pct, cost_reduction_factor, cost_savings_pct, cost_per_task | bootstrap_ci + paired_bootstrap_pvalue (EM,F1) | F3 fig4_pareto_<ds>; F6 fig5_utilization_<ds> | T1,T2 | Sec 6.1,6.3 | PENDING routed CSV; F1 PENDING |
| C4 | adaptive,cascade vs complexity (matched cost) x {all} | results/routing/{ds}_{adaptive,cascade,complexity}.csv; problem_id,correct,f1,cost_usd | build_master + matched-cost selection (analysis-time) | workflow_context_gain (HEADLINE) | paired_bootstrap_pvalue ONE-SIDED (Sec 8) + Wilcoxon F1 | F3 fig4_pareto_<ds> (matched markers) | T6,T7 | Sec 6.4 | PENDING routed CSV (HEADLINE) |
| C5 | adaptive vs adaptive_no_{role,confidence,complexity,budget} x {all}, matched budget | results/routing/{ds}_adaptive*.csv; problem_id,correct,f1,cost_usd,tier,escalated_from | build_master (+over/under_provision) | exact_match, mean_f1, over_provision_rate, under_provision_rate; Budget Violations spec-only | paired_bootstrap_pvalue per pair + bootstrap_ci; Holm | F4 fig6_ablation_<ds> | T4 | Sec 6.5 | PENDING ablation runs; F1 PENDING |
| C6 | learned vs random/rule-based/oracle x {all} | results/routing/{ds}_{learned,random}.csv; problem_id,correct,f1,cost_usd,tier | build_master + oracle_tiers_for | exact_match, mean_f1, routing_accuracy, cost_per_task; Utility/Win spec-only | paired_bootstrap_pvalue (vs random, vs complexity) + bootstrap_ci | F3 fig4_pareto_<ds>; F6 fig5_utilization_<ds> | T1,T6 | Sec 6.6 | PENDING train_router + routed CSV |
| C7 | all proposed + refs x {gsm8k,hotpotqa,musique} | results/routing/{ds}_{complexity,cascade,adaptive,learned}.csv + baselines; correct,f1,cost_usd | build_master(all 3 ds) | cost_savings_pct, quality_retention_pct, workflow_context_gain (per ds) | bootstrap_ci + paired_bootstrap_pvalue per ds; Holm across ds | F3 fig4_pareto_{gsm8k,hotpotqa,musique} | T7,T1 | Sec 6.1,7 | GSM8K partial; multi-hop PENDING |
| C8 | all routers x {all} (EM+F1+CI) | all baseline+routed CSV; correct,f1,predicted,ground_truth,confidence,cost_usd | build_master/write_outputs + scripts/validate_baselines.py | exact_match+mean_f1, cost_reduction_factor; ECE spec-only | bootstrap_ci on every headline (seed=42,n_boot=10000) | F7 Failure Categories (spec-only, no generator yet) | T5,T1 | Sec 6.7,6.8,8 | Anomaly LOCKED; F1 + F7 PENDING |

---

## 4. PENDING-link register (explicit gaps, by cause)

| # | Pending link | Affects | Root cause | Clears when |
|---|--------------|---------|-----------|-------------|
| P1 | `results/routing/*.csv` do not exist | C1,C3,C4,C5,C6,C7 (all router rows) | no live routed runs yet | `run_experiment.py` per (dataset x router) lands -> aggregate |
| P2 | Multi-hop F1 (hotpotqa/musique) = TBD in every table | C2,C3,C4,C5,C6,C7,C8 F1 columns/QRR/WCG | legacy logger truncated `response_text` at 500 chars | clean N=200 re-run of multi-hop baselines + routed runs |
| P3 | HotpotQA/MuSiQue baseline EM on MIXED N/source | C2,C7 multi-hop EM | T2/T3 partial-clean, T4 truncated backup, MuSiQue T4 N=199 | clean N=200 re-run (validate_baselines.py gate) |
| P4 | F7 Failure Categories has no generator in `figures.py` | C8 (F7), C5 (under-provision viz) | spec-only / analysis-time plot, not coded | analysis-time script over logged CSV columns post-run |
| P5 | Matched-cost comparator selection for WCG | C4 (headline) | analysis-time selection (no code change), needs routed CSVs first | C4 routed runs land; selection done in analysis notebook |
| P6 | `learned` model artifact | C6 | `train_router.py` not yet run on oracle labels | run `train_router.py` then `--router learned` |
| P7 | Spec-only metrics/tests (McNemar, Wilcoxon, permutation, Holm, Win Rate, Utility, ECE, Budget Violations, Pareto Dominance) | C4,C5,C6,C8 supports | by design not in `routing_metrics.py`; analysis-time only | analysis notebook (scipy/statsmodels) post-run |

---

## 5. Reproduction quick-reference (one command per stage)

```
# 0. (anomaly + completeness audit; runs today on existing baselines)
python scripts/validate_baselines.py

# 1. baselines (one per tier per dataset; GSM8K already LOCKED)
python run_experiment.py --dataset <gsm8k|hotpotqa|musique> --router fixed_t<1|2|3|4> --num-problems 200

# 2. routed runs (proposed + ablations + learned + references)
python run_experiment.py --dataset <ds> --router <complexity|cascade|adaptive|learned|random|fixed_mixed> --num-problems 200
python run_experiment.py --dataset <ds> --router adaptive_no_<role|confidence|complexity|budget> --num-problems 200 --cost-budget <B>
python train_router.py            # before --router learned

# 3. aggregate CSV -> master_results.{json,csv,md}
python aggregate_results.py                       # all datasets
python aggregate_results.py --datasets gsm8k      # one dataset

# 4. figures (schematics today; data figures after step 3)
python make_figures.py

# offline preview only (NEVER cite as live; claim_evidence_matrix.md Sec 4)
python simulate_routing.py --dataset gsm8k
python simulate_routing.py --dataset gsm8k --with-questions --routers complexity learned
```

Per-claim "one-command" entry point (after its routed CSVs exist): each claim block above lists
its ONE-COMMAND REPRO; for every data-driven claim it reduces to
`python aggregate_results.py && python make_figures.py` once the required
`results/routing/*.csv` are present. Claims C1 (schematics), C2 (GSM8K Pareto), and C8 (anomaly
audit) have commands that run on artifacts present TODAY.

---

## 6. Integrity guarantees of this map

- Every file path above is a real path produced by `src/pipeline/experiment.py` (L7-8, 44-48, 71)
  or `src/evaluation/aggregate.py` `write_outputs` (L158-186) or `src/visualization/figures.py`
  `_save` (L33-40), or a confirmed-on-disk CSV under `results/`.
- Every metric names an actual function in `src/evaluation/routing_metrics.py` (line numbers in
  Section 0) or is explicitly tagged "spec-only" (analysis-time, no code change).
- Every statistical test is either `routing_metrics.bootstrap_ci` /
  `routing_metrics.paired_bootstrap_pvalue` (implemented) or a spec-only test named in
  statistical_validation_plan.md (McNemar/Wilcoxon/permutation/Holm-Bonferroni).
- Every figure names a real generator function + output stem in `src/visualization/figures.py`
  (or F7 = spec-only, no generator, stated as such).
- Every table (T1-T7) and paper section (Sec 6.1-6.8 / Sec 2-5 / Sec 8) is a real anchor in
  paper_tables_template.md and publishable_paper_skeleton.md.
- No claim is shown as live where its `results/routing/*.csv` is absent; such links carry
  [PENDING] with the cause in Section 4. Documentation only; no code modified.
```
