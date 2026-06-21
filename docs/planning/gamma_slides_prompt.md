# Gamma AI Prompt — 8 Slides

---

## MASTER PROMPT (paste this first into Gamma)

Create an 8-slide research presentation with the following settings:
- **Title:** "Context-Aware LLM Routing for Multi-Agent AI Systems"
- **Theme:** Dark modern (dark navy/charcoal background, white text)
- **Accent colors:** Purple (#6c63ff), Teal (#2ed8a3), Pink (#f472b6), Gold (#fbbf24)
- **Font:** Clean sans-serif (Inter, Jakarta Sans, or similar)
- **Layout:** Landscape 16:9
- **Tone:** Academic but accessible. Faculty research presentation for engineering students.
- **Style:** Professional, data-driven, minimal blank space. Use cards, tables, and icons generously. Every slide should feel full and informative, not sparse.

---

## SLIDE 1 — TITLE / COVER (Siddharth)

**Layout:** Centered. Large title in gradient purple-blue. Subtitle below. Team names at bottom.

**Content:**

Title: **Context-Aware LLM Routing for Multi-Agent AI Systems**

Subtitle: Intelligent per-subtask model selection to reduce inference cost while maintaining output quality in multi-agent workflows

Team:
- Kushagra Mehta · Siddharth Maru · Tanmay Ahuja
- Under the guidance of Dr. Himani Deshpande
- Thadomal Shahani Engineering College
- Research Internship · June 2026

---

## SLIDE 2 — INTRODUCTION & PROBLEM (Siddharth)

**Layout:** Title at top. One paragraph of intro text. A side-by-side comparison box (❌ vs ✅). Three stat cards at bottom.

**Heading:** The Problem: Wasted Inference Budget

**Intro paragraph:**
Multi-agent AI systems are teams of specialized AI agents — each with a role like researcher, coder, or writer — that collaborate to solve complex tasks. Each agent uses a Large Language Model (LLM) to process its subtasks. 

**The problem:** In today's systems, every subtask gets sent to the same expensive LLM (like GPT-4o), even when the task is simple — a data lookup, a reformatting, a basic summary. This "one-model-fits-all" approach wastes compute, money, and energy. Research shows ~70% of subtasks are simple enough for smaller, cheaper models.

**Our solution:** A Context-Aware Router that dynamically picks the right-sized model for each subtask. Simple tasks → small free local model. Complex tasks → expensive frontier model. Only the hard parts use the big models.

**Side-by-side comparison (two cards):**

| ❌ Current: One-Model-Fits-All | ✅ Ours: Context-Aware Routing |
|---|---|
| Data lookup → GPT-4o ($$$) | Data lookup → Llama-8B (free, local) |
| Formatting → GPT-4o ($$$) | Formatting → Llama-8B (free, local) |
| Complex reasoning → GPT-4o ($$$) | Complex reasoning → GPT-4o ($$) |
| **Every subtask → same expensive model** | **Right model for each subtask** |

**Three stat cards at bottom (side by side):**

| **52%** cost reduction | **3.66×** cost savings | **31%** less energy |
|---|---|---|
| MasRouter, ACL 2025 — on HumanEval benchmark | RouteLLM, ICLR 2025 — on MT-Bench | GreenServ, arXiv 2026 — vs random routing |

---

## SLIDE 3 — HOW ROUTING WORKS (Siddharth)

**Layout:** Title at top. Two-column comparison. Left = existing approach. Right = our approach. Use the generated routing comparison diagram image if possible, otherwise recreate from description below.

**Heading:** Core Concept: How LLM Routing Works

**Left column — "Existing: Single-Query Routing"**

Existing papers like RouteLLM (ICLR 2025) and BEST-Route (ICML 2025) analyze one user query at a time and use a classifier (BERT or DeBERTa) to decide: send this query to the strong expensive model, or the weak cheap model.

Flow: `User Query → Router (BERT classifier) → Strong Model OR Weak Model`

⚠️ **Limitation:** Only sees raw query text. No awareness of the broader workflow, what agent is handling it, what happened in previous steps, or task dependencies.

**Right column — "Ours: Multi-Agent Context-Aware Routing ⭐"**

Our router sits INSIDE the multi-agent workflow. Before deciding which model to use, it reads 4 context signals that single-query routers don't have access to:

| Signal | What It Tells the Router |
|---|---|
| **1. Task Type** | Is this subtask extraction, reasoning, synthesis, or formatting? Simple types → small model is fine. |
| **2. Agent Role** | Which agent is handling this? A DataResearcher agent handles simpler queries than a CodeWriter agent. |
| **3. Upstream Output** | Was the previous step's output high-quality? If the research was done well, the writing step is easier. |
| **4. Complexity Score** | Estimated difficulty — can be rule-based (keywords/length) or learned via a multi-armed bandit that improves over time. |

Based on these signals, the router selects from **3 model tiers:**
- 🟢 **Tier 1:** Local Llama 8B Q4 via Ollama (free, runs on laptop)
- 🔵 **Tier 2:** GPT-4o-mini via API ($0.15 per 1M tokens — cheap)
- 🔴 **Tier 3:** GPT-4o via API (frontier, expensive — only for complex tasks)

**Bottom callout:**
Key Insight from MasRouter (ACL 2025): Multi-agent routing requires jointly deciding three things: (1) collaboration mode (chain vs tree), (2) role allocation, and (3) LLM routing. Our system addresses all three using context signals.

---

## SLIDE 4 — SYSTEM ARCHITECTURE (Kushagra)

**Layout:** Title at top. Full-width architecture diagram image below. Use the generated blueprint-style architecture diagram.

**Heading:** System Architecture: The Context-Aware Blueprint

**Diagram description (for reference — use the generated image):**

Horizontal flow, left to right:
1. **User Query** → sends task to
2. **Frontier Planning Model** (orchestrator, always uses GPT-4o) → decomposes into subtasks with metadata (type, role, dependencies) →
3. **Context-Aware Router** (central decision node, teal colored) — receives 4 signal inputs: Task Type (top-left), Agent Role (top-right), History (bottom-left), Complexity (bottom-right) →
4. **Parallel Agent Execution zone** — contains 5 agent task boxes on different model tiers:
   - Agent Task 1 (Small Model), Agent Task 2 (Medium Model)
   - Agent Task 3 (Specialized Model)
   - Agent Task 4 (Medium Model), Agent Task 5 (Small Model)
5. All agent outputs → **Aggregated Output** (orange box)

**Cascade Fallback:** Dotted red arrow going FROM the agent tasks BACK TO the router. Meaning: if a small model produces poor output, the router re-assigns the task to a bigger model. Direction: right-to-left (agents → router).

**Design Highlights legend (bottom-right):**
- 🔵 Strategic Frontier Usage: GPT-4o is reserved strictly for high-level planning
- 🟢 Signal-Driven Routing: Subtasks are dynamically assigned via the 4 context signals
- 🔴 Cascade Fallback: If a smaller model fails, it seamlessly cascades to a larger model
- 🟠 Parallel Execution: Non-dependent agent tasks are executed simultaneously to cut latency

---

## SLIDE 5 — RELATED RESEARCH (Kushagra)

**Layout:** Title at top. Two-column grid of paper cards. Each card has: venue tag (colored badge), paper title (bold), and 2-3 line summary with key stat highlighted. Bottom has an "Our Contribution" callout box.

**Heading:** Literature Survey — 7 Research Papers

**Column 1:**

**[ACL 2025] MasRouter** — Learning to Route LLMs for Multi-Agent Systems
arXiv:2502.11133
Formalizes the Multi-Agent System Routing (MASR) problem — jointly deciding collaboration mode (chain/tree/star), role allocation, and per-agent LLM selection using a cascaded controller network. Achieved **52% cost reduction** on HumanEval and 1.8–8.2% accuracy gain on MBPP coding tasks. This is the most directly related paper to our work.

**[ICLR 2025] RouteLLM** — Learning to Route LLMs with Preference Data
arXiv:2406.18665
Pioneered single-query LLM routing using preference-trained classifiers. A BERT-based model scores whether a query needs a strong or weak LLM, achieving up to **3.66× cost savings** (85% reduction on MT-Bench, 45% on MMLU). Major limitation: only sees individual queries, no multi-agent workflow context.

**[ICML 2025] BEST-Route** — Adaptive Routing with Test-Time Optimal Compute
arXiv:2506.22716
Extends single-query routing with a DeBERTa-based difficulty estimator combined with best-of-n sampling. Achieves **60% cost reduction with less than 1% accuracy drop**. Demonstrates that routing can save money without sacrificing quality, but still limited to individual queries.

**[arXiv 2026] GreenServ** — Energy-Efficient Context-Aware Dynamic Routing
arXiv:2601.17551
Uses a contextual multi-armed bandit algorithm to learn which LLM performs best for different query types over time. Achieved **22% higher accuracy and 31% lower energy consumption** compared to random routing. Demonstrates near Pareto-optimal accuracy-energy tradeoffs.

**Column 2:**

**[arXiv 2025] RCR-Router** — Role-Aware Context Routing for Multi-Agent LLM Systems
arXiv:2508.04903
Introduces role-aware context routing specifically for multi-agent systems. Uses structured memory and dynamically routes semantically relevant memory subsets to agents based on their role and task stage. Achieves **30% token reduction** on HotPotQA and MuSiQue benchmarks while maintaining performance.

**[ICLR 2025] GraphRouter** — A Graph-based Router for LLM Selections
Represents the relationships between tasks, queries, and LLMs as a heterogeneous graph. Uses inductive edge prediction to estimate which model is optimal for a given query. Shows **12.3%+ improvement** over baselines and can generalize to new LLMs without full retraining.

**[arXiv 2025] MoMA** — Mixture of Models and Agents
arXiv:2509.07571
A framework for jointly routing queries to both LLMs and domain-specific AI agents. Uses precise intent recognition and a context-aware state machine with dynamic masking for Pareto-efficient orchestration of heterogeneous execution units.

**Bottom callout box (purple border):**
**Our Research Gap:** Existing routers are either single-query (RouteLLM, BEST-Route) or multi-agent but without workflow history awareness (MasRouter). Our work extends MasRouter by adding upstream output quality signals, dependency graph awareness, and adaptive feedback loops — enabling truly context-aware per-subtask model selection.

---

## SLIDE 6 — DATASETS & BENCHMARKS (Tanmay)

**Layout:** Title at top. Full-width table. Metrics callout box at bottom.

**Heading:** Datasets & Benchmarks for Evaluation

**Intro line:** All datasets are publicly available and free via HuggingFace and GitHub. We prioritize multi-step, multi-agent evaluation tasks.

**Table (7 rows):**

| Dataset | Size | Task Type & Features | Used By |
|---|---|---|---|
| **AgentBench** | ~1,014 test tasks | 8 diverse environments: OS shell commands, Database queries, Knowledge Graph QA, Digital card games, Lateral puzzles, ALFWorld house tasks, WebShop, Mind2Web browsing. Multi-turn agent evaluation. | ICLR 2024 |
| **RouterBench** | 405,467 outcomes | 64 tasks across 8 datasets. Contains cost-quality tradeoff data and routing outcomes from 11 different LLMs. Standard benchmark for routing evaluation. | RouteLLM (ICLR 2025) |
| **HumanEval + MBPP** | 164 + 974 tasks | Python code generation with automated test cases. Natural fit for multi-agent pipelines: planner agent → coder agent → verifier agent. | MasRouter (ACL 2025) |
| **MMLU** | 15,908 questions | 57 academic subjects spanning STEM, humanities, and social sciences. Multiple-choice knowledge and reasoning test. | RouteLLM, BEST-Route |
| **GSM8K** | 8,500 problems | Grade-school math word problems requiring multi-step reasoning and calculation. Tests step-by-step logic chains. | BEST-Route |
| **HotPotQA** | 113,000 pairs | Multi-hop reasoning QA requiring retrieval and synthesis across multiple Wikipedia documents. Tests 2-hop reasoning. | RCR-Router |
| **MT-Bench** | 80 prompts | Multi-turn conversations across 10 domains (writing, math, coding, reasoning). Scored by LLM-as-judge system. | RouteLLM |

**Bottom callout box:**
📏 **Evaluation Metrics:** Output accuracy (Exact Match, F1, pass@1) · Total inference cost (tokens consumed, dollars spent) · Latency per query (milliseconds) · Model utilization distribution (% of tasks per tier) · Quality-vs-cost Pareto curves · Energy consumption

---

## SLIDE 7 — TECH STACK & EXPECTED OUTCOMES (Tanmay)

**Layout:** Two-column. Left = tech stack (use generated tech stack diagram image or recreate as layered blocks). Right = three stat cards at top + bullet list of deliverables below.

**Heading:** Implementation & Expected Outcomes

**Left side — Technology Stack (4 layers, top to bottom):**

| Layer | Components |
|---|---|
| **Orchestration** | LangGraph (graph-based workflow — each node is an agent, edges are control flow) + CrewAI (role-based agent orchestration with YAML config) |
| **Routing Engine** | BERT/DeBERTa classifier trained on subtask difficulty labels + rule-based heuristics as fallback |
| **Model Pool** | 🟢 Tier 1: Ollama serving Llama 3.1 8B Q4 locally (free, ~4.5GB VRAM) · 🔵 Tier 2: GPT-4o-mini via API ($0.15/1M tokens) · 🔴 Tier 3: GPT-4o via API (frontier, expensive) |
| **Infrastructure** | Python 3.11+ · Weights & Biases or MLflow for experiment tracking · RTX 4050 Laptop (6GB VRAM) |

**Green callout:** ✅ Entire system runs on a laptop with RTX 4050 (6GB VRAM). Ollama serves quantized 8B models locally (~4.5GB fits). Frontier API calls only when the router decides a subtask is truly complex. No cloud GPU required.

**Right side — Expected Outcomes:**

Three stat cards:
| **30–52%** | **<5%** | **100%** |
|---|---|---|
| Inference cost reduction | Accuracy drop tolerance | Open-source tools |
| (MasRouter achieved 52% on HumanEval) | (BEST-Route showed <1% drop at 60% savings) | (LangGraph + Ollama + Python) |

Key deliverables:
- Extends MasRouter (ACL 2025) with workflow context signals — history, dependencies, upstream output quality
- Integrates insights from RouteLLM, GreenServ, RCR-Router into multi-agent routing
- Cascade fallback mechanism — if a small model produces poor output, auto-escalate to a larger model. Quality is never compromised.
- Evaluated comprehensively on 7 public benchmarks: AgentBench, HumanEval/MBPP, MMLU, GSM8K, HotPotQA, MT-Bench, RouterBench
- Conference paper submission target: mid-July 2026

---

## SLIDE 8 — THANK YOU (Tanmay)

**Layout:** Centered. Large "Thank You" title. Team names. References in small text at bottom.

**Title:** Thank You

**Subtitle:** Questions & Discussion

**Team:**
Kushagra Mehta · Siddharth Maru · Tanmay Ahuja
Under the guidance of Dr. Himani Deshpande
Thadomal Shahani Engineering College

**References (small, bottom):**
MasRouter (ACL 2025, arXiv:2502.11133) · RouteLLM (ICLR 2025, arXiv:2406.18665) · BEST-Route (ICML 2025, arXiv:2506.22716) · GreenServ (arXiv:2601.17551) · RCR-Router (arXiv:2508.04903) · GraphRouter (ICLR 2025) · MoMA (arXiv:2509.07571) · AgentBench (ICLR 2024, arXiv:2308.03688)

---

## GENERATED DIAGRAM IMAGES (use these in slides 3, 4, 7)

The following diagram images have been generated and saved. Upload them to Gamma when creating slides 3, 4, and 7:

1. **Architecture Blueprint** (Slide 4) — Horizontal flow diagram with cascade fallback
2. **Routing Comparison** (Slide 3) — Single-query vs multi-agent side-by-side
3. **Tech Stack** (Slide 7) — 4-layer stack diagram
