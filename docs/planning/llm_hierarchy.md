# Complete LLM Model Hierarchy — June 2026

## 🏆 Frontier Tier (Best in Class)

| Model | Provider | Params | Pricing (per 1M tokens) | Best At | Availability |
|:--|:--|:--|:--|:--|:--|
| **Claude Opus 4.8** | Anthropic | ~2T MoE | $15 / $75 | #1 overall intelligence, coding, agentic | API (paid) |
| **GPT-5.5** | OpenAI | Undisclosed | $5 / $15 | General purpose, tool use, autonomous tasks | API (paid) |
| **Gemini 3.1 Pro** | Google | Undisclosed | $1.25 / $5 | Multimodal, reasoning, multilingual | API (paid + free tier) |
| **Grok 4** | xAI | Undisclosed | $3 / $15 | 2M context window, real-time X integration | API (paid) |

---

## 🔵 High Tier (Production Grade)

| Model | Provider | Params | Pricing (per 1M tokens) | Best At | Availability |
|:--|:--|:--|:--|:--|:--|
| **Claude Sonnet 4.5** | Anthropic | ~700B MoE | $3 / $15 | Best balance of speed + quality | API (paid) |
| **GPT-4o** | OpenAI | Undisclosed | $2.50 / $10 | Multimodal, strong general | API (paid) |
| **Gemini 2.5 Pro** | Google | Undisclosed | $1.25 / $5 | Thinking, long context | API (legacy) |
| **Llama 4 Maverick** | Meta | 400B MoE | Free (self-host) / varies | Open-weight, production workloads | Ollama, Groq, etc. |
| **Mistral Large 3** | Mistral | ~120B | $2 / $6 | Multilingual, European data sovereignty | API + self-host |
| **DeepSeek V3** | DeepSeek | 671B MoE | $0.27 / $1.10 | Cheapest frontier, coding | API + open-weight |

---

## 🟢 Mid Tier (Sweet Spot — Quality + Speed)

| Model | Provider | Params | Pricing (per 1M tokens) | Best At | Availability |
|:--|:--|:--|:--|:--|:--|
| **Claude Haiku 4** | Anthropic | ~70B | $0.25 / $1.25 | Fast, cheap, great for routing | API (paid) |
| **GPT-4o-mini** | OpenAI | Undisclosed | $0.15 / $0.60 | Cheap GPT, great accuracy/cost | API (paid) + **GitHub Models (free!)** |
| **Gemini 3.5 Flash** | Google | Undisclosed | $0.075 / $0.30 | Ultra-fast, cheapest Google | API (free tier: 20/day 😢) |
| **Gemini 3.1 Flash-Lite** | Google | Undisclosed | $0.02 / $0.10 | High-volume, cost-sensitive | API |
| **Llama 3.3 70B** | Meta | 70B | $0.59 / $0.79 (Groq) | Best open-weight 70B, great reasoning | **Groq (free!), Ollama** |
| **Llama 4 Scout 17B** | Meta | 17B MoE | Free (self-host) | Efficient MoE, good quality | Ollama, Groq |
| **Mistral Medium** | Mistral | ~70B | $0.40 / $1.20 | Good multilingual, function calling | API |
| **Qwen 3 72B** | Alibaba | 72B | Free (self-host) | Strong coding, math, multilingual | Ollama |
| **DeepSeek R1** | DeepSeek | ~70B distill | $0.14 / $0.55 | Chain-of-thought reasoning | API + open-weight |

---

## 🟡 Small Tier (Fast + Cheap)

