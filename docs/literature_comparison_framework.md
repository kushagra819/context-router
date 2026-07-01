> Status: FROZEN (methodology freeze; results are placeholders)
> Related docs: 01_RESEARCH_GAP.md, 12_RESEARCH_CONTRIBUTION.md, 13_METRICS_AND_FORMULAS.md, 14_PAPER_OUTLINE.md, 17_RESEARCH_CLAIMS.md, 02_DATASET_SPECS.md, 03_MODEL_MATRIX.md, 06_EVALUATION_PROTOCOL.md, 07_RISK_REGISTER.md, 08_RESULTS_LEDGER.md, BASELINE_VALIDATION_REPORT.md. This doc is PART 4: how our results sit next to the routing literature. It does NOT restate the gap (see 01) or the contribution (see 12); it specifies comparability.

# Literature Comparison Framework

## 0. Purpose and scope

This document answers one question: **on which axes are our results comparable to the
established LLM-routing literature, and where are they not?** For each prior system we record
(a) the metrics we share, (b) the benchmarks we share, (c) the experimental-design elements we
share, (d) the components we would still need to be *directly* comparable, and (e) a one-line
**Comparability Verdict** (Direct / Partial / Conceptual-only). We then give a synthesis of the
comparable axes and a **comparability checklist** of what we MUST report to be citable next to
these works.

A single structural difference cuts across every comparison and must be stated up front so
reviewers do not expect apples-to-apples numbers:

> **Unit-of-routing difference.** All six prior systems route **once per query** (query -> model,
> or query -> system). We route **once per agent call** inside a *fixed* multi-agent pipeline
> (Analyzer -> Solver -> Verifier), using signals that only exist *during* execution
> (agent role, workflow stage, upstream output/confidence). This is claim **C1**. The
> consequence for comparability: our cost is summed over up to three calls per problem, our tier
> distribution is per-call not per-query, and our "router accuracy" is defined against a
> per-problem oracle tier computed from baseline pipelines (13_METRICS_AND_FORMULAS.md SS.B), not
> against a per-query strong/weak label. Whenever we place a number next to a prior system, the
> per-call vs per-query basis must be annotated.

Numbers in this doc are PLACEHOLDERS ([X.X] / TBD-after-run) except those explicitly tagged
"verified offline" (from scripts/validate_baselines.py + simulate_routing.py; see
BASELINE_VALIDATION_REPORT.md and 08_RESULTS_LEDGER.md).

---

## 1. What the field shares (the common comparison surface)

The routing literature has converged on a small set of comparison axes. We adopt all of them so
that our results can be read on the same plot as prior work:

| Axis | Field-standard form | Our implementation (13_METRICS_AND_FORMULAS.md) |
|------|---------------------|--------------------------------------------------|
| Cost-vs-quality curve | quality plotted against $ (or token) cost; the headline artifact in routing papers | Pareto figure F3 (`fig4_pareto_<ds>`); cost = `cost_per_task`, quality = EM and F1 |
| Fraction of calls per tier / call-cost | % of queries sent to the strong model (FrugalGPT, RouteLLM, Hybrid-LLM) | per-tier **call** distribution (F6 `fig5_utilization_<ds>`); we report per-call %, not per-query % |
| Oracle gap / headroom | distance from an omniscient router (cost ceiling vs quality ceiling) | `oracle` reference router; oracle EM @ cost (C2); GSM8K verified offline below |
| Pareto frontier / dominance | which operating points are non-dominated | F3 frontier; `Pareto Dominance` (spec-only / analysis-time) |
| Quality retention at reduced cost | % of strong-model quality kept (FrugalGPT "match GPT-4 at X% cost") | Quality Retention Rate vs all-Tier-4 (C3); `quality_retention_pct` |
| Statistical validity | rarely reported in prior routing papers; we add it | bootstrap 95% CIs, paired-bootstrap p-values (C8) |

