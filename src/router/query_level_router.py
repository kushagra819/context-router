"""
Query-Level Router (the per-QUERY baseline)
==========================================
The control that isolates the paper's central claim. RouteLLM / FrugalGPT /
Hybrid-LLM route at the QUERY level: one model is chosen for the whole query.
This router does exactly that inside our pipeline -- it picks ONE tier from query
complexity and uses it for ALL THREE agents (analyzer = solver = verifier),
ignoring agent role, upstream confidence, and stage.

Comparing our per-AGENT routers (complexity/cascade/adaptive) against this
per-QUERY router on identical problems is the direct test of reviewer question
"what does per-agent routing buy over running a query-level router once per
pipeline?". It is deterministic per problem (same tier for every role), so it
truly represents a single per-query decision.

It deliberately reuses the SAME complexity score and thresholds as the per-agent
ComplexityRouter's "solver" profile, so any measured gap is attributable to the
PER-AGENT degree of freedom, not to a different difficulty estimator.
"""

from src.router.base_router import BaseRouter, RoutingDecision
from src.router.signals import extract_question_features, extract_context_complexity


class QueryLevelRouter(BaseRouter):
    """One tier per QUERY (role-agnostic) from query+context complexity."""

    def __init__(self, thresholds: tuple[float, float, float] = (0.15, 0.35, 0.6)):
        # Same cutoffs as ComplexityRouter's "solver" profile (the answering role),
        # so the only difference vs ComplexityRouter is that role is ignored here.
        self._thresholds = thresholds
        self._cache: dict[tuple, int] = {}

    def _tier_for(self, question: str, context) -> int:
        features = extract_question_features(question)
        combined = features["complexity_score"] * 0.7 + extract_context_complexity(context) * 0.3
        t0, t1, t2 = self._thresholds
        if combined < t0:
            return 1
        if combined < t1:
            return 2
        if combined < t2:
            return 3
        return 4

    def select_tier(
        self,
        question: str,
        agent_role: str,
        context: dict | None = None,
        upstream_output: str | None = None,
        upstream_confidence: float | None = None,
        cost_spent: float = 0.0,
        cost_budget: float = float("inf"),
        problem_id: int | None = None,
        dataset: str = "",
    ) -> RoutingDecision:
        # One decision per query: cache by problem so every role gets the SAME tier.
        key = (dataset, problem_id) if problem_id is not None else ("_", question)
        if key not in self._cache:
            self._cache[key] = self._tier_for(question, context)
        tier = self._cache[key]
        return RoutingDecision(
            tier=tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=f"Query-level (role-agnostic) tier T{tier} for the whole pipeline",
            confidence=0.6,
            base_tier=tier,
        )

    def reset(self):
        pass  # cache is keyed by (dataset, problem_id); safe to persist across problems

    @property
    def name(self) -> str:
        return "query_level"
