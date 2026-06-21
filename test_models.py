"""
Test script to verify all 3 model tiers are working.
Run this after setup to confirm everything is connected.

Usage: python test_models.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import OllamaModel, GroqModel, GitHubModel, GPT41Model, OpenRouterModel, SambaNovaModel


TEST_PROMPT = (
    "A store sells apples at $2 each. If you buy 5 or more, you get 20% off. "
    "How much do 7 apples cost? Show your calculation."
)


def test_tier(name: str, model_cls, require_api_key: bool = False):
    """Test a single model tier."""
    print(f"\n{'─'*60}")
    print(f"Testing {name}...")
    print(f"{'─'*60}")

    try:
        model = model_cls()
        print(f"  Model:    {model.model_name}")
        print(f"  Tier:     {model.tier}")
        print(f"  Pricing:  ${model.cost_per_1m_input}/1M in, ${model.cost_per_1m_output}/1M out")
        print(f"  Sending test prompt...")

        response = model.generate(TEST_PROMPT)

        print(f"  Latency:  {response.latency:.2f}s")
        print(f"  Tokens:   {response.input_tokens} in + {response.output_tokens} out")
        print(f"  Cost:     ${response.cost_usd:.6f}")
        print(f"  Output:   {response.text[:200]}...")

        # ── Strict validation ──────────────────────────────────
        if "[ERROR]" in response.text:
            print(f"  ❌ FAILED: Response contains an error message.")
            return False
        if response.output_tokens == 0:
            print(f"  ❌ FAILED: Model returned 0 output tokens.")
            return False

        print(f"  ✅ Passed!")
        return True

    except ValueError as e:
        if require_api_key:
            print(f"  ⚠️  Skipped (no API key): {e}")
            return None
        raise
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def main():
    print("=" * 60)
    print("  Context-Aware Router — Model Tier Testing")
    print("=" * 60)

    results = {}

    # Tier 1: Ollama (local)
    results["Tier 1 (Ollama/Gemma 4B)"] = test_tier(
        "Tier 1 — Local Gemma 4 E4B via Ollama",
        OllamaModel,
    )

    # Tier 2: Groq (free API)
    results["Tier 2 (Groq/Llama 70B)"] = test_tier(
        "Tier 2 — Groq Llama 3.3 70B",
        GroqModel,
        require_api_key=True,
    )

    # Tier 3: GitHub Models (free tier Llama 3.1 405B)
    results["Tier 3 (Llama 3.1 405B)"] = test_tier(
        "Tier 3 — Llama 3.1 405B via GitHub Models",
        GitHubModel,
        require_api_key=True,
    )

    # Tier 4: GitHub Models (GPT-4.1 — oracle/ceiling)
    results["Tier 4 (GPT-4.1)"] = test_tier(
        "Tier 4 — GPT-4.1 via GitHub Models",
        GPT41Model,
        require_api_key=True,
    )

    # Summary
    print(f"\n{'='*60}")
    print("  RESULTS SUMMARY")
    print(f"{'='*60}")
    for name, status in results.items():
        if status is True:
            icon = "✅"
        elif status is None:
            icon = "⚠️  (no API key — set up .env)"
        else:
            icon = "❌"
        print(f"  {icon}  {name}")

    all_ok = all(v is True for v in results.values() if v is not None)
    if all_ok:
        print(f"\n  🎉 All available tiers working! Ready for experiments.")
    else:
        print(f"\n  ⚙️  Fix the issues above, then re-run this script.")

    print(f"\n  Next steps:")
    print(f"  1. If missing API keys → copy .env.example to .env and fill in keys")
    print(f"  2. If Ollama failed → make sure Ollama is running: 'ollama serve'")
    print(f"  3. If model not found → pull it: 'ollama pull gemma4:e4b'")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
