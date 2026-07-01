"""
RoutedPipeline
==============
The single multi-agent pipeline used for BOTH baselines and routed experiments.

For each problem it runs Analyzer -> Solver -> Verifier. Before every agent call
it asks the router which tier to use, fetches that tier's model from the registry,
runs the agent, extracts a confidence signal from the output, and threads the
output + confidence + running cost into the next routing decision.

A "baseline" is simply this pipeline driven by a FixedTierRouter(tier), so the
ONLY thing that differs between a baseline and a routed run is the routing policy
-- which is exactly the comparison the research makes.

The pipeline is model-agnostic: pass a registry built with mock=True to exercise
the whole flow offline with no API calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.base import ModelResponse
from src.models.registry import ModelRegistry
from src.pipeline.dataset_adapters import DatasetAdapter, Problem, ROLES
from src.router.base_router import BaseRouter, RoutingDecision
from src.router.signals import extract_confidence, confidence_from_logprob


@dataclass
class AgentCall:
    role: str
    tier: int
    decision: RoutingDecision
    response: ModelResponse
    confidence: float
    confidence_source: str = "lexical"   # "logprob" (calibrated) or "lexical" (fallback)


@dataclass
class PipelineResult:
    problem_id: int
    dataset: str
    router_name: str
    predicted: object
    ground_truth: object
    correct: bool
    f1: float
    calls: list[AgentCall] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(c.response.cost_usd for c in self.calls)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.response.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.response.output_tokens for c in self.calls)

    @property
    def total_latency(self) -> float:
        return sum(c.response.latency for c in self.calls)

    @property
    def tier_path(self) -> list[int]:
        return [c.tier for c in self.calls]


class RoutedPipeline:
    def __init__(
        self,
        adapter: DatasetAdapter,
        registry: ModelRegistry,
        cost_budget: float = float("inf"),
    ):
        self.adapter = adapter
        self.registry = registry
        self.cost_budget = cost_budget

    def run_problem(self, problem: Problem, router: BaseRouter) -> PipelineResult:
        router.reset()
        problem.formatted_context = self.adapter.format_context(problem.context)
        # The router receives the formatted context as a string so that
        # context-complexity signals work uniformly across datasets.
        router_context = problem.formatted_context or None

        upstream_text: str | None = None
        upstream_conf: float | None = None
        cost_spent = 0.0
        calls: list[AgentCall] = []

        for role in ROLES:
            decision = router.select_tier(
                question=problem.question,
                agent_role=role,
                context=router_context,
                upstream_output=upstream_text,
                upstream_confidence=upstream_conf,
                cost_spent=cost_spent,
                cost_budget=self.cost_budget,
                problem_id=problem.id,
                dataset=self.adapter.name,
            )
            model = self.registry.get(decision.tier)
            system, user = self.adapter.build_prompt(role, problem, upstream_text)
            response = model.generate(user, system)
            # Prefer the CALIBRATED logprob confidence; fall back to the lexical
            # heuristic only when the provider returned no logprobs.
            lp_conf = confidence_from_logprob(response.mean_logprob)
            if lp_conf is not None:
                confidence, conf_source = lp_conf, "logprob"
            else:
                confidence, conf_source = extract_confidence(response.text), "lexical"

            calls.append(AgentCall(role, decision.tier, decision, response, confidence, conf_source))

            cost_spent += response.cost_usd
            upstream_text = response.text
            upstream_conf = confidence

        final_output = calls[-1].response.text
        predicted = self.adapter.extract_answer(final_output)
        correct = self.adapter.check_correct(predicted, problem.ground_truth)
        f1 = self.adapter.compute_f1(predicted, problem.ground_truth)

        return PipelineResult(
            problem_id=problem.id,
            dataset=self.adapter.name,
            router_name=router.name,
            predicted=predicted,
            ground_truth=problem.ground_truth,
            correct=correct,
            f1=f1,
            calls=calls,
        )
