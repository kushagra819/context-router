"""
Base Router Interface
=====================
All router variants must implement this ABC.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    tier: int                    # Selected model tier (1-4)
    router_name: str             # Name of the router that made this decision
    agent_role: str              # Which agent this is for
    reason: str = ""             # Human-readable explanation
    confidence: float = 0.0      # Router's confidence in this decision [0,1]
    base_tier: int | None = None # Tier the router would pick WITHOUT cascading/escalation
    escalated_from: int | None = None  # If escalated, the tier escalated up from (else None)

    @property
    def escalated(self) -> bool:
        return self.escalated_from is not None and self.tier > self.escalated_from


class BaseRouter(ABC):
    """
    Abstract base class for all routing strategies.
    
    The router receives context about the current agent invocation
    and returns a tier selection (1-4).
    """

    @abstractmethod
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
        """
        Select a model tier for the given agent invocation.

        Args:
            question: The original question text.
            agent_role: "analyzer", "solver", or "verifier".
            context: Dataset-specific context (paragraphs, etc.).
            upstream_output: The previous agent's response text (None for analyzer).
            upstream_confidence: Parsed confidence from upstream response [0,1].
            cost_spent: Total cost already spent on this problem.
            cost_budget: Maximum budget for this problem.
            problem_id: Problem index (useful for oracle/deterministic routers).
            dataset: Dataset name ("gsm8k", "hotpotqa", "musique").

        Returns:
            RoutingDecision with the selected tier and metadata.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable router name for logging."""
        ...

    def reset(self):
        """Optional: reset any per-problem state between problems."""
        pass