The first four axes are the *shared comparison surface*: any of the six systems below can be
laid on the same cost-vs-quality plane as our routers, even when the underlying mechanism
differs. The friction is always in normalization (per-call vs per-query, hypothetical $ vs real
provider $, EM-only vs EM+F1) -- enumerated per system in SS.2 and resolved in the checklist (SS.4).

---

## 2. Per-system comparison

Each subsection uses the same five fields. "Shared Experimental Design" covers protocol-level
overlap (N, splits, escalation logic, tier count, label source). "Missing Components" lists what
*we* would have to add (or what a reproduction would require) for a **direct** numerical
comparison -- not a critique of the prior work.

### 2.1 RouteLLM (Ong et al., 2024; arXiv:2406.18665)

A trained binary router (strong vs weak) using preference data; reports cost-vs-quality and the
"% calls to strong model" curve, with a calibratable cost threshold.

| Field | Detail |
|-------|--------|
| Shared Metrics | Cost-vs-quality curve; fraction of calls to the strong tier; quality retention vs the strong model; Pareto/threshold sweep. Maps to our F3, F6, Quality Retention Rate. |
| Shared Benchmarks | None of our three exactly (RouteLLM headlines MT-Bench, MMLU, GSM8K). **GSM8K overlaps in name** but we use N=200 test, numeric EM only (02_DATASET_SPECS.md), so it is a partial overlap, not a shared split. |
| Shared Experimental Design | Threshold-swept cost-quality tradeoff; explicit strong/weak cost reference; a learned router trained on labels (our `learned`, DecisionTree on oracle labels, is the analogue). |
| Missing Components (for direct comparability) | (a) RouteLLM is **2-tier**; we are **4-tier** -- to compare we must collapse to a 2-tier slice (e.g. T1 vs T4) or report the 2-tier point on our frontier. (b) RouteLLM routes **per query**; we route **per call** -- our "% to strong" is per agent call. (c) Preference-data training signal vs our oracle-tier-correctness label. (d) Real vendor $ vs our hypothetical $ (R10). |
| Comparability Verdict | **Partial** -- shared cost-quality + %-strong axes and a shared learned-router idea, but 2-tier/per-query vs 4-tier/per-call and different GSM8K split prevent identical numbers. |

### 2.2 FrugalGPT (Chen et al., 2023; arXiv:2305.05176)

Sequential **LLM cascade**: call a cheap model, score its answer, escalate to a costlier model
only if the score is low. Headline framing: "match GPT-4 quality at a fraction of cost."

| Field | Detail |
|-------|--------|
| Shared Metrics | Cost reduction at matched quality (our Cost Reduction Factor / Cost Savings %, C3); quality retention vs the top model; cost-vs-quality curve. |
| Shared Benchmarks | None shared by split (FrugalGPT uses HEADLINES, OVERRULING, COQA, etc.). No overlap with GSM8K/HotpotQA/MuSiQue. |
| Shared Experimental Design | **Confidence/score-gated escalation** -- this is exactly our `cascade` router (confidence escalation) and the escalation step inside `adaptive`. Escalation Rate (`escalation_rate`, SECONDARY) and `escalated_from` (logged column) are the directly comparable mechanism-level quantities. |
| Missing Components (for direct comparability) | (a) FrugalGPT cascades **within a single query**; we escalate **within an agent call** while the pipeline shape stays fixed -- our escalation is per-call, gated on *upstream* confidence as well as own confidence. (b) FrugalGPT also learns an LLM-scorer; our confidence is the logged `confidence` (lexical, not calibrated -- Limitations, 14_PAPER_OUTLINE.md SS.9). (c) Different benchmarks; would need a shared dataset. (d) Hypothetical vs real cost. |
| Comparability Verdict | **Partial** -- the cascade/confidence-escalation mechanism is shared and directly nameable (`cascade`), but no shared benchmark and per-query vs per-call escalation block identical numbers. |

### 2.3 LLM Cascades / AutoMix (Aggarwal et al., 2024; arXiv:2310.12963)

Self-verification then escalation: a model judges its own answer (a meta-verifier / POMDP-style
router) and escalates on low self-confidence. Reports cost-vs-quality and an Incremental Benefit
Per Cost style efficiency.

