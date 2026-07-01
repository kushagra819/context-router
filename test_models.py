"""
Connectivity test for the 4 experiment tiers (LIVE — makes one API call each).

Verifies each tier model can be constructed and answers a trivial prompt. Run this
after setting up .env / Ollama on the home machine. For an OFFLINE check that the
whole pipeline works without any API/keys, run `python tests/test_offline.py`.

Usage:
    python test_models.py            # test all 4 tiers
    python test_models.py --tier 2   # test one tier
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.models import get_model
from src.utils.config import MODEL_CONFIG

TEST_PROMPT = (
    "A store sells apples at $2 each. If you buy 5 or more, you get 20% off. "
    "How much do 7 apples cost? End with 'Final Answer: <number>'."
)


def test_tier(tier: int) -> bool | None:
    name = MODEL_CONFIG[tier]["name"]
    print(f"\n[tier {tier}] {name}")
    try:
        model = get_model(tier)
        resp = model.generate(prompt=TEST_PROMPT, system="Show your calculation, be concise.")
        if "[ERROR]" in resp.text or resp.output_tokens == 0:
            print(f"  -> FAILED | {resp.text[:160].strip()!r}")
            return False
        print(f"  -> OK | {resp.input_tokens} in / {resp.output_tokens} out | "
              f"{resp.latency:.2f}s | ${resp.cost_usd:.6f}")
        print(f"     {resp.text[:160].strip()!r}")
        return True
    except ValueError as e:
        print(f"  -> SKIPPED (no API key / config): {e}")
        return None
    except Exception as e:
        print(f"  -> FAILED to construct/call: {e}")
        return False


def main():
    ap = argparse.ArgumentParser(description="Live connectivity test for the 4 tiers.")
    ap.add_argument("--tier", type=int, choices=[1, 2, 3, 4], default=None)
    args = ap.parse_args()

    print("=" * 56)
    print("  Context-Aware Router — Tier connectivity test (LIVE)")
    print("=" * 56)
    tiers = [args.tier] if args.tier else [1, 2, 3, 4]
    results = {t: test_tier(t) for t in tiers}

    print("\n" + "=" * 56)
    for t, ok in results.items():
        label = "OK" if ok is True else ("SKIPPED" if ok is None else "FAILED")
        print(f"  Tier {t}: {label}")
    print("=" * 56)
    print("  Tip: Ollama not running? 'ollama serve'.  Missing keys? copy .env.example -> .env")
    failed = [t for t, ok in results.items() if ok is False]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
