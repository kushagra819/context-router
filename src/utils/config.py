"""Configuration and constants for the routing research project."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional; env vars may be set by the shell
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

# Load .env file (if python-dotenv is installed and a .env exists)
load_dotenv()

# ──────────────────────────────────────────
# PROJECT PATHS
# ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "baselines").mkdir(exist_ok=True)
(RESULTS_DIR / "routing").mkdir(exist_ok=True)
(RESULTS_DIR / "figures").mkdir(exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────
# API KEYS (loaded from .env)
# ──────────────────────────────────────────
def _load_keys(prefix: str, count: int = 15) -> list[str]:
    """Load up to `count` API keys from .env with pattern PREFIX, PREFIX_2, ..., PREFIX_15."""
    keys = []
    for i in range(1, count + 1):
        env_var = prefix if i == 1 else f"{prefix}_{i}"
        val = os.getenv(env_var)
        if val and not val.startswith("your_"):
            keys.append(val)
    return keys

GROQ_API_KEYS = _load_keys("GROQ_API_KEY")
GOOGLE_API_KEYS = _load_keys("GOOGLE_API_KEY")
GITHUB_TOKENS = _load_keys("GITHUB_TOKEN")
OPENROUTER_API_KEYS = _load_keys("OPENROUTER_API_KEY")
SAMBANOVA_API_KEYS = _load_keys("SAMBANOVA_API_KEY")
OPENAI_API_KEYS = _load_keys("OPENAI_API_KEY")   # Tier 4 direct frontier (preferred over GitHub)

# ──────────────────────────────────────────
# MODEL CONFIGURATIONS
# ──────────────────────────────────────────
MODEL_CONFIG = {
    1: {  # Tier 1: Local small model
        "name": "Gemma 4 E4B",
        "model_id": "gemma4:e4b",
        "provider": "ollama",
        "cost_per_1m_input": 0.03,    # Equivalent cloud pricing (actual = $0)
        "cost_per_1m_output": 0.06,
        "max_tokens": 2048,
        "temperature": 0.1,
    },
    2: {  # Tier 2: Cloud medium model
        "name": "Llama 3.3 70B",
        "model_id": "llama-3.3-70b-versatile",
        "provider": "groq",
        "cost_per_1m_input": 0.59,    # Groq paid-tier pricing
        "cost_per_1m_output": 0.79,
        "max_tokens": 2048,
        "temperature": 0.1,
    },
    3: {  # Tier 3: Strong open model (Llama-4-Maverick sunset -> GPT-OSS 120B)
        "name": "GPT-OSS 120B",
        "model_id": "openai/gpt-oss-120b",  # Groq ID; OpenRouter ID: openai/gpt-oss-120b:free
        "provider": "groq+openrouter (failover)",
        "cost_per_1m_input": 0.60,    # Representative hosted price (hypothetical; R10), kept > Tier 2
        "cost_per_1m_output": 0.90,
        "max_tokens": 2048,
        "temperature": 0.1,
    },
    4: {  # Tier 4: Proprietary frontier (oracle/ceiling); own key pool (decoupled from T3, R1)
        "name": "GPT-4.1",
        "model_id": "gpt-4.1",        # direct OpenAI; GitHub fallback id: openai/gpt-4.1
        "provider": "openai (direct) | github (fallback)",
        "cost_per_1m_input": 2.00,     # Official OpenAI GPT-4.1 pricing
        "cost_per_1m_output": 8.00,
        "max_tokens": 2048,
        "temperature": 0.1,
    },
}

# ──────────────────────────────────────────
# EXPERIMENT DEFAULTS
# ──────────────────────────────────────────
DEFAULT_GSM8K_COUNT = 200
DEFAULT_MMLU_COUNT = 500
DEFAULT_HUMANEVAL_COUNT = 164  # Full set

# Rate limiting (requests per minute)
RATE_LIMITS = {
    "ollama": 999,     # No limit (local)
    "groq": 28,        # 30 RPM with buffer (Tier 2 Llama-70B AND Tier 3 GPT-OSS 120B: per-model limits)
    "openrouter": 10,  # Conservative for OpenRouter free tier (Tier 3 GPT-OSS 120B fallback)
    "openai": 60,      # Tier 4 direct OpenAI (paid; ample headroom)
    "github": 15,      # GitHub Models free tier (Tier 4 GPT-4.1 fallback only)
    "sambanova": 8,    # Optional alt Tier-3 backend (DeepSeek-V3.1)
}
