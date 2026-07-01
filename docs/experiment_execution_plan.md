# Experiment Execution Plan (PART 7)

> Status: FROZEN (methodology freeze; results are placeholders). No code changes; commands are quoted verbatim from 16_EXPERIMENT_MANIFEST.md.
> Related docs (do not duplicate): [16_EXPERIMENT_MANIFEST.md](16_EXPERIMENT_MANIFEST.md), [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md), [13_METRICS_AND_FORMULAS.md](13_METRICS_AND_FORMULAS.md), [07_RISK_REGISTER.md](07_RISK_REGISTER.md), [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md), [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md), [15_FIGURE_PLAN.md](15_FIGURE_PLAN.md), [08_RESULTS_LEDGER.md](08_RESULTS_LEDGER.md), [04_BASELINE_PROTOCOL.md](04_BASELINE_PROTOCOL.md), [06_EVALUATION_PROTOCOL.md](06_EVALUATION_PROTOCOL.md).

This is the optimal order to execute the remaining experiments given current repo state. It is optimized for, in priority order: (1) maximum publication value, (2) minimum API spend, (3) maximum information gain. Every command is copy-paste identical to 16_EXPERIMENT_MANIFEST.md so the home machine "only runs commands".

---

## 0. Current repo state (the starting point)

What is already DONE and needs no re-run:

- GSM8K baselines T1-T4 are LOCKED (EM + cost final). Verified offline: GSM8K EM T1/T2/T3/T4 = 94.5/96.0/97.0/97.0; cost(200) = $0.031/0.219/0.822/1.182. Source: [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md) section 2.
- Oracle (sim, GSM8K) = 98.5% EM @ $0.0485/200 (verified offline). This already gives C2 on GSM8K.
- Schematic figures F1, F2, F3 (fig1_architecture, fig2_workflow, fig3_router_decision_flow) generated.
- Data figures F3/F4 Pareto + utilization for GSM8K (fig4_pareto_gsm8k, fig5_utilization_gsm8k) generated from baselines.

What is PENDING (drives this plan):

- HotpotQA/MuSiQue F1 is unreliable everywhere (legacy logger truncated response_text at 500 chars; some cells partial). All 8 multi-hop baselines must be re-run clean under the new logger/schema. EM-only values exist today (preliminary): HotpotQA EM T1=63.0, T2=65.25 (118/200), T3=54.17 (48/200), T4=37.5; MuSiQue EM T1=31.5, T2=55.0, T3=47.5, T4=25.6 (199/200).
- All routed runs (proposed routers, references live, ablations) are PENDING for all datasets.
- The learned router .pkl is not trained yet.

Known anomaly (carry through all reporting, C8 / R2 / R3): Tier-4 EM is LOWER than weaker tiers on multi-hop (likely EM brittleness to verbose frontier answers). ALWAYS report token-F1 alongside EM.

---

## 1. Cost / risk model used to rank the phases

- All models are free in practice; "API Cost" below means hypothetical published-price spend used only for cost ratios (R10), plus the REAL operational constraint: rate limits and shared token pools.
- The only hard operational constraint is RISK R1: Tier 3 (Llama 3.1 405B, GitHub Models) and Tier 4 (GPT-4.1, GitHub Models) share ONE GitHub Models token pool. Never run T3 and T4 concurrently. T1 is Ollama-local (no quota). T2 is Groq (separate quota).
- GitHub throttling (~8s effective per call observed) makes any T3/T4-heavy run multi-hour; this is the dominant runtime cost, not money.
- Offline phases (Phase 0) consume zero API and zero quota and are therefore always run first.

---

## PHASE 0 - Offline (free) wins available NOW

Goal: bank every result that needs no API before spending a single token. These validate the simulation, train the learned router, and refresh all data figures that can come from baselines/sim. Run on the office machine today. Zero quota, zero R1 exposure.

