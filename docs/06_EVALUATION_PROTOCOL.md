# Evaluation Protocol

## 1. Metrics

### 1.1 Primary Metrics

| Metric | Applies To | Definition |
|--------|-----------|-----------|
| **Accuracy** | GSM8K | `correct_count / total_count × 100` |
| **Exact Match (EM)** | HotpotQA, MuSiQue | `normalize(predicted) == normalize(gold_truth)` |
| **Cost** | All | Sum of hypothetical USD cost across all agent calls |
| **Cost Savings %** | Router experiments | `(1 - router_cost / baseline_t4_cost) × 100` |

### 1.2 Secondary Metrics

| Metric | Applies To | Definition |
|--------|-----------|-----------|
| **Token F1** | HotpotQA, MuSiQue | Harmonic mean of token-level precision and recall |
| **Quality Retention %** | Router experiments | `router_em / baseline_t4_em × 100` |
| **Avg Latency** | All | Mean wall-clock time per problem |
| **Avg Tokens** | All | Mean total tokens (input + output) per problem |

### 1.3 Answer Normalization

Applied to both predicted and ground truth before comparison:
1. Lowercase
2. Remove punctuation
3. Remove articles (`a`, `an`, `the`)
4. Collapse whitespace

Implemented in `src/evaluation/metrics.py::normalize_answer()`.

### 1.4 Answer Extraction

| Dataset | Primary Pattern | Fallback |
|---------|----------------|----------|
| GSM8K | `Final Answer: <number>` | `#### <number>`, `answer is <number>`, last number in text |
| HotpotQA | `Final Answer: <text>` | `answer is <text>`, last non-empty line |
| MuSiQue | Same as HotpotQA | Same as HotpotQA |

## 2. Cost Model

All models are free to use, but we assign hypothetical costs based on published pricing:

```python
cost_usd = (input_tokens / 1_000_000) * cost_per_1m_input + 
           (output_tokens / 1_000_000) * cost_per_1m_output
```

| Tier | Input $/1M | Output $/1M |
|:----:|:----------:|:-----------:|
| 1 | $0.03 | $0.06 |
| 2 | $0.59 | $0.79 |
| 3 | $2.66 | $2.66 |
| 4 | $2.00 | $8.00 |

## 3. Statistical Validity

### For Final Paper
- Report bootstrap confidence intervals (95% CI) for EM and F1
- Use paired bootstrap test for significance between router variants
- Report effect sizes alongside p-values

### Current Phase
- Report point estimates with N=200 per condition
- Flag any result where N < 200

## 4. Evaluation Scripts

| Script | Purpose |
|--------|---------|
| `scripts/verify_baseline_integrity.py` | Verifies CSV completeness and truncation |
| `scripts/recompute_and_update_metrics.py` | Recomputes EM/F1/cost from CSVs |
| `scripts/recompute_metrics.py` | Older version (may have bugs) |

## 5. Pareto Analysis (For Router Evaluation)

Plot: **Quality (EM/Accuracy) vs. Cost (USD)**

Each point represents a router variant or baseline tier. The Pareto frontier shows optimal quality-cost tradeoffs.

```
Quality (EM%)
  100 ─┤         ● T4
       │       ● T3
   90 ─┤     ● T2
       │   ● Router
   80 ─┤ ● T1
       │
   70 ─┤
       └──────────────────── Cost ($)
        0.01  0.1   1.0   10.0
```

The router should appear **above and to the left** of the baseline tier line, achieving better quality-cost tradeoff.
