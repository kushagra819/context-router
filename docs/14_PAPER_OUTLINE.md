# 14 — Paper Outline & Evidence Checklist

> **Status:** Canonical outline (the paper itself is intentionally **not** written — see
> mission). Each section lists the **evidence** that must be in hand before it can be drafted,
> mapped to the artifact/command that produces it. Tracks against
> [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md). Target venues: EMNLP/ACL or NeurIPS Efficient-ML
> workshop (see [12_RESEARCH_CONTRIBUTION.md](12_RESEARCH_CONTRIBUTION.md)).

**Working title:** *Context-Aware Per-Agent LLM Routing for Cost-Efficient Multi-Agent Reasoning*

---

## Section-by-section outline + evidence

### Abstract
One paragraph: gap (no per-agent routing in multi-agent workflows) → method (workflow-aware
per-agent tier routing) → result (X% cost cut at Y% quality retention; positive WCG).
- **Evidence needed:** final headline numbers. ⏳ (fill from master table).

### 1. Introduction
LLMs span ~100× cost; multi-agent pipelines multiply calls; current routers are per-query.
Contribution bullets (C1–C7).
- **Evidence:** cost-ratio table (✅ `03_MODEL_MATRIX.md`); contribution list (✅ doc 12/17).

### 2. Related Work
Single-agent routing (RouteLLM, FrugalGPT, AutoMix, Hybrid-LLM); multi-agent routing
(MasRouter); multi-agent frameworks (AutoGen, MetaGPT). Positioning table: *who routes per
agent? who uses upstream confidence/role/stage?* → none.
- **Evidence:** comparison table. ✅ basis in `01_RESEARCH_GAP.md`; **TODO:** finalize a
  feature-matrix table (rows = systems, cols = per-agent? role? confidence? stage? budget?).

### 3. Research Gap
The intersection (adaptive routing × multi-agent workflows) is unexplored.
- **Evidence:** ✅ `01_RESEARCH_GAP.md`, `12_RESEARCH_CONTRIBUTION.md`.

### 4. Methodology
- 4.1 Multi-agent pipeline (Analyzer→Solver→Verifier) — Fig 2.
- 4.2 Datasets & tiers — `02_DATASET_SPECS.md`, `03_MODEL_MATRIX.md`.
- 4.3 Metrics — `13_METRICS_AND_FORMULAS.md`.
- **Evidence:** ✅ all specs exist; Fig 2 ✅ generated.

### 5. Router Design
Signals, the four-step `adaptive` procedure, `cascade`, `complexity`, `learned`, references
(oracle/random/fixed/fixed_mixed) — Figs 1 & 3.
- **Evidence:** ✅ `ROUTER_FINAL_SPEC.md`, code in `src/router/`, Figs 1 & 3 generated.

### 6. Experiments
Setup, N=200/condition, resume/reproducibility, the full router matrix + ablations.
- **Evidence:** ✅ `16_EXPERIMENT_MANIFEST.md` (exact commands), `04_BASELINE_PROTOCOL.md`,
  `06_EVALUATION_PROTOCOL.md`.

### 7. Results
- 7.1 **Cost–quality Pareto** (Fig 4) — headline.
- 7.2 Main table: EM/F1, cost, savings×, QRR per router×dataset (`master_results.md`).
- 7.3 **Workflow Context Gain** (C4) with paired-bootstrap significance.
- 7.4 Ablation (Fig 6, C5). 7.5 Model utilization (Fig 5) & escalation (Fig 7).
- **Evidence:** ⏳ live routed runs → `aggregate_results.py` → `make_figures.py`.
  🟡 GSM8K baselines + oracle + Pareto already available.

### 8. Discussion
When per-agent routing helps most (multi-hop > single-hop, since GSM8K is near-ceiling, R6);
verifier-tier sensitivity; the Tier-4 EM-vs-F1 story.
- **Evidence:** per-dataset trends; ✅ anomaly analysis in `BASELINE_VALIDATION_REPORT.md` §4.

### 9. Limitations
N=200; hypothetical costs (ratios only, R10); confidence is lexical not calibrated; offline
simulation is an estimate; 3 datasets / 1 pipeline shape.
- **Evidence:** ✅ `07_RISK_REGISTER.md`, simulation caveat in `src/evaluation/simulate.py`.

### 10. Future Work
Full-pipeline cascade (re-run at higher tier on low final confidence); learned per-agent
labels via per-agent ablation; calibrated confidence; dynamic pipeline depth; more datasets/N.
- **Evidence:** ✅ noted across ADR-004 / `01_RESEARCH_GAP.md`.

---

## Master evidence checklist (gate before submission)

| # | Artifact | Produced by | Status |
|---|----------|-------------|--------|
| E1 | Locked baselines, all 12 cells, EM+F1, N=200 | `run_experiment.py` (§A) + `validate_baselines.py` | 🟡 GSM8K done; multi-hop ⏳ |
| E2 | `results/master_results.{json,csv,md}` | `aggregate_results.py` | 🟡 baselines only |
| E3 | Pareto Fig 4 (×3 datasets) | `make_figures.py` | 🟡 GSM8K |
| E4 | WCG numbers + paired p-values | `aggregate_results.py` + `routing_metrics` | ⏳ |
| E5 | Ablation Fig 6 + table | §D runs → aggregate/figures | ⏳ |
| E6 | Learned-router report | `train_router.py` | ⏳ (path verified) |
| E7 | Bootstrap 95% CIs on headlines | `routing_metrics.bootstrap_ci` | ⏳ |
| E8 | Related-work feature-matrix table | manual (from doc 01) | TODO |
| E9 | Figs 1–3 schematics | `make_figures.py` | ✅ done |
| E10 | Reproducibility appendix (commands, seeds, env) | `16_EXPERIMENT_MANIFEST.md` + `requirements.txt` | ✅ done |

> When E1–E8 are green, the paper can be drafted end-to-end with no missing evidence.
