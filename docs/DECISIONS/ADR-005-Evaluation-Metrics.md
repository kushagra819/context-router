# ADR-005: Evaluation Metrics

## Status: ACCEPTED

## Decision
Use **Exact Match (EM)** as the primary quality metric and **hypothetical cost in USD** as the primary efficiency metric. Token F1, latency, and cost savings percentage are secondary metrics.

## Alternatives Considered
1. **F1 as primary** — Rejected as primary because F1 from truncated CSVs is unreliable. EM is computed at runtime and is always valid. F1 remains secondary.
2. **BLEU/ROUGE** — Rejected: Inappropriate for short-answer QA tasks.
3. **Actual cost** — Rejected: All models are free via academic access. Hypothetical cost based on published pricing is the standard approach in routing papers (see FrugalGPT).
4. **Latency as primary** — Rejected: Latency is heavily influenced by rate limiting and network conditions, not model capability. Include but don't optimize for.

## Reason Chosen
EM is the standard metric for HotpotQA and MuSiQue evaluation. Accuracy (a form of EM) is standard for GSM8K. Hypothetical cost enables Pareto analysis even with free-tier APIs.

## Impact
- All results tables lead with EM/Accuracy
- Pareto plots use EM vs. Cost axes
- F1 is reported but not used for routing decisions
- Cost savings % = primary efficiency claim
- Report bootstrap 95% CIs for final paper
