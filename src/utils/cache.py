"""
Simple disk-based response cache.
If the same (model, prompt, system) was called before, return cached result.
Saves API calls during re-runs and debugging.
"""

import hashlib
import json
import os
from pathlib import Path


CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(model_name: str, prompt: str, system: str = "") -> str:
    """Generate a unique hash for this (model, prompt, system) combo."""
    content = f"{model_name}||{system}||{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()


def get_cached(model_name: str, prompt: str, system: str = "") -> dict | None:
    """Return cached response dict if exists, else None."""
    key = _cache_key(model_name, prompt, system)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_to_cache(model_name: str, prompt: str, system: str, response_data: dict):
    """Save a response to disk cache."""
    key = _cache_key(model_name, prompt, system)
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(response_data, f, ensure_ascii=False)


def cache_stats() -> dict:
    """Return cache statistics."""
    files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    return {
        "cached_responses": len(files),
        "total_size_mb": round(total_size / 1_000_000, 2),
    }
