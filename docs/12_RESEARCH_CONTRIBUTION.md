# Research Contribution Statement

## 1. Title
**Context-Aware LLM Routing for Multi-Agent AI Systems**

## 2. One-Sentence Summary
We propose the first context-aware routing framework that makes per-agent model-tier decisions within multi-agent workflows, using workflow signals (agent role, upstream confidence, task complexity) to optimize the quality-cost tradeoff.

## 3. Contributions

### Primary Contribution
**Per-Agent Routing in Multi-Agent Pipelines.** We demonstrate that in a multi-agent workflow (Analyzer → Solver → Verifier), each agent has different capability requirements. By routing each agent to the appropriate model tier independently, we achieve comparable quality to always using the frontier model while significantly reducing cost.

### Secondary Contributions
1. **Workflow-Aware Routing Signals.** We introduce novel routing signals: agent role, workflow stage, and upstream confidence — signals that are unavailable in single-agent routing systems.

2. **Comprehensive Baseline Study.** We provide a systematic evaluation of a 4-tier LLM hierarchy (4B to GPT-4.1) across 3 standard benchmarks (GSM8K, HotpotQA, MuSiQue) with a 3-agent pipeline, producing 12 complete baseline configurations.

3. **Cost-Quality Pareto Analysis.** We map the Pareto frontier of quality vs. cost across routing strategies, showing where mixed-tier pipelines create new operating points unachievable by single-tier baselines.

4. **Signal Ablation Study.** We quantify the impact of each routing signal (agent role, complexity, confidence, cost budget) through systematic ablation.

## 4. Novelty Argument

| Claim | Evidence |
|-------|---------|
| No prior work routes per-agent in multi-agent pipelines | Literature survey of FrugalGPT, RouteLLM, AutoMix, Hybrid LLM, EcoAssistant — all single-agent |
| Agent role is a useful routing signal | Ablation shows removing role signal degrades quality by X% |
| Upstream confidence improves routing | Cascading router outperforms complexity-only router |
| Mixed-tier pipelines create new Pareto-optimal points | Pareto plot shows router points above single-tier line |

## 5. Positioning

### What This Paper Is
- A routing framework for multi-agent LLM systems
- An empirical study on per-agent model selection
- A practical contribution to cost-efficient AI deployment

### What This Paper Is NOT
- Not a new multi-agent architecture (we use standard Analyzer→Solver→Verifier)
- Not a new LLM (we use existing models)
- Not a theoretical paper (empirical focus)

## 6. Publication Targets (Discussion)

| Venue | Fit | Notes |
|-------|:---:|-------|
| EMNLP / ACL Workshop | High | NLP community, multi-agent track |
| NeurIPS Efficient ML Workshop | High | Cost-efficiency focus |
| AAAI | Medium | Broader AI venue |
| IEEE/ACM Conference | Medium | Systems-oriented angle |
| arXiv preprint | High | For visibility while targeting venue |

## 7. Related Work Positioning

```
                    Single-Agent              Multi-Agent
                 ┌────────────────┐      ┌────────────────┐
  Per-Query      │  FrugalGPT     │      │                │
  Routing        │  RouteLLM      │      │   (No prior    │
                 │  AutoMix       │      │    work)       │
                 │  Hybrid LLM    │      │                │
                 └────────────────┘      └────────────────┘
                                                  ↑
                                          OUR CONTRIBUTION
                 ┌────────────────┐      ┌────────────────┐
  Per-Agent      │  (Not          │      │  Context-Aware │
  Routing        │   applicable)  │      │  Multi-Agent   │
                 │                │      │  Router        │
                 └────────────────┘      └────────────────┘
```
