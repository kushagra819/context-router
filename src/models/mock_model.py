"""
MockModel
=========
A deterministic, offline stand-in for a real tier model. It makes NO network
calls, so it lets the full baseline/routing pipeline be smoke-tested on any
machine (e.g. an office laptop without API keys or a local Ollama install).

Behaviour:
  * Returns a deterministic response derived from a hash of the prompt, always
    ending in a parseable "Final Answer: <token>" line.
  * Reports plausible token counts (word-count based) and computes a cost using
    the same per-tier published pricing as the real models, so cost/latency
    aggregation can be exercised end-to-end.
  * Higher tiers are made deterministically "more correct" when a ground-truth
    hint is embedded in the prompt, which is only used by the smoke tests; on
    real prompts it just returns a stable pseudo-answer.

This is a TEST/DEV utility. It is never used for reported results.
"""

import hashlib

from src.models.base import BaseModel, ModelResponse
from src.utils.config import MODEL_CONFIG


class MockModel(BaseModel):
    """Deterministic offline model for a given tier."""

    def __init__(self, tier: int, simulate_latency: bool = False):
        if tier not in MODEL_CONFIG:
            raise ValueError(f"Invalid tier: {tier}")
        self._tier = tier
        self._cfg = MODEL_CONFIG[tier]
        self._simulate_latency = simulate_latency

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        digest = hashlib.sha256((system + "||" + prompt).encode("utf-8")).hexdigest()
        pseudo_answer = digest[:6]
        text = (
            f"[MOCK tier{self._tier}] Reasoning about the task deterministically. "
            f"Step 1 ... Step 2 ... Step 3.\n"
            f"Final Answer: {pseudo_answer}"
        )
        input_tokens = max(1, len((system + " " + prompt).split()))
        output_tokens = max(1, len(text.split()))
        latency = round(0.001 * input_tokens, 4) if self._simulate_latency else 0.0
        # Deterministic pseudo-logprob: higher tiers are "more confident" (closer to
        # 0). Lets the offline tests exercise the calibrated-confidence path.
        mean_logprob = -0.6 + 0.12 * self._tier - 0.0005 * (int(digest[6:8], 16))
        return ModelResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency=latency,
            tier=self._tier,
            model_name=self.model_name,
            cost_usd=self.calculate_cost(input_tokens, output_tokens),
            mean_logprob=round(mean_logprob, 4),
        )

    @property
    def tier(self) -> int:
        return self._tier

    @property
    def model_name(self) -> str:
        return f"Mock/{self._cfg['name']}"

    @property
    def cost_per_1m_input(self) -> float:
        return self._cfg["cost_per_1m_input"]

    @property
    def cost_per_1m_output(self) -> float:
        return self._cfg["cost_per_1m_output"]
