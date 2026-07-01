"""
Model wrappers for all 4 tiers.

Provider SDKs (openai / groq / ollama) are imported LAZILY inside get_model(),
so importing this package — and therefore the router/pipeline/evaluation code —
never requires those SDKs to be installed. This is what lets the MockModel
pipeline and all offline analysis run on a machine with no API stack.
"""

from src.models.base import BaseModel, ModelResponse
from src.models.mock_model import MockModel


def get_model(tier: int) -> BaseModel:
    """Factory: return a freshly constructed real model for the given tier.

    Imports the provider wrapper lazily so unused providers' SDKs are never
    required just to import this package.
    """
    if tier == 1:
        from src.models.ollama_model import OllamaModel
        return OllamaModel()
    elif tier == 2:
        from src.models.groq_model import GroqModel
        return GroqModel()
    elif tier == 3:
        # GPT-OSS 120B (Llama-4-Maverick sunset): Groq primary + OpenRouter failover.
        from src.models.tier3_model import build_tier3_model
        return build_tier3_model(backend="auto")
    elif tier == 4:
        # GPT-4.1 frontier, decoupled key pool (R1): direct OpenAI preferred, GitHub fallback.
        from src.models.gpt41_model import GPT41Model
        from src.models.failover_model import FailoverModel
        from src.utils.config import OPENAI_API_KEYS, GITHUB_TOKENS
        backends = []
        if OPENAI_API_KEYS:
            backends.append(GPT41Model(backend="openai"))
        if GITHUB_TOKENS:
            backends.append(GPT41Model(backend="github"))
        if not backends:
            raise ValueError("No Tier-4 keys: set OPENAI_API_KEY (preferred) or GITHUB_TOKEN in .env.")
        return backends[0] if len(backends) == 1 else FailoverModel(backends, tier=4)
    else:
        raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, 3, or 4.")


__all__ = ["BaseModel", "ModelResponse", "MockModel", "get_model"]
