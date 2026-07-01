"""
Oracle Router
=============
Upper bound on cost savings. Uses the precomputed baselines to pick, for each
problem, the cheapest tier that answered it correctly (across all agents).

This router cannot be used in production -- it requires knowing the correct
answer in advance. It exists purely as a theoretical benchmark (the routing
ceiling). The "cheapest correct tier" logic is the SINGLE canonical definition in
src/router/training_data.py, so the oracle router, the learned-router labels, and
the metrics layer never drift apart. Problems no tier solves are routed to T1
(spending more cannot help) -- the same "unsolvable" convention the labels use.

The metric (EM vs F1) and whether to restrict to the 4-tier problem-id
intersection are configurable; defaults reproduce the historical EM behaviour.
"""

from pathlib import Path

from src.router.base_router import BaseRouter, RoutingDecision
from src.router.training_data import tier_correctness, cheapest_correct_tier, DEFAULT_F1_THRESHOLD
from src.utils.config import RESULTS_DIR

TIERS = (1, 2, 3, 4)


class OracleRouter(BaseRouter):
    """For each problem, route every agent to the cheapest tier that was correct."""

    def __init__(self, baselines_dir: Path | None = None, metric: str = "em",
                 f1_threshold: float = DEFAULT_F1_THRESHOLD, restrict_intersection: bool = False):
        self._baselines_dir = baselines_dir or (RESULTS_DIR / "baselines")
        self._metric = metric
        self._f1_threshold = f1_threshold
        self._restrict_intersection = restrict_intersection
        self._lookup: dict[str, dict[int, int]] = {}   # dataset -> {pid -> best_tier}
        self._loaded: set[str] = set()

    def _load_dataset(self, dataset: str):
        if dataset in self._loaded:
            return
        correct, eligible, _ = tier_correctness(
            dataset, self._metric, self._f1_threshold, self._baselines_dir,
            self._restrict_intersection)
        lookup: dict[int, int] = {}
        for pid in eligible:
            tier = cheapest_correct_tier(correct, pid)
            lookup[pid] = tier if tier is not None else 1  # unsolvable -> cheapest
        self._lookup[dataset] = lookup
        self._loaded.add(dataset)

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
        self._load_dataset(dataset)
        if problem_id is not None and dataset in self._lookup:
            tier = self._lookup[dataset].get(problem_id, 4)
        else:
            tier = 4  # fallback to strongest when no oracle info exists
        return RoutingDecision(
            tier=tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=f"Oracle: cheapest correct tier for {dataset} #{problem_id}",
            confidence=1.0,
            base_tier=tier,
        )

    @property
    def name(self) -> str:
        return "oracle"
