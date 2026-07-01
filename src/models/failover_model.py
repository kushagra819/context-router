"""
FailoverModel
=============
Wraps an ordered list of model backends for ONE tier and transparently fails
over to the next backend when the current one's keys are fully exhausted
(BaseMultiKeyModel raises RuntimeError) or it returns an [ERROR] response.

Why (reproducibility, R1/R2): GitHub Models' shared-PAT 405B endpoint was the
reliability bottleneck. We now back the strong-open tier (Tier 3) with a PRIMARY
provider and an automatic FALLBACK on a SEPARATE key pool, so a strong tier never
goes dark mid-run. CRITICAL for science: a single results TABLE should be produced
on ONE (provider, model) pair -- cross-provider switching is a documented FAILOVER
for robustness, not silent substitution. Every call logs which backend served it,
and `provider_log` records the realized backend mix so the paper can report it.
"""

from __future__ import annotations

from src.models.base import BaseModel, ModelResponse


class FailoverModel(BaseModel):
    def __init__(self, backends: list, tier: int):
        if not backends:
            raise ValueError("FailoverModel needs at least one backend")
        self._backends = backends
        self._tier = tier
        self._active = 0
        self.provider_log: dict[str, int] = {}

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        last: ModelResponse | None = None
        for i in range(self._active, len(self._backends)):
            backend = self._backends[i]
            try:
                resp = backend.generate(prompt, system)
            except RuntimeError as e:
                # All keys for this backend are exhausted -> permanently advance.
                print(f"    [failover] backend '{backend.model_name}' exhausted ({e}); "
                      f"advancing to next provider for Tier {self._tier}.")
                self._active = i + 1
                continue
            if "[ERROR]" in (resp.text or ""):
                last = resp
                print(f"    [failover] backend '{backend.model_name}' returned [ERROR]; "
                      f"trying next provider for Tier {self._tier}.")
                self._active = i + 1
                continue
            self.provider_log[backend.model_name] = self.provider_log.get(backend.model_name, 0) + 1
            return resp
        # Everything failed: return the last error (or synthesize one).
        if last is not None:
            return last
        return ModelResponse(
            text=f"[ERROR] All Tier-{self._tier} failover backends exhausted",
            input_tokens=len(prompt.split()) * 2, output_tokens=0, latency=0.0,
            tier=self._tier, model_name=self.model_name, cost_usd=0.0,
        )

    @property
    def tier(self) -> int:
        return self._tier

    @property
    def model_name(self) -> str:
        return self._backends[self._active].model_name if self._active < len(self._backends) \
            else self._backends[-1].model_name

    @property
    def cost_per_1m_input(self) -> float:
        return self._backends[min(self._active, len(self._backends) - 1)].cost_per_1m_input

    @property
    def cost_per_1m_output(self) -> float:
        return self._backends[min(self._active, len(self._backends) - 1)].cost_per_1m_output
