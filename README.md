# Context-Aware LLM Routing for Multi-Agent AI Systems

## Research Project — June 2026

### Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull local model
ollama pull gemma4:e4b

# 4. Set up API keys
copy .env.example .env
# Edit .env with your Groq, GitHub, Gemini, OpenRouter, and SambaNova keys

# 5. Test all tiers
python test_models.py

# 6. Diagnostic key status check
python check_all_keys.py
```

### Model Stack (100% Free / $0 Budget)

| Tier | Model | Provider | Published Price | Description |
|------|-------|----------|-----------------|-------------|
| 🟢 1 | Gemma 4 E4B | Ollama (local) | $0.03/1M* | Local 4B-parameter model |
| 🔵 2 | Llama 3.3 70B | Groq (free API) | $0.59/1M | Cloud 70B-parameter model |
| 🔴 3 | Llama 3.1 405B | GitHub Models | $2.66/1M | Cloud 405B-parameter frontier model |
| 🟣 4 | GPT-4.1 | GitHub Models | $2.00/1M (in) / $8.00/1M (out) | Cloud proprietary frontier model (oracle) |

\*Equivalent cloud pricing. Actual cost = $0.

#### Alternative Tiers/Providers Supported:
- **SambaNova:** DeepSeek-V3.1 (frontier MoE)
- **OpenRouter:** Nous Hermes 3 405B (dense frontier)
- **Google AI Studio:** Gemini 3.5 Flash / 2.5 Flash

### Key Rotation & Throttling
All cloud wrappers subclass `BaseMultiKeyModel` in `src/models/base.py`, offering:
- **Key Rotation:** Automatically rotates across multiple accounts/keys loaded from `.env`.
- **IP-Rate Protection:** Enforces minimum request delays (e.g. `8.0s` for GitHub Models to bypass WAF scraping blocks).
- **Error Classification:** Classifies errors as transient rate-limits (TPM/RPM) or permanent exhaustion, terminating cleanly and saving checkpoints if all keys exhaust.

### Project Structure

```
context-router/
├── src/
│   ├── models/      # Model wrappers (Ollama, Groq, GitHub, OpenRouter, SambaNova, Gemini)
│   ├── agents/      # Agent definitions (GSM8K, HotpotQA, MuSiQue pipelines)
│   ├── router/      # Routing logic (rule-based, learned, cascade)
│   ├── evaluation/  # Metrics & scoring
│   └── utils/       # Config, logging
├── data/            # Datasets (auto-downloaded)
├── results/         # Experiment outputs
├── test_models.py   # Verify all tiers work
├── check_all_keys.py # Key status diagnostic tool
└── requirements.txt
```
