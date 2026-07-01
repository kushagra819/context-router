# Documentation Index

The repository is **self-describing**: these docs + the CSVs are sufficient to continue the
project with no chat history. Start at [00_PROJECT_STATE.md](00_PROJECT_STATE.md).

> All links are **relative** (portable across machines). Older docs that contained absolute
> `C:\Users\...` paths or stale claims carry a banner pointing to the current source of truth.

---

## Operating-system docs (numbered, canonical)

| Doc | Purpose |
|-----|---------|
| [00_PROJECT_STATE.md](00_PROJECT_STATE.md) | **Start here.** Current stage, what's done, what remains. |
| [01_RESEARCH_GAP.md](01_RESEARCH_GAP.md) | Literature survey (RouteLLM, FrugalGPT, AutoMix, MasRouter…) + the gap. |
| [02_DATASET_SPECS.md](02_DATASET_SPECS.md) | GSM8K / HotpotQA / MuSiQue specs. |
| [03_MODEL_MATRIX.md](03_MODEL_MATRIX.md) | 4-tier hierarchy, pricing, rate limits, alt providers. |
| [04_BASELINE_PROTOCOL.md](04_BASELINE_PROTOCOL.md) | How baselines are run. |
| [05_ROUTER_SPEC.md](05_ROUTER_SPEC.md) | Early router spec (→ superseded by ROUTER_FINAL_SPEC). |
| [06_EVALUATION_PROTOCOL.md](06_EVALUATION_PROTOCOL.md) | Metrics, cost model, statistical plan. |
| [07_RISK_REGISTER.md](07_RISK_REGISTER.md) | Risks + mitigations (R1 token pool, R2/R3 T4 anomaly, R10 cost). |
| [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md) | Canonical results table (verified numbers). |
| [09_PRESENTATION_OUTLINE.md](09_PRESENTATION_OUTLINE.md) | Slide-by-slide deck outline. |
| [10_SESSION_HANDOFF.md](10_SESSION_HANDOFF.md) | Last-session summary + next actions. |
| [11_BASELINE_VALIDATION.md](11_BASELINE_VALIDATION.md) | Baseline-validation protocol. |
| [12_RESEARCH_CONTRIBUTION.md](12_RESEARCH_CONTRIBUTION.md) | Formal contribution & novelty. |
| [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) | Every metric's formula ↔ code. |
| [14_PAPER_OUTLINE.md](14_PAPER_OUTLINE.md) | Paper outline + evidence checklist. |
| [15_FIGURE_PLAN.md](15_FIGURE_PLAN.md) | All figures ↔ generation code. |
| [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md) | **Exact home-machine commands.** |
| [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md) | Claims ↔ evidence ↔ command. |

## Key reports & specs (un-numbered)

| Doc | Purpose |
|-----|---------|
| [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) | **Authoritative** baseline status (from `validate_baselines.py`). |
| [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md) | **Authoritative** implemented router design (15 routers). |
| [METRICS_AND_FORMULAS.md](METRICS_AND_FORMULAS.md) · [FIGURE_PLAN.md](FIGURE_PLAN.md) · [PAPER_OUTLINE.md](PAPER_OUTLINE.md) · [RESEARCH_CONTRIBUTION.md](RESEARCH_CONTRIBUTION.md) | Aliases → the numbered canonical docs. |

## Methodology freeze (publication readiness — results are placeholders)

Frozen before the expensive API runs so every experiment maps to a publishable claim.

| Doc | Purpose |
|-----|---------|
| [claim_evidence_matrix.md](claim_evidence_matrix.md) | Every claim (C1–C8) ↔ experiment ↔ metric ↔ stat test ↔ figure ↔ table; "no claim without evidence". |
| [publication_metrics_spec.md](publication_metrics_spec.md) | Final metric set (primary/secondary/diagnostic): formula, code location, implemented vs spec-only. |
| [statistical_validation_plan.md](statistical_validation_plan.md) | CIs, bootstrap, sample size, hypothesis test per metric; pre-registered primary hypothesis (WCG>0). |
| [literature_comparison_framework.md](literature_comparison_framework.md) | Comparability vs RouteLLM/FrugalGPT/AutoMix/MasRouter/Hybrid-LLM. |
| [paper_tables_template.md](paper_tables_template.md) | Tables 1–7 (placeholder cells). |
| [paper_figures_template.md](paper_figures_template.md) | Figures 1–7 (purpose, data source, plot type, expected insight). |
| [experiment_execution_plan.md](experiment_execution_plan.md) | Optimal run order: runtime/cost/risk/publication-value per experiment. |
| [publishable_paper_skeleton.md](publishable_paper_skeleton.md) | Full ACL/EMNLP skeleton, numbers-free, ready to fill. |

### Adversarial / integrity (pre-mortem before spending API quota)

| Doc | Purpose |
|-----|---------|
| [learned_router_risk_assessment.md](learned_router_risk_assessment.md) | Senior-reviewer audit of the learned router: 17 risks (3 Critical) — leakage, oracle-label quality, role-collapse, overfitting, calibration, bias, generalization — ranked with mitigations. |
| [reviewer_attack_report.md](reviewer_attack_report.md) | 4 hostile reviewers (ACL×2, EMNLP, NeurIPS Systems) try to reject the paper; severity matrix + top-10 rejection reasons + rebuttals. |
| [RESULT_PROVENANCE_MAP.md](RESULT_PROVENANCE_MAP.md) | Every claim C1–C8 traced: claim → experiment → raw logs+columns → aggregation script → metric → stat test → figure → table → paper section, with PENDING-link register. |
| [learned_router_recovery_plan.md](learned_router_recovery_plan.md) | Minimum protocol changes to make the learned router publishable (closes L1/L2/L5): group-by-problem CV, reframe as role-agnostic learned difficulty router (C4→cascade/adaptive), offline + cross-fit/LODO eval; prioritized by validity-gained/effort. |

## Decision records

[DECISIONS/](DECISIONS/): ADR-001 (CSV truth source) · ADR-002 (dataset strategy) ·
ADR-003 (per-agent routing) · ADR-004 (innovation selection) · ADR-005 (evaluation metrics).

## Historical (kept for context; carry "stale/superseded" banners)

- [project_audit.md](project_audit.md) — original automated audit (pre-router).
- [implementation_plan.md](implementation_plan.md) — Stage-1 plan (baseline-status section corrected).
- [SESSION_CONTEXT.md](SESSION_CONTEXT.md), [ROADMAP.md](ROADMAP.md) — earlier session/roadmap notes.
- `planning/` — research-trajectory archive (proposals, slides, literature, walkthroughs).
  Deprecated GraphRAG explorations are marked **[DEPRECATED]** inside those files.
