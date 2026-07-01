> Status: FROZEN (methodology freeze; results are placeholders). No code changes; every quantitative slot is a [placeholder], a TBD-after-run marker, a Table/Figure reference, or an explicitly labelled "verified offline" number.
> Related freeze docs (cross-reference, do not duplicate): 00_PROJECT_STATE, 01_RESEARCH_GAP, 02_DATASET_SPECS, 03_MODEL_MATRIX, 04_BASELINE_PROTOCOL, 06_EVALUATION_PROTOCOL, 07_RISK_REGISTER, 08_RESULTS_LEDGER, 12_RESEARCH_CONTRIBUTION, 13_METRICS_AND_FORMULAS, 14_PAPER_OUTLINE, 15_FIGURE_PLAN, 16_EXPERIMENT_MANIFEST, 17_RESEARCH_CLAIMS, ROUTER_FINAL_SPEC, BASELINE_VALIDATION_REPORT.

# Publishable Paper Skeleton (PART 8)

ACL/EMNLP-style skeleton for the methodology freeze. Sections are drafted in full where the
argument is final (Introduction, Related Work, Methodology, Experiments setup, Discussion,
Limitations, Ethics, Conclusion). Quantitative results are intentionally empty:
Results prose references Tables T1-T7 / Figures F1-F7 and states the EXPECTED direction
neutrally, with no numbers. Claim ids C1-C8 and metric/table/figure labels match the canonical
ids used across the freeze docs.

---

## 0. Title options

1. Context-Aware Per-Agent LLM Routing for Cost-Efficient Multi-Agent Reasoning
2. Right-Sizing Every Agent: Workflow-Aware Tier Routing in Multi-Agent LLM Pipelines
3. Beyond Query Routing: Per-Call Model Selection inside Analyzer-Solver-Verifier Workflows
4. Workflow Context Beats Difficulty: Per-Agent LLM Routing for the Cost-Quality Frontier
5. Who Needs the Frontier Model? Per-Agent Tier Routing for Multi-Agent LLM Systems

Working title (from 14_PAPER_OUTLINE.md): *Context-Aware Per-Agent LLM Routing for
Cost-Efficient Multi-Agent Reasoning*.

---

## 1. Abstract (TEMPLATE)

> Fill every [placeholder] from results/master_results.* after the live runs; do not leave a
> bare number unbracketed. GSM8K baseline cells may cite the verified-offline values where
> explicitly labelled.

Large language models span roughly [COST_RATIO_X]x in price between the cheapest and strongest
tiers, and multi-agent pipelines multiply this cost by issuing several model calls per query.
Existing routers select a single model per *query*; none route *per agent* inside a fixed
multi-agent workflow, where the agent's role, workflow stage, and the upstream agent's output
and confidence are available as routing signals. We introduce context-aware per-agent routing:
before each call in an Analyzer -> Solver -> Verifier pipeline, a router assigns a model tier
(1-4) using these workflow signals in addition to query difficulty. On [N_DATASETS=3] standard
benchmarks (GSM8K, HotpotQA, MuSiQue; N=[N=200] each) across a [N_TIERS=4]-tier hierarchy
(4B local to GPT-4.1) and [N_ROUTERS=15] routing policies, our adaptive router retains
[QRR_EM=PLACEHOLDER]% of the all-Tier-4 Exact Match (and [QRR_F1=PLACEHOLDER]% of token-F1)
while reducing cost by [COST_SAVINGS_PCT=PLACEHOLDER]% (a [CRF=PLACEHOLDER]x cost reduction).
Our headline result is a positive Workflow Context Gain of [WCG_EM=PLACEHOLDER] EM points
([WCG_F1=PLACEHOLDER] F1; paired bootstrap p=[P=PLACEHOLDER]): at matched cost, workflow-aware
routing beats the best difficulty-only router, showing that workflow context -- not difficulty
alone -- drives the gains. An ablation shows each signal (role, confidence, complexity, budget)
contributes [ABLATION_DELTA=PLACEHOLDER] EM at fixed budget, and a learned router approximates
the per-problem oracle. We report EM and F1 with 95% confidence intervals throughout and flag a
Tier-4 EM anomaly on multi-hop QA. Code, configs, and seeds are released for full reproduction.

---

## 2. Introduction

