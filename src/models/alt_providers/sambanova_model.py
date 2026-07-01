"""SambaNova Cloud backend (OpenAI-compatible). Thin config over OpenAICompatibleModel.

Optional alternative Tier-3 backend (DeepSeek-V3.1) -- NOT in the default 4-tier
matrix (default Tier 3 is GPT-OSS 120B via Groq/OpenRouter). Kept for users who
prefer a DeepSeek-class strong tier; wire it in via get_model if desired."""

from src.models.openai_compatible import OpenAICompatibleModel
from src.utils.config import SAMBANOVA_API_KEYS

SAMBANOVA_BASE = "https://api.sambanova.ai/v1"


class SambaNovaModel(OpenAICompatibleModel):
    def __init__(self, model_id: str = "DeepSeek-V3.1", tier: int = 3,
                 price_in: float = 0.60, price_out: float = 0.90,
                 tokens: list[str] | None = None, min_delay: float | None = None,
                 temperature: float = 0.1, max_tokens: int = 2048):
        keys = list(tokens or SAMBANOVA_API_KEYS)
        delay = min_delay if min_delay is not None else max(3.0, 60.0 / (max(len(keys), 1) * 8))
        print(f"    SambaNova ({model_id}): {len(keys)} key(s), {delay:.1f}s delay")
        super().__init__(
            provider_name="SambaNova", base_url=SAMBANOVA_BASE, model_id=model_id,
            tier=tier, price_in=price_in, price_out=price_out, keys=keys, min_delay=delay,
            rotate_every=3, temperature=temperature, max_tokens=max_tokens,
            model_name_prefix="SambaNova")
