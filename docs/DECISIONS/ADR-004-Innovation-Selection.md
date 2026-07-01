# ADR-004: Innovation Selection

## Status: ACCEPTED

## Decision
The primary innovation is **Workflow-Aware Multi-Agent Routing with Confidence-Based Cascading**. Secondary explorations include dynamic pipeline depth, signal ablation, and cost-quality Pareto analysis.

## Alternatives Considered
1. **Complexity-only routing** — Partially adopted but insufficient alone. Similar to RouteLLM's approach.
2. **Learned router from scratch** — Deferred. Requires sufficient training data and careful feature engineering. Will explore as stretch goal.
3. **Dynamic agent graph (skip agents)** — Interesting but risky. May confuse reviewers. Keep as future work.
4. **Provider fallback routing** — Too operational, not research-grade.

## Reason Chosen
Confidence-based cascading within a per-agent framework is:
- Genuinely novel (no prior work)
- Implementable without ML training
- Produces measurable cost savings
- Tells a clear story for presentation/publication
- Can be enhanced with learned components later

## Impact
- Build 6+ router variants to tell a complete story
- Oracle/Random/Fixed establish bounds
- Complexity + Cascade are the proposed methods
- Ablation study validates each signal's contribution
