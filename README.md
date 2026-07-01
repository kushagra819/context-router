# Context-Aware LLM Routing for Multi-Agent AI Systems

Per-agent, run-time model-tier **routing inside a multi-agent pipeline**
(Analyzer → Solver → Verifier). Instead of choosing one model per *query* (RouteLLM,
FrugalGPT) or fixing one model for the whole pipeline (AutoGen, MetaGPT), the router
picks a tier (1–4) **before every agent call** using signals that only exist inside a
workflow — agent **role**, **upstream output/confidence**, **workflow stage** — plus
ordinary query complexity and a cost budget.

> **Status (2026-06-25, Stage 6):** a full engineering pass fixed the reviewer-blocking issues
> offline (Tier-4 EM anomaly corrected, F1-aware oracle labels, leakage-free learned-router
> evaluation, real statistics, cost-sensitivity, confidence validation) and migrated Tier 3 off
> the sunset Llama-3.1-405B to **GPT-OSS 120B**. Only computation remains.
> **Start here: [docs/STAGE6_ENGINEERING_REPORT.md](docs/STAGE6_ENGINEERING_REPORT.md)**
> (exact home-machine commands in §8), then [docs/00_PROJECT_STATE.md](docs/00_PROJECT_STATE.md).

---

## TL;DR — what's where

| You want to… | Go to |
|--------------|-------|
| Understand current state | [docs/00_PROJECT_STATE.md](docs/00_PROJECT_STATE.md) |
| Run the remaining experiments | [docs/16_EXPERIMENT_MANIFEST.md](docs/16_EXPERIMENT_MANIFEST.md) |
| Understand the router | [docs/ROUTER_FINAL_SPEC.md](docs/ROUTER_FINAL_SPEC.md) |
| Trust the baseline numbers | [docs/BASELINE_VALIDATION_REPORT.md](docs/BASELINE_VALIDATION_REPORT.md) |
| See the metrics' definitions | [docs/13_METRICS_AND_FORMULAS.md](docs/13_METRICS_AND_FORMULAS.md) |
| See claims ↔ evidence | [docs/17_RESEARCH_CLAIMS.md](docs/17_RESEARCH_CLAIMS.md) |

The repository is **self-describing**: a future session needs only these files, not chat history.

---

## Quick start

```bash
python -m venv venv && venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Verify the whole pipeline works with NO API keys / network (uses MockModel):
python tests/test_offline.py

# Produce preliminary router results + figures OFFLINE from existing baselines:
python simulate_routing.py --dataset gsm8k
python aggregate_results.py
python make_figures.py
```

For live runs (home machine): `ollama pull gemma4:e4b`, `copy .env.example .env`
(add Groq + GitHub keys), `python test_models.py`, then follow the manifest.

---

## How it works

```
question + context
      │
      ▼  for each agent: Analyzer → Solver → Verifier
  ┌────────── Router.select_tier(role, upstream output+confidence, complexity, budget) ──────────┐
  │  Tier 1 Gemma 4B (local)   Tier 2 Llama 70B (Groq)   Tier 3 Llama 405B   Tier 4 GPT-4.1      │
  └───────────────────────────────────────────────────────────────────────────────────────────┘
      ▼
   final answer  →  EM / F1 / cost / latency  →  metrics & figures
```

A **baseline is just `FixedTierRouter(tier)`** through the *same* pipeline, so baselines and
routed runs are perfectly comparable — only the routing policy changes.

### Routers (16, via `get_router(name)`)

- **Reference:** `oracle` (ceiling), `random` (floor), `fixed_t1..t4` (= baselines), `fixed_mixed`
- **Per-query control:** `query_level` (one tier for the whole pipeline — the RouteLLM/FrugalGPT
  baseline; the head-to-head that isolates the value of *per-agent* routing)
- **Proposed (per-agent):** `complexity`, `cascade` (confidence escalation), `adaptive` (full method), `learned`
- **Ablations:** `adaptive_no_{complexity,role,confidence,budget}`

---

## Project structure

```
context-router/
├── run_experiment.py          # unified runner: baselines + routed (resume, --mock)
├── simulate_routing.py        # OFFLINE router estimates from baselines (no API)
├── train_router.py            # train the learned router
├── aggregate_results.py       # build results/master_results.{json,csv,md}
├── make_figures.py            # generate all figures
├── test_models.py             # LIVE 4-tier connectivity test
├── check_all_keys.py, check_github_models.py, check_limits.py, measure_overhead.py   # diagnostics
├── src/
│   ├── models/      base, registry, mock + 4 tiers; alt_providers/ (optional)
│   ├── agents/      Analyzer/Solver/Verifier prompt templates per dataset
│   ├── pipeline/    dataset_adapters, routed_pipeline, experiment driver
│   ├── router/      base + 11 routers + signals + learned + training_data
│   ├── evaluation/  metrics, routing_metrics, csv_io, aggregate, simulate
│   └── visualization/ figures
├── scripts/         validate_baselines.py, recompute_metrics_from_dataset.py
├── tests/           test_offline.py (9 offline smoke tests)
├── results/         baselines/ (truth source), routing/, figures/, master_results.*
└── docs/            00–17 + ROUTER_FINAL_SPEC + BASELINE_VALIDATION_REPORT + DECISIONS/
```

---

## Model tiers (free / $0 budget; hypothetical prices for cost analysis)

| Tier | Model | Provider | $/1M in | $/1M out |
|:----:|-------|----------|:-------:|:--------:|
| 1 | Gemma 4 E4B | Ollama (local) | 0.03 | 0.06 |
| 2 | Llama 3.3 70B | Groq | 0.59 | 0.79 |
| 3 | GPT-OSS 120B | Groq (primary) + OpenRouter (failover) | 0.60 | 0.90 |
| 4 | GPT-4.1 | OpenAI direct (preferred) + GitHub (fallback) | 2.00 | 8.00 |

Tier 3 was migrated off the sunset Llama-3.1-405B → Llama-4-Maverick → **GPT-OSS 120B**;
Tiers 3 & 4 use **separate key pools** (resolves the shared-pool confound R1).
Prices are representative/hypothetical (R10).

Details + alternative providers: [docs/03_MODEL_MATRIX.md](docs/03_MODEL_MATRIX.md).

---

## Results snapshot (GSM8K, verified offline)

| Router | EM | Cost (200 problems) |
|--------|:--:|:--:|
| Tier 1 only | 94.5% | $0.031 |
| Tier 4 only | 97.0% | $1.182 |
| **Oracle** | **98.5%** | **$0.049** |

The oracle beats every single tier at ~1.5× Tier-1 cost — the headroom the router targets.
Multi-hop datasets and the proposed routers populate after the home-machine runs.

---

## Reproducibility

Deterministic seeds; resumable runs; CSVs are the single source of truth (ADR-001); every
metric is defined in [docs/13_METRICS_AND_FORMULAS.md](docs/13_METRICS_AND_FORMULAS.md) and
implemented in `src/evaluation/`. Offline analysis uses only the Python standard library.
