"""Model wrappers for all 4 tiers."""

from src.models.base import BaseModel, ModelResponse
from src.models.ollama_model import OllamaModel
from src.models.groq_model import GroqModel
from src.models.github_model import GitHubModel
from src.models.gpt5_model import GPT5Model
from src.models.openrouter_model import OpenRouterModel
from src.models.sambanova_model import SambaNovaModel


def get_model(tier: int) -> BaseModel:
    """Factory function to get a model by tier number."""
    if tier == 1:
        return OllamaModel()
    elif tier == 2:
        return GroqModel()
    elif tier == 3:
        return GitHubModel()
    elif tier == 4:
        return GPT5Model()
    else:
        raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, 3, or 4.")


__all__ = ["BaseModel", "ModelResponse", "OllamaModel", "GroqModel", "GitHubModel", "GPT5Model", "OpenRouterModel", "SambaNovaModel", "get_model"]
