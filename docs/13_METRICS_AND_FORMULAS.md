# 13 — Metrics & Formulas

> **Status:** Canonical. Every metric here is implemented in
> [`src/evaluation/metrics.py`](../src/evaluation/metrics.py) (task scorers) and
> [`src/evaluation/routing_metrics.py`](../src/evaluation/routing_metrics.py) (routing /
> efficiency / research), and aggregated by
> [`src/evaluation/aggregate.py`](../src/evaluation/aggregate.py). Doc and code are kept in
> lockstep — if you change one, change the other.

Notation: a run evaluates `N` problems. For problem `i`, `correct_i ∈ {0,1}` is exact match,
`f1_i ∈ [0,1]` token-F1, `cost_i` the summed hypothetical USD over its agent calls,
`tok_i` total tokens, `lat_i` summed latency (s). Tier prices are in
[`03_MODEL_MATRIX.md`](03_MODEL_MATRIX.md) / `MODEL_CONFIG`.

---

## A. Task-quality metrics

| Metric | Formula | Code | Notes |
|--------|---------|------|-------|
| **Accuracy / Exact Match (EM)** | `EM = (1/N) Σ correct_i` | `metrics.gsm8k_check_correct`, `hotpotqa_check_correct`, `routing_metrics.exact_match` | GSM8K: numeric equality (\|a−b\|<1e−6). HotpotQA/MuSiQue: normalized string equality. |
| **Answer normalization** | lowercase → strip punctuation → remove articles (a/an/the) → collapse whitespace | `metrics.normalize_answer` | Standard SQuAD/HotpotQA normalization. |
| **Token-F1** | `F1 = 2·P·R/(P+R)`, `P = overlap/len(pred)`, `R = overlap/len(gold)` (bag-of-tokens on normalized text) | `metrics.hotpotqa_compute_f1` | `F1 ≥ EM` always; "F1 < EM" ⇒ a bug. GSM8K F1 collapses to EM. |
| **Macro F1** | `(1/N) Σ f1_i` | `routing_metrics.mean_f1` | Reported per (dataset, router). |

---

## B. Routing-quality metrics

The **oracle tier** for a problem is the cheapest tier whose baseline answered it correctly
(`routing_metrics.oracle_tier`); `None` if no tier did. A router's **representative tier** for
a problem is the tier it assigned to the **verifier** (the agent that emits the final answer).

| Metric | Formula | Code |
|--------|---------|------|
| **Routing Accuracy** | fraction of *solvable* problems where `chosen_tier == oracle_tier` | `routing_metrics.routing_accuracy` |
| **Over-Provision Rate** | fraction of solvable problems with `chosen_tier > oracle_tier` (paid for unneeded capability) | `routing_metrics.over_provision_rate` |
| **Under-Provision Rate** | fraction of solvable problems the router got **wrong** (winnable but under-powered) | `routing_metrics.under_provision_rate` |
| **Escalation Rate** | fraction of **agent calls** where the router escalated above its base tier (`decision.escalated`) | `routing_metrics.escalation_rate` |

"Solvable" = oracle tier is not `None`. These exclude problems no tier could solve, so they
measure *routing decision quality*, not model ceiling.

---

## C. Efficiency metrics

| Metric | Formula | Code |
|--------|---------|------|
| **Cost per Task** | `Σ cost_i / N` | `routing_metrics.cost_per_task` |
| **Total Cost** | `Σ cost_i` (hypothetical USD; all models are free in practice) | `aggregate` |
| **Cost Reduction Factor (×)** | `cost(all-Tier-4) / cost(router)` | `routing_metrics.cost_reduction_factor` |
| **Cost Savings %** | `(1 − cost(router)/cost(all-Tier-4)) · 100` | `routing_metrics.cost_savings_pct` |
| **Latency** | `(1/N) Σ lat_i` (per problem, seconds) | `aggregate` |
| **Throughput** | `N / (Σ lat_i / 60)` (problems/min; sum-of-latency as wall-clock proxy) | `routing_metrics.throughput_per_min` |
| **Token Efficiency** | `correct_count / (Σ tok_i / 1e6)` (correct answers per 1M tokens) | `routing_metrics.token_efficiency` |

Reference for savings/retention = the **all-Tier-4 pipeline** (quality ceiling, cost
reference); set by `aggregate.REFERENCE_TIER`.

---

## D. Research metrics

| Metric | Formula | Code |
|--------|---------|------|
| **Quality Retention Rate (QRR)** | `quality(router) / quality(all-Tier-4) · 100` (EM or F1) | `routing_metrics.quality_retention_pct` |
| **Workflow Context Gain (WCG)** | `quality(workflow-aware router) − quality(best context-free router)` **at matched (≤) cost** | `routing_metrics.workflow_context_gain` |

**WCG is the headline scientific metric.** It isolates the value of the workflow-only signals
(agent role, upstream confidence, workflow stage) by comparing the proposed router
(`cascade`/`adaptive`) against the best router that uses **only** query-difficulty signals
(`complexity`) — or `random`/`fixed_mixed` — *constrained to spend no more*. A positive WCG is
direct evidence that workflow context, not just difficulty, drives the gains.
QRR > 100% can occur on HotpotQA/MuSiQue because Tier-4 EM is anomalously low (see
[BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) §4); report F1-based QRR too.

---

## E. Statistical validity

| Tool | Use | Code |
|------|-----|------|
| **Percentile bootstrap 95% CI** | CI on EM/F1 means (per-problem 0/1 or F1 resampled) | `routing_metrics.bootstrap_ci` |
| **Paired bootstrap p-value** | router-vs-baseline significance on the *same* problems | `routing_metrics.paired_bootstrap_pvalue` |

N=200 per condition gives EM 95% CIs of roughly ±7 pts at 50% (±3.4 pts at 90%). Report CIs
on every headline number; report paired p-values for router-vs-T4 and WCG comparisons. Final
paper may raise N to 500 (RISK R4).

---

## F. How metrics are computed from outputs (data flow)

```
results/baselines/*.csv  ─┐
results/routing/*.csv    ─┼─► src/evaluation/csv_io.py  (dedup, per-problem records)
                          │        │
                          │        ├─► routing_metrics.py  (formulas above)
                          │        └─► aggregate.py        (master table + savings/retention/oracle)
                          ▼
       results/master_results.{json,csv,md}  ─►  make_figures.py  ─►  results/figures/*.png
```

Run: `python aggregate_results.py` → master tables; `python make_figures.py` → figures.
Offline preview without live runs: `python simulate_routing.py` (see §F of
[16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md)).
