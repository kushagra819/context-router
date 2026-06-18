from src.models.base import BaseMultiKeyModel, ModelResponse
from src.utils.config import SAMBANOVA_API_KEYS
from openai import OpenAI
import time


class SambaNovaModel(BaseMultiKeyModel):
    """
    Tier 3 — Cloud frontier model.
    Runs DeepSeek-V3.1 via SambaNova Cloud API (OpenAI-compatible endpoint).
    Free tier model: DeepSeek-V3.1

    Supports API key rotation across multiple SambaNova accounts.
    Published pricing (DeepSeek): $2.19/1M input, $2.19/1M output.
    """

    def __init__(
        self,
        model_id: str = "DeepSeek-V3.1",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        tokens: list[str] | None = None,
        min_delay: float | None = None,
    ):
        self._model_id = model_id
        self._temperature = temperature
        self._max_tokens = max_tokens
        
        keys = list(tokens or SAMBANOVA_API_KEYS)
        num_tokens = len(keys)
        delay = min_delay if min_delay is not None else max(1.0, 60.0 / (num_tokens * 8))
        
        print(f"    SambaNova: {num_tokens} token(s), {delay:.1f}s delay between calls")
        
        super().__init__("SambaNova", keys, delay)
        self._init_client()

    def _init_client(self):
        self._client = OpenAI(
            base_url="https://api.sambanova.ai/v1",
            api_key=self._current_key,
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
                if self._call_count % 2 == 0 and len(self._get_live_keys()) > 1:
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
                    print(f"    ⏳ SambaNova rate limited (transient), rotated key, waiting {backoff}s...")
                    time.sleep(backoff)
                    continue

        latency = time.perf_counter() - start
        return ModelResponse(
            text=f"[ERROR] SambaNova call failed: All keys exhausted or server error",
            input_tokens=len(prompt.split()) * 2,
            output_tokens=0,
            latency=latency,
            tier=self.tier,
            model_name=self.model_name,
            cost_usd=0.0,
        )

    @property
    def tier(self) -> int:
        return 3

    @property
    def model_name(self) -> str:
        return f"SambaNova/{self._model_id}"

    @property
    def cost_per_1m_input(self) -> float:
        return 2.19

    @property
    def cost_per_1m_output(self) -> float:
        return 2.19

