# Research Defense: Context-Aware LLM Routing

This document provides detailed, rigorous answers to four critical research dimensions. It is designed to be used as a study guide or direct submission for faculty evaluations and reviewer defenses.

---

## 1. Dataset Mastery & Sufficiency

**Question:** *Know your datasets thoroughly and ensure that the dataset size is sufficient to suit your problem.*

### Primary Dataset: GSM8K (Grade School Math 8K)
*   **Structure:** 8,792 high-quality linguistic grade school math word problems. Each problem takes 2-8 steps to solve and yields a deterministic numeric answer (always formatted after `####`).
*   **Why it suits our problem:** Multi-agent systems shine in multi-step reasoning. Math problems require a clear division of labor (Analysis → Solving → Verification), making GSM8K the perfect testbed for our 3-agent pipeline. The deterministic answers allow for automated, objective accuracy scoring without needing a separate LLM judge.
*   **Sufficiency Argument:** While GSM8K contains 8.5K problems, we are sampling **200 problems** for our initial experiments. Is this sufficient? **Yes, mathematically and practically.**
    *   In our architecture, 1 problem = 3 agent calls (Analyzer, Solver, Verifier).
    *   We run these across 3 model tiers.
    *   Therefore, 200 problems generate **1,800 independent data points** (agent interactions).
    *   Because our router is a lightweight classifier (e.g., Logistic Regression, XGBoost, or rule-based heuristics) operating on a small feature space (~5-10 features like `agent_role`, `word_count`, `num_operations`), 1,800 data points is statistically robust to train and validate the routing model without overfitting. LLM routing does not require millions of rows like foundation model pre-training.

### Secondary Datasets (For Generalization Testing)
*   **HumanEval:** 164 Python coding problems testing logical generation. Generates ~1,400 agent interactions. Tests if the router's logic generalizes from math to code.
*   **MMLU (Massive Multitask Language Understanding):** Used to test factual retrieval and general knowledge.

---

## 2. Evaluation Parameters (Metrics Framework)

**Question:** *Know all the evaluation parameters to be used (as many evaluation parameters as possible).*

To rigorously prove the value of our router, we must evaluate across three dimensions: **Quality, Efficiency, and System Dynamics.**

### A. Quality & Performance Metrics
1.  **End-to-End Accuracy (E2E-Acc):** The percentage of problems solved correctly by the full multi-agent pipeline.
2.  **Quality Retention Rate (QRR):** `(Router Pipeline Accuracy) / (All-Tier-3 Pipeline Accuracy)`. This measures how closely our routed system matches the "Oracle" (using the most expensive model for everything). A QRR of >0.97 is considered highly successful.
3.  **Agent-Level Success Rate:** Evaluates how often specific agents (e.g., the Verifier) successfully catch and correct errors.

### B. Efficiency & Cost Metrics
4.  **Cost per Problem (USD):** The average API cost incurred to solve one problem end-to-end.
5.  **Cost Reduction Factor (CRF):** `1 - (Routed Cost / All-Tier-3 Cost)`. The primary business metric. We aim for >70% CRF.
6.  **Token Efficiency:** Total tokens processed per dollar spent.

### C. System & Routing Metrics
7.  **Routing Accuracy:** The percentage of times the router selected the *minimum sufficient tier*. If Tier 1 could have solved it, but the router chose Tier 3, it's a routing failure (over-provisioning).
8.  **Escalation Rate:** The percentage of agent calls sent to Tier 2 or Tier 3. A successful router keeps the escalation rate low (e.g., <20%).
9.  **End-to-End Latency:** Average time to solve a problem. Because local/smaller models are faster, effective routing should decrease overall latency compared to an All-Tier-3 approach.

---

## 3. Implementation of Existing/Basic Architectures

**Question:** *Implementation of existing/basic architectures and getting results using these architectures.*

Before building the intelligent router, we implemented the fundamental "unrouted" multi-agent baselines to establish our floor and ceiling.

### The Basic Architecture
We built a sequential 3-Agent Pipeline:
1.  **Analyzer Agent:** Parses the prompt, identifies variables, and outlines a strategy.
2.  **Solver Agent:** Executes the mathematical steps based on the analysis.
3.  **Verifier Agent:** Reviews the solver's work and outputs the final answer.

### Baseline Implementations & Results
We ran this pipeline using a static, single-model approach to gather training data for our future router:
*   **Baseline 1 (The Cost Floor): All-Tier-1 (Gemma 4B - Local)**
    *   *Result:* Achieved **94.5% accuracy** at an incredibly low cost ($0.032 for 200 problems).
    *   *Insight:* The multi-agent pipeline itself is highly robust. By having a Verifier agent, even a tiny 4B model can correct its own mistakes, drastically raising the baseline accuracy.
*   **Baseline 2 (The Mid-Point): All-Tier-2 (Llama 3.3 70B - Cloud)**
    *   *Result:* Achieved **96.0% accuracy** ($0.219 for 200 problems).
*   **Baseline 3 (The Oracle): All-Tier-3 (GPT-4o-mini - Cloud)**
    *   *Result:* Baseline data collection currently in progress.

### What these results mean for our project:
Because the Tier 1 baseline is so high (94.5%), it proves that **using Frontier models for every agent is a massive waste of resources.** The basic architecture proves that ~94% of the sub-tasks are "easy". Our intelligent router now only needs to focus on identifying the ~5% of highly complex edge cases that actually require escalation to Tier 2 or 3.

---

## 4. Recent Work & Literature Context

**Question:** *Have a basic idea of recent work done.*

The field of LLM routing has exploded between 2023 and 2025. Our work stands on the shoulders of these papers, but targets a specific unsolved gap.

### Key Recent Works:
1.  **RouteLLM (Ong et al., 2024 - UC Berkeley/LMSYS):**
    *   *What they did:* Used Chatbot Arena data to train classifiers (like Matrix Factorization) to route between weak and strong models.
    *   *Limitation:* They only route based on the *user's initial prompt text*. They do not account for agents, workflows, or roles.
2.  **FrugalGPT (Chen et al., 2023 - Stanford):**
    *   *What they did:* Introduced "LLM Cascades". Try a cheap model; if its self-reported confidence is low, retry with a more expensive model.
    *   *Limitation:* High latency. If the cheap model fails, you have to wait for a second API call. Our router is *predictive/preemptive*, avoiding retry latency.
3.  **MasRouter (2025):**
    *   *What they did:* Explored routing specifically for multi-agent systems using semantic embeddings of the tasks.
    *   *Limitation:* Highly rigid and requires extensive pre-training data specific to the exact agent configuration being used.

### Our Novel Contribution (The Gap):
Current routers treat every LLM call as an isolated event. Our **Context-Aware Router** is the first to use the *state of the multi-agent system* as routing features. We use:
1.  **Agent Role:** (e.g., Is this the Analyzer or the Verifier? Analyzers rarely need 70B models).
2.  **Workflow Position:** (e.g., Is this step 1 or step 3 of the pipeline? Later steps have more context and are "easier").
3.  **Upstream Output:** (How complex was the text generated by the previous agent?)

By integrating workflow context, we hypothesize we can achieve higher Routing Accuracy than prompt-only routers like RouteLLM.
