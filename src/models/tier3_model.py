"""
Tier 3: GPT-OSS 120B (strong open model) with provider failover.
====================================================================
Replaces Llama-4-Maverick (sunset 03/09/2026). GPT-OSS 120B is OpenAI's large open
model. It is free/cheap and OpenAI-compatible on multiple hosts; we use:

  PRIMARY  : Groq  (openai/gpt-oss-120b) -- fast, the
             same reliable provider as Tier 2, on a separate per-model rate limit.
  FALLBACK : OpenRouter (openai/gpt-oss-120b:free) -- a SEPARATE key pool,
             so the strong tier never goes dark mid-run.

Decoupled from Tier 4 (GPT-4.1), which fixes the shared-GitHub-PAT confound (R1).
For a single results table use ONE backend; the fallback is a documented
robustness failover, not a silent substitution (see FailoverModel).

Representative (hypothetical) price -- all models are free in practice (R10):
$0.60 / $0.90 per 1M in/out, kept monotonically above Tier 2.
"""

from src.models.openai_compatible import OpenAICompatibleModel
from src.models.failover_model import FailoverModel
from src.utils.config import GROQ_API_KEYS, OPENROUTER_API_KEYS, MODEL_CONFIG

GROQ_OAI_BASE = "https://api.groq.com/openai/v1"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/context-router/context-router",
    "X-Title": "Context-Aware LLM Router Research Project",
}

PRICE_IN = MODEL_CONFIG[3]["cost_per_1m_input"]
PRICE_OUT = MODEL_CONFIG[3]["cost_per_1m_output"]


def _groq_gpt_oss(min_delay=None):
    keys = list(GROQ_API_KEYS)
    delay = min_delay if min_delay is not None else max(0.5, 60.0 / (max(len(keys), 1) * 25))
    print(f"    Tier-3 Groq/GPT-OSS 120B: {len(keys)} key(s), {delay:.1f}s delay")
    return OpenAICompatibleModel(
        provider_name="Groq (GPT-OSS 120B)", base_url=GROQ_OAI_BASE,
        model_id="openai/gpt-oss-120b", tier=3,
        price_in=PRICE_IN, price_out=PRICE_OUT, keys=keys, min_delay=delay,
        rotate_every=5, model_name_prefix="Groq")


def _openrouter_gpt_oss(min_delay=None):
    keys = list(OPENROUTER_API_KEYS)
    delay = min_delay if min_delay is not None else max(1.0, 60.0 / (max(len(keys), 1) * 10))
    print(f"    Tier-3 OpenRouter/GPT-OSS 120B: {len(keys)} key(s), {delay:.1f}s delay")
    return OpenAICompatibleModel(
        provider_name="OpenRouter (GPT-OSS 120B)", base_url=OPENROUTER_BASE,
        model_id="openai/gpt-oss-120b:free", tier=3,
        price_in=PRICE_IN, price_out=PRICE_OUT, keys=keys, min_delay=delay,
        default_headers=OPENROUTER_HEADERS, rotate_every=2, model_name_prefix="OpenRouter")


def build_tier3_model(backend: str = "auto"):
    """Build the Tier-3 model.
      * backend="groq"       -> Groq only
      * backend="openrouter" -> OpenRouter only
      * backend="auto"       -> FailoverModel([Groq, OpenRouter]) over whichever
                                providers have keys (Groq primary).
    """
    backends = []
    if backend in ("groq", "auto") and GROQ_API_KEYS:
        backends.append(_groq_gpt_oss())
    if backend in ("openrouter", "auto") and OPENROUTER_API_KEYS:
        backends.append(_openrouter_gpt_oss())
    if not backends:
        raise ValueError(
            "No Tier-3 keys found. Set GROQ_API_KEY (Groq GPT-OSS 120B) and/or "
            "OPENROUTER_API_KEY in .env. See .env.example.")
    if len(backends) == 1:
        return backends[0]
    return FailoverModel(backends, tier=3)