| # | Experiment | Command | Depends-on | Expected Runtime | Expected API Cost | Expected Risk | Expected Publication Value |
|---|-----------|---------|-----------|------------------|-------------------|---------------|----------------------------|
| 0.1 | Offline sanity (pipeline runs without API) | `python tests/test_offline.py` | one-time setup (section 0 of manifest) | seconds-minutes | None (offline) | None | Gate: confirms runner/router code path is healthy before any spend. |
| 0.2 | Validate baselines (confirm GSM8K LOCKED, multi-hop status) | `python scripts/validate_baselines.py` | existing baseline CSVs | seconds (offline) | None | None | Establishes truth table for [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md); confirms what Phase 1 must re-run. |
| 0.3 | Simulate routing on GSM8K (4 complete tiers + oracle) | `python simulate_routing.py --dataset gsm8k` | 0.2 | seconds (offline) | None | None | C2 oracle gap on GSM8K (oracle 98.5% EM @ $0.0485 verified offline); preliminary T1 main row; de-risks live routed runs by predicting their numbers. |
| 0.4 | Simulate complexity/learned with question features | `python simulate_routing.py --with-questions --routers complexity learned` | 0.3, needs `datasets` | minutes (offline; dataset load) | None | R4 (N=200 CI width only) | Preliminary C4/C6 estimates on GSM8K to sanity-check live runs; feeds T6 Router Comparison preview. |
| 0.5 | Train the learned router | `python train_router.py --datasets gsm8k hotpotqa musique --model tree --max-depth 5` | 0.2, needs `datasets` + scikit-learn | minutes (offline) | None | R5 (no test guard on metrics; mitigated by 0.1) | C6: produces `results/routing/learned_router.pkl` + `_report.json` (train accuracy). REQUIRED before any live `--router learned`. |
| 0.6 | Aggregate current results | `python aggregate_results.py` | 0.2 | seconds (offline) | None | None | Refreshes `results/master_results.{json,csv,md}`; populates T1/T2 columns for locked GSM8K + preliminary multi-hop EM. |
| 0.7 | Build figures from sim/baselines | `python make_figures.py` | 0.6 (falls back to sim if no live data) | seconds (offline) | None | None | F1/F2/F3 schematics + F3 Pareto (fig4_pareto_gsm8k) and utilization (fig5_utilization_gsm8k); the GSM8K Pareto is the first headline-figure draft. |

Phase 0 exit criterion: `results/master_results.*` regenerated, learned_router.pkl exists, GSM8K Pareto/utilization figures refreshed, simulation numbers recorded so live runs can be checked against them. After this, GSM8K-side C2 (and a GSM8K preview of C3/C4/C6) is in hand with zero spend.

---

## PHASE 1 - Complete the 8 multi-hop baselines (GSM8K LOCKED)

Goal: clean, untruncated, N=200 EM + F1 for HotpotQA and MuSiQue across all four tiers under one logger/schema. This is the single highest-value paid block: it is a hard dependency for the oracle on multi-hop (oracle reads baselines), for every Quality-Retention / Cost-Savings reference (the all-Tier-4 ceiling), and for C7 generalization. GSM8K is LOCKED - do NOT re-run it.

Ordering within Phase 1 minimizes R1 exposure: run T1 (Ollama-local, free, no quota) first; then T2 (Groq, separate quota); then T3 and T4 STRICTLY ONE AT A TIME (shared GitHub pool). HotpotQA before MuSiQue because HotpotQA already has clean partial T2/T3 CSVs that `--resume` extends (less new spend) and HotpotQA is the mid-difficulty anchor that unlocks the first multi-hop Pareto.

