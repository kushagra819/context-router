"""
ModelRegistry
=============
A lazy, cached provider of tier models for the routed pipeline.

The routed multi-agent pipeline asks the router for a tier (1-4) before every
agent call, then asks this registry for the corresponding model. Real model
clients are expensive to construct (they open API clients and print key status),
so we instantiate each tier at most once and reuse it.

Two modes:
  * real  -> uses src.models.get_model(tier) (Ollama / Groq / GitHub).
  * mock  -> uses MockModel(tier) (offline, deterministic, no network).

Mock mode is what makes the whole pipeline runnable on a machine with no API
keys, which is how we smoke-test orchestration before the API-heavy runs.
"""

from src.models.base import BaseModel
from src.models import get_model
from src.models.mock_model import MockModel


class ModelRegistry:
    """Lazily instantiates and caches one model per tier."""

    def __init__(self, mock: bool = False):
        self.mock = mock
        self._cache: dict[int, BaseModel] = {}

    def get(self, tier: int) -> BaseModel:
        if tier not in self._cache:
            self._cache[tier] = MockModel(tier) if self.mock else get_model(tier)
        return self._cache[tier]

    def warm(self, tiers) -> None:
        """Pre-instantiate the given tiers (e.g. to print key status up front)."""
        for t in tiers:
            self.get(t)

    @property
    def loaded_tiers(self) -> list[int]:
        return sorted(self._cache.keys())
