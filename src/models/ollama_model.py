"""Tier 1: Local Gemma 4 E4B via Ollama."""

import time
import ollama as ollama_client
from src.models.base import BaseModel, ModelResponse


class OllamaModel(BaseModel):
    """
    Tier 1 — Local small model.
    Runs Gemma 4 E4B (4B params, Q4 quantized, ~2.5GB VRAM) on your RTX 4050.
    Cost: $0 actual, $0.03/1M equivalent for paper calculations.
    """

    def __init__(self, model_id: str = "gemma4:e4b", temperature: float = 0.1, max_tokens: int = 2048):
        self._model_id = model_id
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.perf_counter()
        try:
            response = ollama_client.chat(
                model=self._model_id,
                messages=messages,
                options={
                    "temperature": self._temperature,
                    "num_predict": self._max_tokens,
                },
            )
            latency = time.perf_counter() - start

            text = response["message"]["content"]
            # Ollama provides token counts in eval_count and prompt_eval_count
            input_tokens = response.get("prompt_eval_count", 0)
            output_tokens = response.get("eval_count", 0)

            # Fallback: estimate tokens if not provided
            if input_tokens == 0:
                input_tokens = len(prompt.split()) * 2  # rough estimate
            if output_tokens == 0:
                output_tokens = len(text.split()) * 2

        except Exception as e:
            latency = time.perf_counter() - start
            text = f"[ERROR] Ollama call failed: {str(e)}"
            input_tokens = len(prompt.split()) * 2
            output_tokens = 0

        return ModelResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency=latency,
            tier=self.tier,
            model_name=self.model_name,
            cost_usd=self.calculate_cost(input_tokens, output_tokens),
        )

    @property
    def tier(self) -> int:
        return 1

    @property
    def model_name(self) -> str:
        return f"Ollama/{self._model_id}"

    @property
    def cost_per_1m_input(self) -> float:
        return 0.03  # Equivalent cloud pricing

    @property
    def cost_per_1m_output(self) -> float:
        return 0.06