Modern LLM deployments face a steep cost-capability tradeoff: published prices differ by about
two orders of magnitude across model tiers, while the strongest models are only marginally
better than weaker ones on many inputs. Model routing -- selecting a cheaper model when it
suffices and an expensive one only when necessary -- is the standard response. To date,
however, routing has been studied almost exclusively at the granularity of a single query: a
classifier or cascade picks one model for the whole request (FrugalGPT, RouteLLM, AutoMix,
Hybrid-LLM).

Multi-agent LLM systems break this assumption. A growing class of applications decomposes a
task across several cooperating agents -- e.g., an Analyzer that decomposes the problem, a
Solver that produces the answer, and a Verifier that checks it. Such pipelines issue multiple
model calls per query and therefore multiply per-query cost. Crucially, the agents have
*different* capability requirements: decomposition, solving, and verification are not equally
hard, and verification in particular is often easy enough for a small model. Yet existing
multi-agent frameworks (AutoGen, MetaGPT) use a single model for every agent, and existing
routers cannot exploit per-agent structure because they route once, before the workflow begins.

**Research gap (see 01_RESEARCH_GAP.md).** The intersection of adaptive routing and multi-agent
workflows is unexplored. No prior router makes a *per-agent* tier decision informed by the
agent's role, the workflow stage, and the *upstream* agent's output and confidence -- signals
that exist only *inside* a running workflow. MasRouter (the nearest prior work) routes the
*system* per query (which agents/roles/LLMs to assemble), then leaves the assembled agents
un-routed per call; our method is orthogonal and finer-grained and is composable with it.

**This work.** We treat each agent invocation as a routing decision. Before every call, a
deterministic, training-free router maps workflow signals plus query difficulty to a model tier
(1-4). We instantiate this in a fixed Analyzer -> Solver -> Verifier pipeline and evaluate it
on three benchmarks spanning a difficulty gradient (GSM8K 1-hop -> HotpotQA 2-hop -> MuSiQue
2-4 hop), over a 4-tier hierarchy and 15 routing policies including a per-problem oracle
(ceiling), random (floor), single-tier baselines, our proposed routers, signal ablations, and a
learned router. Baselines and routers share one code path
(src/pipeline/routed_pipeline.py), so the only varying factor is the routing policy.

**Contributions.** (referencing canonical claims C1-C8; see 17_RESEARCH_CLAIMS.md)

- **C1.** We define and motivate *per-agent routing* inside a fixed multi-agent pipeline as a
  novel design point distinct from query-level routing, enabled by signals (role, upstream
  confidence, workflow stage) absent in single-agent routing.
- **C2.** We quantify the *oracle headroom* between tiers, establishing that a per-problem
  oracle reaches near-ceiling quality at near-floor cost -- i.e., routing has room to cut cost
  without losing quality.
- **C3.** We show that context-aware routing (cascade/adaptive) *preserves quality* (high
  Quality Retention) while cutting cost (large Cost Reduction Factor) relative to the all-Tier-4
  ceiling.
- **C4 (headline).** We show that *workflow context beats difficulty-only routing*: Workflow
  Context Gain > 0, i.e., adaptive/cascade beat the best difficulty-only router at matched cost.
- **C5.** We show via ablation that *each routing signal contributes*: removing role,
  confidence, complexity, or budget degrades quality at fixed budget.
- **C6.** We show that a *learned router* approximates the oracle and beats random and
  rule-based routers at matched cost.
- **C7.** We show the cost-quality benefit *generalizes across difficulty* (GSM8K -> HotpotQA
  -> MuSiQue).
- **C8.** We adopt *robustness/honesty* practices: report EM and F1, confidence intervals, and
  explicitly flag the Tier-4 EM anomaly and the hypothetical-cost assumption.

---

## 3. Related Work

We position against single-agent routing, multi-agent routing, and multi-agent frameworks. A
feature matrix (Table T6 / related-work matrix, TODO per 14_PAPER_OUTLINE.md E8) summarizes
which systems route per-agent and which use role / upstream-confidence / stage / budget signals.

**FrugalGPT (Chen et al., 2023).** Sequential cascade through a list of LLMs, escalating on the
*current* model's score. Positioning: single-agent and query-level; it cascades within one
response and never sees agent role or an *upstream agent's* confidence inside a pipeline.

**RouteLLM (Ong et al., 2024).** A trained classifier routes each query between a strong and a
weak model from preference data. Positioning: query-level, two-tier, no workflow context; our
complexity/learned routers generalize its difficulty signal to per-agent, multi-tier decisions.

