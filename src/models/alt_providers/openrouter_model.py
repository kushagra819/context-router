"""OpenRouter backend (OpenAI-compatible). Thin config over OpenAICompatibleModel.

Used as a Tier-3 fallback for GPT-OSS 120B (see src/models/tier3_model.py).
Kept here as a standalone wrapper for ad-hoc OpenRouter models too."""

from src.models.openai_compatible import OpenAICompatibleModel
from src.utils.config import OPENROUTER_API_KEYS

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/context-router/context-router",
    "X-Title": "Context-Aware LLM Router Research Project",
}


class OpenRouterModel(OpenAICompatibleModel):
    def __init__(self, model_id: str = "openai/gpt-oss-120b:free", tier: int = 3,
                 price_in: float = 0.60, price_out: float = 0.90,
                 tokens: list[str] | None = None, min_delay: float | None = None,
                 temperature: float = 0.1, max_tokens: int = 2048):
        keys = list(tokens or OPENROUTER_API_KEYS)
        delay = min_delay if min_delay is not None else max(1.0, 60.0 / (max(len(keys), 1) * 10))
        print(f"    OpenRouter ({model_id}): {len(keys)} key(s), {delay:.1f}s delay")
        super().__init__(
            provider_name="OpenRouter", base_url=OPENROUTER_BASE, model_id=model_id,
            tier=tier, price_in=price_in, price_out=price_out, keys=keys, min_delay=delay,
            default_headers=OPENROUTER_HEADERS, rotate_every=2,
            temperature=temperature, max_tokens=max_tokens, model_name_prefix="OpenRouter")
