"""Abstract base class for all LLM model wrappers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class ModelResponse:
    """Standardized response from any model tier."""
    text: str
    input_tokens: int
    output_tokens: int
    latency: float           # seconds
    tier: int
    model_name: str
    cost_usd: float          # calculated from published pricing

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseModel(ABC):
    """
    Every model wrapper must implement this interface.
    Returns a standardized ModelResponse regardless of provider.
    """

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        """Send a prompt and return a standardized response."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tier(self) -> int:
        """Return the tier number (1, 2, 3, or 4)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return human-readable model name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def cost_per_1m_input(self) -> float:
        """Published cost per 1M input tokens."""
        raise NotImplementedError

    @property
    @abstractmethod
    def cost_per_1m_output(self) -> float:
        """Published cost per 1M output tokens."""
        raise NotImplementedError

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD based on published pricing."""
        input_cost = (input_tokens / 1_000_000) * self.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * self.cost_per_1m_output
        return round(input_cost + output_cost, 8)


class BaseMultiKeyModel(BaseModel):
    """
    Subclass of BaseModel that adds provider-agnostic API key rotation,
    throttling, error logging, and rate limit classification (temporary vs permanent).
    """

    def __init__(
        self,
        provider_name: str,
        keys: list[str],
        min_delay: float,
    ):
        self._provider_name = provider_name
        self._keys = list(keys)
        self._dead_keys = {}
        self._key_index = 0
        self._min_delay = min_delay
        self._last_call_time = 0.0
        self._call_count = 0

        if not self._keys:
            raise ValueError(f"No API keys provided for {provider_name}")

        self._current_key = self._keys[0]

    def _get_live_keys(self) -> list[str]:
        """Return list of keys that have not been marked exhausted."""
        return [k for k in self._keys if k not in self._dead_keys]

    def _mark_key_dead(self, key: str, reason: str = "daily limit hit"):
        """Mark a key as permanently exhausted for this session."""
        if key not in self._dead_keys:
            self._dead_keys[key] = reason
            live = self._get_live_keys()
            masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "..."
            print(f"    🚫 {self._provider_name} key {masked} marked EXHAUSTED ({reason}). {len(live)}/{len(self._keys)} keys remaining.")
            if not live:
                raise RuntimeError(f"❌ All {self._provider_name} API keys exhausted. Benchmark stopped.")
            self._rotate_key()

    def _rotate_key(self):
        """Switch to next live API key, skipping dead ones."""
        live = self._get_live_keys()
        if not live:
            raise RuntimeError(f"❌ All {self._provider_name} API keys exhausted. Benchmark stopped.")

        # Cycle through full list to find next live key
        for _ in range(len(self._keys)):
            self._key_index = (self._key_index + 1) % len(self._keys)
            candidate = self._keys[self._key_index]
            if candidate not in self._dead_keys:
                self._current_key = candidate
                self._init_client()
                return

    def get_key_status(self) -> dict:
        """Get counts of total, active, and exhausted keys."""
        total = len(self._keys)
        active = len(self._get_live_keys())
        exhausted = len(self._dead_keys)
        return {
            "total": total,
            "active": active,
            "exhausted": exhausted
        }

    def print_key_status(self, startup: bool = False):
        """Print the active vs exhausted key counts."""
        status = self.get_key_status()
        if startup:
            print(f"\n{self._provider_name}:")
            print(f"  Total Keys: {status['total']}")
            print(f"  Active:     {status['active']}")
            print(f"  Exhausted:  {status['exhausted']}\n")
        else:
            print(f"\n{self._provider_name} Status:")
            print(f"  Active:     {status['active']}")
            print(f"  Exhausted:  {status['exhausted']}\n")

    def _extract_reason_summary(self, error_msg: str) -> str:
        """Extract a user-friendly summary of the rate limit/exhaustion reason."""
        error_lower = error_msg.lower()
        if "byday" in error_lower or "daily limit" in error_lower or "daily quota" in error_lower or "tokens per day" in error_lower or "tokens_per_day" in error_lower:
            return "Tokens Per Day limit reached"
        if "abusepenalty" in error_lower:
            return "Abuse penalty active"
        if "free model" in error_lower:
            return "Free model daily limit exceeded"
        if "insufficient" in error_lower or "credit" in error_lower or "balance" in error_lower:
            return "Credits or account balance exhausted"
        if "unauthorized" in error_lower or "invalid_api_key" in error_lower or "invalid api key" in error_lower or "401" in error_lower:
            return "Invalid API key / Unauthorized"
        if "scraping" in error_lower:
            return "GitHub scraping / abuse block triggered"
        # Fallback to truncated version of original error message
        return error_msg[:60] + "..." if len(error_msg) > 60 else error_msg

    def print_final_status(self):
        """Print the final provider status summary when benchmark exits."""
        status = self.get_key_status()
        print("\n=================================")
        print("Provider Status Summary")
        print("=================================")
        print(f"\n{self._provider_name}:")
        print(f"Total Keys: {status['total']}")
        print(f"Exhausted: {status['exhausted']}")
        print(f"Active: {status['active']}")
        
        if self._dead_keys:
            reasons = sorted(list(set(self._dead_keys.values())))
            print("\nReason:")
            for r in reasons:
                print(r)
        print("=================================\n")


    def _init_client(self):
        """Initialize provider-specific client using self._current_key. Must be implemented in subclass."""
        raise NotImplementedError

    def _throttle(self):
        """Enforce minimum delay between API calls."""
        now = time.time()
        elapsed = now - self._last_call_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_call_time = time.time()

    def _log_error(self, exception: Exception):
        """Log full provider response details."""
        print("Provider Response:")
        if hasattr(exception, "response") and hasattr(exception.response, "text") and exception.response.text:
            print(exception.response.text)
        elif hasattr(exception, "body") and exception.body is not None:
            import json
            try:
                print(json.dumps(exception.body, indent=2))
            except Exception:
                print(str(exception.body))
        else:
            print(str(exception))

    def _classify_error(self, error_msg: str) -> str:
        """Classify rate limit error as TEMPORARY_RATE_LIMIT or PERMANENT_EXHAUSTION."""
        error_lower = error_msg.lower()

        # Auth/Invalid key errors are always permanent exhaustion
        auth_keywords = ["401", "403", "unauthorized", "forbidden", "invalid_api_key", "invalid api key", "key_invalid"]
        if any(kw in error_lower for kw in auth_keywords):
            return "PERMANENT_EXHAUSTION"

        # General permanent exhaustion terms
        permanent_keywords = [
            "byday", "daily", "quota", "credit", "fund", "balance", 
            "subscription", "billing", "account_limit", "free model",
            "abusepenalty", "abuse_penalty", "rate limit byday",
            "scraping"
        ]
        for kw in permanent_keywords:
            if kw in error_lower:
                return "PERMANENT_EXHAUSTION"

        # General rate limit messages: if they don't explicitly reference per-minute (RPM/TPM), check provider context
        if "limit exceeded" in error_lower or "rate limit" in error_lower:
            if not any(kw in error_lower for kw in ["minute", "rpm", "tpm", "requests per", "tokens per"]):
                if self._provider_name.lower() == "groq" and "day" in error_lower:
                    return "PERMANENT_EXHAUSTION"
                if self._provider_name.lower() == "openrouter" and ("free" in error_lower or "daily" in error_lower):
                    return "PERMANENT_EXHAUSTION"

        return "TEMPORARY_RATE_LIMIT"

