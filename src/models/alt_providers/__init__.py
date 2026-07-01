"""
Alternative model providers (NOT part of the 4-tier experiment matrix).

These wrappers are fully implemented and kept as drop-in alternatives / fallbacks
(e.g. if a GitHub Models tier is throttled, see RISK R1) or for future extensions.
They are intentionally NOT imported by `src/models/__init__.py` or used by
`get_model()` — the reported experiments use exactly the four tiers in
docs/03_MODEL_MATRIX.md. Import directly if you need them:

    from src.models.alt_providers import GeminiModel, OpenRouterModel, SambaNovaModel

Each needs its own key(s) in .env (GOOGLE_API_KEY*, OPENROUTER_API_KEY*, SAMBANOVA_API_KEY*).

Imports are LAZY (via __getattr__) so importing this package never requires an
optional SDK (e.g. google-generativeai for GeminiModel) that may not be installed.
"""

__all__ = ["GeminiModel", "OpenRouterModel", "SambaNovaModel"]


def __getattr__(name):  # PEP 562 lazy attribute import
    if name == "GeminiModel":
        from src.models.alt_providers.gemini_model import GeminiModel
        return GeminiModel
    if name == "OpenRouterModel":
        from src.models.alt_providers.openrouter_model import OpenRouterModel
        return OpenRouterModel
    if name == "SambaNovaModel":
        from src.models.alt_providers.sambanova_model import SambaNovaModel
        return SambaNovaModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
