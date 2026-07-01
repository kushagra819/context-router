# Research Gap Analysis

## 1. What Existing Papers Do

### 1.1 LLM Routing / Model Selection

| Paper | Year | Approach | Routing Signal | Limitation |
|-------|:----:|----------|----------------|------------|
| **FrugalGPT** (Chen et al.) | 2023 | Sequential cascading through LLMs | Query difficulty, prior model responses | Single-agent; no pipeline awareness |
| **RouteLLM** (Ong et al.) | 2024 | Trained classifier for binary routing | Prompt features | Only 2 tiers (strong/weak); no workflow context |
| **AutoMix** (Aggarwal et al.) | 2024 | Self-verification then escalation | Model confidence | Single-agent; does not consider agent roles |
| **Hybrid LLM** (Ding et al.) | 2024 | Quality-aware binary routing | Predicted quality | Binary routing only; no multi-step reasoning |
| **EcoAssistant** (Zhang et al.) | 2023 | Cost-aware code generation routing | Past success rate | Domain-specific (code); not generalizable |

### 1.2 Multi-Agent Systems

| Paper | Year | Approach | Limitation for Routing |
|-------|:----:|----------|----------------------|
| **AutoGen** (Wu et al.) | 2023 | Multi-agent conversation framework | No model routing — all agents use same model |
| **MetaGPT** (Hong et al.) | 2023 | Role-based multi-agent software dev | Fixed model per role, no adaptive routing |
| **LLM-Blender** (Jiang et al.) | 2023 | Ensemble multiple LLM outputs | Not routing — ensembling (higher cost) |
| **MasRouter** (Yue et al.) | 2025 | Routes the *multi-agent system itself* (which agents/roles/LLMs to assemble per query) | Routes at the **query→system** level; once the system is chosen, agents are not re-routed *per call* using **upstream output/confidence**. Closest prior work — see §2. |

> **MasRouter is the nearest neighbour.** It selects, per query, a multi-agent configuration
> (collaboration mode, number of agents/roles, and an LLM per role) via a cascaded controller.
> Our work is orthogonal and finer-grained: given a *fixed* pipeline (Analyzer→Solver→Verifier),
> we re-route **each agent call at run time** using signals that only become available *during*
> execution — the **upstream agent's output and confidence** and the **workflow stage** — not
> just the query. The two are composable (MasRouter picks the team; we right-size each member's
> model mid-workflow).

## 2. What Existing Papers Do NOT Do

1. **No per-agent routing in multi-agent pipelines.** Every existing router treats each query as a single routing decision. None consider that a query passes through multiple agents (Analyzer → Solver → Verifier) where each agent has different capability requirements.

2. **No workflow-stage awareness.** Existing routers don't know whether they're routing for decomposition, solving, or verification. Stage context is discarded.

3. **No upstream-confidence signal.** Existing cascading approaches (FrugalGPT, AutoMix) escalate based on the current model's confidence — not based on how well the previous agent performed.

4. **No per-agent cost optimization.** Current approaches optimize total cost per query, not cost allocation across agents within a pipeline.

5. **No mixed-tier pipelines.** All multi-agent systems use the same model tier for every agent. No system routes each agent to a different tier based on the agent's role.

## 3. The Research Gap

> **Gap:** There is no existing work on context-aware LLM routing within multi-agent workflows where the routing decision is informed by the agent's role, workflow stage, upstream output quality, and task complexity.

This gap exists because:
- LLM routing research focuses on single-turn query→response paradigms
- Multi-agent research focuses on architecture/communication, not model selection
- The intersection — routing within multi-agent workflows — is unexplored

## 4. Our Proposed Contribution

### Primary Innovation: Workflow-Aware Multi-Agent Routing

We propose a **context-aware router** that makes per-agent tier decisions within a multi-agent pipeline, using signals from the workflow itself:

| Signal | Description | Novel? |
|--------|-------------|:------:|
| **Agent Role** | Analyzer/Solver/Verifier have different capability needs | ✅ Yes |
| **Task Complexity** | Question features (length, entities, hops) | Exists in RouteLLM |
| **Upstream Confidence** | Quality/uncertainty of previous agent's output | ✅ Yes |
| **Cost Budget** | Remaining budget for this query | Exists in FrugalGPT |
| **Workflow Stage** | Position in the pipeline (early/mid/late) | ✅ Yes |

### Secondary Innovations (to explore)

1. **Dynamic Pipeline Depth:** Skip agents for simple queries (solver-only for easy questions, full pipeline for hard ones)
2. **Signal Ablation Study:** Quantify which routing signals matter most
3. **Cost-Quality Pareto Analysis:** Map the optimal operating points across tier configurations
4. **Learned Router from Baseline Features:** Train a lightweight classifier using baseline CSV features

## 5. Why It Matters

1. **Cost efficiency:** Not all agents need the strongest model. The verifier (which just checks answers) can often use a cheap model.
2. **Latency:** Using local/fast models for simple sub-tasks reduces end-to-end latency.
3. **Scalability:** As multi-agent systems become standard, per-agent routing becomes critical for deployment.
4. **Research precedent:** Opens a new direction connecting LLM routing and multi-agent systems.

## 6. How It Will Be Proven

| Claim | Evidence |
|-------|---------|
| Mixed-tier pipelines can match full-tier quality | Compare EM/F1 of routed vs baseline experiments |
| Cost savings are significant | Show cost reduction on Pareto frontier |
| Per-agent signals improve routing | Ablation study removing signals one by one |
| The approach generalizes across tasks | Test on GSM8K (math), HotpotQA (2-hop QA), MuSiQue (multi-hop QA) |

## 7. Key References

1. Chen, L., et al. "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance." arXiv:2305.05176 (2023).
2. Ong, I., et al. "RouteLLM: Learning to Route LLMs with Preference Data." arXiv:2406.18665 (2024).
3. Aggarwal, P., et al. "AutoMix: Automatically Mixing Language Models." arXiv:2310.12963 (2024).
4. Ding, D., et al. "Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing." arXiv:2404.14618 (2024).
5. Wu, Q., et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." arXiv:2308.08155 (2023).
6. Yue, et al. "MasRouter: Learning to Route LLMs for Multi-Agent Systems." arXiv:2502.11133 (2025). *(Closest prior work; routes the system per query, not each agent per call.)*
7. Hong, S., et al. "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework." arXiv:2308.00352 (2023).
