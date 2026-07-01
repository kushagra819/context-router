"""Tier 4: GPT-4.1 (frontier, closed). Thin config over OpenAICompatibleModel.

Decoupled from Tier 3's key pool (fixes the shared-GitHub-PAT confound R1). Prefers
a DIRECT OpenAI key (OPENAI_API_KEY) when present -- a stable, reproducible frontier
endpoint -- and otherwise uses GitHub Models. Tier-4 failover is assembled in
src/models/__init__.py:get_model(4). Published OpenAI pricing: $2.00 in / $8.00 out.
"""

from src.models.openai_compatible import OpenAICompatibleModel
from src.utils.config import GITHUB_TOKENS, OPENAI_API_KEYS

GITHUB_BASE_URL = "https://models.github.ai/inference"
OPENAI_BASE_URL = "https://api.openai.com/v1"
GITHUB_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9", "Cache-Control": "no-cache",
}


class GPT41Model(OpenAICompatibleModel):
    """GPT-4.1 via a DIRECT OpenAI key (preferred) or GitHub Models (fallback backend)."""

    def __init__(self, backend: str = "openai", tokens: list[str] | None = None,
                 min_delay: float | None = None, temperature: float = 0.1, max_tokens: int = 2048):
        if backend == "openai":
            keys = list(tokens or OPENAI_API_KEYS)
            base_url, model_id, headers, prefix = OPENAI_BASE_URL, "gpt-4.1", None, "OpenAI"
            default_delay = max(0.5, 60.0 / (max(len(keys), 1) * 25))
        else:  # github
            keys = list(tokens or GITHUB_TOKENS)
            base_url, model_id, headers, prefix = GITHUB_BASE_URL, "openai/gpt-4.1", GITHUB_HEADERS, "GitHub"
            default_delay = max(8.0, 60.0 / (max(len(keys), 1) * 10))
        delay = min_delay if min_delay is not None else default_delay
        print(f"    GPT-4.1 ({prefix}): {len(keys)} key(s), {delay:.1f}s delay")
        super().__init__(
            provider_name=f"GPT-4.1 ({prefix})", base_url=base_url, model_id=model_id,
            tier=4, price_in=2.00, price_out=8.00, keys=keys, min_delay=delay,
            default_headers=headers, timeout=30.0, rotate_every=3,
            temperature=temperature, max_tokens=max_tokens, model_name_prefix=prefix,
        )