| # | Experiment | Command | Depends-on | Expected Runtime | Expected API Cost | Expected Risk | Expected Publication Value |
|---|-----------|---------|-----------|------------------|-------------------|---------------|----------------------------|
| 1.1 | HotpotQA baseline T1 (fresh) | `python run_experiment.py --dataset hotpotqa --router fixed_t1 --num-problems 200` | Phase 0 | ~tens of min (Ollama-local, no throttle) | Free; no shared quota (local) | None (T1 local) | C7 + T1 Main Results HotpotQA T1 row with clean F1; cheap-tier ceiling for the routing story. |
| 1.2 | HotpotQA baseline T2 (resume partial 118/200) | `python run_experiment.py --dataset hotpotqa --router fixed_t2 --num-problems 200 --resume` | 1.1 (ordering) | ~tens of min (Groq; only ~82 new problems) | Free; Groq quota only (not R1 pool) | R8 (max_tokens truncation) - monitor for [ERROR] rows | Completes HotpotQA T2 row (EM+F1); T2 is the current best multi-hop EM. |
| 1.3 | HotpotQA baseline T3 (resume partial 48/200) | `python run_experiment.py --dataset hotpotqa --router fixed_t3 --num-problems 200 --resume` | 1.2 done AND no T4 running | ~hours (GitHub Models, ~8s throttle, ~152 new problems) | Free; consumes shared GitHub pool | R1 (shared T3/T4 pool) - run alone | HotpotQA T3 row (EM+F1); needed for oracle + Pareto frontier. |
| 1.4 | HotpotQA baseline T4 (fresh; the all-T4 reference) | `python run_experiment.py --dataset hotpotqa --router fixed_t4 --num-problems 200` | 1.3 FULLY finished (R1) | ~hours (GitHub Models throttle, 200 problems) | Free; consumes shared GitHub pool | R1 (run after T3 only); R2 (verify/explain the T4 EM anomaly) | Defines the all-Tier-4 ceiling => unlocks all HotpotQA Cost-Savings% and Quality-Retention (C3); F1 will likely lift the anomalous T4 EM (C8). |
| 1.5 | MuSiQue baseline T1 (fresh) | `python run_experiment.py --dataset musique --router fixed_t1 --num-problems 200` | 1.4 (or parallel: T1 is local, safe anytime) | ~tens of min (Ollama-local) | Free; local | None (local) | C7 hardest-dataset T1 row (EM+F1). |
| 1.6 | MuSiQue baseline T2 (fresh) | `python run_experiment.py --dataset musique --router fixed_t2 --num-problems 200` | 1.5 | ~tens of min (Groq) | Free; Groq quota | R8 - monitor [ERROR] rows | MuSiQue T2 row; T2 is strong on MuSiQue (EM 55.0 prelim). |
| 1.7 | MuSiQue baseline T3 (fresh) | `python run_experiment.py --dataset musique --router fixed_t3 --num-problems 200` | 1.6 done AND no T4 running | ~hours (GitHub Models throttle, 200) | Free; shared GitHub pool | R1 - run alone | MuSiQue T3 row (EM+F1). |
| 1.8 | MuSiQue baseline T4 (fresh; the all-T4 reference) | `python run_experiment.py --dataset musique --router fixed_t4 --num-problems 200` | 1.7 FULLY finished (R1) | ~hours (GitHub Models throttle, 200) | Free; shared GitHub pool | R1; R3 (MuSiQue T4 EM anomaly) | MuSiQue all-Tier-4 ceiling => MuSiQue C3 reference; completes C7 baseline coverage. |
| 1.9 | Re-validate all 12 cells | `python scripts/validate_baselines.py` | 1.1-1.8 | seconds (offline) | None | None | Confirms all 12 baseline cells LOCKED with clean F1; gate for Phase 2. |
| 1.10 | Aggregate + refresh figures | `python aggregate_results.py` then `python make_figures.py` | 1.9 | seconds (offline) | None | None | T1 Main Results + T2 Cost Analysis full across 3 datasets; F3 Pareto + F6 utilization for HotpotQA/MuSiQue; multi-hop oracle row (extends C2 to C7). |

Phase 1 exit criterion: validate_baselines reports 12/12 LOCKED with non-truncated F1; master table has all baseline rows for all 3 datasets; multi-hop oracle now computable (oracle reads baselines). This alone delivers C2 (full), C7 (baseline side), and the all-Tier-4 reference required by every later cost/retention claim. Re-run `python scripts/recompute_metrics_from_dataset.py` ONLY if any legacy/truncated CSV must be backfilled (per BASELINE_VALIDATION_REPORT section 5).

---

## PHASE 2 - Proposed routers on the highest-value dataset first

Goal: get the headline claims (C3, C4) on the single most informative dataset before spending on all three. Highest-value dataset = HotpotQA (2-hop): it has a real cost/quality spread between tiers (unlike near-ceiling GSM8K, R6) yet is less brittle than MuSiQue, and its clean baselines land first in Phase 1. Run the proposed routers (cascade, adaptive) plus the matched-cost comparator (complexity) and references (random, fixed_mixed, learned) so WCG is computable immediately.

