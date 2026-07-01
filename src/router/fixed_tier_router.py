"""
Fixed-Tier and Fixed Mixed-Tier Routers
=======================================
Static routing strategies as baselines.
"""

from src.router.base_router import BaseRouter, RoutingDecision


class FixedTierRouter(BaseRouter):
    """
    Always routes to the same tier for all agents.
    Equivalent to the baseline experiments.
    """

    def __init__(self, tier: int):
        assert tier in (1, 2, 3, 4), f"Invalid tier: {tier}"
        self._tier = tier

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
        return RoutingDecision(
            tier=self._tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=f"Fixed: always tier {self._tier}",
            confidence=1.0,
        )

    @property
    def name(self) -> str:
        return f"fixed_t{self._tier}"


class FixedMixedTierRouter(BaseRouter):
    """
    Static per-role tier assignment.
    Default: Analyzer→T2, Solver→T4, Verifier→T1
    
    Rationale:
    - Analyzer (decomposition): Needs some reasoning but not precision → T2
    - Solver (answer generation): Needs strong QA capability → T4
    - Verifier (checking): Simpler verification → T1
    """

    def __init__(
        self,
        analyzer_tier: int = 2,
        solver_tier: int = 4,
        verifier_tier: int = 1,
    ):
        self._role_tiers = {
            "analyzer": analyzer_tier,
            "solver": solver_tier,
            "verifier": verifier_tier,
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
        tier = self._role_tiers.get(agent_role, 2)

        return RoutingDecision(
            tier=tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=f"FixedMixed: {agent_role} → T{tier}",
            confidence=1.0,
        )

    @property
    def name(self) -> str:
        tiers = [f"{r[0].upper()}{t}" for r, t in self._role_tiers.items()]
        return f"fixed_mixed_{'_'.join(tiers)}"
