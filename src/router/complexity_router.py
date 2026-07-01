"""
Complexity-Based Router
=======================
Routes based on question features (complexity estimate).
Simple questions → lower tier. Complex questions → higher tier.
Agent role adjusts the threshold.
"""

from src.router.base_router import BaseRouter, RoutingDecision
from src.router.signals import extract_question_features, extract_context_complexity


class ComplexityRouter(BaseRouter):
    """
    Uses question complexity + agent role to select tier.
    
    Logic:
    - Compute complexity_score from question features
    - Adjust threshold per agent role:
      * Analyzer: higher threshold (decomposition is tolerant of weaker models)
      * Solver: lower threshold (solving needs stronger models)
      * Verifier: highest threshold (verification is simplest)
    - Map complexity to tier based on thresholds
    """

    def __init__(
        self,
        thresholds: dict[str, list[float]] | None = None,
    ):
        # Default thresholds: complexity_score cutoffs for [T1|T2, T2|T3, T3|T4]
        # Lower thresholds = more aggressive escalation to higher tiers
        self._thresholds = thresholds or {
            "analyzer": [0.3, 0.6, 0.9],    # Lenient — stays on lower tiers longer
            "solver":   [0.15, 0.35, 0.6],   # Aggressive — escalates earlier
            "verifier": [0.4, 0.7, 0.95],    # Most lenient — rarely needs high tier
        }

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
        features = extract_question_features(question)
        complexity = features["complexity_score"]
        
        # Add context complexity if available
        ctx_complexity = extract_context_complexity(context)
        combined = complexity * 0.7 + ctx_complexity * 0.3
        
        # Get role-specific thresholds
        role_thresholds = self._thresholds.get(agent_role, self._thresholds["solver"])
        
        # Map to tier
        if combined < role_thresholds[0]:
            tier = 1
        elif combined < role_thresholds[1]:
            tier = 2
        elif combined < role_thresholds[2]:
            tier = 3
        else:
            tier = 4

        return RoutingDecision(
            tier=tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=f"Complexity={combined:.2f}, role={agent_role} → T{tier}",
            confidence=0.7,
        )

    @property
    def name(self) -> str:
        return "complexity"