**AutoMix (Aggarwal et al., 2024).** Self-verification then escalation based on model
confidence. Positioning: single-agent; confidence is the *current* model's self-estimate, not a
*prior* agent's output quality consumed by the *next* agent's routing decision.

**MasRouter (Yue et al., 2025).** Routes the multi-agent *system* per query -- collaboration
mode, number of agents/roles, and an LLM per role -- via a cascaded controller. Positioning:
the nearest prior work, but it decides at the query->system level; once the system is chosen,
agents are not re-routed *per call* using upstream output/confidence. Our work is orthogonal and
composable: MasRouter picks the team, we right-size each member's model mid-workflow.

**Hybrid-LLM (Ding et al., 2024).** Quality-aware *binary* routing using predicted answer
quality. Positioning: two-tier and query-level; no multi-step reasoning and no per-agent
allocation of cost within a pipeline.

**Multi-agent frameworks (AutoGen, MetaGPT) and ensembling (LLM-Blender).** AutoGen and MetaGPT
fix one model (or one model per role, statically) for all agents and do not route adaptively;
LLM-Blender ensembles outputs, increasing rather than reducing cost. Positioning: these define
the pipeline structures we route *within*; none adapt model tier per call from workflow signals.

> Summary positioning sentence: every prior router decides once per query; we decide once per
> *agent call*, using signals that only exist *during* a workflow. See 01_RESEARCH_GAP.md and
> 12_RESEARCH_CONTRIBUTION.md for the full novelty argument and the single/multi x query/agent
> quadrant placing our contribution in the otherwise-empty per-agent x multi-agent cell.

---

## 4. Methodology

Canonical specification: ROUTER_FINAL_SPEC.md. Datasets: 02_DATASET_SPECS.md. Tiers:
03_MODEL_MATRIX.md. Metrics: 13_METRICS_AND_FORMULAS.md. Protocols: 04_BASELINE_PROTOCOL.md,
06_EVALUATION_PROTOCOL.md.

### 4.1 The multi-agent pipeline

We use a fixed three-agent pipeline, Analyzer -> Solver -> Verifier (Figure F1 architecture;
the workflow is depicted in the decision-flow figure F2):

- **Analyzer** decomposes the question / extracts structure.
- **Solver** produces the candidate answer (the agent whose tier is the problem's
  *representative* tier for routing-quality metrics).
- **Verifier** checks/finalizes the answer (the agent that emits the final answer).

Baselines and routers run through one shared loop (src/pipeline/routed_pipeline.py); a baseline
is simply a FixedTierRouter(tier), so the only experimental variable is the routing policy.

### 4.2 Routing signals

Per ROUTER_FINAL_SPEC.md Sec. 3 (src/router/signals.py):

| Signal | Availability | Novelty vs single-agent routing |
|--------|--------------|---------------------------------|
| Query complexity (word_count, entity_count, estimated_hops, has_comparison, has_temporal, complexity_score) | pre-call | exists (RouteLLM-style difficulty) |
| Context complexity (token volume of formatted context) | pre-call | refinement of difficulty |
| Agent role (analyzer/solver/verifier) | pre-call | NEW workflow signal |
| Upstream confidence in [0,1] (lexical hedging/assertion cues) | after upstream agent | NEW workflow signal |
| Workflow stage (position in pipeline) | pre-call | NEW workflow signal |
| cost_spent / cost_budget | running | exists (FrugalGPT-style budget) |

### 4.3 The proposed router: the 4-step adaptive procedure

Per ROUTER_FINAL_SPEC.md Sec. 5, for each agent call the `adaptive` router applies:

1. **Complexity -> base tier.** combined = 0.6 * question_complexity + 0.4 * context_complexity;
   map through thresholds (0.2, 0.4, 0.7) to a base tier 1-4. (Disabled -> fixed default_tier.)
2. **Role adjustment.** verifier: -1 tier (verification is easier); solver: +1 (answering needs
   power); analyzer: unchanged. (Disabled -> keep base.)
3. **Confidence cascade.** For solver/verifier: if upstream confidence < tau=0.5, escalate +1
   (record escalated_from); if > 0.8, de-escalate -1 (save cost). (Disabled -> no change.)
4. **Budget cap.** If remaining budget ~ 0, clamp to Tier 1. (Disabled -> ignore budget.)

