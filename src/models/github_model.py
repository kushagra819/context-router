"""GitHub Models backend (OpenAI-compatible). Thin config over OpenAICompatibleModel.

No longer the default Tier-3 backend (Llama-3.1-405B has been sunset; Tier 3 is now
GPT-OSS 120B via Groq/OpenRouter -- see src/models/tier3_model.py). This wrapper
is retained as an optional GitHub-Models backend and as a Tier-4 GPT-4.1 FALLBACK.
"""

from src.models.openai_compatible import OpenAICompatibleModel
from src.utils.config import GITHUB_TOKENS

GITHUB_BASE_URL = "https://models.github.ai/inference"
# A browser-like UA + headers reduce GitHub Models' anti-bot 403s on some networks.
GITHUB_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


class GitHubModel(OpenAICompatibleModel):
    """Generic GitHub Models wrapper (defaults to Llama-3.1-405B for legacy/repro use)."""

    def __init__(self, model_id: str = "Meta-Llama-3.1-405B-Instruct", tier: int = 3,
                 price_in: float = 2.66, price_out: float = 2.66,
                 tokens: list[str] | None = None, min_delay: float | None = None,
                 temperature: float = 0.1, max_tokens: int = 2048):
        keys = list(tokens or GITHUB_TOKENS)
        delay = min_delay if min_delay is not None else max(8.0, 60.0 / (max(len(keys), 1) * 10))
        print(f"    GitHub Models ({model_id}): {len(keys)} token(s), {delay:.1f}s delay")
        super().__init__(
            provider_name="GitHub Models", base_url=GITHUB_BASE_URL, model_id=model_id,
            tier=tier, price_in=price_in, price_out=price_out, keys=keys, min_delay=delay,
            default_headers=GITHUB_HEADERS, timeout=30.0, rotate_every=3,
            temperature=temperature, max_tokens=max_tokens, model_name_prefix="GitHub",
        )