| Field | Detail |
|-------|--------|
| Shared Metrics | Cost-vs-quality curve; escalation rate; efficiency-per-cost (our Token Efficiency / cost-per-task; an Incremental-Benefit-Per-Cost analogue is derivable at analysis time from logged `cost_usd` and `correct`). |
| Shared Benchmarks | None by split (AutoMix uses reading-comprehension / QA sets such as NarrativeQA, QASPER, COQA). **HotpotQA/MuSiQue are conceptually adjacent** (multi-hop QA) but not the same sets. |
| Shared Experimental Design | A **verification-then-escalate** loop -- conceptually the role our `Verifier` agent plays, and the confidence-escalation in `cascade`/`adaptive`. Self-scoring -> route is the same control structure. |
| Missing Components (for direct comparability) | (a) AutoMix's verifier is a *routing controller over a single answer*; our Verifier is a **pipeline stage that is itself routed**. To compare we would isolate the "escalate on low verifier confidence" sub-policy. (b) AutoMix's meta-verifier (POMDP/threshold) vs our rule-based escalation -- different policy class. (c) No shared benchmark/split. (d) Hypothetical cost. |
| Comparability Verdict | **Conceptual-only** -- shared verify-then-escalate idea, but the verifier is a controller there vs a routed pipeline stage here, with no shared benchmark; comparison is qualitative. |

### 2.4 Adaptive Inference (general)

The broad family: input-adaptive compute allocation (early-exit, dynamic depth/width,
mixture-of-experts gating, confidence-based abstention). Not a single benchmark; a methodological
reference point for "spend compute where it helps."

| Field | Detail |
|-------|--------|
| Shared Metrics | Compute/cost-vs-quality tradeoff curve; accuracy-at-fixed-budget; the general Pareto framing. |
| Shared Benchmarks | None -- this is a paradigm, not a benchmarked system. GSM8K appears in some early-exit papers but not as a shared routing split. |
| Shared Experimental Design | Allocate-compute-by-difficulty (our `complexity` router is the difficulty-only instance); fixed-budget operating points (our budget cap in `adaptive`, and `Budget Violations` spec-only check). |
| Missing Components (for direct comparability) | (a) Adaptive-inference typically varies compute *within one model* (layers/experts); we vary the *model tier* across discrete tiers and across *agents*. (b) No shared dataset or metric definition. (c) The "context" signal (role/stage/upstream) has no counterpart in standard adaptive inference -- which is precisely our novelty (C4). |
| Comparability Verdict | **Conceptual-only** -- shared "adapt compute to difficulty" principle and Pareto framing, but no shared benchmark and a different compute-control mechanism (tier/agent vs intra-model). |

### 2.5 MasRouter (Yue et al., 2025; arXiv:2502.11133) -- CLOSEST PRIOR WORK

Learns to route the **multi-agent system itself**: per query it selects the collaboration mode,
number of agents/roles, and an LLM per role, via a cascaded controller. This is the nearest
neighbour (01_RESEARCH_GAP.md SS.2) and our primary point of contrast.

| Field | Detail |
|-------|--------|
| Shared Metrics | Cost-vs-quality / performance-vs-cost curve; per-role / per-tier LLM assignment distribution (their per-role LLM choice vs our per-call tier distribution, F6); accuracy at reduced cost. These are the **most directly alignable** metrics in the whole table. |
| Shared Benchmarks | **GSM8K overlaps in name** (MasRouter evaluates on math + reasoning + QA suites incl. GSM8K-family). Still differs by split/N; HotpotQA/MuSiQue may or may not be in their suite -- treat as partial. |
| Shared Experimental Design | **Multi-agent setting with per-role LLM selection** -- the only prior work that assigns different models inside a multi-agent system. A learned routing controller (their controller vs our `learned`). Cost accounted over multiple agent calls (matches our summed-over-calls cost). |
| Missing Components (for direct comparability) | (a) **Granularity:** MasRouter chooses the team/roles/LLMs **once per query, before execution**; we keep the team fixed and re-route **each call during execution** on *upstream output and confidence*. Their assignment is static-per-query; ours is dynamic-per-call. (b) **Signal set:** MasRouter conditions on the query; we add role + workflow stage + upstream confidence (C1, C4). (c) **Composability, not competition:** the two are orthogonal -- MasRouter picks the team, we right-size each member mid-workflow; a fair head-to-head needs us to fix MasRouter's chosen team and then apply per-call routing, which neither codebase does today. (d) Shared exact split/N; real vs hypothetical cost. |
| Comparability Verdict | **Partial (closest)** -- shares the multi-agent + per-role-LLM + cost-quality surface and (by name) GSM8K, but static-per-query system selection vs dynamic-per-call agent routing means we report **complementary**, not head-to-head, numbers. Frame as orthogonal/composable, not as beating MasRouter. |

