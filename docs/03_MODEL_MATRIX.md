# Model Matrix

## 1. Active Model Hierarchy

| Tier | Model | Parameters | Provider | API | Pricing ($/1M tokens) | Latency Profile |
|:----:|-------|:----------:|----------|-----|:---------------------:|:---------------:|
| 1 | **Gemma 4 E4B** | ~4B | Ollama (local) | REST localhost | In: $0.03, Out: $0.06 | ~98s/problem (CPU) |
| 2 | **Llama 3.3 70B** | 70B | Groq | Cloud API | In: $0.59, Out: $0.79 | ~3s/problem |
| 3 | **GPT-OSS 120B** | 120B | Groq (primary) + OpenRouter (failover) | OpenAI-compatible | In: $0.60, Out: $0.90 | ~5s/problem |
| 4 | **GPT-4.1** | ~1.8T (est.) | GitHub Models | OpenAI-compatible | In: $2.00, Out: $8.00 | ~12s/problem |

> **Note:** All models are accessed for free via academic/free-tier APIs. Pricing above is the published commercial rate, used for hypothetical cost analysis.

## 2. Provider Details

### Tier 1: Ollama (Local)
- **File:** `src/models/ollama_model.py`
- **Model ID:** `gemma4:e4b`
- **Rate limit:** None (local)
- **Key rotation:** N/A
- **Notes:** Runs on home laptop CPU. Slowest but zero cost. Does not extend `BaseMultiKeyModel`.

### Tier 2: Groq
- **File:** `src/models/groq_model.py`
- **Model ID:** `llama-3.3-70b-versatile`
- **Rate limit:** 28 RPM (configured), actual 30 RPM
- **Key rotation:** Up to 15 API keys
- **Notes:** Fastest cloud provider. Best cost-performance ratio.

### Tier 3: Groq (primary) + OpenRouter (failover)
- **File:** `src/models/tier3_model.py`
- **Model ID:** `openai/gpt-oss-120b`
- **Rate limit:** ~25 RPM per key (Groq), ~10 RPM per key (OpenRouter)
- **Key rotation:** Up to 15 Groq keys + 15 OpenRouter keys (separate pools)
- **Notes:** Replaced Llama-3.1-405B (sunset) → Llama-4-Maverick (sunset) → GPT-OSS 120B. Uses separate key pools from Tier 4, resolving the shared-pool confound.

### Tier 4: OpenAI (preferred) + GitHub Models (fallback)
- **File:** `src/models/gpt41_model.py`
- **Model ID:** `openai/gpt-4.1`
- **Rate limit:** 1000 RPM / 1M TPM per GitHub key
- **Key rotation:** Up to 15 GitHub PATs (separate pool from Tier 3)
- **Notes:** Frontier model. Tier 3 and Tier 4 now use separate key pools.

## 3. Inactive Models (Kept for Future Use)

| Model | Provider | File | Notes |
|-------|----------|------|-------|
| Gemini 2.5 Flash | Google GenAI | `src/models/gemini_model.py` | Not in any baseline |
| Hermes 3 Llama 405B | OpenRouter | `src/models/openrouter_model.py` | Potential Tier 3 fallback |
| DeepSeek-V3.1 | SambaNova | `src/models/sambanova_model.py` | Potential Tier 3 fallback |

## 4. Configuration

All model settings are centralized in `src/utils/config.py`:
- API keys loaded from `.env` via `_load_keys()` function
- Up to 15 keys per provider
- Rate limits per provider in `RATE_LIMITS` dict
- Model metadata in `MODEL_CONFIG` dict

## 5. Key Architecture

```
BaseModel (ABC)
├── OllamaModel (Tier 1) — direct implementation
└── BaseMultiKeyModel (ABC) — adds key rotation, throttling, error classification
    ├── GroqModel (Tier 2)
    ├── GitHubModel (Tier 3)
    └── GPT41Model (Tier 4)
```

All models return `ModelResponse(text, input_tokens, output_tokens, latency, tier, model_name, cost_usd)`.