Within Phase 2, order routers to front-load information gain and minimize R1 burn: the proposed routers escalate to T3/T4 only on low-confidence calls, so their shared-pool spend is far below a fixed-T4 baseline. Run them one at a time (any router can touch the shared pool via escalation).

| # | Experiment | Command | Depends-on | Expected Runtime | Expected API Cost | Expected Risk | Expected Publication Value |
|---|-----------|---------|-----------|------------------|-------------------|---------------|----------------------------|
| 2.1 | HotpotQA cascade (primary innovation) | `python run_experiment.py --dataset hotpotqa --router cascade --num-problems 200` | Phase 1 complete (oracle/reference need baselines) | ~hours (some T3/T4 escalations, throttled) | Free; partial shared-pool use on escalations only (<< fixed_t4) | R1 (escalations hit shared pool) - no concurrent T3/T4 jobs | C3 (quality retention @ low cost) + C4 numerator (workflow-aware quality) on HotpotQA; F5 escalation, F3 Pareto marker. |
| 2.2 | HotpotQA adaptive (full method) | `python run_experiment.py --dataset hotpotqa --router adaptive --num-problems 200` | 2.1 done (R1 serialization) | ~hours (escalations, budget-capped) | Free; shared pool on escalations; budget cap reduces it | R1 - run alone | C3 + C4 headline (adaptive vs complexity at matched cost); the single most important routed run. |
| 2.3 | HotpotQA complexity (matched-cost comparator) | `python run_experiment.py --dataset hotpotqa --router complexity --num-problems 200` | 2.2 done (R1) | ~hours (difficulty-driven tier mix) | Free; shared pool when complexity maps to T3/T4 | R1 - run alone | C4 denominator: the best context-free (difficulty-only) router; WCG = quality(adaptive/cascade) - quality(complexity) at <= cost. Without this row C4 cannot be computed. |
| 2.4 | HotpotQA learned | `python run_experiment.py --dataset hotpotqa --router learned --num-problems 200` | 0.5 (.pkl) + Phase 1; after 2.3 (R1) | ~hours (predicted tier mix) | Free; shared pool per predicted tier | R1 - run alone | C6: learned vs random/complexity at matched cost; T6 Router Comparison row. |
| 2.5 | HotpotQA random (floor) | `python run_experiment.py --dataset hotpotqa --router random --num-problems 200` | after 2.4 (R1) | ~hours (uniform tier => frequent T3/T4) | Free; HIGH shared-pool draw (uniform hits T4 ~25% of calls) | R1 - run alone; heaviest pool user in Phase 2 | Lower-bound anchor for C6 and the Pareto; defensible floor. Lower priority than proposed/comparator routers - run after them. |
| 2.6 | HotpotQA fixed_mixed (static role map) | `python run_experiment.py --dataset hotpotqa --router fixed_mixed --num-problems 200` | after 2.5 (R1) | ~hours (static A->2,S->4,V->1; S=T4 each problem) | Free; shared pool every problem (solver=T4) | R1 - run alone | Isolates static role assignment vs adaptive (supports C4 framing: role map alone is not enough). |
| 2.7 | Aggregate + figures (HotpotQA mid-point) | `python aggregate_results.py` then `python make_figures.py` | 2.1-2.6 | seconds (offline) | None | None | First full T6 Router Comparison + WCG (C4) + F3 Pareto with all HotpotQA routers; the paper's headline result in draft. |

Phase 2 exit criterion: master table has all 6 routed rows for HotpotQA; WCG and paired bootstrap p-value computable (routing_metrics.workflow_context_gain, paired_bootstrap_pvalue). At this point C3 + C4 (headline) + C6 are demonstrated on the highest-value dataset. If the budget/quota is throttled here, the paper still has its headline on one strong multi-hop dataset plus full GSM8K - a viable submission.

---

## PHASE 3 - Remaining routers + ablations

Goal: generalize C3/C4/C6 across datasets (C7) and prove each signal contributes (C5). Do GSM8K and MuSiQue routed runs, then the ablations. GSM8K routed runs are cheap (near-ceiling, mostly T1/T2; R6) and validate the live-vs-sim agreement, so run them first within Phase 3; MuSiQue next (hardest, most expensive). Ablations run on HotpotQA (the dataset where signals matter most and baselines/proposed rows already exist).

