"""
Dataset Adapters
================
A single, uniform interface over the three benchmarks (GSM8K, HotpotQA, MuSiQue)
so that ONE pipeline can run baselines and routed experiments for all of them.

Each adapter knows how to:
  * load N problems into a uniform record: {id, question, context, ground_truth}
  * format the raw context into a prompt string
  * build the (system, user) prompt for each agent role (analyzer/solver/verifier)
  * extract the predicted answer, check correctness (EM), and compute F1

Prompt templates and metric functions are imported from the existing
src/agents/* and src/evaluation/metrics.py modules so the unified pipeline is
byte-for-byte consistent with the original per-dataset baseline runners.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.agents import gsm8k_agents as G
from src.agents import hotpotqa_agents as H
from src.agents import musique_agents as M
from src.agents.hotpotqa_agents import format_hotpotqa_context
from src.agents.musique_agents import format_musique_context
from src.evaluation.metrics import (
    extract_gsm8k_answer,
    extract_gsm8k_ground_truth,
    gsm8k_check_correct,
    extract_hotpotqa_answer,
    hotpotqa_check_correct,
    hotpotqa_compute_f1,
)

ROLES = ("analyzer", "solver", "verifier")


@dataclass
class Problem:
    id: int
    question: str
    context: object          # raw context (dict / list / None)
    ground_truth: str | None
    formatted_context: str = ""


class DatasetAdapter:
    """Base adapter. Subclasses fill in the dataset-specific behaviour."""

    name: str = ""
    hf_id: str = ""
    hf_config: str | None = None
    hf_split: str = "validation"
    uses_f1: bool = True

    # -- loading -----------------------------------------------------------
    def load(self, num_problems: int) -> list[Problem]:
        from datasets import load_dataset  # lazy: only needed for real runs

        ds = load_dataset(self.hf_id, self.hf_config, split=self.hf_split)
        problems: list[Problem] = []
        for i, item in enumerate(list(ds)[:num_problems]):
            problems.append(self._to_problem(i, item))
        return problems

    def _to_problem(self, idx: int, item: dict) -> Problem:  # pragma: no cover - overridden
        raise NotImplementedError

    # -- prompting ---------------------------------------------------------
    def format_context(self, context) -> str:
        return ""

    def build_prompt(self, role: str, problem: Problem, upstream_text: str | None) -> tuple[str, str]:
        raise NotImplementedError

    # -- scoring -----------------------------------------------------------
    def extract_answer(self, text: str):
        raise NotImplementedError

    def check_correct(self, predicted, ground_truth) -> bool:
        raise NotImplementedError

    def compute_f1(self, predicted, ground_truth) -> float:
        return 0.0


class GSM8KAdapter(DatasetAdapter):
    name = "gsm8k"
    hf_id = "openai/gsm8k"
    hf_config = "main"
    hf_split = "test"
    uses_f1 = False

    def _to_problem(self, idx, item):
        return Problem(
            id=idx,
            question=item["question"],
            context=None,
            ground_truth=extract_gsm8k_ground_truth(item["answer"]),
        )

    def format_context(self, context):
        return ""

    def build_prompt(self, role, problem, upstream_text):
        if role == "analyzer":
            return G.ANALYZER_SYSTEM, G.ANALYZER_USER.format(problem=problem.question)
        if role == "solver":
            return G.SOLVER_SYSTEM, G.SOLVER_USER.format(problem=problem.question, analysis=upstream_text or "")
        if role == "verifier":
            return G.VERIFIER_SYSTEM, G.VERIFIER_USER.format(problem=problem.question, solution=upstream_text or "")
        raise ValueError(role)

    def extract_answer(self, text):
        return extract_gsm8k_answer(text)

    def check_correct(self, predicted, ground_truth):
        return gsm8k_check_correct(predicted, ground_truth)

    def compute_f1(self, predicted, ground_truth):
        # GSM8K is exact numeric match; F1 collapses to EM.
        return 1.0 if self.check_correct(predicted, ground_truth) else 0.0


class HotpotQAAdapter(DatasetAdapter):
    name = "hotpotqa"
    hf_id = "hotpotqa/hotpot_qa"
    hf_config = "distractor"
    hf_split = "validation"
    uses_f1 = True

    def _to_problem(self, idx, item):
        return Problem(
            id=idx,
            question=item["question"],
            context=item["context"],
            ground_truth=item["answer"],
        )

    def format_context(self, context):
        return format_hotpotqa_context(context)

    def build_prompt(self, role, problem, upstream_text):
        ctx = problem.formatted_context
        if role == "analyzer":
            return H.ANALYZER_SYSTEM, H.ANALYZER_USER.format(question=problem.question, formatted_context=ctx)
        if role == "solver":
            return H.SOLVER_SYSTEM, H.SOLVER_USER.format(
                question=problem.question, formatted_context=ctx, analysis=upstream_text or "")
        if role == "verifier":
            return H.VERIFIER_SYSTEM, H.VERIFIER_USER.format(
                question=problem.question, formatted_context=ctx, solution=upstream_text or "")
        raise ValueError(role)

    def extract_answer(self, text):
        return extract_hotpotqa_answer(text)

    def check_correct(self, predicted, ground_truth):
        return hotpotqa_check_correct(predicted, ground_truth)

    def compute_f1(self, predicted, ground_truth):
        return hotpotqa_compute_f1(predicted, ground_truth)


class MuSiQueAdapter(DatasetAdapter):
    name = "musique"
    hf_id = "bdsaglam/musique"
    hf_config = "answerable"
    hf_split = "validation"
    uses_f1 = True

    def _to_problem(self, idx, item):
        return Problem(
            id=idx,
            question=item["question"],
            context=item["paragraphs"],
            ground_truth=item["answer"],
        )

    def format_context(self, context):
        return format_musique_context(context)

    def build_prompt(self, role, problem, upstream_text):
        ctx = problem.formatted_context
        if role == "analyzer":
            return M.ANALYZER_SYSTEM, M.ANALYZER_USER.format(question=problem.question, formatted_context=ctx)
        if role == "solver":
            return M.SOLVER_SYSTEM, M.SOLVER_USER.format(
                question=problem.question, formatted_context=ctx, analysis=upstream_text or "")
        if role == "verifier":
            return M.VERIFIER_SYSTEM, M.VERIFIER_USER.format(
                question=problem.question, formatted_context=ctx, solution=upstream_text or "")
        raise ValueError(role)

    def extract_answer(self, text):
        # MuSiQue reuses the HotpotQA short-answer extractor + scorer (documented).
        return extract_hotpotqa_answer(text)

    def check_correct(self, predicted, ground_truth):
        return hotpotqa_check_correct(predicted, ground_truth)

    def compute_f1(self, predicted, ground_truth):
        return hotpotqa_compute_f1(predicted, ground_truth)


_ADAPTERS = {
    "gsm8k": GSM8KAdapter,
    "hotpotqa": HotpotQAAdapter,
    "musique": MuSiQueAdapter,
}


def get_adapter(name: str) -> DatasetAdapter:
    name = name.lower()
    if name not in _ADAPTERS:
        raise ValueError(f"Unknown dataset '{name}'. Choices: {sorted(_ADAPTERS)}")
    return _ADAPTERS[name]()


def available_datasets() -> list[str]:
    return sorted(_ADAPTERS)
