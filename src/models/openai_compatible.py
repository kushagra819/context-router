"""
OpenAICompatibleModel
=====================
A single, configurable wrapper for every OpenAI-compatible provider (GitHub
Models, NVIDIA NIM, OpenRouter, SambaNova, a direct OpenAI key, ...). It folds the
five previously near-identical `generate()` implementations (GitHubModel /
GPT41Model / OpenRouterModel / SambaNovaModel) into ONE faithful copy of the
key-rotation + error-classification + backoff loop, on top of BaseMultiKeyModel.

Adding a provider is now a ~10-line config subclass (see github_model.py,
nim_model.py, ...). The rotation/throttle/retry semantics are byte-for-byte the
same as the original per-provider wrappers, so live-run behaviour is unchanged.
"""

from __future__ import annotations

import time

from src.models.base import BaseMultiKeyModel, ModelResponse


class OpenAICompatibleModel(BaseMultiKeyModel):
    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        model_id: str,
        tier: int,
        price_in: float,
        price_out: float,
        keys: list[str],
        min_delay: float,
        default_headers: dict | None = None,
        timeout: float = 30.0,
        rotate_every: int = 3,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        model_name_prefix: str | None = None,
        request_logprobs: bool = True,
    ):
        self._base_url = base_url
        self._model_id = model_id
        self._tier = tier
        self._price_in = price_in
        self._price_out = price_out
        self._default_headers = default_headers or {}
        self._timeout = timeout
        self._rotate_every = rotate_every
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._name_prefix = model_name_prefix or provider_name
        # Request token logprobs so the pipeline can use a CALIBRATED confidence
        # (exp(mean logprob)) instead of the lexical heuristic. Auto-disables if the
        # provider rejects the param (see generate()).
        self._request_logprobs = request_logprobs
        super().__init__(provider_name, keys, min_delay)
        self._init_client()

    @staticmethod
    def _mean_logprob(choice) -> float | None:
        """Mean per-token logprob from an OpenAI-compatible choice, or None."""
        try:
            content = choice.logprobs.content  # list of per-token objects with .logprob
            lps = [t.logprob for t in content if getattr(t, "logprob", None) is not None]
            return sum(lps) / len(lps) if lps else None
        except Exception:
            return None

    def _init_client(self):
        from openai import OpenAI  # lazy: importing this module never needs the SDK
        self._client = OpenAI(
            base_url=self._base_url,
            api_key=self._current_key,
            timeout=self._timeout,
            default_headers=self._default_headers,
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
                except RuntimeError:
                    raise
                except Exception as ex:
                    print(f"    [x] {ex}")
                    break

            try:
                self._throttle()
                kwargs = dict(model=self._model_id, messages=messages,
                              temperature=self._temperature, max_tokens=self._max_tokens)
                if self._request_logprobs:
                    kwargs["logprobs"] = True
                response = self._client.chat.completions.create(**kwargs)
                latency = time.perf_counter() - start

                choice = response.choices[0]
                text = choice.message.content or ""
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                mean_lp = self._mean_logprob(choice) if self._request_logprobs else None

                self._call_count += 1
                if self._call_count % self._rotate_every == 0 and len(self._get_live_keys()) > 1:
                    self._rotate_key()

                return ModelResponse(
                    text=text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency=latency,
                    tier=self.tier,
                    model_name=self.model_name,
                    cost_usd=self.calculate_cost(input_tokens, output_tokens),
                    mean_logprob=mean_lp,
                )

            except Exception as e:
                error_msg = str(e)
                # If the provider rejects the logprobs param, disable it and retry
                # the SAME key immediately (no backoff) instead of mis-classifying it.
                if self._request_logprobs and "logprob" in error_msg.lower():
                    self._request_logprobs = False
                    print("    (provider rejected logprobs; disabling and retrying without)")
                    continue
                self._log_error(e)
                classification = self._classify_error(error_msg)
                print(f"    Classified error as: {classification}")

                if classification == "PERMANENT_EXHAUSTION":
                    try:
                        self._mark_key_dead(self._current_key, reason=self._extract_reason_summary(error_msg))
                    except RuntimeError:
                        raise
                    except Exception as ex:
                        print(f"    [x] {ex}")
                        break
                    continue
                else:
                    try:
                        self._rotate_key()
                    except RuntimeError:
                        raise
                    except Exception as ex:
                        print(f"    [x] {ex}")
                        break
                    backoff = min(5, 2 * (attempt + 1))
                    print(f"    [~] {self._provider_name} rate limited (transient), rotated key, waiting {backoff}s...")
                    time.sleep(backoff)
                    continue

        latency = time.perf_counter() - start
        return ModelResponse(
            text=f"[ERROR] {self._provider_name} call failed: All keys exhausted or server error",
            input_tokens=len(prompt.split()) * 2,
            output_tokens=0,
            latency=latency,
            tier=self.tier,
            model_name=self.model_name,
            cost_usd=0.0,
        )

    @property
    def tier(self) -> int:
        return self._tier

    @property
    def model_name(self) -> str:
        return f"{self._name_prefix}/{self._model_id}"

    @property
    def cost_per_1m_input(self) -> float:
        return self._price_in

    @property
    def cost_per_1m_output(self) -> float:
        return self._price_out