### 3a. GSM8K routed runs (cheap; validates simulation)

| # | Experiment | Command | Depends-on | Expected Runtime | Expected API Cost | Expected Risk | Expected Publication Value |
|---|-----------|---------|-----------|------------------|-------------------|---------------|----------------------------|
| 3.1 | GSM8K proposed + references (loop) | `python run_experiment.py --dataset gsm8k --router <R> --num-problems 200` for `<R>` in `random, fixed_mixed, complexity, cascade, adaptive, learned` (one at a time) | 0.5 (.pkl), GSM8K baselines LOCKED | ~hours total (mostly T1/T2; few escalations) | Free; low shared-pool draw (near-ceiling => rarely escalates) | R1 (serialize the rare T3/T4 escalations); R6 (small headroom on GSM8K) | C7 single-hop generalization; live validation of the Phase 0 GSM8K simulation (sim-vs-live agreement is itself a credibility result for C8). |

### 3b. MuSiQue routed runs (hardest dataset; most expensive)

| # | Experiment | Command | Depends-on | Expected Runtime | Expected API Cost | Expected Risk | Expected Publication Value |
|---|-----------|---------|-----------|------------------|-------------------|---------------|----------------------------|
| 3.2 | MuSiQue proposed + references (loop) | `python run_experiment.py --dataset musique --router <R> --num-problems 200` for `<R>` in `cascade, adaptive, complexity, learned, random, fixed_mixed` (one at a time; proposed first) | Phase 1 (MuSiQue baselines), 0.5 | ~hours each (most escalations of any dataset; deepest reasoning) | Free; HIGHEST shared-pool draw of all phases (2-4 hop => frequent T3/T4) | R1 - strictly serialize; R3 (MuSiQue T4 anomaly); R8 (truncation on long contexts) | Completes C7 across the full difficulty gradient (1->2->2-4 hop); MuSiQue is the strongest test of the workflow-context story (C4) under hard multi-hop. |

### 3c. Ablations on HotpotQA (proves C5; supports C4)

Run the four single-signal-removed variants of the full method against `adaptive`. Per ROUTER_FINAL_SPEC section 6, the variants are registered routers (`adaptive_no_role`, `adaptive_no_confidence`, `adaptive_no_complexity`, `adaptive_no_budget`); the manifest also shows `cascade` as the "full" anchor for the ablation pattern. Use the registered router names so each is logged under a distinct id.

| # | Experiment | Command | Depends-on | Expected Runtime | Expected API Cost | Expected Risk | Expected Publication Value |
|---|-----------|---------|-----------|------------------|-------------------|---------------|----------------------------|
| 3.3 | HotpotQA full anchor (already from 2.1/2.2) | `python run_experiment.py --dataset hotpotqa --router cascade --num-problems 200` (full anchor per manifest section D) | 2.1/2.2 | reuse existing run (no re-run if present) | Free | R1 if re-run | Ablation baseline ("full method") row for F4. |
| 3.4 | HotpotQA adaptive_no_confidence | `python run_experiment.py --dataset hotpotqa --router adaptive_no_confidence --num-problems 200` | 1.x baselines; after prior job (R1) | ~hours (no cascade escalation => fewer T3/T4 calls) | Free; lower shared-pool draw (confidence off) | R1 - run alone | C5: does workflow cascading matter? (removing confidence is the most direct WCG ablation; highest-value ablation - run first). |
| 3.5 | HotpotQA adaptive_no_role | `python run_experiment.py --dataset hotpotqa --router adaptive_no_role --num-problems 200` | after 3.4 (R1) | ~hours | Free; shared pool on escalations | R1 - run alone | C5: does per-agent role routing matter? |
| 3.6 | HotpotQA adaptive_no_complexity | `python run_experiment.py --dataset hotpotqa --router adaptive_no_complexity --num-problems 200` | after 3.5 (R1) | ~hours | Free; shared pool on escalations | R1 - run alone | C5: how much is "just difficulty"? (directly supports the C4 framing). |
| 3.7 | HotpotQA adaptive_no_budget | `python run_experiment.py --dataset hotpotqa --router adaptive_no_budget --num-problems 200` | after 3.6 (R1) | ~hours (no budget cap => may escalate more) | Free; HIGHER shared-pool draw (cap removed) | R1 - run alone | C5: does budget-capping matter? (also exposes Budget Violations, spec-only/analysis-time). |
| 3.8 | Aggregate + figures | `python aggregate_results.py` then `python make_figures.py` | 3.1-3.7 | seconds (offline) | None | None | T4 Ablation Study + F4 ablation (fig6_ablation_hotpotqa); T7 Cross-Dataset Generalization across all 3 datasets; completes C5 and C7. |

