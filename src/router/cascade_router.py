"""
Confidence-Based Cascading Router
==================================
Starts each agent at a low tier. If the upstream agent's confidence
is below a threshold, escalates the current agent to a higher tier.

This is the primary innovation: workflow-aware cascading within
a multi-agent pipeline.
"""

from src.router.base_router import BaseRouter, RoutingDecision
from src.router.signals import extract_question_features, extract_confidence


class CascadeRouter(BaseRouter):
    """
    Confidence-based cascading with per-role defaults.
    
    Logic:
    1. Analyzer always starts at `default_tiers["analyzer"]` (no upstream)
    2. Solver checks analyzer's confidence:
       - High confidence → use `default_tiers["solver"]`
       - Low confidence → escalate to `escalation_tiers["solver"]`
    3. Verifier checks solver's confidence:
       - High confidence → use `default_tiers["verifier"]`
       - Low confidence → escalate to `escalation_tiers["verifier"]`
    
    Optional complexity gating: if question is very simple, start at T1 regardless.
    """

    def __init__(
        self,
        default_tiers: dict[str, int] | None = None,
        escalation_tiers: dict[str, int] | None = None,
        confidence_threshold: float = 0.5,
        complexity_floor: float = 0.15,  # Below this, always use T1
    ):
        self._default_tiers = default_tiers or {
            "analyzer": 2,
            "solver": 2,
            "verifier": 1,
        }
        self._escalation_tiers = escalation_tiers or {
            "analyzer": 3,   # N/A (no upstream), but if needed
            "solver": 4,     # If analyzer was uncertain, give solver the best model
            "verifier": 3,   # If solver was uncertain, give verifier a stronger check
        }
        self._confidence_threshold = confidence_threshold
        self._complexity_floor = complexity_floor

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
        # Complexity floor: very simple questions get T1 for all agents
        features = extract_question_features(question)
        if features["complexity_score"] < self._complexity_floor:
            return RoutingDecision(
                tier=1,
                router_name=self.name,
                agent_role=agent_role,
                reason=f"Simple question (complexity={features['complexity_score']:.2f} < {self._complexity_floor}) → T1",
                confidence=0.8,
            )

        # Analyzer: no upstream signal, use default
        if agent_role == "analyzer" or upstream_output is None:
            tier = self._default_tiers.get(agent_role, 2)
            return RoutingDecision(
                tier=tier,
                router_name=self.name,
                agent_role=agent_role,
                reason=f"No upstream → default T{tier} for {agent_role}",
                confidence=0.6,
            )

        # Extract upstream confidence if not provided
        if upstream_confidence is None:
            upstream_confidence = extract_confidence(upstream_output)

        # Cascading decision
        base_tier = self._default_tiers.get(agent_role, 2)
        escalated_from = None
        if upstream_confidence >= self._confidence_threshold:
            tier = base_tier
            reason = f"Upstream confident ({upstream_confidence:.2f} >= {self._confidence_threshold}) → default T{tier}"
        else:
            tier = self._escalation_tiers.get(agent_role, 4)
            if tier > base_tier:
                escalated_from = base_tier
            reason = f"Upstream uncertain ({upstream_confidence:.2f} < {self._confidence_threshold}) → escalate T{tier}"

        # Budget check: don't escalate beyond budget
        if cost_budget < float("inf"):
            remaining = cost_budget - cost_spent
            if remaining < 0.001 and tier > 1:
                tier = 1
                escalated_from = None
                reason += " [budget constrained to T1]"

        return RoutingDecision(
            tier=tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=reason,
            confidence=0.7 if upstream_confidence >= self._confidence_threshold else 0.5,
            base_tier=base_tier,
            escalated_from=escalated_from,
        )

    @property
    def name(self) -> str:
        return "cascade"
