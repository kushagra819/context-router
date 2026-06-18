"""Tier 4: GPT-4.1 via GitHub Models API (free with any GitHub account)."""

import os
import time
import itertools
from openai import OpenAI
from src.models.base import BaseMultiKeyModel, ModelResponse
from src.utils.config import GITHUB_TOKENS


class GPT5Model(BaseMultiKeyModel):
    """
    Tier 4 — Proprietary frontier model.
    Runs OpenAI GPT-4.1 via GitHub Models API (OpenAI-compatible endpoint).
    Free with any GitHub account.

    Supports up to 15 GitHub PAT tokens for rotation.
    Auto-detects and skips exhausted tokens (UserByModelByDay limits).
    Published pricing (OpenAI): $2.00/1M input, $8.00/1M output.
    """

    def __init__(
        self,
        model_id: str = "openai/gpt-4.1",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        tokens: list[str] | None = None,
        min_delay: float | None = None,
    ):
        self._model_id = model_id
        self._temperature = temperature
        self._max_tokens = max_tokens

        keys = list(tokens or GITHUB_TOKENS)
        num_tokens = len(keys)
        delay = min_delay if min_delay is not None else max(8.0, 60.0 / (num_tokens * 10))

        print(f"    GPT-4.1 (GitHub): {num_tokens} token(s), {delay:.1f}s delay between calls")

        super().__init__("GPT-4.1 (GitHub)", keys, delay)
        self._init_client()

    def _init_client(self):
        self._client = OpenAI(
            base_url="https://models.github.ai/inference",
            api_key=self._current_key,
            timeout=15.0,
        )

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        live_keys = self._get_live_keys()
        max_attempts = len(live_keys) + 2 if live_keys else 1
        start = time.perf_counter()

        for attempt in range(max_attempts):
            if self._current_key in self._dead_keys:
                try:
                    self._rotate_key()
                except RuntimeError as re:
                    raise re
                except Exception as ex:
                    print(f"    ❌ {ex}")
                    break

            try:
                self._throttle()
                response = self._client.chat.completions.create(
                    model=self._model_id,
                    messages=messages,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )
                latency = time.perf_counter() - start

                text = response.choices[0].message.content or ""
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0

                self._call_count += 1
                if self._call_count % 3 == 0 and len(self._get_live_keys()) > 1:
                    self._rotate_key()

                return ModelResponse(
                    text=text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency=latency,
                    tier=self.tier,
                    model_name=self.model_name,
                    cost_usd=self.calculate_cost(input_tokens, output_tokens),
                )

            except Exception as e:
                self._log_error(e)
                error_msg = str(e)
                classification = self._classify_error(error_msg)
                print(f"    Classified error as: {classification}")

                if classification == "PERMANENT_EXHAUSTION":
                    try:
                        self._mark_key_dead(self._current_key, reason=self._extract_reason_summary(error_msg))
                    except RuntimeError as re:
                        raise re
                    except Exception as ex:
                        print(f"    ❌ {ex}")
                        break
                    continue
                else:
                    try:
                        self._rotate_key()
                    except RuntimeError as re:
                        raise re
                    except Exception as ex:
                        print(f"    ❌ {ex}")
                        break
                    backoff = min(5, 2 * (attempt + 1))
                    print(f"    ⏳ GPT-4.1 rate limited (transient), rotated token, waiting {backoff}s...")
                    time.sleep(backoff)
                    continue

        latency = time.perf_counter() - start
        return ModelResponse(
            text=f"[ERROR] GPT-4.1 call failed: All keys exhausted or server error",
            input_tokens=len(prompt.split()) * 2,
            output_tokens=0,
            latency=latency,
            tier=self.tier,
            model_name=self.model_name,
            cost_usd=0.0,
        )

    @property
    def tier(self) -> int:
        return 4

    @property
    def model_name(self) -> str:
        return f"GitHub/{self._model_id}"

    @property
    def cost_per_1m_input(self) -> float:
        return 2.00

    @property
    def cost_per_1m_output(self) -> float:
        return 8.00

