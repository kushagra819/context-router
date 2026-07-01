# ADR-003: Router Strategy

## Status: ACCEPTED

## Decision
Implement per-agent routing within the multi-agent pipeline. The router selects a model tier independently for each agent call (Analyzer, Solver, Verifier) rather than routing the entire query to one model.

## Alternatives Considered
1. **Per-query routing (like FrugalGPT/RouteLLM)** — Rejected: This is what existing papers already do. No novelty.
2. **Ensemble routing (like LLM-Blender)** — Rejected: Higher cost than any single tier. Defeats the purpose.
3. **Fixed mixed-tier (no adaptive element)** — Partially adopted as a baseline, but not the primary method. Too static.
4. **Full RL-based learned router** — Deferred to future work. Requires training infrastructure not yet built.

## Reason Chosen
Per-agent routing is the key innovation. No existing work routes at the agent level within a pipeline. It's conceptually clean, implementable without heavy ML training, and produces a compelling cost-quality story.

## Impact
- Router interface accepts `agent_role` as a first-class signal
- Each experiment logs the tier used per agent (not per query)
- Evaluation must track per-agent cost allocation
- Requires 9 router variants to tell the full story