### 2.6 Hybrid-LLM (Ding et al., 2024; arXiv:2404.14618)

Quality-aware **binary** router (small vs large) with a predicted-quality / router-probability
threshold and a tunable cost-quality knob.

| Field | Detail |
|-------|--------|
| Shared Metrics | Cost-vs-quality curve via threshold sweep; fraction routed to the large model; quality retention at a chosen cost; Pareto position. |
| Shared Benchmarks | None by split (Hybrid-LLM uses MixInstruct / preference-style data). No overlap with our three. |
| Shared Experimental Design | A tunable threshold that traces a frontier (our cost knob is the `adaptive` budget cap + escalation thresholds); a predicted-quality routing signal (our `complexity`/`learned` predict where cheap suffices). |
| Missing Components (for direct comparability) | (a) **2-tier** vs our 4-tier (same collapse needed as RouteLLM). (b) Per-query vs per-call. (c) Quality-predictor trained on response-quality labels vs our oracle-tier-correctness labels. (d) No shared benchmark; hypothetical cost. |
| Comparability Verdict | **Partial** -- shared threshold-swept cost-quality frontier and %-to-large axis, but 2-tier/per-query and no shared benchmark prevent identical numbers. |

### 2.7 Verdict summary

| System | Routes at | Tiers | Shared benchmark | Mechanism we share | Verdict |
|--------|-----------|:-----:|------------------|--------------------|---------|
| RouteLLM | query -> model | 2 | GSM8K (name only) | learned router, %-strong curve | Partial |
| FrugalGPT | query (cascade) | N | none | confidence-gated escalation (`cascade`) | Partial |
| AutoMix | query (self-verify) | N | none (multi-hop adjacent) | verify-then-escalate | Conceptual-only |
| Adaptive Inference | input -> compute | n/a | none | adapt-compute-to-difficulty (`complexity`) | Conceptual-only |
| **MasRouter** | **query -> system** | per-role | **GSM8K (name)** | **multi-agent per-role LLM selection** | **Partial (closest)** |
| Hybrid-LLM | query -> model | 2 | none | threshold-swept frontier, %-to-large | Partial |

No system is a **Direct** match: there is no prior per-agent, per-call router on our exact
splits. The honest framing for the paper is that we are *citable on shared axes* (cost-quality,
%-per-tier, oracle gap, Pareto, retention) and *novel on the routing unit* (per-call inside a
fixed pipeline, conditioned on workflow context).

---

## 3. Synthesis: which axes make us comparable

Four axes carry comparability across the whole table; each maps to a concrete artifact we already
produce. These are exactly the field's lingua franca (SS.1) and are what reviewers will look for.

1. **Cost-vs-quality curve.** The universal axis -- every system above reports it. We report it
   as F3 (`fig4_pareto_<ds>`) with EM and F1 on the y-axis and `cost_per_task` on the x-axis,
   one curve per dataset. *Comparable to all six.* Caveat to annotate: x-axis is **hypothetical
   $** (ratios are meaningful; absolute $ are not -- R10) and cost is **summed over agent calls**.

