# 15 — Figure Plan

> **Status:** Canonical. Every figure is implemented in
> [`src/visualization/figures.py`](../src/visualization/figures.py) and produced by
> `python make_figures.py` into `results/figures/` (PNG; vector PDF for schematics).
> Schematic figures render today; data figures use `results/master_results.json`
> (live, from `aggregate_results.py`) or fall back to `results/routing_sim/*.json`
> (offline, from `simulate_routing.py`).

| # | File stem | Type | Purpose | Required data | Function |
|---|-----------|------|---------|---------------|----------|
| 1 | `fig1_architecture` | schematic | System architecture: problem → signals → router → tiers; pipeline below | none | `fig_architecture` |
| 2 | `fig2_workflow` | schematic | Multi-agent workflow Analyzer→Solver→Verifier; upstream feeds next decision | none | `fig_workflow` |
| 3 | `fig3_router_decision_flow` | schematic | Per-call decision flow (complexity floor → confidence → role base → escalate → budget) | none | `fig_router_decision_flow` |
| 4 | `fig4_pareto_<dataset>` | data | **Cost vs Quality Pareto frontier** (the headline figure): EM vs cost/task (log x), frontier stepline; routers vs baselines vs oracle | rows with `em`, `cost_per_task` per router | `fig_pareto` |
| 5 | `fig5_utilization_<dataset>` | data | Model utilization: stacked tier distribution per router | rows with `tier_distribution` | `fig_model_utilization` |
| 6 | `fig6_ablation_<dataset>` | data | Ablation: EM of `adaptive` vs `adaptive_no_*` variants | ≥2 ablation/proposed rows | `fig_ablation` |
| 7 | `fig7_escalation_<dataset>` | data | Escalation behaviour: escalation-rate per routed router | rows with `escalation_rate` | `fig_escalation` |

## Status today (office machine, offline)
- Figures 1–3: **generated** (verified PNG+PDF).
- Figures 4–5: **generated for GSM8K** from baselines (`results/figures/fig4_pareto_gsm8k.png`,
  `fig5_utilization_gsm8k.png`). HotpotQA/MuSiQue Pareto need their baselines completed.
- Figures 6–7: pending routed/ablation runs (skip gracefully until data exists).

## Styling / reproducibility
- Non-interactive Agg backend → headless-safe on any machine.
- Tier colors fixed (`TIER_COLORS`): T1 red, T2 orange, T3 blue, T4 green — consistent across
  all figures and the architecture diagram.
- 200 DPI PNG for slides; PDF for the four vector-friendly figures for the paper.
- Regenerate everything: `python make_figures.py` (after `aggregate_results.py`).

## Mermaid alternatives (for slides / GitHub rendering)
The three schematics also exist conceptually as Mermaid in
[09_PRESENTATION_OUTLINE.md](09_PRESENTATION_OUTLINE.md); the matplotlib versions are the
publication artifacts (embeddable, vector).
