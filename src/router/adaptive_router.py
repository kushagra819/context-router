"""
Adaptive Mixed-Tier Router
============================
Combines complexity-based routing with confidence cascading
and per-agent role awareness. This is the full innovation.

Unlike CascadeRouter (which has fixed defaults and escalation targets),
AdaptiveRouter dynamically adjusts based on:
1. Question complexity → sets initial tier range
2. Agent role → adjusts within the range
3. Upstream confidence → escalates or de-escalates
4. Cost budget → constrains final selection
"""

from src.router.base_router import BaseRouter, RoutingDecision
from src.router.signals import (
    extract_question_features,
    extract_confidence,
    extract_context_complexity,
)


class AdaptiveRouter(BaseRouter):
    """
    Full adaptive mixed-tier router combining all signals.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        complexity_thresholds: tuple[float, float, float] = (0.2, 0.4, 0.7),
        default_tier: int = 2,
        use_complexity: bool = True,
        use_role: bool = True,
        use_confidence: bool = True,
        use_budget: bool = True,
    ):
        """The full context-aware router.

        The ``use_*`` flags toggle individual signal families and exist for the
        ablation study (see docs/ROUTER_FINAL_SPEC.md §6). With a flag off, that
        signal is ignored: e.g. use_complexity=False fixes the base tier to
        ``default_tier`` so only role/confidence/budget remain.
        """
        self._confidence_threshold = confidence_threshold
        self._complexity_thresholds = complexity_thresholds
        self._default_tier = default_tier
        self._use_complexity = use_complexity
        self._use_role = use_role
        self._use_confidence = use_confidence
        self._use_budget = use_budget

    def _base_tier_from_complexity(self, complexity: float) -> int:
        """Map complexity score to a base tier."""
        if complexity < self._complexity_thresholds[0]:
            return 1
        elif complexity < self._complexity_thresholds[1]:
            return 2
        elif complexity < self._complexity_thresholds[2]:
            return 3
        else:
            return 4

    def _role_adjustment(self, base_tier: int, agent_role: str) -> int:
        """
        Adjust tier based on agent role.
        - Verifier: can go 1 tier lower (verification is simpler)
        - Solver: stays at base or goes 1 higher (solving needs strength)
        - Analyzer: stays at base (decomposition is moderate)
        """
        if agent_role == "verifier":
            return max(1, base_tier - 1)
        elif agent_role == "solver":
            return min(4, base_tier + 1) if base_tier < 4 else 4
        else:  # analyzer
            return base_tier

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
        # Step 1: Complexity -> base tier (ablatable).
        features = extract_question_features(question)
        if self._use_complexity:
            ctx_complexity = extract_context_complexity(context)
            combined_complexity = features["complexity_score"] * 0.6 + ctx_complexity * 0.4
            base_tier = self._base_tier_from_complexity(combined_complexity)
            cstr = f"complexity={combined_complexity:.2f} → base_T{base_tier}"
        else:
            base_tier = self._default_tier
            cstr = f"complexity OFF → base_T{base_tier}"

        # Step 2: Role adjustment (ablatable).
        role_tier = self._role_adjustment(base_tier, agent_role) if self._use_role else base_tier

        # Step 3: Confidence cascading for solver/verifier (ablatable). Track escalation.
        final_tier = role_tier
        escalated_from = None
        cascade_reason = ""
        if self._use_confidence and upstream_output is not None and agent_role in ("solver", "verifier"):
            if upstream_confidence is None:
                upstream_confidence = extract_confidence(upstream_output)
            if upstream_confidence < self._confidence_threshold and role_tier < 4:
                escalated_from = role_tier
                final_tier = min(4, role_tier + 1)
                cascade_reason = f" → escalated (conf={upstream_confidence:.2f})"
            elif upstream_confidence > 0.8 and role_tier > 1:
                final_tier = max(1, role_tier - 1)
                cascade_reason = f" → de-escalated (conf={upstream_confidence:.2f})"

        # Step 4: Budget constraint (ablatable).
        if self._use_budget and cost_budget < float("inf"):
            if (cost_budget - cost_spent) < 0.001 and final_tier > 1:
                final_tier = 1
                escalated_from = None
                cascade_reason += " [budget-capped to T1]"

        reason = f"{cstr}, role={agent_role} → T{role_tier}{cascade_reason}"
        return RoutingDecision(
            tier=final_tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=reason,
            confidence=0.7,
            base_tier=role_tier,
            escalated_from=escalated_from,
        )

    @property
    def name(self) -> str:
        return "adaptive"