2. **Fraction of calls per tier / call-cost.** RouteLLM/Hybrid-LLM report "% to strong";
   MasRouter reports per-role LLM mix; we report the **per-call tier distribution** (F6,
   `fig5_utilization_<ds>`). *Comparable in shape, not unit* -- ours is per agent call, theirs is
   per query; this MUST be labelled so a 2-tier "% to strong" is not read against our 4-tier
   per-call histogram.

3. **Oracle gap (headroom).** Less common in prior routing papers but the cleanest way to show
   how much room a router has. Our `oracle` reference (C2) gives the upper-left corner of the
   Pareto plane. *Verified offline (GSM8K):* oracle **98.5% EM @ $0.0485 / 200** vs Tier-4
   **97.0% @ $1.182** and Tier-1 **94.5% @ $0.031** -- oracle beats every single tier at ~1.5x
   Tier-1 cost. This frames "how much of the gap a real router closes," directly comparable to
   any system that reports an oracle/upper-bound.

4. **Pareto frontier / dominance.** Whether our routed points are non-dominated by the single-tier
   baselines (fixed_t1..t4) and where mixed-tier points (`fixed_mixed`, `cascade`, `adaptive`,
   `learned`) sit. `Pareto Dominance` is computable at analysis time from the (cost, quality)
   points (spec-only). *Comparable to all six* as a frontier picture; the novel claim is that
   per-call routing opens operating points the single-tier line cannot reach (12_RESEARCH_CONTRIBUTION.md SS.3).

Supporting (mechanism-level) comparability:
- **Quality Retention Rate** vs all-Tier-4 (C3) is the FrugalGPT/RouteLLM "match the strong model
  at X% cost" statement in our terms. Report **F1-based QRR too**, because Tier-4 EM is
  anomalously low on multi-hop and QRR can exceed 100% on EM alone (13_METRICS_AND_FORMULAS.md SS.D;
  BASELINE_VALIDATION_REPORT.md SS.4; C8).
- **Escalation Rate** + `escalated_from` align mechanism-for-mechanism with FrugalGPT/AutoMix
  cascades.
- **Cost Reduction Factor / Cost Savings %** give the headline "Nx cheaper" number in the same
  form prior work uses.

### Where we are NOT comparable (state plainly so reviewers do not expect apples-to-apples)

- **Routing unit.** Per-call inside a fixed Analyzer->Solver->Verifier pipeline vs per-query
  (all six). Our cost/tier numbers aggregate over up to three calls per problem. (C1)
- **Signal set.** We add role + workflow stage + **upstream** confidence; prior single-agent
  cascades use only the current model's own confidence; MasRouter conditions on the query. The
  **Workflow Context Gain** metric (C4, headline) has *no analogue* in prior work -- it is an
  internal contrast (`adaptive`/`cascade` minus `complexity` at matched cost), not a cross-paper
  comparison.
- **Tier count.** 4 tiers vs the 2-tier RouteLLM/Hybrid-LLM; comparisons to 2-tier systems
  require collapsing to a T1-vs-T4 slice.
- **Benchmarks/splits.** Only GSM8K overlaps *by name* (RouteLLM, MasRouter); even there our
  N=200 test split + numeric-EM-only protocol differs. HotpotQA/MuSiQue are multi-hop adjacent to
  AutoMix's domain but not shared splits.
- **Cost basis.** Hypothetical $/1M (03_MODEL_MATRIX.md); only **cost ratios** transfer across
  papers, never absolute dollars (R10).
- **Multi-agent vs single-agent.** Four of the six are single-agent; only MasRouter is
  multi-agent, and even there it is static-per-query system selection vs our dynamic-per-call
  agent routing -> **complementary, not head-to-head**.

---

## 4. Comparability checklist (what we MUST report to be citable next to these works)

Report all of the following, per dataset (GSM8K, HotpotQA, MuSiQue), for every router in the
matrix. Values are PLACEHOLDERS until the live runs land (E1-E8, 14_PAPER_OUTLINE.md); the one
verified-offline anchor is noted.

