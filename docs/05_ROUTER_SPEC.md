# Router Specification

> [!NOTE]
> **SUPERSEDED by [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md)** (the implemented design:
> 15 routers, ablation variants, signal table, file map). This earlier spec is retained for
> history; where they differ, the FINAL spec and the code in `src/router/` win.

> **Status:** APPROVED — implemented (see ROUTER_FINAL_SPEC.md)
> **Last Updated:** 2026-06-22

---

## 1. Core Design Principle

> The router does NOT route entire queries. It routes **individual agent invocations** within a multi-agent pipeline.

For each problem, the pipeline calls 3 agents sequentially:
```
Question → [Router→Analyzer] → [Router→Solver] → [Router→Verifier] → Answer
```

The router decides the model tier (1-4) independently for each agent call.

---

## 2. Router Interface

```python
class BaseRouter(ABC):
    """Abstract router interface."""
    
    @abstractmethod
    def select_tier(
        self,
        question: str,
        agent_role: str,           # "analyzer" | "solver" | "verifier"
        context: dict | None,      # dataset context (paragraphs, etc.)
        upstream_output: str | None, # previous agent's response text
        upstream_confidence: float | None,  # parsed confidence [0,1]
        cost_spent: float,          # cost already spent on this problem
        cost_budget: float,         # total budget for this problem
    ) -> int:
        """Return tier (1, 2, 3, or 4) for this agent call."""
        ...
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable router name."""
        ...
```

---

## 3. Router Variants

### 3.1 Baselines (no API calls needed — computed from CSVs)

| Router | Logic | Purpose |
|--------|-------|---------|
| **Oracle** | For each problem × agent, picks the cheapest tier that produces the correct answer (from baseline data) | Upper bound on cost savings |
| **Random** | Uniform random tier for each agent call | Lower bound / sanity check |
| **Fixed-Tier** | Always uses the same tier for all agents (Tier 1, 2, 3, or 4) | Equivalent to current baselines |
| **Fixed Mixed-Tier** | Static mapping: Analyzer→T2, Solver→T4, Verifier→T1 | Tests if role-based assignment helps |

### 3.2 Proposed Methods (require API calls for evaluation)

| Router | Logic | Innovation |
|--------|-------|-----------|
| **Complexity-Based** | Use question features (length, entity count, estimated hops) to pick tier per agent | Lightweight, interpretable |
| **Confidence-Cascading** | Start each agent at Tier 1; if confidence < threshold, retry at next tier up | Adaptive, query-dependent |
| **Adaptive Mixed-Tier** | Learn the best tier mapping per agent role from training data, with complexity gating | Full innovation — per-agent + per-complexity |

### 3.3 Stretch Goals (if time permits)

| Router | Logic | Innovation |
|--------|-------|-----------|
| **Learned Router** | Train a small classifier (logistic regression or decision tree) from baseline CSV features to predict optimal tier | Data-driven routing |
| **Dynamic Pipeline** | Skip agents for simple queries (e.g., solver-only for GSM8K) | Pipeline depth optimization |

---

## 4. Routing Signals

### 4.1 Pre-routing Signals (available before any agent runs)

| Signal | Source | How to Extract |
|--------|--------|---------------|
| `question_length` | Input | `len(question.split())` |
| `entity_count` | Input | Named entity count via simple heuristic (capitalized words) |
| `estimated_hops` | Input/Dataset | From dataset metadata or sentence count in question |
| `dataset_type` | Input | "gsm8k", "hotpotqa", "musique" |
| `context_length` | Input | Total tokens in supporting paragraphs |

### 4.2 Intra-pipeline Signals (available after upstream agent runs)

| Signal | Source | How to Extract |
|--------|--------|---------------|
| `upstream_confidence` | Previous agent output | Parse phrases like "I am confident", hedging words, answer definiteness |
| `upstream_length` | Previous agent output | Response length (proxy for reasoning depth) |
| `upstream_has_answer` | Previous agent output | Whether "Final Answer:" pattern is present |
| `cost_spent` | Logger | Cumulative cost so far for this problem |