| Model | Provider | Params | Pricing (per 1M tokens) | Best At | Availability |
|:--|:--|:--|:--|:--|:--|
| **Llama 3.1 8B** | Meta | 8B | $0.05 / $0.08 (Groq) | Fast cloud inference, basic tasks | **Groq (free!)**, Ollama |
| **Gemma 4 E4B** | Google | 4B | $0.03 / $0.06 (equiv.) | Local inference, edge deployment | **Ollama (free!)** |
| **Gemma 3 4B** | Google | 4B | Free | Smaller, fits in 6GB VRAM | Ollama |
| **Mistral 7B** | Mistral | 7B | Free | Pioneer small model, still solid | Ollama, API |
| **Phi-4** | Microsoft | 14B | Free | Reasoning for its size, math | Ollama, GitHub Models |
| **Phi-4 Mini** | Microsoft | 3.8B | Free | Tiny but capable | Ollama |
| **Qwen 3 8B** | Alibaba | 8B | Free | Good multilingual small model | Ollama |
| **SmolLM 2** | HuggingFace | 1.7B | Free | Ultra-tiny, on-device | Ollama |

---

## 🟠 Specialized / Coding Models

| Model | Provider | Params | Best At | Availability |
|:--|:--|:--|:--|:--|
| **Claude Code** | Anthropic | Opus-based | Agentic coding, multi-file edits | API (paid) |
| **GPT-5.5 Codex** | OpenAI | Undisclosed | Code generation, debugging | API (paid) |
| **DeepSeek Coder V3** | DeepSeek | 236B MoE | Coding at fraction of cost | API + open-weight |
| **Qwen Coder 2.5** | Alibaba | 32B | Strong OSS coding model | Ollama |
| **StarCoder 2** | BigCode | 15B | Code completion, infilling | Open-weight |
| **MAI-Code-1-Flash** | Microsoft | Undisclosed | Fast code generation | GitHub Copilot |

---

## 🔴 Open-Weight Kings (Self-Host, No API Limits)

| Model | Provider | Params | VRAM Needed (Q4) | Run Via |
|:--|:--|:--|:--|:--|
| **Llama 4 Maverick** | Meta | 400B MoE | ~80GB+ | Multi-GPU only |
| **Llama 3.3 70B** | Meta | 70B | ~40GB | Cloud or multi-GPU |
| **Llama 4 Scout 17B** | Meta | 17B MoE | ~12GB | Ollama |
| **Llama 3.1 8B** | Meta | 8B | ~5GB | **Ollama** |
| **Qwen 3 72B** | Alibaba | 72B | ~40GB | Cloud |
| **Qwen 3 8B** | Alibaba | 8B | ~5GB | **Ollama** |
| **Gemma 4 E4B** | Google | 4B | ~2.5GB* | **Ollama** |
| **Mistral 7B** | Mistral | 7B | ~5GB | **Ollama** |
| **DeepSeek V3** | DeepSeek | 671B MoE | 100GB+ | Multi-GPU |
| **Phi-4** | Microsoft | 14B | ~8GB | Ollama |

*Gemma 4 E4B download is 9.6GB but quantized runs ~2.5GB per original spec (actual may vary)

---

## 📊 What WE Are Using in Our Research

| Our Tier | Model | Why This One |
|:--|:--|:--|
| 🟢 **Tier 1** (Cheap) | Gemma 4B (Ollama) | Free, local, no limits, 94.5% on GSM8K |
| 🔵 **Tier 2** (Medium) | Llama 70B (Groq) | Free API, fast, 96.0% on GSM8K |
| 🔴 **Tier 3** (Premium) | Llama 3.1 405B (GitHub) | Free via GitHub Models, **405B dense active parameters** (5.7× Llama 70B) |

### Why This Stack Works for the Paper

1. **Clear cost hierarchy:** $0.03 → $0.59 → $2.66 per 1M tokens (an **88× cost delta**)
2. **All free:** $0 total budget
3. **Reproducible:** Anyone can replicate with Ollama + Groq free tier + GitHub Models
4. **Credible names:** Google (Gemma) + Meta (Llama 3.3 70B) + Meta (Llama 3.1 405B)
5. **Diverse architectures:** Local small → Cloud large dense → Cloud frontier dense

> [!TIP]
> **For the paper, we write:** *"We evaluate across three model tiers spanning an 88× cost range: a local 4B parameter model (Gemma 4, Google), a cloud-hosted 70B dense model (Llama 3.3, Meta), and a frontier 405B dense model (Llama 3.1, Meta)."*