| # | Item | Why it is required | Artifact / metric | Status |
|---|------|--------------------|-------------------|--------|
| K1 | Cost-vs-quality curve, EM **and** F1 on y, cost-per-task on x | the universal routing axis (all six) | F3 `fig4_pareto_<ds>`; `cost_per_task`, `exact_match`, `mean_f1` | [X.X] |
| K2 | Per-call tier distribution, **labelled per-call** | RouteLLM/Hybrid %-strong; MasRouter per-role mix | F6 `fig5_utilization_<ds>` | [X.X] |
| K3 | Oracle gap: oracle EM @ cost vs each single tier | headroom (C2) | `oracle` row | GSM8K verified offline (98.5% @ $0.0485) |
| K4 | Pareto frontier + dominance flags vs single-tier line | non-dominance vs baselines | F3 + `Pareto Dominance` (spec-only) | [X.X] |
| K5 | Cost Reduction Factor (x) and Cost Savings % vs all-Tier-4 | the "Nx cheaper" headline | `cost_reduction_factor`, `cost_savings_pct` | [X.X] |
| K6 | Quality Retention Rate, **EM and F1** vs all-Tier-4 | "match strong at X% cost"; F1 guards the Tier-4 EM anomaly | `quality_retention_pct` | [X.X] |
| K7 | Escalation Rate + `escalated_from` summary | cascade mechanism vs FrugalGPT/AutoMix | `escalation_rate` | [X.X] |
| K8 | Routing/Over/Under-provision rates vs oracle tier | routing-decision quality (not model ceiling) | `routing_accuracy`, `over_provision_rate`, `under_provision_rate` | [X.X] |
| K9 | Bootstrap 95% CIs on every headline; paired-bootstrap p for router-vs-T4 and WCG | statistical validity prior routing papers usually omit (C8) | `bootstrap_ci`, `paired_bootstrap_pvalue` | [X.X] |
| K10 | Workflow Context Gain (EM and F1) at matched cost, with p-value | our novel axis; internal contrast, not cross-paper (C4) | `workflow_context_gain` | [X.X] |
| K11 | Cost-basis disclosure: hypothetical $/1M, ratios-only | so dollars are not over-read (R10) | 03_MODEL_MATRIX.md note | required text |
| K12 | Routing-unit disclosure: per-call vs per-query | prevents apples-to-apples misreading (C1) | this doc SS.0 / SS.3 | required text |
| K13 | Tier-collapse note for 2-tier comparisons (RouteLLM, Hybrid-LLM) | makes 4-tier results readable against 2-tier work | T1-vs-T4 slice of frontier | [X.X] |
| K14 | Tier-4 EM anomaly flag + EM/F1 dual reporting | honesty; explains QRR > 100% on EM (C8) | BASELINE_VALIDATION_REPORT.md SS.4 | documented |

When K1-K14 are reported, our results can be placed on the same cost-vs-quality plane as
RouteLLM, FrugalGPT, AutoMix, Adaptive-Inference, Hybrid-LLM, and -- most importantly --
**MasRouter**, with the per-call / multi-agent / workflow-signal differences (K12, K13, SS.3)
explicitly annotated so no reviewer expects a head-to-head that the experimental design does not
support.

---

## 5. Citable framing (one paragraph for the related-work section)

We do not claim to beat any prior router head-to-head; we claim a **new routing unit**. On the
shared comparison surface -- cost-vs-quality curve, fraction of calls per tier, oracle gap, and
Pareto frontier (SS.1) -- our routers are reportable in the same units as RouteLLM, FrugalGPT,
AutoMix, Adaptive-Inference, and Hybrid-LLM (modulo per-call vs per-query and hypothetical cost,
SS.3). The closest prior work, **MasRouter**, selects the multi-agent system per query; we keep
the system fixed and re-route each agent per call on upstream context, so our results are
**complementary and composable** with MasRouter rather than competing. Our distinctive,
non-borrowed evidence is the **Workflow Context Gain** (C4), an internal matched-cost contrast
that isolates the value of workflow signals and has no equivalent in the prior literature.
