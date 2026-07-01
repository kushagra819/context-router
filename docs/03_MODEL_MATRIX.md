# Model Matrix

## 1. Active Model Hierarchy

| Tier | Model | Parameters | Provider | API | Pricing ($/1M tokens) | Latency Profile |
|:----:|-------|:----------:|----------|-----|:---------------------:|:---------------:|
| 1 | **Gemma 4 E4B** | ~4B | Ollama (local) | REST localhost | In: $0.03, Out: $0.06 | ~98s/problem (CPU) |
| 2 | **Llama 3.3 70B** | 70B | Groq | Cloud API | In: $0.59, Out: $0.79 | ~3s/problem |
| 3 | **Llama 3.1 405B** | 405B | GitHub Models | OpenAI-compatible | In: $2.66, Out: $2.66 | ~54s/problem |
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

### Tier 3: GitHub Models
- **File:** `src/models/github_model.py`
- **Model ID:** `Meta-Llama-3.1-405B-Instruct`
- **Rate limit:** ~15 RPM (conservative), 8.0s enforced delay
- **Key rotation:** Up to 15 GitHub PATs
- **Notes:** Shares GitHub token pool with Tier 4. 8s delay = ~27 min overhead per 200 problems.

### Tier 4: GitHub Models
- **File:** `src/models/gpt41_model.py`
- **Model ID:** `openai/gpt-4.1`
- **Rate limit:** ~15 RPM, 8.0s enforced delay
- **Key rotation:** Up to 15 GitHub PATs (same pool as Tier 3)
- **Notes:** Frontier model. Shares token pool with Tier 3 — cannot run both simultaneously.

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
