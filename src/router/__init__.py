"""
Router package
==============
Context-aware, per-agent model-tier routers for multi-agent pipelines.

Public API:
    get_router(name, **kwargs) -> BaseRouter
    ROUTER_REGISTRY            -> {name: factory}

Router families
---------------
Reference (no learning, used as anchors):
    oracle        cheapest tier that was correct in the baselines (upper bound)
    random        uniform random tier (lower bound)
    fixed_t1..t4  single tier for all agents (== the baselines)
    fixed_mixed   static per-role tier map (analyzer/solver/verifier)

Proposed (context-aware):
    complexity    tier from question/context complexity, per-role thresholds
    cascade       confidence-based escalation across the pipeline
    adaptive      complexity + role + confidence + budget (full method)
    learned       small classifier trained on baseline "oracle" labels
"""

from src.router.base_router import BaseRouter, RoutingDecision
from src.router.oracle_router import OracleRouter
from src.router.random_router import RandomRouter
from src.router.fixed_tier_router import FixedTierRouter, FixedMixedTierRouter
from src.router.complexity_router import ComplexityRouter
from src.router.cascade_router import CascadeRouter
from src.router.adaptive_router import AdaptiveRouter
from src.router.query_level_router import QueryLevelRouter

__all__ = [
    "BaseRouter",
    "RoutingDecision",
    "OracleRouter",
    "RandomRouter",
    "FixedTierRouter",
    "FixedMixedTierRouter",
    "ComplexityRouter",
    "CascadeRouter",
    "AdaptiveRouter",
    "QueryLevelRouter",
    "get_router",
    "ROUTER_REGISTRY",
    "list_routers",
]


def _learned(**kwargs):
    # Imported lazily so the package works without scikit-learn / a trained model.
    from src.router.learned_router import LearnedRouter
    return LearnedRouter(**kwargs)


ROUTER_REGISTRY = {
    # reference / baselines
    "oracle": lambda **kw: OracleRouter(**kw),
    "random": lambda **kw: RandomRouter(**kw),
    "fixed_t1": lambda **kw: FixedTierRouter(1),
    "fixed_t2": lambda **kw: FixedTierRouter(2),
    "fixed_t3": lambda **kw: FixedTierRouter(3),
    "fixed_t4": lambda **kw: FixedTierRouter(4),
    "fixed_mixed": lambda **kw: FixedMixedTierRouter(**kw),
    # per-QUERY baseline (RouteLLM/FrugalGPT-style: one tier for the whole pipeline)
    "query_level": lambda **kw: QueryLevelRouter(**kw),
    # proposed (per-AGENT, context-aware)
    "complexity": lambda **kw: ComplexityRouter(**kw),
    "cascade": lambda **kw: CascadeRouter(**kw),
    "adaptive": lambda **kw: AdaptiveRouter(**kw),
    "learned": _learned,
    # ablations of the full method (one signal family removed each) — see
    # docs/ROUTER_FINAL_SPEC.md §6. Used by the ablation study / WCG metric.
    "adaptive_no_complexity": lambda **kw: AdaptiveRouter(use_complexity=False, **kw),
    "adaptive_no_role": lambda **kw: AdaptiveRouter(use_role=False, **kw),
    "adaptive_no_confidence": lambda **kw: AdaptiveRouter(use_confidence=False, **kw),
    "adaptive_no_budget": lambda **kw: AdaptiveRouter(use_budget=False, **kw),
}


def get_router(name: str, **kwargs) -> BaseRouter:
    """Instantiate a router by name. See ROUTER_REGISTRY for valid names."""
    key = name.lower()
    if key not in ROUTER_REGISTRY:
        raise ValueError(
            f"Unknown router '{name}'. Choices: {sorted(ROUTER_REGISTRY)}"
        )
    return ROUTER_REGISTRY[key](**kwargs)


def list_routers() -> list[str]:
    return sorted(ROUTER_REGISTRY)