Phase 3 exit criterion: all 15 routers represented on at least HotpotQA; proposed + references on all 3 datasets; ablations complete on HotpotQA. C5, C6, C7 fully evidenced; T4, T6, T7 and F4 populated.

---

## PHASE 4 - Diagnostics

Goal: convert logged columns into the diagnostic and honesty metrics. These require NO new runs and NO code changes - they are computed at analysis time from the existing CSV columns (timestamp, ..., confidence, escalated_from, ground_truth, predicted, etc.). Implemented diagnostics come straight from routing_metrics.py; the spec-only metrics are computed from the logged columns during analysis.

| # | Experiment | Command | Depends-on | Expected Runtime | Expected API Cost | Expected Risk | Expected Publication Value |
|---|-----------|---------|-----------|------------------|-------------------|---------------|----------------------------|
| 4.1 | Implemented diagnostics (over/under-provision, escalation rate, routing accuracy, token efficiency, throughput) | `python aggregate_results.py` (re-emits master table with routing_metrics: over_provision_rate, under_provision_rate, escalation_rate, routing_accuracy, token_efficiency, throughput_per_min) | Phase 2/3 routed CSVs | seconds (offline) | None | None | T3 Latency + SECONDARY/DIAGNOSTIC columns; F5 escalation (fig7_escalation_*); supports C3/C4 narrative. |
| 4.2 | Bootstrap CIs + paired p-values | computed by `python aggregate_results.py` via `routing_metrics.bootstrap_ci`, `routing_metrics.paired_bootstrap_pvalue` (router-vs-T4 and WCG comparisons) | 4.1 | seconds (offline) | None | None; R4 (N=200 CI width, ~+/-7pts at 50%) | C8 statistical honesty; significance on every headline + WCG (C4). |
| 4.3 | Spec-only / analysis-time metrics (no code change): Win Rate (paired correct/f1), Utility Score (= quality - lambda*cost, freeze lambda), Pareto Dominance (from (cost,quality) points), Budget Violations (cost_spent vs cost_budget on budget runs), Confidence Calibration Error / ECE (confidence vs correct) | analysis-time computation from logged CSV columns (no script in manifest; derive from `results/routing/*.csv` + `results/baselines/*.csv`); freeze lambda before computing Utility | Phase 2/3 CSVs | minutes (offline analysis) | None | None | DIAGNOSTIC tier of T5 Error Analysis + F7 failure categories; ECE/calibration directly supports the cascade confidence-signal story (C4/C5). Mark all five as spec-only / analysis-time in the paper. |
| 4.4 | T4 anomaly inspection (EM vs F1 on T4 verifier outputs) | manual inspection of full (untruncated) `response_text` for fixed_t4 rows on HotpotQA/MuSiQue (no script; clean responses exist after Phase 1) | 1.4, 1.8 | minutes (offline reading) | None | R2, R3 (resolve/explain anomaly) | C8: confirms EM brittleness hypothesis; if confirmed, strengthens the efficiency story (cheap tier matches frontier on EM). |
| 4.5 | Final aggregate + figures | `python aggregate_results.py` then `python make_figures.py` | 4.1-4.4 | seconds (offline) | None | None | Final master_results.* + all figures F1-F7; paper-ready tables T1-T7. |

Phase 4 exit criterion: all PRIMARY/SECONDARY/DIAGNOSTIC metric tiers populated; CIs and p-values on every headline; anomaly explained with EM+F1; all figures regenerated. Paper is data-complete (C1-C8 evidenced).

---

## Critical path