`cascade` is the lighter primary innovation (complexity floor + role defaults + step 3 only);
`adaptive` is the full method (all four steps). Both are deterministic, interpretable,
training-free, and add no extra LLM calls for routing.

### 4.4 Router catalogue (15 routers; ROUTER_FINAL_SPEC.md Sec. 4)

- **Reference/anchors:** `oracle` (cheapest tier correct per problem; cost-savings upper bound),
  `random` (uniform tier per call, seeded; lower bound), `fixed_t1..fixed_t4` (single tier for
  all agents; the baselines), `fixed_mixed` (static role->tier map, default A->2, S->4, V->1).
- **Proposed (context-aware):** `complexity` (tier from complexity + per-role thresholds),
  `cascade` (role defaults + confidence escalation), `adaptive` (the full 4-step method),
  `learned` (DecisionTree classifier trained on per-problem oracle labels).
- **Ablations of `adaptive`:** `adaptive_no_complexity`, `adaptive_no_role`,
  `adaptive_no_confidence`, `adaptive_no_budget`.

### 4.5 Datasets and difficulty gradient (02_DATASET_SPECS.md)

| Dataset | Split | Hops | Quality metric | N |
|---------|-------|------|----------------|---|
| GSM8K | test | 1-hop (numeric) | Exact Match (numeric equality; no F1) | 200 |
| HotpotQA | validation / distractor | 2-hop | EM + token-F1 | 200 |
| MuSiQue | validation / answerable | 2-4 hop | EM + token-F1 | 200 |

The gradient 1-hop -> 2-hop -> 2-4 hop lets us test generalization across difficulty (C7).

### 4.6 Model tiers (03_MODEL_MATRIX.md)

Hypothetical published prices ($/1M tokens in,out); we report cost *ratios*, not absolute USD,
and state the assumption explicitly (RISK R10, 07_RISK_REGISTER.md):

| Tier | Model | $/1M in | $/1M out | Provider |
|------|-------|---------|----------|----------|
| T1 | Gemma 4B | 0.03 | 0.06 | Ollama (local) |
| T2 | Llama 3.3 70B | 0.59 | 0.79 | Groq |
| T3 | Llama 3.1 405B | 2.66 | 2.66 | GitHub Models |
| T4 | GPT-4.1 | 2.00 | 8.00 | GitHub Models |

T3 and T4 share one token pool (RISK R1, 07_RISK_REGISTER.md), which constrains scheduling of
the frontier-tier runs.

### 4.7 Metrics (13_METRICS_AND_FORMULAS.md)

- **PRIMARY:** EM/Accuracy, Token-F1, Cost-per-task, Cost Reduction Factor / Cost Savings %,
  Quality Retention Rate (QRR, vs all-Tier-4), Workflow Context Gain (WCG; headline), Pareto
  position. WCG = quality(workflow-aware router) - quality(best context-free router) at matched
  (<=) cost; positive WCG isolates the value of workflow-only signals (role + confidence).
- **SECONDARY:** Latency, Throughput, Token Efficiency, Routing Accuracy, Escalation Rate, Tier
  distribution.
- **DIAGNOSTIC:** Over-Provision Rate, Under-Provision Rate; and spec-only / analysis-time
  metrics computable from logged CSV columns without rerunning -- Budget Violations (cost_spent
  vs cost_budget on budget runs), Win Rate (paired correct/f1), Utility Score
  (quality - lambda * cost; lambda frozen at analysis time), Pareto Dominance (from
  (cost, quality) points), Confidence Calibration Error / ECE (confidence vs correct). These are
  marked spec-only: derivable from logged columns at analysis time with no code/router change.
- **Statistics:** percentile bootstrap 95% CIs on EM/F1; paired bootstrap p-values for
  router-vs-T4 and WCG comparisons. N=200 gives EM 95% CIs of roughly +/-7 pts at 50%.

---

## 5. Experiments

Commands and seeds: 16_EXPERIMENT_MANIFEST.md. Protocols: 04_BASELINE_PROTOCOL.md,
06_EVALUATION_PROTOCOL.md. Reproducibility appendix: 16_EXPERIMENT_MANIFEST.md +
requirements.txt.

### 5.1 Setup

- N=200 problems per (dataset) condition; per-problem records deduplicated via
  src/evaluation/csv_io.py.
