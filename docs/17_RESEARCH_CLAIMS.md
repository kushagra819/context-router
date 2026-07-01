# 17 — Research Claims & Evidence

> **Status:** Canonical. Each claim is paired with the **exact evidence** that proves it and
> the **command** that produces that evidence. A claim may only enter the paper/slides once its
> evidence box is green. This is the contract between the experiments and the writing.

Legend: ✅ evidence in hand · 🟡 partial (e.g. GSM8K only) · ⏳ needs the home-machine runs.

---

## C1 — Per-agent routing is a real, unexplored design point
**Claim.** Routing each agent in a multi-agent pipeline (not the whole query) is novel and
enabled by signals absent in single-agent routing (role, upstream confidence, stage).
- **Evidence:** literature positioning + the interface that consumes these signals.
- **Source:** [01_RESEARCH_GAP.md](01_RESEARCH_GAP.md), [12_RESEARCH_CONTRIBUTION.md](12_RESEARCH_CONTRIBUTION.md), `src/router/base_router.py`.
- **Status:** ✅ (argument + implementation). Strengthen with a related-work table (RouteLLM, FrugalGPT, AutoMix, MasRouter) — see [14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md) §Related Work.

## C2 — There is large, exploitable headroom between tiers (oracle gap)
**Claim.** A per-problem oracle reaches near-ceiling quality at near-floor cost, so good
routing can save most of the cost without losing quality.
- **Evidence:** oracle EM vs cost vs single-tier baselines.
- **Source:** `oracle` row in `results/master_results.*`; offline today via `simulate_routing.py`.
- **Status (GSM8K, verified):** oracle **98.5% EM @ $0.0485/200** vs Tier-4 **97.0% @ $1.18** and
  Tier-1 **94.5% @ $0.031** — oracle beats every single tier at ~1.5× Tier-1 cost. 🟡 (extend to HotpotQA/MuSiQue after baselines).

## C3 — The proposed router retains quality at much lower cost
**Claim.** `cascade`/`adaptive` achieve high **Quality Retention** vs all-Tier-4 at a large
**Cost Reduction Factor**.
- **Evidence:** QRR (EM & F1) and cost-savings% for the proposed routers vs `baseline_t4`.
- **Source:** `results/master_results.md` (`quality_retention_pct_vs_t4`, `cost_savings_pct_vs_t4`).
- **Command:** §C+E of [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md) → `aggregate_results.py`.
- **Status:** ⏳ (needs live routed runs).

## C4 — Workflow context, not just difficulty, drives the gains (the key claim)
**Claim.** **Workflow Context Gain > 0**: `adaptive`/`cascade` beat the best difficulty-only
router (`complexity`) at matched cost.
- **Evidence:** WCG (EM & F1) + paired bootstrap significance.
- **Source:** [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) §D; `routing_metrics.workflow_context_gain`, `paired_bootstrap_pvalue`.
- **Command:** run `complexity`, `cascade`, `adaptive` live (§C) → `aggregate_results.py`.
- **Status:** ⏳.

## C5 — Each workflow signal contributes (ablation)
**Claim.** Removing role / confidence / complexity / budget each degrades EM at fixed budget.
- **Evidence:** `adaptive` vs `adaptive_no_*` EM/cost.
- **Source:** Figure 6 (`fig6_ablation_*`), ablation rows in master table.
- **Command:** §D of [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md).
- **Status:** ⏳ (router variants implemented & unit-tested; runs pending).

## C6 — A learned router approximates the oracle from cheap features
**Claim.** A small classifier trained on baseline "oracle" labels routes better than random
and approaches hand-built routers.
- **Evidence:** learned-router test accuracy + its live EM/cost vs `random`/`complexity`.
- **Source:** `results/routing/learned_router_report.json`; `learned` row in master table.
- **Command:** `train_router.py` (§B) then run `--router learned` (§C).
- **Status:** ⏳ (train→load→predict path verified offline on synthetic data).

## C7 — Results generalize across difficulty (single-hop → multi-hop)
**Claim.** The cost-quality benefit holds on GSM8K (1-hop), HotpotQA (2-hop), MuSiQue (2–4 hop).
- **Evidence:** consistent savings/retention across all three datasets.
- **Source:** master table grouped by dataset; Pareto figures per dataset.
- **Status:** 🟡 (GSM8K baselines + oracle done; multi-hop pending).

## C8 — Robustness / honesty caveats (stated, not hidden)
**Claim.** We report EM **and** F1, bootstrap CIs, and flag the Tier-4 EM anomaly and the
hypothetical-cost assumption.
- **Evidence:** CIs on every headline; F1 alongside EM; anomaly write-up.
- **Source:** [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) §4, [07_RISK_REGISTER.md](07_RISK_REGISTER.md) (R2/R3/R10), `routing_metrics.bootstrap_ci`.
- **Status:** ✅ (anomaly + method documented; CIs computed once routed runs land).

---

## Claim → figure/table map

| Claim | Primary figure | Primary table column |
|-------|----------------|----------------------|
| C2 oracle gap | Fig 4 Pareto | `oracle` row |
| C3 retention@cost | Fig 4 Pareto | `cost_savings_pct_vs_t4`, `quality_retention_pct_vs_t4` |
| C4 WCG | Fig 4 (matched-cost markers) | WCG (derived) |
| C5 ablation | Fig 6 ablation | `adaptive_no_*` EM |
| C6 learned | Fig 4/5 | `learned` row, learned report |
| C7 generalization | Fig 4 ×3 datasets | per-dataset rows |