```
0.1 test_offline
  -> 0.2 validate_baselines
       -> 0.5 train_router (learned_router.pkl; GATE for every --router learned)
       -> [PHASE 1, R1-serialized] 1.1 hpqa_t1 -> 1.2 hpqa_t2 -> 1.3 hpqa_t3 -> 1.4 hpqa_t4
               -> 1.5 musq_t1 -> 1.6 musq_t2 -> 1.7 musq_t3 -> 1.8 musq_t4
               -> 1.9 validate -> 1.10 aggregate+figures   (all-Tier-4 ceiling + multi-hop oracle ready)
                    -> [PHASE 2 headline] 2.3 complexity (denominator)
                                         + 2.1 cascade / 2.2 adaptive (numerator)
                          -> 2.7 aggregate  => C3 + C4 (WCG) on HotpotQA  <== MINIMUM VIABLE PAPER
                               -> [PHASE 3] 3.2 MuSiQue proposed + 3.4-3.7 ablations
                                    -> [PHASE 4] 4.1 aggregate -> 4.2 CIs/p-values -> 4.5 final figures
```

The longest chain is the HotpotQA tier ladder (1.1->1.4) and the MuSiQue tier ladder (1.5->1.8), both forced serial by R1 on the T3/T4 hops, followed by the R1-serialized routed runs. T1 (Ollama-local) and T2 (Groq) hops can in principle overlap with a GitHub-pool job since they do not touch the shared pool, but only the T3/T4 GitHub-pool jobs are the binding constraint - never overlap two of those.

Minimum viable paper = Phase 0 + Phase 1 (HotpotQA) + Phase 2 steps 2.1/2.2/2.3 + aggregate: this yields full GSM8K (C2), the all-Tier-4 ceiling, and the C3/C4 headline on one strong multi-hop dataset. Everything after that buys breadth (C7), ablation depth (C5), the learned-router story (C6), and diagnostics/CIs (C8).

---

## Stop conditions / what to do if a tier is throttled

R1 is the controlling risk. If the GitHub Models token pool (T3 + T4) is depleted or WAF-banned mid-run:

1. STOP all GitHub-pool jobs immediately (both T3 and T4). Do not retry in a loop (R1). Every run is resumable - re-add `--resume` later to continue the same CSV from where it stopped.
2. Switch to non-pool work that needs no GitHub quota: run/continue T1 (Ollama-local) and T2 (Groq) cells, and run all offline steps (validate_baselines, train_router, simulate_routing, aggregate_results, make_figures). Phase 0 and the T1/T2 portions of Phase 1 are always safe.
3. If only T3 or only T4 is throttled, finish the other one alone (still never concurrently), then resume the throttled one in a later session.
4. If the pool stays down, fall back per R1 mitigation to OpenRouter / SambaNova for the T3/T4 models in a separate session (configuration only; no code change), keeping T3 and T4 serialized.
5. If Groq (T2) is throttled: pause T2, proceed with T1-local and offline steps, resume T2 when quota resets.
6. Token-budget pressure (R1) ranking - if you can only afford a subset of paid runs, spend in this order of value-per-token: (a) Phase 1 HotpotQA T1-T4 (unlocks ceiling + oracle), (b) Phase 2 complexity + adaptive + cascade on HotpotQA (the C4 headline), (c) Phase 1 MuSiQue T1-T4, (d) Phase 3 MuSiQue proposed routers, (e) ablations, (f) random/fixed_mixed references (highest pool draw, lowest marginal claim value - cut these first).
7. Anomaly stop (R2/R3): if a clean re-run still shows Tier-4 EM below weaker tiers, do NOT block - it is an analysis item. Report EM AND F1 (C8); F1 is expected to lift the T4 number. Proceed.
8. Truncation/error stop (R8): if `[ERROR]` rows appear in a CSV (max_tokens=2048 truncation), note the affected problems, finish the run (it is resumable), and exclude/flag those rows at analysis time. Do not change code (freeze).
9. Sample-size note (R4): N=200 gives ~+/-7pt EM CIs at 50%. If reviewers demand more, N=500 is a post-freeze extension, not part of this plan.

All result numbers in downstream tables remain PLACEHOLDERS ([X.X] / TBD-after-run) until the corresponding live run lands; the only numbers cited as real are the VERIFIED-OFFLINE GSM8K baselines and GSM8K oracle in section 0, explicitly labelled "verified offline".
