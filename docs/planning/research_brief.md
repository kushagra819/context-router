# Research Brief: Context-Aware Compute Routing for Multi-Agent Systems

**Official Research Title (working):**  
*"Context-Aware Compute Routing for Multi-Agent LLM Systems: Leveraging Task Decomposition Signals for Cost-Efficient Inference"*

**Researcher:** Kushagra  
**Start Date:** June 1, 2026  
**End Date:** July 15–21, 2026  
**Target:** Conference paper  

---

## 1. THE PROBLEM — Why This Matters

### The Industry Reality (2026)

| Fact | Source |
|:-----|:-------|
| Average enterprise AI inference budget grew from **$1.2M → $7M** (2024→2026) | Gartner, industry reports |
| Inference accounts for **80-90%** of enterprise AI budgets | Industry surveys 2026 |
| Agentic workflows consume **5-30x more tokens** than simple chatbots | Anthropic, industry studies |
| **70%+ of agent sub-tasks** are simple enough for small models | RouteLLM findings, industry practice |
| Model routing can reduce costs by **30-70%** at scale | RouteLLM (ICLR 2025), BEST-Route (ICML 2025) |

### The Specific Gap

```
WHAT EXISTS:              WHAT'S MISSING:
─────────────             ──────────────
RouteLLM                  Multi-agent-aware routing
 → Routes SINGLE queries  → Nobody routes within 
 → Binary: strong/weak      multi-agent workflows
 → No task context         → Nobody uses task
                             decomposition signals
BEST-Route                → Nobody uses inter-agent
 → Adds sample count        dependency information
 → Still single query     → Nobody routes decomposed
                             sub-tasks differently
TAB                         than raw queries
 → Per-turn budgets
 → Single-agent only
 
DisCIPL
 → Planner + followers
 → Fixed 2-tier, not
   dynamic per sub-task
```

**Your research fills this gap.**

---

## 2. COMPLETE LITERATURE MAP

### Tier 1 — Direct Baselines (MUST READ DEEPLY)

These are the papers your work directly compares against. Read the full method sections.

---

#### Paper 1: RouteLLM ⭐ PRIMARY BASELINE

