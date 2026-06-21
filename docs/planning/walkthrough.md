# Walkthrough: Unified Key Rotation & Exhaustion Management

I have implemented a unified key rotation, rate limit classification, and error logging infrastructure across all model wrappers. This ensures consistent, robust handling of API keys across different providers.

## Changes Completed

### 1. Created `BaseMultiKeyModel` in `src/models/base.py`
Created a reusable, provider-agnostic subclass of `BaseModel` that manages:
* **Key rotation:** Houses the active rotation pool (`_keys`, `_key_index`, `_dead_keys`).
* **Active throttling:** Enforces the minimum delay (`_min_delay`) between calls.
* **Response logging:** Automatically captures and displays the full response payload returned by the provider on failure.
* **Error classification:** Analyzes the error string for keywords indicating temporary rate limits (RPM/TPM exceeded) vs. permanent exhaustion (daily quotas reached, out of credits, invalid authentication tokens, or scraping blocks).
* **Safety termination:** Immediately raises a fatal `RuntimeError("❌ All {provider} API keys exhausted. Benchmark stopped.")` if all keys in the pool are marked as exhausted, stopping infinite retry loops.
* **Status reporting:** Added helper methods `get_key_status` and `print_key_status` to report key details.

### 2. Refactored Model Wrappers to Subclass `BaseMultiKeyModel`
Removed duplicate rotation, throttling, and error handling code, and shifted all wrappers to inherit from `BaseMultiKeyModel` while ensuring `RuntimeError` bubble-up propagation is maintained:
* **Groq Wrapper (`src/models/groq_model.py`)**
* **OpenRouter Wrapper (`src/models/openrouter_model.py`)**
* **GitHub Models Wrapper (`src/models/github_model.py`)** — increased default minimum delay to `8.0s` to avoid IP scraping blocks.
* **GPT-5 Wrapper (`src/models/gpt5_model.py`)** — increased default minimum delay to `8.0s` to avoid IP scraping blocks.
* **SambaNova Wrapper (`src/models/sambanova_model.py`)**
* **Gemini Wrapper (`src/models/gemini_model.py`)**

### 3. Integrated Clean Termination & Status Logging in Benchmark Runners
Updated the loops in the three benchmark runners:
* `run_baseline.py` (GSM8K)
* `run_hotpotqa_baseline.py` (HotpotQA)
* `run_musique_baseline.py` (MuSiQue)

**Added features:**
* **Startup status:** Prints the total, active, and exhausted keys on launch.
* **Interval status:** Prints active vs. exhausted keys every 25 processed items.
* **Fatal error catching:** Intercepts `RuntimeError` exceptions. If they indicate key exhaustion, it prints a fatal error, breaks the loop immediately, aggregates the completed items, and saves all stats/results to JSON and CSV files cleanly.
* **Provider Status Summary on Exit:** Prints a formatted summary block displaying the provider name, total keys, active keys, exhausted keys, and the set of unique exhaustion reasons when the benchmark exits or terminates prematurely.

---

## Validation & Testing

A verification script was created at `scratch/test_exhaustion.py` which:
1. Passes invalid API keys to the `GroqModel` wrapper and verifies that it captures the auth failure response, logs the full provider error, marks the keys as exhausted, and raises `❌ All Groq API keys exhausted` immediately.
2. Passes invalid API keys to the `OpenRouterModel` wrapper and verifies the same behavior.