- Each agent call logs a fixed CSV schema (timestamp, experiment_id, problem_id, dataset,
  agent_role, tier, model_name, router_type, input_tokens, output_tokens, latency_s, cost_usd,
  correct, f1, ground_truth, predicted, confidence, routing_reason, escalated_from,
  response_text), enabling all primary/secondary/diagnostic metrics -- including the spec-only
  ones -- without rerunning.
- Cost is hypothetical (RISK R10); we report ratios. Reference for savings/retention is the
  all-Tier-4 pipeline (quality ceiling, cost reference).

### 5.2 Reproducibility

Seeded random router; deterministic adaptive/cascade/complexity routers; resume-able run driver
(src/pipeline/experiment.py) with a mock model registry for dry runs. All commands, seeds, and
environment are pinned in 16_EXPERIMENT_MANIFEST.md and requirements.txt.

### 5.3 Router matrix

We evaluate all 15 routers x 3 datasets. Reference anchors (oracle, random, fixed_t1..t4,
fixed_mixed) bound the achievable region; proposed routers (complexity, cascade, adaptive,
learned) populate the interior of the Pareto plot; ablations isolate signal contributions.

### 5.4 Ablations

We compare `adaptive` against `adaptive_no_complexity`, `adaptive_no_role`,
`adaptive_no_confidence`, `adaptive_no_budget` (one signal family removed each) to attribute the
contribution of each signal at fixed budget (C5), and we compute WCG against `complexity` (the
best difficulty-only router) to test C4.

### 5.5 Learned router

A DecisionTree is trained on (feature vector, per-problem oracle tier) examples derived from the
baselines (src/router/training_data.py), then run live as `learned`; we report its held-out
classification behavior and its live EM/cost vs random/complexity (C6).

---

## 6. Results

> FREEZE RULE: no numbers below. Each subsection points at a canonical Table (T1-T7) or Figure
> (F1-F7) and states the EXPECTED direction neutrally. Replace "Table X shows ..." with the
> measured value only after the live runs (results/master_results.*). GSM8K baseline cells may
> be reported with the verified-offline values where explicitly labelled (Sec. 6.8).
>
> Canonical tables: T1 Main Benchmark Results, T2 Cost Analysis, T3 Latency Analysis,
> T4 Ablation Study, T5 Error Analysis, T6 Router Comparison, T7 Cross-Dataset Generalization.
> Canonical figures: F1 System Architecture, F2 Routing Decision Flow,
> F3 Cost-vs-Quality / Pareto Frontier, F4 Ablation Results, F5 Escalation Distribution,
> F6 Routing Frequency / Model Utilization, F7 Failure Categories.

### 6.1 Main benchmark results (C3, C7)

Table T1 reports EM and token-F1 (with 95% CIs) per router per dataset; we expect the proposed
routers (cascade/adaptive) to land near the all-Tier-4 quality ceiling while costing
substantially less, and the single-tier baselines to trace the cost-quality tradeoff from T1
(cheap, lower quality) to T4 (expensive, highest quality). Headline retention/savings values are
[QRR_EM=PLACEHOLDER]% / [QRR_F1=PLACEHOLDER]% and [COST_SAVINGS_PCT=PLACEHOLDER]%
(TBD-after-run).

### 6.2 Oracle headroom (C2)

Figure F3 (Pareto) and the `oracle` row of Table T1/T6 are expected to show the per-problem
oracle reaching near-ceiling quality at near-floor cost, establishing the headroom that routing
aims to capture. Oracle gap = [ORACLE_GAP=PLACEHOLDER] (TBD-after-run; GSM8K verified-offline
values in Sec. 6.8).

### 6.3 Cost-quality Pareto (C3)

Figure F3 plots EM vs cost-per-task (log x) with the Pareto frontier; Table T2 gives the cost
analysis (cost-per-task, Cost Reduction Factor, Cost Savings % vs all-Tier-4). We expect the
proposed routers to sit on or above the single-tier baseline frontier -- i.e., new operating
points unachievable by any single tier. Cost Reduction Factor = [CRF=PLACEHOLDER]x
(TBD-after-run).

### 6.4 Workflow Context Gain -- headline (C4)

Table T6 (router comparison) and the matched-cost markers in Figure F3 are expected to show
Workflow Context Gain > 0: at matched (<=) cost, adaptive/cascade exceed the best difficulty-only
router (`complexity`) on EM and on F1, with paired-bootstrap significance. WCG =
[WCG_EM=PLACEHOLDER] EM / [WCG_F1=PLACEHOLDER] F1, p=[P=PLACEHOLDER] (TBD-after-run).