| Field | Detail |
|:------|:-------|
| **Title** | RouteLLM: Learning to Route LLMs with Preference Data |
| **Authors** | Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, et al. |
| **Venue** | ICLR 2025 |
| **arXiv** | [2406.18665](https://arxiv.org/abs/2406.18665) |
| **GitHub** | [lm-sys/RouteLLM](https://github.com/lm-sys/RouteLLM) |
| **What it does** | Routes single queries between strong/weak model using trained router (BERT, MF, or causal LLM classifier) |
| **Key result** | 2x+ cost reduction, maintains quality on MT-Bench, MMLU, GSM8K |
| **Limitation** | Binary routing only. Single query. No multi-agent awareness. No task decomposition context. |
| **What to extract** | Router architecture, evaluation methodology, cost metrics, threshold tuning |
| **Read time** | ~2 hours (full paper) |

---

#### Paper 2: BEST-Route

| Field | Detail |
|:------|:-------|
| **Title** | BEST-Route: Adaptive LLM Routing with Test-Time Optimal Compute |
| **Authors** | Ding, D., Mallick, A., Zhang, S., Wang, C., et al. |
| **Venue** | ICML 2025 |
| **arXiv** | [2506.22716](https://arxiv.org/abs/2506.22716) |
| **What it does** | Difficulty-aware routing that also decides how many responses to sample (best-of-n). Uses DeBERTa-v3-small as router. |
| **Key result** | Up to 60% cost reduction with <1% accuracy drop |
| **Limitation** | Single-query. Doesn't handle multi-agent collaboration context. |
| **What to extract** | Difficulty estimation method, DeBERTa router architecture, best-of-n strategy |
| **Read time** | ~1.5 hours |

---

#### Paper 3: DisCIPL

| Field | Detail |
|:------|:-------|
| **Title** | Self-Steering Language Models (DisCIPL) |
| **Authors** | Grand, G., Tenenbaum, J. B., Mansinghka, V. K., et al. |
| **Venue** | arXiv preprint, April 2025 |
| **arXiv** | [2504.07081](https://arxiv.org/abs/2504.07081) |
| **What it does** | A large Planner LM generates an "inference program" executed by smaller Follower LMs. Llama-3.2-1B matches GPT-4o on constrained tasks. |
| **Limitation** | Fixed 2-tier. Not dynamic per sub-task. Designed for constrained generation, not general agents. |
| **What to extract** | Planner-follower paradigm, cost comparison methodology |
| **Read time** | ~1 hour |

---

#### Paper 4: TAB (Turn-Adaptive Budgets)

| Field | Detail |
|:------|:-------|
| **Title** | Not All Turns Are Equally Hard: Adaptive Thinking Budgets For Efficient Multi-Turn Reasoning |
| **Authors** | Jali, N., Nayak, A., Joshi, G. |
| **Venue** | arXiv, April 2026 |
| **arXiv** | [2604.05164](https://arxiv.org/abs/2604.05164) |
| **What it does** | Models multi-turn reasoning as MDP. Allocates variable token budgets per turn. Saves 35-40% tokens. |
| **Limitation** | Single-agent. Per-turn compute, not per-agent or per-sub-task. |
| **What to extract** | MDP formulation, GRPO training, per-turn budget allocation idea |
| **Read time** | ~1 hour |

---

### Tier 2 — Compute Allocation & Efficiency

---

#### Paper 5: OSCA

| Field | Detail |
|:------|:-------|
| **Title** | Scaling LLM Inference Efficiently with Optimized Sample Compute Allocation |
| **Authors** | Zhang, K., Zhou, S., Wang, D., Wang, W. Y., Li, L. |
| **Venue** | NAACL 2025 |
| **What it does** | Learns optimal allocation of compute across configurations (models, temperatures, prompts). Hill-climbing algorithm. |
| **Key result** | 128x less compute on code gen, 3x less on SWE-Bench |
| **What to extract** | Mixed allocation strategy, optimization methodology |
| **Read time** | ~45 min (skim) |

---

#### Paper 6: Bayesian Orchestration of Multi-LLM Agents

| Field | Detail |
|:------|:-------|
| **Title** | Bayesian Orchestration of Multi-LLM Agents |
| **Venue** | arXiv, 2026 |
| **What it does** | Treats LLMs as approximate likelihood models. Sequential decisions based on expected cost and value-of-information. |
| **What to extract** | Cost-aware decision framework, Bayesian routing theory |
| **Read time** | ~45 min (skim) |

---

### Tier 3 — Multi-Agent Systems Foundations

---

#### Paper 7: Anthropic — Building Effective Agents ⭐ MUST READ

| Field | Detail |
|:------|:-------|
| **Title** | Building Effective Agents |
| **Author** | Anthropic Engineering Team |
| **URL** | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| **What it covers** | Production agent patterns: workflows vs agents, orchestrator-worker, evaluator-optimizer, specialization |
| **What to extract** | Orchestrator-worker pattern (your architecture), agent design principles |
| **Read time** | ~30 min |

---

#### Paper 8: Multi-Agent System Failure Taxonomy (MAST)

| Field | Detail |
|:------|:-------|
| **What it covers** | How multi-agent systems fail: specification ambiguity, coordination breakdown, verification gaps |
| **What to extract** | Failure categories — your routing system should reduce some of these failures |
| **Read time** | ~30 min (skim) |

---

### Tier 4 — Industry Context & Broader Landscape

---

#### Paper 9: AutoTool (2025)
- Tool usage inertia — sequential tool call patterns
- Shows agents follow predictable patterns (supports your sub-task classification idea)

#### Paper 10: COPE — Efficient LLM Collaboration via Planning
- arXiv: [2506.11578](https://arxiv.org/abs/2506.11578)  
- Planner-executor collaboration between small and large models

#### Paper 11: SATER — Unified Routing + Cascading Framework
- Integrates routing (upfront choice) and cascading (fallback) into single system

#### Paper 12: AB-MCTS — Adaptive Branching MCTS
- Decides "go wide" vs "go deep" for inference-time compute

---

## 3. YOUR RESEARCH — What Exactly Are You Doing?

### Research Question

> *"Can context-aware compute routing — where a router leverages multi-agent task decomposition signals (sub-task type, dependencies, upstream agent outputs, expected output complexity) — reduce inference costs by 40-60% while maintaining task accuracy in collaborative agent workflows?"*

### Your Novel Contribution

You are building **the first compute routing system designed specifically for multi-agent workflows.** Existing routers see a raw query and decide "big model or small model." YOUR router sees:

```
STANDARD ROUTER INPUT:          YOUR ROUTER INPUT:
─────────────────────           ──────────────────
"Summarize the legal            Sub-task #3 of 5
 Document and find              Type: data_extraction
 liability issues"              Depends on: sub-task #1 (completed)
                                Upstream output: 2KB structured JSON
 → Hard to classify             Expected output: list of strings
 → Sends to GPT-4o              Agent: DataAgent
 → Costs $0.05                  Previous similar sub-tasks: 12
                                 (all succeeded on small model)
                                
                                 → Clearly easy
                                 → Sends to Llama-8B
                                 → Costs $0.0001
```

### The 5 Key Signals Your Router Uses

| Signal | What It Is | Why It Helps |
|:-------|:-----------|:-------------|
| **Sub-task type** | Category assigned by orchestrator (extraction, reasoning, synthesis, validation) | "Extraction" is almost always easy |
| **Dependency status** | Which upstream sub-tasks are done, what they produced | If hard reasoning is already done upstream, downstream tasks are easier |
| **Expected output format** | List, JSON, paragraph, code, boolean | Structured outputs are easier for small models |
| **Historical success** | Did similar sub-tasks succeed on small model before? | Past success predicts future success |
| **Complexity estimate** | Orchestrator's assessment of sub-task difficulty | Rough but useful signal |

### System Architecture

```
                      ┌──────────────────────┐
                      │     USER TASK         │
                      │  "Research and write  │
                      │   a report on X"      │
                      └──────────┬───────────┘
                                 │
                      ┌──────────▼───────────┐
                      │    ORCHESTRATOR       │
                      │  (always frontier     │
                      │   model — GPT-4o)     │
                      │                       │
                      │  Decomposes into      │
                      │  sub-tasks with       │
                      │  metadata:            │
                      │  • type               │
                      │  • dependencies       │
                      │  • expected_output    │
                      │  • complexity_hint    │
                      └──────────┬───────────┘
                                 │
               ┌─────────────────▼─────────────────┐
               │         CONTEXT-AWARE ROUTER       │
               │                                     │
               │  Input: sub-task + all 5 signals    │
               │                                     │
               │  Decision:                          │
               │  ┌─────────────┐ ┌──────────────┐  │
               │  │  SMALL TIER  │ │ FRONTIER TIER│  │
               │  │  Llama 8B    │ │ GPT-4o-mini  │  │
               │  │  (Yotta GPU) │ │ (API)        │  │
               │  │  Cost: ~$0   │ │ Cost: $0.15/ │  │
               │  │              │ │  1M tokens   │  │
               │  └──────┬──────┘ └──────┬───────┘  │
               │         │               │           │
               │  ┌──────▼───────────────▼───────┐  │
               │  │     CASCADE HANDLER           │  │
               │  │  If small model confidence    │  │
               │  │  < threshold → escalate       │  │
               │  └──────────────────────────────┘  │
               └────────────────┬───────────────────┘
                                │
               ┌────────────────▼───────────────────┐
               │          AGENT TEAM                 │
               │                                     │
               │  ┌────────┐ ┌────────┐ ┌────────┐  │
               │  │Research │ │ Code   │ │ Data   │  │
               │  │Agent    │ │ Agent  │ │ Agent  │  │
               │  └────────┘ └────────┘ └────────┘  │
               │                                     │
               │  Each executes its routed sub-task  │
               │  using the MODEL assigned by router │
               └────────────────┬───────────────────┘
                                │
               ┌────────────────▼───────────────────┐
               │         COST TRACKER                │
               │  Logs: model used, tokens in/out,   │
               │  cost ($), latency, success/fail,   │
               │  cascade events                     │
               └────────────────────────────────────┘
```

### 5 Experiments

| # | Experiment | Baseline | Your System | What It Proves |
|:--|:-----------|:---------|:------------|:---------------|
| **E1** | Cost comparison | All-frontier (everything to GPT-4o-mini) | Context-aware router | Your system saves X% cost |
| **E2** | Accuracy preservation | All-frontier | Context-aware router | Quality doesn't drop |
| **E3** | Router comparison | RouteLLM (single-query router) applied to same tasks | Context-aware router | Multi-agent context improves routing |
| **E4** | Ablation | Remove each signal one at a time | Full router | Which signals matter most |
| **E5** | Cascade analysis | Direct routing (no cascade) | Router + cascade | Cascade overhead is justified |

### How To Defend Against Reviewers

| Reviewer Attack | Your Defense |
|:---|:---|
| *"RouteLLM already does this"* | RouteLLM routes single queries. We route decomposed sub-tasks using 5 multi-agent context signals. Table X shows our router makes different (better) decisions than RouteLLM on the same sub-tasks. |
| *"Difficulty classification is unreliable"* | We don't classify raw queries — we classify orchestrator-decomposed sub-tasks with type, dependency, and output format metadata. Table Y shows classification accuracy of Z%. Plus cascade mechanism catches errors. |
| *"What if cascade costs negate savings?"* | Experiment E5 shows cascade rate is only X%. Even accounting for cascade overhead, total savings are Y%. |
| *"Results are model-pair specific"* | We test 2 model pairs (Llama-8B/GPT-4o-mini and Mistral-7B/GPT-4o-mini) and show consistent savings across both. |

---

## 4. WHAT TO DO RIGHT NOW (May 30-31)

### Today (May 30) — Read Core Papers

| Priority | Paper | What to Read | Time |
|:---------|:------|:-------------|:-----|
| 🔴 P0 | **Anthropic: Building Effective Agents** | Full blog post | 30 min |
| 🔴 P0 | **RouteLLM** (arXiv:2406.18665) | Abstract + Section 3 (Method) + Section 4 (Experiments) | 90 min |
| 🟡 P1 | **BEST-Route** (arXiv:2506.22716) | Abstract + Method section | 45 min |
| 🟡 P1 | **DisCIPL** (arXiv:2504.07081) | Abstract + Section 2 | 30 min |

### Tomorrow (May 31) — Read Supporting Papers + Prep

| Priority | Paper | What to Read | Time |
|:---------|:------|:-------------|:-----|
| 🟡 P1 | **TAB** (arXiv:2604.05164) | Abstract + Method | 30 min |
| 🟢 P2 | **OSCA** (NAACL 2025) | Abstract + Results | 20 min |
| ✅ | **Write 1-paragraph pitch** for your mentor | | 15 min |
| ✅ | **Confirm topic** with mentor | | |

### Mentor Pitch (copy-paste ready)

> *"I'm proposing research on **cost-efficient inference routing for multi-agent LLM systems.** Current model routers like RouteLLM (ICLR 2025) only handle single queries, but multi-agent workflows decompose tasks into sub-tasks with rich metadata — type, dependencies, expected outputs — that can be used to make smarter routing decisions. I'll build a context-aware router that uses these signals to route sub-tasks to appropriately-sized models (small local models for easy sub-tasks, frontier APIs for hard ones), with a cascade mechanism for safety. The goal is 40-60% inference cost reduction while maintaining accuracy. This is a hot problem — enterprise AI inference budgets have grown to $7M average and agents use 5-30x more tokens than chatbots."*

---

## 5. JUNE 1 — What I'll Set Up For You

When you confirm you've read the papers and are ready:

1. **Project directory structure** in `c:\Users\Kumud\Desktop\Research\`
2. **Python project scaffold** — `pyproject.toml`, requirements, module structure
3. **LangGraph multi-agent prototype** — basic orchestrator + 2 agents
4. **Router module** — pluggable router with baseline (random, always-frontier) + your context-aware router
5. **Cost tracker** — logs every LLM call with model, tokens, cost
6. **Week-by-week task tracker** — execution roadmap

---

> [!TIP]
> **Your reading priority for tonight:**
> 1. Anthropic blog (30 min) — gives you the big picture of agent architecture
> 2. RouteLLM paper (90 min) — your primary baseline, understand it deeply
> 
> Everything else can wait until tomorrow. Start with these two.