### 4.3 Confidence Extraction

```python
def extract_confidence(response_text: str) -> float:
    """Extract a confidence score [0, 1] from agent response text."""
    text = response_text.lower()
    
    # High confidence signals
    high_signals = ["i am confident", "clearly", "definitely", "without doubt",
                    "the answer is", "final answer:"]
    # Low confidence signals  
    low_signals = ["i'm not sure", "uncertain", "might be", "possibly",
                   "it's unclear", "cannot determine", "insufficient"]
    
    high_count = sum(1 for s in high_signals if s in text)
    low_count = sum(1 for s in low_signals if s in text)
    
    if high_count > 0 and low_count == 0:
        return 0.9
    elif low_count > 0 and high_count == 0:
        return 0.3
    elif high_count > low_count:
        return 0.7
    elif low_count > high_count:
        return 0.4
    else:
        return 0.6  # neutral
```

---

## 5. Cost Model

All models are free (academic access), but we assign **hypothetical costs** based on published pricing to demonstrate economic value:

| Tier | Model | Input $/1M | Output $/1M | Relative Cost |
|:----:|-------|:----------:|:-----------:|:-------------:|
| 1 | Gemma 4 E4B | $0.03 | $0.06 | 1× (baseline) |
| 2 | Llama 3.3 70B | $0.59 | $0.79 | ~15× |
| 3 | Llama 3.1 405B | $2.66 | $2.66 | ~60× |
| 4 | GPT-4.1 | $2.00 | $8.00 | ~100× |

---

## 6. Evaluation Plan

### 6.1 Metrics

| Metric | Definition | Priority |
|--------|-----------|:--------:|
| **Exact Match (EM)** | Normalized answer equality | Primary |
| **F1 Score** | Token-level precision/recall | Secondary |
| **Total Cost** | Sum of hypothetical costs | Primary |
| **Cost Savings %** | `(1 - router_cost / baseline_t4_cost) × 100` | Primary |
| **Quality Retention %** | `router_em / baseline_t4_em × 100` | Primary |
| **Avg Latency** | Mean per-problem latency | Secondary |

### 6.2 Comparison Table Structure

```
| Router          | GSM8K EM | HotpotQA EM | MuSiQue EM | Avg Cost | Cost Savings |
|-----------------|:--------:|:-----------:|:----------:|:--------:|:------------:|
| Baseline T1     |          |             |            |          |              |
| Baseline T2     |          |             |            |          |              |
| Baseline T3     |          |             |            |          |              |
| Baseline T4     |          |             |            |          |              |
| Oracle          |          |             |            |          |              |
| Random          |          |             |            |          |              |
| Fixed Mixed     |          |             |            |          |              |
| Complexity      |          |             |            |          |              |
| Cascade         |          |             |            |          |              |
| Adaptive Mixed  |          |             |            |          |              |
```

### 6.3 Ablation Design

| Ablation | What's Removed | Tests |
|----------|---------------|-------|
| No role signal | Same tier for all agents | Does per-agent routing matter? |
| No complexity signal | Ignore question features | Does complexity help? |
| No confidence signal | No upstream feedback | Does cascading help? |
| No cost budget | Ignore remaining budget | Does budget awareness help? |

---

## 7. Implementation Files

```
src/router/
├── __init__.py           # Exports all routers
├── base_router.py        # BaseRouter ABC + SignalExtractor
├── oracle_router.py      # Oracle (from CSVs)
├── random_router.py      # Random baseline
├── fixed_tier_router.py  # Single-tier baseline
├── fixed_mixed_router.py # Static role→tier mapping
├── complexity_router.py  # Feature-based routing
├── cascade_router.py     # Confidence-based cascading
├── adaptive_router.py    # Full adaptive mixed-tier
└── signals.py            # Signal extraction utilities
```
