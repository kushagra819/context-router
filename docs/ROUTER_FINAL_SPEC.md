# Router — Final Specification

> **Status:** FINAL & IMPLEMENTED. This is the canonical router design; it supersedes the
> earlier sketch in [05_ROUTER_SPEC.md](05_ROUTER_SPEC.md). Every component here exists in
> [`src/router/`](../src/router/) and is exercised by `tests/test_offline.py`.

---

## 1. Core principle (the contribution)

The router does **not** route whole queries (as RouteLLM/FrugalGPT do). It routes **each
agent invocation** inside a multi-agent pipeline:

```
question → [router→Analyzer] → [router→Solver] → [router→Verifier] → answer
```

Before every agent call the router picks a tier (1–4) using signals that **only exist inside
a workflow**: the agent's **role**, the **upstream agent's output + confidence**, the
**workflow stage**, and the running **cost budget** — in addition to ordinary query
complexity. See [12_RESEARCH_CONTRIBUTION.md](12_RESEARCH_CONTRIBUTION.md) and
[01_RESEARCH_GAP.md](01_RESEARCH_GAP.md).

Baselines and routers share **one** code path (`src/pipeline/routed_pipeline.py`): a baseline
is just `FixedTierRouter(tier)`. The only thing that varies across all experiments is the
routing policy — a clean, fair comparison.

---

## 2. Interface

`src/router/base_router.py`:

```python
class BaseRouter(ABC):
    def select_tier(self, question, agent_role, context=None, upstream_output=None,
                    upstream_confidence=None, cost_spent=0.0, cost_budget=inf,
                    problem_id=None, dataset="") -> RoutingDecision: ...
    @property
    def name(self) -> str: ...
    def reset(self): ...   # per-problem state hook

@dataclass
class RoutingDecision:
    tier: int; router_name: str; agent_role: str
    reason: str = ""; confidence: float = 0.0
    base_tier: int | None = None        # tier without escalation
    escalated_from: int | None = None   # set when escalated (drives escalation-rate metric)
    @property
    def escalated(self) -> bool: ...
```

Instantiate by name via the factory: `get_router(name, **kwargs)` (`src/router/__init__.py`).

---

## 3. Signals (`src/router/signals.py`)

| Signal | Availability | Extractor |
|--------|-------------|-----------|
| word_count, entity_count, estimated_hops, has_comparison, has_temporal, **complexity_score** | pre-call | `extract_question_features` |
| **context_complexity** | pre-call | `extract_context_complexity` (token volume of formatted context) |
| **agent_role** (analyzer/solver/verifier) | pre-call | pipeline-supplied (the workflow signal) |
| **upstream_confidence** ∈ [0,1] | after upstream agent | `extract_confidence` (lexical hedging/assertion cues) |
| **cost_spent / cost_budget** | running | pipeline-supplied |

`router_feature_vector(question, role, context)` produces the ordered feature vector
(`FEATURE_NAMES`) shared by training and the learned router.

---

## 4. Router catalogue (15 registered)

**Reference / anchors**

| name | logic | role |
|------|-------|------|
| `oracle` | cheapest tier correct in baselines (per problem) | cost-savings **upper bound** |
| `random` | uniform tier per call (seeded) | **lower bound** / sanity |
| `fixed_t1..fixed_t4` | one tier for all agents | **the baselines** |
| `fixed_mixed` | static role→tier map (default A→2, S→4, V→1) | tests role assignment without adaptation |

**Proposed (context-aware)**

| name | logic | key signals |
|------|-------|-------------|
| `complexity` | tier from complexity, per-role thresholds | complexity + role |
| `cascade` | per-role default; escalate next agent if upstream confidence < τ | role + **confidence** |
| `adaptive` | complexity→base, role adjust, confidence escalate/de-escalate, budget cap | **all** (the full method) |
| `learned` | classifier predicts tier from features (trained on oracle labels) | complexity + role (data-driven) |

**Ablations of `adaptive`** (one signal family removed): `adaptive_no_complexity`,
`adaptive_no_role`, `adaptive_no_confidence`, `adaptive_no_budget`.

---

## 5. The proposed method — `adaptive` (decision procedure)

For each agent call:
1. **Complexity → base tier.** `combined = 0.6·question_complexity + 0.4·context_complexity`;
   map through thresholds `(0.2, 0.4, 0.7)` to a base tier 1–4. *(off → fixed `default_tier`)*
2. **Role adjustment.** verifier → −1 tier (verification is easier), solver → +1 (answering
   needs power), analyzer → unchanged. *(off → keep base)*
3. **Confidence cascade.** For solver/verifier, if upstream confidence < `τ=0.5` escalate +1
   (record `escalated_from`); if > 0.8 de-escalate −1 (save cost). *(off → no change)*
4. **Budget cap.** If remaining budget ≈ 0, clamp to Tier 1. *(off → ignore budget)*

`cascade` is the lighter primary innovation (steps 1-floor + role defaults + step 3); `adaptive`
is the full method (all four). Both are cheap, deterministic, and interpretable — no training,
no extra LLM calls for routing.

---

## 6. Ablation design (supports the WCG claim)

| Variant (router name) | Removes | Question it answers |
|-----------------------|---------|---------------------|
| `adaptive` | — | full method |
| `adaptive_no_role` | agent-role signal | does per-agent role routing matter? |
| `adaptive_no_confidence` | upstream confidence | does workflow cascading matter? |
| `adaptive_no_complexity` | query complexity | how much is "just difficulty"? |
| `adaptive_no_budget` | budget awareness | does budget-capping matter? |

**Workflow Context Gain** = `quality(adaptive) − quality(best context-free router at ≤ cost)`,
where "context-free" = `complexity` (difficulty only). Positive WCG ⇒ the workflow signals
(role + confidence), not just difficulty, drive the improvement. (See
[13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md) §D.)

---

## 7. Cost model

All models are free in practice; we assign **hypothetical** published prices (per 1M tokens,
in/out) so cost ratios are meaningful (`MODEL_CONFIG`, [03_MODEL_MATRIX.md](03_MODEL_MATRIX.md)):
T1 0.03/0.06 · T2 0.59/0.79 · T3 2.66/2.66 · T4 2.00/8.00. We report cost **ratios** (savings ×),
not absolute USD, and state the assumption explicitly (RISK R10).

---

## 8. Files

```
src/router/
  __init__.py          get_router() factory + ROUTER_REGISTRY (15 routers)
  base_router.py       BaseRouter ABC + RoutingDecision
  signals.py           feature/confidence/context extractors + router_feature_vector
  oracle_router.py     oracle (reads baselines via stdlib csv_io; no pandas)
  random_router.py     random baseline
  fixed_tier_router.py FixedTierRouter + FixedMixedTierRouter
  complexity_router.py complexity + role thresholds
  cascade_router.py    confidence cascading (primary innovation)
  adaptive_router.py   full method + ablation flags
  learned_router.py    classifier-backed router (loads results/routing/learned_router.pkl)
  training_data.py     builds (features, oracle-tier) examples from baselines
src/pipeline/
  routed_pipeline.py   the shared multi-agent loop
  dataset_adapters.py  gsm8k/hotpotqa/musique behind one interface
  experiment.py        run driver (baseline+routed, resume, mock)
src/models/registry.py ModelRegistry (real | mock)
```

---

## 9. Decision record

Per-agent routing, confidence cascading as the primary innovation, EM+cost as primary metrics,
and "keep it simple/defensible over complex" are recorded in
[DECISIONS/ADR-003](DECISIONS/ADR-003-Router-Strategy.md) and
[ADR-004](DECISIONS/ADR-004-Innovation-Selection.md).
