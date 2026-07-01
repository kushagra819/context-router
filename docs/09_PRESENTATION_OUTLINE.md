# Presentation Outline

> **Audience:** Professor / Dean / Review Committee
> **Duration:** 15-20 minutes + Q&A
> **Goal:** Demonstrate research novelty, methodology rigor, and practical impact

---

## Slide 1: Title
**Context-Aware LLM Routing for Multi-Agent AI Systems**
- Name, Institution, Date
- "Workflow-aware model selection for cost-efficient multi-agent reasoning"

## Slide 2: The Problem
- LLMs vary in cost by 100× (Gemma 4B → GPT-4.1)
- Multi-agent systems use the SAME expensive model for every agent
- Not all agents need the strongest model
- **Research question:** Can we route each agent to the right model tier?

## Slide 3: Background — LLM Routing
- FrugalGPT, RouteLLM, AutoMix: route based on query difficulty
- All treat routing as a single per-query decision
- None consider multi-agent pipelines or agent roles

## Slide 4: The Gap
- **No existing work** on routing within multi-agent workflows
- Agent roles (Analyzer/Solver/Verifier) have different capability needs
- Workflow signals (upstream confidence, stage) are untapped

## Slide 5: Our Approach
- Context-aware router that makes **per-agent tier decisions**
- Diagram: Question → [Router→Analyzer] → [Router→Solver] → [Router→Verifier]
- Signals: agent role, task complexity, upstream confidence, cost budget

## Slide 6: Experimental Setup
- 4-tier model hierarchy (4B → 70B → 405B → GPT-4.1)
- 3 datasets: GSM8K, HotpotQA, MuSiQue
- 3-agent pipeline: Analyzer → Solver → Verifier
- 200 problems per tier per dataset

## Slide 7: Baseline Results
- Table: Tier × Dataset → EM/Accuracy + Cost
- Key insight: performance plateaus but cost doesn't
- Highlight: Tier 2 gets 96% on GSM8K at 1/5th the cost of Tier 4

## Slide 8: Router Variants
- Oracle (upper bound), Random (lower bound), Fixed Mixed
- Complexity-based, Confidence Cascading, Adaptive Mixed-Tier
- Show the spectrum from simple to sophisticated

## Slide 9: Main Results
- Comparison table: Router vs Baselines
- Pareto frontier plot: Quality vs Cost
- Key finding: X% cost savings with Y% quality retention

## Slide 10: Ablation Study
- Which signals matter most?
- Bar chart: EM change when removing each signal
- Agent role signal is most impactful (hypothesis)

## Slide 11: Analysis
- When does routing help most? (complex questions)
- When does it hurt? (edge cases)
- Per-dataset breakdown

## Slide 12: Broader Impact
- Multi-agent systems are becoming standard (AutoGen, MetaGPT)
- Per-agent routing enables cost-efficient deployment
- Opens new research direction at intersection of routing + multi-agent

## Slide 13: Limitations & Future Work
- Sample size (200 → 500+)
- Static pipeline (→ dynamic pipeline depth)
- Learned router (→ RL-based routing policy)
- More providers/models

## Slide 14: Summary
- First work on per-agent routing in multi-agent pipelines
- Novel signals: agent role, upstream confidence, workflow stage
- Demonstrated on 3 benchmarks with 4-tier hierarchy
- X% cost savings with Y% quality retention

## Slide 15: Thank You / Q&A

---

## Anticipated Questions

1. **"Why not just use the cheapest model that works?"**
   → Different agents have different requirements. The solver needs strong reasoning, but the verifier just needs to check facts.

2. **"How do you measure confidence?"**
   → We parse linguistic confidence cues from the agent's response text. Show the confidence extraction function.

3. **"What about inference latency?"**
   → Include latency comparison. Local models (T1) are slow on CPU but free. Cloud models (T2) are fastest.

4. **"Is this publishable?"**
   → Yes — the per-agent routing in multi-agent workflows is genuinely novel. No existing work addresses this.

5. **"What's the baseline for comparison?"**
   → Each fixed-tier baseline (all agents use same model) is the comparison. Oracle router provides the theoretical upper bound.