### 6.5 Ablation (C5)

Figure F4 and Table T4 are expected to show that removing any single signal (role / confidence /
complexity / budget) degrades EM at fixed budget relative to full `adaptive`, with the largest
drops indicating the most load-bearing signals. Per-signal deltas = [ABLATION_DELTA=PLACEHOLDER]
(TBD-after-run).

### 6.6 Learned router (C6)

Table T6 and Figure F3/F6 are expected to show the `learned` router beating `random` and at
least matching rule-based routers at comparable cost, approximating the oracle's tier
assignments. Learned-vs-random delta = [LEARNED_DELTA=PLACEHOLDER] (TBD-after-run).

### 6.7 Secondary and diagnostic results

- Figure F6 (model utilization / routing frequency) and Figure F5 (escalation distribution) are
  expected to show the proposed routers concentrating cheap tiers on the verifier and escalating
  selectively when upstream confidence is low; escalation rate = [ESCALATION_RATE=PLACEHOLDER].
- Table T3 (latency) and throughput/token-efficiency columns are expected to favor routers that
  use local/fast tiers for easy sub-tasks; values TBD-after-run.
- Table T5 (error analysis) and Figure F7 (failure categories) characterize where routing under-
  or over-provisions (Over-/Under-Provision Rate); spec-only diagnostics (Win Rate, Utility
  Score at frozen lambda, Pareto Dominance, Budget Violations, ECE) are computed at analysis
  time from the logged CSV columns. Values TBD-after-run.

### 6.8 Verified-offline reference values (GSM8K baselines; explicitly labelled)

The following are REAL numbers produced offline by scripts/validate_baselines.py and
simulate_routing.py (see BASELINE_VALIDATION_REPORT.md); everything else above is a placeholder
until the live runs. GSM8K baselines are LOCKED; all HotpotQA/MuSiQue F1 is PENDING clean
re-runs (legacy logger truncated responses at 500 chars).

| Quantity (verified offline) | Value |
|-----------------------------|-------|
| GSM8K EM by tier T1/T2/T3/T4 | 94.5 / 96.0 / 97.0 / 97.0 |
| GSM8K cost over 200 problems, T1/T2/T3/T4 ($) | 0.031 / 0.219 / 0.822 / 1.182 |
| GSM8K oracle (sim) | 98.5% EM @ $0.0485 / 200 |
| HotpotQA EM by tier T1/T2/T3/T4 | 63.0 / 65.25 (118/200) / 54.17 (48/200) / 37.5 (backup) |
| MuSiQue EM by tier T1/T2/T3/T4 | 31.5 / 55.0 / 47.5 / 25.6 (199/200) |

These corroborate C2 on GSM8K (oracle beats every single tier at ~1.5x Tier-1 cost) and surface
the Tier-4 EM anomaly used in the Discussion. All HotpotQA/MuSiQue values here are EM only and
PENDING clean re-runs; F1 is not yet available.

---

## 7. Discussion

**When per-agent routing helps most.** We expect the benefit to grow with task difficulty: on
near-ceiling GSM8K (1-hop) all tiers are close, leaving little headroom, whereas on multi-hop
HotpotQA/MuSiQue tiers diverge and per-agent allocation has more to exploit (consistent with the
difficulty gradient and C7). The verifier is the natural place to spend the least, since
checking is easier than solving; the solver is where capability matters most.

**EM-vs-F1 and the Tier-4 anomaly.** On multi-hop QA we observe (verified offline) that Tier-4
EM is *lower* than weaker tiers (e.g., the GSM8K-locked vs HotpotQA/MuSiQue EM pattern above).
The most likely cause is EM brittleness to verbose frontier-model answers: a correct answer
embedded in a longer, well-hedged response fails strict EM but should score well on token-F1.
We therefore ALWAYS report F1 alongside EM, and QRR can exceed 100% on these datasets purely
because the Tier-4 EM reference is depressed (see 13_METRICS_AND_FORMULAS.md Sec. D and
BASELINE_VALIDATION_REPORT.md Sec. 4). The headline WCG claim (C4) is reported on both EM and F1
to avoid relying on the anomalous metric.

**Why workflow context (not just difficulty) matters.** If WCG > 0 holds (C4), the gain over the
difficulty-only `complexity` router at matched cost is attributable to the workflow-only signals
-- role and upstream confidence -- since complexity is held in common. The ablation (C5) further
attributes the gain to specific signals.

