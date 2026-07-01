"""
Random Router
=============
Lower bound baseline. Uniformly random tier selection for each agent call.
"""

import random

from src.router.base_router import BaseRouter, RoutingDecision


class RandomRouter(BaseRouter):
    """
    Selects a tier uniformly at random for each agent call.
    Provides a lower bound — any real router should beat this.
    """

    def __init__(self, tiers: list[int] | None = None, seed: int | None = 42):
        self._tiers = tiers or [1, 2, 3, 4]
        self._rng = random.Random(seed)

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
        tier = self._rng.choice(self._tiers)

        return RoutingDecision(
            tier=tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=f"Random: tier {tier} selected uniformly",
            confidence=0.25,  # 1/4 chance
        )

    @property
    def name(self) -> str:
        return "random"
