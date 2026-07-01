from google import genai
from google.genai import types
from src.models.base import BaseMultiKeyModel, ModelResponse
from src.utils.config import GOOGLE_API_KEYS
import time


class GeminiModel(BaseMultiKeyModel):
    """
    Tier 3 — Cloud frontier model.
    Runs Gemini 3.5 Flash via Google AI Studio free tier.
    
    Built-in rate limiter with key rotation and exhaustion tracking.
    """

    def __init__(
        self,
        model_id: str = "gemini-3.5-flash",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        api_keys: list[str] | None = None,
        min_delay: float | None = None,
    ):
        self._model_id = model_id
        self._temperature = temperature
        self._max_tokens = max_tokens
        
        keys = list(api_keys or GOOGLE_API_KEYS)
        num_keys = len(keys)
        delay = min_delay if min_delay is not None else max(1.0, 60.0 / (num_keys * 12))
        
        print(f"    Gemini: {num_keys} token(s), {delay:.1f}s delay between calls")
        
        super().__init__("Gemini", keys, delay)
        self._init_client()

    def _init_client(self):
        self._client = genai.Client(api_key=self._current_key)

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        contents = prompt
        config = types.GenerateContentConfig(
            temperature=self._temperature,
            max_output_tokens=self._max_tokens,
        )
        if system:
            config.system_instruction = system

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
                response = self._client.models.generate_content(
                    model=self._model_id,
                    contents=contents,
                    config=config,
                )
                latency = time.perf_counter() - start

                text = response.text if response.text else ""
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    output_tokens = getattr(usage, "candidates_token_count", 0) or 0
                else:
                    input_tokens = len(prompt.split()) * 2
                    output_tokens = len(text.split()) * 2

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
                    print(f"    ⏳ Gemini rate limited (transient), rotated key, waiting {backoff}s...")
                    time.sleep(backoff)
                    continue

        latency = time.perf_counter() - start
        return ModelResponse(
            text=f"[ERROR] Gemini call failed: All keys exhausted or server error",
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
        return f"Google/{self._model_id}"

    @property
    def cost_per_1m_input(self) -> float:
        return 1.25

    @property
    def cost_per_1m_output(self) -> float:
        return 5.00