---

## 8. Limitations

- **Sample size.** N=200 per condition; EM 95% CIs are roughly +/-7 pts at 50%. The paper may
  raise N to 500 (RISK R4); current claims are scoped to N=200.
- **Hypothetical cost.** All models are free in practice; we assign published list prices and
  report cost *ratios* only, not absolute USD (RISK R10). Absolute-dollar claims are out of
  scope.
- **Lexical confidence.** Upstream confidence is extracted from lexical hedging/assertion cues,
  not a calibrated probability; calibrated confidence is future work.
- **Offline simulation estimate.** Oracle and some preview numbers come from offline simulation
  (simulate_routing.py); these are estimates pending the live routed runs.
- **One pipeline shape.** We study a single fixed Analyzer -> Solver -> Verifier pipeline of
  depth three; dynamic depth and other topologies are not evaluated.
- **Shared token pool.** T3 and T4 share one token pool (RISK R1), constraining frontier-tier
  experiment scheduling.
- **Pending F1.** All HotpotQA/MuSiQue F1 awaits clean re-runs (legacy logger truncated
  responses at 500 chars); only GSM8K baselines are LOCKED.

(Full risk accounting: 07_RISK_REGISTER.md.)

---

## 9. Ethics and Broader Impact

- **Cost and energy efficiency.** The method's purpose is to reduce compute by using smaller
  models where they suffice, which lowers monetary cost and, correspondingly, the energy
  footprint of multi-agent inference.
- **No human subjects.** No human-subjects data or annotation is involved.
- **Public benchmarks.** All evaluation uses public benchmarks (GSM8K, HotpotQA, MuSiQue) under
  their standard licenses; no private or personally identifying data is used.
- **Dual-use.** Risk is minimal: the contribution is an efficiency layer over existing models
  and does not increase model capability or enable new harmful applications. Routing to weaker
  models could, in principle, reduce answer quality if mis-tuned; we mitigate by reporting EM
  and F1 with CIs and by including conservative reference anchors (all-Tier-4 ceiling).

---

## 10. Conclusion

We introduced context-aware per-agent routing for multi-agent LLM pipelines: before each
Analyzer/Solver/Verifier call, a training-free router selects a model tier from workflow signals
(role, upstream confidence, stage) plus query difficulty. Across three benchmarks, a 4-tier
hierarchy, and 15 routing policies, we (will) show that per-agent routing preserves quality while
cutting cost (C3), that this is driven by workflow context rather than difficulty alone
(positive Workflow Context Gain, C4), that each signal contributes (C5), that a learned router
approximates the oracle (C6), and that the benefit generalizes across difficulty (C7) -- all
reported with EM, F1, and confidence intervals and with the Tier-4 EM anomaly and
hypothetical-cost assumption flagged (C8). Per-agent routing opens a new direction at the
intersection of LLM routing and multi-agent systems; promising extensions include full-pipeline
cascading, learned per-agent labels, calibrated confidence, and dynamic pipeline depth.

---

## Appendix A. Claim -> evidence -> figure/table map (cross-reference 17_RESEARCH_CLAIMS.md)

| Claim | Evidence locus | Primary figure | Primary table |
|-------|----------------|----------------|---------------|
| C1 per-agent novelty | related-work matrix + interface | F1 architecture | T6 router comparison (matrix) |
| C2 oracle headroom | oracle row, Pareto | F3 Pareto | T1 / T2 (oracle row) |
| C3 retention @ cost | QRR, cost-savings vs T4 | F3 Pareto | T1, T2 |
| C4 WCG (headline) | matched-cost comparison + paired bootstrap | F3 (matched-cost markers) | T6 |
| C5 ablation | adaptive vs adaptive_no_* | F4 ablation | T4 |
| C6 learned | learned vs random/rule-based | F3 / F6 | T6 |
| C7 generalization | per-dataset rows | F3 x3 datasets | T7 cross-dataset |
| C8 honesty | EM+F1, CIs, anomaly flag | F7 failure categories | T5 error analysis |

## Appendix B. Fill-in checklist before submission (gate)

Replace every [placeholder] and TBD-after-run with values from results/master_results.* once the
live runs land (evidence gate E1-E8 in 14_PAPER_OUTLINE.md). Verified-offline GSM8K cells in
Sec. 6.8 may remain, explicitly labelled. Do not introduce any number outside this process.
