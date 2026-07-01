# Reviewer Attack Report (Adversarial Pre-Mortem)

> Status: FROZEN (adversarial pre-mortem)
>
> Cross-referenced freeze docs (single sources of truth; this report does not
> duplicate them, it points at them): [claim_evidence_matrix.md](claim_evidence_matrix.md),
> [statistical_validation_plan.md](statistical_validation_plan.md),
> [learned_router_risk_assessment.md](learned_router_risk_assessment.md),
> [experiment_execution_plan.md](experiment_execution_plan.md). Supporting:
> [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md), [ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md),
> [BASELINE_VALIDATION_REPORT.md](BASELINE_VALIDATION_REPORT.md), [07_RISK_REGISTER.md](07_RISK_REGISTER.md).

## Meta-review (area chair)

Four independent reviewers (ACL x2, EMNLP x1, NeurIPS Systems x1) converge, without
coordination, on the same verdict: Strong Reject, severity 4.5-4.7/5, and -- critically --
all four state that they would NOT be moved by a rebuttal that merely promises to run the
missing experiments, because the central comparative claims (C3 quality-retention, C4 the
headline Workflow Context Gain, C5 the signal ablation, C6 the learned router, C7 cross-dataset)
are unrun placeholders by the authors' own freeze documents ("Status: pending", "[X.X]/
TBD-after-run"; see claim_evidence_matrix.md Sec 2 and 17_RESEARCH_CLAIMS.md C3-C7), so there
is at present no result to review. Beyond the missing data, every reviewer independently
verified two design-level defects that would invalidate the results even after the runs land:
(a) the learned router's train/test split is per-example not per-problem, leaking each problem's
near-duplicate role rows across the split (learned_router_risk_assessment.md L1, Critical), and
its oracle labels are problem-level and identical across roles, so the role one-hot is provably
label-irrelevant and the "workflow-aware" learned router mathematically collapses to a
difficulty classifier (L5, Critical), structurally contradicting the C4/C6 novelty; and (b) the
multi-hop baselines that every downstream number is computed against are on mixed N and mixed
active/backup sources with a documented Tier-4 EM anomaly (the most expensive tier scores the
LOWEST multi-hop EM) and zero trustworthy F1 (BASELINE_VALIDATION_REPORT.md Sec 2/4), so no
paired test, oracle label, or quality-retention reference is currently admissible. The cost
story is admittedly hypothetical (ROUTER_FINAL_SPEC.md Sec 7; R10) and never sensitivity-
analyzed; the "confidence" signal that powers the cascade is a five-bucket lexical keyword
counter plus a hardcoded constant 0.7 at inference, making the calibration/ECE story vacuous;
and the registered one-sided WCG test is not even the test that is implemented (the only engine,
paired_bootstrap_pvalue, is two-sided). The engineering discipline -- one shared code path for
baselines and routers, the claim-evidence matrix, the freeze, the unusually honest baseline
report -- is genuinely commendable and is the project's strongest asset, but it is currently a
careful experiment plan and system spec, not a finished research contribution. The path to a
submittable paper is the one the authors already wrote down in experiment_execution_plan.md
(Phases 1-4) plus the corrected protocols in learned_router_risk_assessment.md ("minimum bar to
publish", items 1-9); until at least the three Critical learned-router fixes and the clean
N=200 multi-hop F1 re-runs land, the headline cannot be stated honestly.

## Severity matrix

Rows = the five concern areas. Columns = the four reviewers. Each cell = the WORST severity that
reviewer raised in that area (5 = paper-killing / disqualifying; 4 = major, blocks acceptance;
3 = significant). All four reviewers raised all five areas (verified below the table).

| Concern area | ACL #1 | ACL #2 | EMNLP #1 | NeurIPS Systems #1 |
|------------------|--------------------------------|--------------------------------|--------------------------------|--------------------------------|
| Novelty | 5 (incremental; C1 is an API, not a finding; role-collapse) | 4 (positional; signals shown to do no work) | 4 (workflow signal inert in learned variant) | 4 (incremental heuristic; learned = difficulty clf) |
| Baseline | 5 (mixed-N; T4 EM anomaly; all multi-hop F1 pending) | 5 (fails hardest here; apples-to-oranges; broken ceiling) | 4 (mixed-N/source; offline-sim-as-result) | 5 (disqualifying for multi-hop; broken T4 ceiling) |
| Evaluation | 5 (headline does not exist; offline sim as evidence) | 5 (sim-as-result; broken EM as label source) | 5 (T4 anomaly poisons labels; WCG arms from different regimes) | 5 (headline unmeasured; one pipeline shape; no OOD) |
| Statistical | 5 (leakage; underpowered; no MC correction) | 5 (leakage + circular + role-collapse all Critical) | 5 (registered test != implemented; underpowered; forking paths) | 5 (leakage voids the one number; underpowered; MC) |
| Reproducibility  | 4 (results are placeholders; fragile label selection) | 4 (placeholders; truncated F1; non-deterministic labels) | 4 (placeholders; provider drift; truncation) | 5 (core area; free-tier quota + shared pool + provider drift) |

Coverage verification (all 5 areas x all 4 reviewers present):
- ACL #1: Novelty (primary), Baseline, Evaluation, Statistical, Reproducibility -- all 5 present.
- ACL #2: Novelty, Baseline (primary), Evaluation, Statistical, Reproducibility -- all 5 present.
- EMNLP #1: Novelty, Baseline, Evaluation, Statistical (primary angle), Reproducibility -- all 5 present.
- NeurIPS Systems #1: Novelty, Baseline, Evaluation, Statistical, Reproducibility (core area) -- all 5 present.

## TOP 10 reasons this paper gets rejected (ranked, with required rebuttal/mitigation)

Ranked by how many reviewers raised it x severity x whether it is fixable by a re-run vs a
redesign. Each item names the rebuttal needed and the exact freeze doc that already specifies it.

1. THE HEADLINE DOES NOT EXIST YET (raised by all 4; severity 5).
 C3, C4 (the headline WCG), C5, C6, C7 are status "pending"/placeholder
 (claim_evidence_matrix.md Sec 2; 17_RESEARCH_CLAIMS.md C3-C7 marked TBD/needs home-machine
 runs). The only live numbers are GSM8K single-tier EM and an offline-simulated oracle.
 - Rebuttal/mitigation: there is no rebuttal short of running it. Execute
 experiment_execution_plan.md Phase 1 (clean N=200 multi-hop baselines) then Phase 2 steps
 2.1/2.2/2.3 (cascade, adaptive, complexity on HotpotQA) -- the plan's own
 "MINIMUM VIABLE PAPER" milestone -- to produce C3 + C4 on one strong dataset, then Phases
 3-4 for C5/C6/C7/diagnostics. Report each number only when its claim_evidence_matrix.md row
 is fully green (experiment run, metric computed, CI + paired test reported, figure + table
 present).

2. LEARNED-ROUTER ROLE-COLLAPSE STRUCTURALLY CONTRADICTS THE NOVELTY (all 4; severity 5).
 Oracle labels are problem-level and identical across the three roles
 (learned_router_risk_assessment.md L5, Critical), so the role one-hot has zero mutual
 information with the label; a depth-5 tree will (correctly) ignore role and the "workflow-
 aware learned router" is mathematically a difficulty classifier -- the exact thing C4 claims
 to beat. The headline distinction collapses for the one data-driven component.
 - Rebuttal/mitigation: learned_router_risk_assessment.md "minimum bar" item 6 -- report
 role-feature importances/coefficients (show whether they are ~0), and either construct
 ROLE-SPECIFIC oracle labels (cheapest tier sufficient for that role's sub-task, so role
 carries label signal) or retract the workflow-aware claim for the learned router. Do not
 claim workflow-awareness until role demonstrably changes the router's output.

3. TRAIN/TEST LEAKAGE VOIDS THE ONLY MODEL NUMBER THAT EXISTS (all 4; severity 5).
 train_router.py:53-55 uses train_test_split(X, y, test_size=0.25, stratify=y) with no
 groups= and no problem_id; build_training_data emits 3 near-duplicate rows per problem
 (7/10 features byte-identical, same label), so the same problem lands in both train and test
 (learned_router_risk_assessment.md L1, Critical; L14/L15 compound it). The reported
 test_accuracy is an in-sample near-duplicate-retrieval score, not generalization. This is
 the single most damaging methodological flaw and a guaranteed desk-level objection.
 - Rebuttal/mitigation: learned_router_risk_assessment.md "minimum bar" item 1 -- re-evaluate
 with repeated GroupKFold/GroupShuffleSplit grouped by problem_id; report mean +/- std over
 >=5 seeds; report effective N = #problems not #rows; state explicitly that the per-example
 split was discarded. statistical_validation_plan.md Sec 3 names paired/grouped resampling
 as the contract. The current learned_router_report.json test_accuracy must NOT be cited.

4. MIXED-N, MIXED-SOURCE MULTI-HOP BASELINES POISON EVERY DOWNSTREAM COMPARISON (all 4; sev 5).
 Per BASELINE_VALIDATION_REPORT.md Sec 2: HotpotQA T2 = 118/200, T3 = 48/200 (PARTIAL),
 T4 from a truncated backup; MuSiQue T4 = 199/200, T2/T3 from backup. oracle_labels picks
 whichever CSV has more rows (training_data.py: len(recs) > len(best)). Paired bootstrap
 requires the SAME problems; EM-on-118 vs EM-on-48 is not a controlled contrast, and every
 oracle label / QRR-vs-T4 / cost-savings number inherits the incomparability.
 - Rebuttal/mitigation: experiment_execution_plan.md Phase 1 (steps 1.1-1.9) re-runs all 8
 multi-hop baselines clean at N=200 under one logger, then validate_baselines reports 12/12
 LOCKED. learned_router_risk_assessment.md item 5 -- restrict label construction to the
 intersection of problem_ids present and untruncated across all four tiers; report dropped-N
 and label-4 rate before/after. Redo every cross-tier comparison on the common problem_id
 intersection only.

5. THE TIER-4 EM ANOMALY CORRUPTS THE ORACLE LABELS, NOT JUST THE HEADLINE (all 4; severity 5).
 On multi-hop, the most expensive tier scores the LOWEST EM (HotpotQA T4=37.5 vs T1=63.0/
 T2=65.25; MuSiQue T4=25.63 vs T2=55.0; BASELINE_VALIDATION_REPORT.md Sec 4; R2/R3). Oracle
 labels use the brittle EM correct column (learned_router_risk_assessment.md L3, High), so a
 genuinely-best-but-verbose T4 answer is scored 0 and mislabeled, and the label=4 fallback
 conflates "hardest" with "no tier EM-solved it" (L4, High). The paper cannot simultaneously
 use fixed_t4 as the quality ceiling (C3 "retention vs all-Tier-4") and report T4 as the
 worst tier; QRR > 100% becomes a measurement artifact.
 - Rebuttal/mitigation: claim_evidence_matrix.md C8 mandates F1 alongside EM on all multi-hop
 and forbids EM-only multi-hop claims. learned_router_risk_assessment.md item 5 -- produce
 F1-aware oracle labels, report EM-vs-F1 label agreement, ablate router results under both
 label definitions, and re-report how many labels flip. experiment_execution_plan.md step
 4.4 inspects untruncated T4 responses to confirm/explain the anomaly. State the corrected
 quality reference explicitly.

6. THE REGISTERED STATISTICAL TEST IS NOT THE IMPLEMENTED TEST; PLAN != INSTRUMENT (EMNLP #1
 primary, echoed by ACL #1/#2, NeurIPS; severity 5).
 statistical_validation_plan.md Sec 8 pre-registers a ONE-SIDED primary (H1: WCG > 0), but
 the only implemented engine, paired_bootstrap_pvalue, computes a TWO-SIDED p (centers diffs,
 counts abs(s) >= abs(obs)). McNemar/Wilcoxon/permutation/Holm are all spec-only / analysis-
 time, run in a notebook that is not in the artifact (statistical_validation_plan.md Sec 11).
 So the entire significance apparatus, including multiple-comparison correction, is currently
 aspirational.
 - Rebuttal/mitigation: implement the registered one-sided WCG test (or state precisely which
 function emits the registered p) and the spec-only McNemar/Wilcoxon/Holm pipeline against
 the frozen per-problem CSVs per statistical_validation_plan.md Sec 5-6, then report the
 (effect size, CI, Holm-adjusted p) triple from Sec 7 for every claim-backing comparison.

7. CIRCULAR / IN-SAMPLE EVALUATION; NO HELD-OUT-BY-PROBLEM OR OOD SPLIT (all 4; severity 5
 statistical, also the core of C7).
 Oracle labels are derived from the SAME 200 problems on which the router is then evaluated
 (learned_router_risk_assessment.md L2, Critical), and training pools all three datasets and
 evaluates on the same three (L10, High; NeurIPS "one pipeline shape, no generality"). So
 "generalizes across difficulty" (C7) is in-distribution interpolation, not generalization.
 - Rebuttal/mitigation: learned_router_risk_assessment.md "minimum bar" item 2 -- train labels
 and evaluate routing on DISJOINT problem_id sets, AND add leave-one-dataset-out cross-
 dataset results (train on 2, test on the third) with the in-distribution-vs-OOD gap.
 statistical_validation_plan.md Sec 6 treats each dataset as its own correction family;
 C7 requires the effect to hold on the pre-specified primary dataset and be directionally
 consistent on the others.

8. UNDERPOWERED N=200 WITH NO MULTIPLE-COMPARISON CORRECTION FOR THE EFFECTS CLAIMED (all 4;
 severity 5 statistical).
 The authors concede ~+/-7 pt EM 95% CI half-width at N=200 and that only >=8-10 pt effects
 are reliably detectable per dataset (statistical_validation_plan.md Sec 10; R4). A plausible
 WCG and the C5 ablation deltas are smaller than this, and the family is 15 routers x 3
 datasets x 2 metrics with overlapping baselines. A one-sided primary on an underpowered
 design invites a false positive.
 - Rebuttal/mitigation: report achieved power for the one-sided WCG and justify (or drop) the
 one-sided choice; apply the Holm-Bonferroni correction already specified in
 statistical_validation_plan.md Sec 6 within each comparison family; lean on the paired-
 power advantage (Sec 10) but report the actual per-problem difference variances post-run;
 escalate to the N=500 target (statistical_validation_plan.md Sec 10; R4) for the headline.

9. OFFLINE SIMULATION PRESENTED AS THE QUANTITATIVE RESULT; THE SIMULATOR ASSUMES AWAY THE
 EFFECT (all 4; severity 5 evaluation).
 The only "verified" numbers (GSM8K oracle 98.5% EM @ $0.0485) come from simulate_routing.py.
 Its INDEPENDENCE ASSUMPTION approximates routed correctness by the verifier-tier baseline
 correctness and proxies F1 by EM -- i.e. it assumes the Analyzer/Solver tier choices have no
 effect on the final answer, which is precisely the cross-agent interaction the paper claims
 to exploit. cascade/adaptive are flagged NOT_SIMULABLE while complexity is simulable, so the
 matched-cost WCG would pit a live-only arm against a simulable arm. claim_evidence_matrix.md
 Sec 4 explicitly forbids treating simulate_routing.py estimates as live results.
 - Rebuttal/mitigation: provide LIVE (not simulated) cost/quality for the oracle and all
 proposed routers on identical N=200 problems (experiment_execution_plan.md Phases 2-3);
 quantify how far the independence-assumption simulator deviates from live runs on GSM8K
 where both are computable; label every offline number "verified offline" per the matrix.

10. HYPOTHETICAL COSTS + UNCALIBRATED/HARDCODED CONFIDENCE + SHARED-POOL CONFOUND MAKE THE
 EFFICIENCY AND MECHANISM CLAIMS UNFALSIFIABLE (all 4; severity 4-5 across evaluation /
 statistical / reproducibility).
 All models are free in practice; tier prices are assigned published list prices
 (ROUTER_FINAL_SPEC.md Sec 7; R10), and the T4 2.00/8.00 output skew single-handedly drives
 the savings narrative -- never sensitivity-analyzed. The cascade's "confidence" is a five-
 bucket lexical keyword counter (extract_confidence in signals.py) and the learned router
 hardcodes confidence=0.7 at inference (learned_router_risk_assessment.md L8, Medium), so
 any ECE/calibration discussion (C8) is vacuous and the "workflow confidence drives gains"
 mechanism is untestable. T3 and T4 share one GitHub Models token pool (R1), so every
 latency/throughput number is confounded by rate-limit queueing, and the endpoints are
 unversioned moving targets (provider drift; R2/R3 partly attribute the T4 anomaly to it).
 - Rebuttal/mitigation: run a price-vector sensitivity analysis (especially the T4 8.0 output
 price) and stop framing ratios as deployment savings, per claim_evidence_matrix.md Sec 4
 out-of-scope list and R10; for confidence, learned_router_risk_assessment.md item 7 --
 expose max(predict_proba) and report ECE + reliability diagram, or exclude the learned
 router from all confidence/ECE analysis and state the constant-0.7 limitation; validate
 that extract_confidence correlates with correctness before claiming the cascade works; per
 experiment_execution_plan.md Sec 1 and R1, never run T3/T4 concurrently and demote latency
 to a secondary proxy with the shared-pool confound disclosed (it should not appear as
 efficiency evidence at all).

---

## The four full reviews (verbatim)

## ACL Reviewer #1

### Summary & Recommendation

The paper proposes *per-agent* LLM tier routing inside a fixed Analyzer -> Solver -> Verifier pipeline: before each agent call, a router picks one of four model tiers using question complexity plus three "workflow-only" signals (the agent's role, an upstream-confidence cascade, and a running cost budget). The headline scientific claim (C4) is a positive "Workflow Context Gain" -- that workflow-aware routing beats a difficulty-only router at matched cost. Supporting claims cover an oracle headroom argument (C2), quality-retention-at-lower-cost (C3), a signal ablation (C5), a learned classifier router (C6), cross-dataset generalization (C7), and an honesty/robustness section (C8).

**Recommendation: Strong Reject (severity ~4.5/5).** Two independent grounds each suffice on their own. (1) **Novelty:** the contribution is an incremental, engineering-grade variation on query-level routing/cascading (RouteLLM, FrugalGPT, AutoMix, MasRouter); the "per-agent" framing does not constitute a new research idea, and C1 is argued by a related-work checklist rather than demonstrated. (2) **Evidence:** the headline result (C4) and essentially every comparative claim (C3, C5, C6, C7) are placeholders -- by the repo's own status flags they are "pending"/"TBD-after-run". The only live numbers are GSM8K single-tier EM baselines and an *offline-simulated* oracle. A paper whose central claim has not been run, built on a learned-router pipeline that leaks by construction and multi-hop baselines that are on mixed-N broken data, is not ready for a top-tier venue. This is, at present, a well-documented **system spec masquerading as a research paper**.

### Novelty concerns (primary)

This is the crux. The submission positions itself against RouteLLM/FrugalGPT/AutoMix/MasRouter (17_RESEARCH_CLAIMS.md C1; ROUTER_FINAL_SPEC.md Sec 1), and the *entire* claimed delta is moving the routing decision from the query to the agent invocation. After stripping the framing, the actual mechanism (ROUTER_FINAL_SPEC.md Sec 5) is:

1. complexity -> base tier via fixed thresholds (0.2, 0.4, 0.7) -- this is FrugalGPT/RouteLLM difficulty routing;
2. **role adjustment**: verifier -1 tier, solver +1, analyzer unchanged -- a three-entry lookup table, not a learned or theoretically-motivated policy;
3. **confidence cascade**: escalate +1 if upstream confidence < tau=0.5, de-escalate if > 0.8 -- this is *exactly* the AutoMix/cascade pattern, with a hand-coded lexical confidence in place of AutoMix's self-verification;
4. **budget clamp** to Tier 1 when budget is near zero.

None of (1)-(4) is novel in isolation, and the composition is a hand-tuned heuristic with magic constants. MasRouter already does multi-agent / role-conditioned routing; the paper must show concretely what per-agent routing buys *over* MasRouter and over simply running RouteLLM three times (once per agent) -- and it must show it with significance, not a feature-matrix table. As written, C1's "evidence" is "literature positioning + the interface that consumes these signals" (17_RESEARCH_CLAIMS.md, C1) -- i.e., the contribution is an API, not a finding. That is a system contribution dressed as a research claim.

Worse, the supposed differentiator is undercut by the implementation. The "learned" router (the data-driven embodiment of the per-agent idea) is trained on **problem-level** oracle labels that are *identical across all three roles* (src/router/training_data.py, build_training_data emits one row per (problem, role) but assigns the same `tier` to analyzer/solver/verifier). The role one-hot is therefore non-predictive of the label by construction, so any reasonable classifier ignores role and **collapses to a difficulty classifier** -- the very thing the paper claims to transcend. The headline workflow-vs-difficulty distinction (C4) is thus structurally contradicted by the learned router's own design. If the central novelty cannot survive contact with the authors' own training pipeline, the novelty is not there.

### Baseline concerns

The baselines are not in a publishable state, and this poisons everything downstream:

- **Mixed N, mixed sources.** Per BASELINE_VALIDATION_REPORT.md Sec 2: HotpotQA T2 = 118/200, T3 = 48/200 (PARTIAL); MuSiQue T4 = 199/200; several cells come from `baselines_backup` rather than the active run; T4 cells are from truncated backups. Comparing oracle/router quality and cost against tiers measured on *different problem subsets* is not a fair comparison -- the oracle's "cheapest correct tier" is computed over inconsistent coverage (oracle_labels in training_data.py simply takes whichever CSV has more rows).
- **The Tier-4 EM anomaly.** T4 EM is *below* T1/T2/T3 on both multi-hop sets (HotpotQA T1=63.0 vs T4=37.5; MuSiQue T1=31.5 vs T4=25.63; BASELINE_VALIDATION_REPORT.md Sec 4). The authors hypothesize EM brittleness to verbose answers, which is plausible -- but until the clean F1 re-run exists, the strongest tier is *mismeasured*, and the oracle labels that flow into the learned router are correspondingly wrong (a genuinely-best-but-verbose T4 answer is labeled "incorrect" -> mislabeled oracle, L3). The paper cannot simultaneously claim T4 is the quality ceiling (C3 quality-retention "vs all-Tier-4") and report T4 as the *worst* tier on two of three datasets.
- **All multi-hop F1 is pending** (legacy logger truncated `response_text[:500]`). Two of three datasets therefore have *no* trustworthy soft-match metric, yet C7 (generalization across the difficulty gradient) and C8 (always report F1) depend on it.

Until HotpotQA/MuSiQue are re-run clean at N=200 under one logger, no multi-hop claim is admissible.

### Evaluation concerns

- **The headline does not exist yet.** C4 (Workflow Context Gain) is status "pending" (17_RESEARCH_CLAIMS.md). So are C3, C5, C6, C7. The matrix (claim_evidence_matrix.md) is explicit that "All result numbers are PLACEHOLDERS". A reviewer cannot accept a paper on the promise of its central experiment.
- **Offline simulation as evidence.** The oracle gap (C2) -- the one quantitative headline offered -- is produced by `simulate_routing.py` (oracle 98.5% EM @ \$0.0485 vs T4 97.0% @ \$1.18 on GSM8K). The oracle is a per-problem upper bound by construction; reporting it as a "savings" result, computed offline, overstates what a deployable router can achieve. Live routed runs are exactly what is missing.
- **Hypothetical costs.** All models are free in practice; tier prices are assigned published list prices (ROUTER_FINAL_SPEC.md Sec 7). Reporting "cost savings x" on fabricated unit costs is fragile -- the entire cost-quality Pareto (F3) tilts with the chosen price vector (note T4 out-price 8.00 vs T3 2.66 is what makes T4 "expensive"; pick different prices and the story changes). Ratios on hypothetical prices are not a deployment result.
- **Confidence signal is a keyword counter.** `extract_confidence` (src/router/signals.py) returns one of {0.3,0.4,0.6,0.7,0.9} by counting hand-listed phrases ("clearly", "i'm not sure"). The cascade -- the "primary innovation" -- is driven by this. It is trivially gameable, language-specific, and not validated. C5-confidence's degradation, if observed, may reflect noise in a keyword heuristic rather than the value of "workflow cascading".
- **Shared token pool / confound.** T3 and T4 share the GitHub Models token pool (R1; BASELINE_VALIDATION_REPORT.md Sec 5 warns not to run them simultaneously). Any latency/throughput comparison (T3) across these tiers is confounded by rate-limit contention, not model speed.

### Statistical concerns

- **N=200 is underpowered for the comparisons that matter.** The authors themselves note EM 95% CIs of ~+/-7 pts at p=0.5 (claim_evidence_matrix.md Sec 4). The WCG effect (adaptive minus complexity at matched cost) is plausibly a few points; distinguishing it from zero at N=200, with a one-sided test, is borderline at best and invites a false positive. A power analysis is required before C4 can be the headline.
- **Learned-router leakage inflates the one statistic that exists for C6.** `train_test_split(X, y, test_size=0.25, stratify=y)` splits **by example, stratified by label**, not grouped by `problem_id`. Each problem contributes 3 rows with the same label and near-identical features (only the role one-hot differs), so the *same problem appears in train and test* (L1, CRITICAL). The reported test accuracy is therefore an upper-biased in-sample estimate. Compounding this, the labels are derived from the same 200 problems on which the router is later evaluated (L2): there is no held-out-by-problem or cross-dataset split anywhere. The only number backing C6 ("learned approximates oracle") is thus untrustworthy by construction.
- **Multiple comparisons.** C5 runs four ablations x three datasets, C3/C4/C6/C7 add many more paired bootstrap tests, all against overlapping baselines. No correction (Bonferroni/Holm/FDR) is mentioned in the matrix's statistical plan. With this many tests at p<0.05, spurious "significant" deltas are expected.
- **Class imbalance on tiny data.** GSM8K labels are dominated by T1; a depth-5 DecisionTree with `class_weight='balanced'` on ~200 problems and skewed labels (L7) is high-variance; reported accuracies will swing with the random seed. Grouped cross-validation, not a single split, is the minimum bar.

### Reproducibility concerns

To the authors' credit the repo is meticulously documented and the pipeline is unified (baselines = FixedTierRouter), which aids reproducibility *in principle*. But the *results* are not reproducible because they largely do not exist yet, and the data that does exist is inconsistent:

- Results are explicitly placeholders (claim_evidence_matrix.md); a reader cannot re-derive the paper's tables.
- The multi-hop CSVs are partial / truncated / drawn from `baselines_backup`; reproducing the oracle labels depends on which CSV happened to have more rows (training_data.py picks `len(recs) > len(best)`), a fragile, non-deterministic-across-environments rule.
- The learned router hardcodes `RoutingDecision.confidence = 0.7` at inference rather than emitting the model's probability, so the logged `confidence` column is meaningless for the learned router -- any ECE/calibration analysis (C8 diagnostic) on it is vacuous.
- The Tier-4 anomaly resolution, the F1 re-runs, and all routed runs are deferred to a "home machine" -- i.e., the reproducibility-critical experiments are future work.

### Questions to authors

1. Concretely, what does per-agent routing achieve that running an existing query-level router (RouteLLM/FrugalGPT) once *per agent* does not? Provide that head-to-head, with paired significance, as a baseline. How does it compare to MasRouter, which already does multi-agent routing?
2. Given that oracle labels are identical across the three roles, by what mechanism can the learned router use the role feature to do anything role-specific? Please report the learned tree's feature importances; if role importance ~ 0, the workflow-aware claim (C6/C4) collapses.
3. Will you re-run the learned-router evaluation with a **GroupShuffleSplit by problem_id** and a **cross-dataset (train on 2, test on 1)** protocol? Report both numbers; the per-example stratified split should not appear in the paper.
4. How do you reconcile "quality retention vs all-Tier-4" (C3) with T4 being the *worst* tier on HotpotQA and MuSiQue? Does the reference ceiling switch per dataset, and if so what does QRR > 100% mean?
5. After the clean F1 re-runs, do the oracle labels change (because verbose T4 answers flip from "incorrect" to high-F1)? If so, the entire training signal changes -- please rebuild and re-report.
6. What is the statistical power to detect WCG > 0 at N=200, and what correction will you apply across the dozens of paired tests in the matrix?
7. Validate the lexical confidence: how well does `extract_confidence` correlate with actual answer correctness? Without that, the cascade's contribution (C5-confidence) is uninterpretable.
8. Replace hypothetical prices with a sensitivity analysis: does the Pareto/savings story survive reasonable perturbations of the price vector?

---

## ACL Reviewer #2

### Summary & Recommendation
The paper proposes per-agent LLM tier routing inside a fixed Analyzer->Solver->Verifier pipeline, with a catalogue of 15 routers (oracle/random/fixed/complexity/cascade/adaptive/learned + ablations) evaluated on GSM8K, HotpotQA, and MuSiQue (N=200 each), and headline claims of (C3) quality retention at lower cost, (C4) "Workflow Context Gain > 0", (C5) per-signal ablation, and (C6) a learned router that approximates the oracle.

The framing is clean and the engineering discipline (one shared code path for baselines and routers; an explicit claim-evidence matrix) is commendable. But as a scientific artifact this submission is not evaluable in its current state. By the authors' own freeze documents, the central comparative claims (C3, C4, C5, C6) are unrun placeholders ("Status: pending", "[X.X]/TBD-after-run"); the multi-hop baselines that everything else is computed against are on mixed N and mixed sources with a known Tier-4 EM anomaly and zero trustworthy F1; the cost model is admittedly hypothetical; and the one learned component I could audit in code has a textbook train/test leak plus a label construction that makes its "workflow-aware" framing impossible. I recommend **Strong Reject** (severity 4.5/5; soundness 1.5/5). I would not be moved to borderline without a complete re-run with corrected protocols.

### Novelty concerns
The novelty claim (C1) is narrow and largely positional: "route each agent, not the whole query." That is a reasonable design point relative to RouteLLM/FrugalGPT/AutoMix/MasRouter, but the paper supplies no head-to-head against any of them  -- only a feature-checklist "positioning matrix" is promised (claim_evidence_matrix.md, C1 row). A novel control surface is only interesting if the extra signals it exposes (role, upstream confidence, stage, budget) actually buy something. Two findings in the code cut against that:
- The "workflow" signal `agent_role` cannot help the learned router at all, because the training label is problem-level and identical across roles (see Baseline/Statistical concerns). So the most data-driven instantiation of the contribution reduces to a difficulty classifier  -- the exact thing C4 claims to beat.
- The "upstream confidence" signal that powers the cascade is `extract_confidence()` in signals.py: a hand-listed keyword matcher returning one of {0.3,0.4,0.6,0.7,0.9}. That is not a confidence estimate; it is a lexical sentiment proxy. Building a "primary innovation" (confidence cascading) on a five-bucket keyword heuristic is a weak foundation for a novelty claim.

Net: the design point may be new, but the paper does not yet demonstrate that the new signals are doing any work, which is the only thing that would make the novelty matter.

### Baseline concerns
This is where the paper fails hardest, and it is squarely in my lane.

1. Mixed-N, mixed-source baselines. Per BASELINE_VALIDATION_REPORT.md Sec 2, the multi-hop fixed-tier baselines are not comparable to each other: HotpotQA T2 = 118/200, T3 = 48/200 (both "PARTIAL"), T4 = 200 but from a truncated backup; MuSiQue has three cells from backup and T4 = 199/200. Reporting EM across tiers computed on different problem subsets, from different CSV sources, is an apples-to-oranges comparison. Any cross-tier statement (oracle gap, QRR-vs-T4, cost savings) inherits this incomparability. EM-on-118 vs EM-on-48 is not a controlled contrast, and a paired bootstrap requires the SAME problems  -- which these cells do not share.

2. The Tier-4 EM anomaly is treated as a feature, not a bug. T4 (the most expensive tier) scores the LOWEST multi-hop EM (HotpotQA 37.5 vs T1 63.0/T2 65.25; MuSiQue 25.63 vs T2 55.0). The authors hypothesize EM brittleness to verbose answers and say it "strengthens" the efficiency story. That is exactly backwards for the evaluation: if the metric mis-scores the strongest model, then (a) the oracle labels are corrupted (oracle = cheapest EM-correct tier, training_data.py:31-56, so genuinely-best-but-verbose T4 answers are mislabeled), (b) QRR-vs-T4 can exceed 100% as a measurement artifact, and (c) the headline "cheaper tier beats frontier" claim may be a tokenizer/extractor artifact rather than a finding. Until clean F1 exists, no multi-hop baseline number is trustworthy, and the authors' own report concedes "F1 is not [reliable]... every multi-hop CSV is either truncated or partial."

3. Unfair/weak comparison targets. The strongest scientific contrast (C4) is `adaptive`/`cascade` vs `complexity` at matched cost. But this comparison is entirely unrun (placeholder), and `complexity` itself is a hand-weighted linear score (signals.py:46-52) with arbitrary thresholds (0.2/0.4/0.7). A reviewer cannot tell whether a positive WCG, if it ever materializes, reflects "workflow context" or just a luckier threshold setting. There is no tuning protocol, no held-out threshold selection, and no comparison to the trivial 1-line complexity-threshold baseline that an ablation-minded reader would demand.

4. Hypothetical costs. ROUTER_FINAL_SPEC.md Sec 7: all models are free in practice; the paper assigns published prices and reports ratios. Every "cost reduction factor", Pareto position, and "matched-cost" WCG marker therefore depends on invented in/out prices (note T4 = 2.00/8.00 has a 4x output skew that single-handedly drives the savings narrative). Cost-based claims built on counterfactual prices are not deployment evidence; the conclusions are a function of the assumed price vector, which is never sensitivity-analyzed.

### Evaluation concerns
1. Offline simulation presented as results. The only "verified" numbers (GSM8K oracle 98.5% @ $0.0485) come from `simulate_routing.py` / `validate_baselines.py`  -- offline estimates, not live routed runs. The freeze docs are explicit that no claim may be made "solely from simulate_routing.py estimates as if they were live results", yet the only quantitative evidence in hand is exactly that. The proposed routers (cascade/adaptive/learned) appear never to have been executed end-to-end; their rows are TBD. There is no paper here yet  -- there is an experiment plan.

2. Brittle EM as the primary metric on tasks where it demonstrably misfires. The authors know EM is unreliable on verbose multi-hop answers (that is the whole T4 anomaly) yet EM is the label source for the oracle and the learned router, and F1  -- the metric that would fix this  -- is "PENDING" everywhere on multi-hop. You cannot anchor labels and headline accuracy on the metric you have already shown to be broken on two of three datasets.

3. Dataset choice and N. Three benchmarks, N=200 each, is thin for a routing paper whose claim is generalization across a difficulty gradient (C7). The authors themselves note ~+/-7pt EM 95% CIs at N=200. With three skewed-difficulty datasets and no OOD/cross-dataset test, the "generalization" claim is at best suggestive. GSM8K (EM-only, mostly solvable by T1) dominates the pooled label distribution, biasing any pooled learned router toward T1.

4. Token pool confound. T3 and T4 share the GitHub Models token pool (R1), and the report warns "do not run them simultaneously." Any latency/throughput numbers (T3 table) are therefore confounded by shared-quota throttling, not model speed  -- the paper correctly demotes latency to secondary, but it should not appear as efficiency evidence at all under a shared pool.

### Statistical concerns
1. Learned-router leakage (critical). train_router.py:53-55 calls `train_test_split(X, y, test_size=0.25, stratify=y)`. Examples are per (problem, role) rows (training_data.py:84-92), three per problem, sharing one problem-level label and feature vectors that differ only in a role one-hot. Per-example, label-stratified splitting therefore places the same problem in both train and test. The reported "test accuracy" is in-sample and inflated. The only defensible protocols  -- GroupKFold on problem_id, or train-on-dataset-A/test-on-B  -- are absent. Every C6 number derived from this split is invalid.

2. Circular/in-sample evaluation (critical). Oracle labels are derived from the SAME 200 baseline problems the learned router is then evaluated on. Even with a correct per-problem split for training, evaluating the deployed router on those same 200 problems is in-sample. There is no held-out-by-problem or cross-dataset evaluation set.

3. Role-collapse makes C6/C4 unfalsifiable in the intended direction (critical). Because the label is identical across roles, the role one-hot has zero mutual information with y; a depth-5 tree will (correctly) ignore it. So the "learned, workflow-aware" router is mathematically a difficulty classifier. It cannot demonstrate that role/workflow context helps, which is the paper's headline.

4. Underpowered and uncorrected. N=200 with ~+/-7pt CIs, multiple comparisons across 15 routers x 3 datasets x 2 metrics, and a one-sided pre-registered WCG test  -- yet no multiple-comparison correction is described, and the paired bootstrap requires same-problem alignment that the mixed-N baselines violate. A depth-5 tree on ~7 effective numeric features with class_weight="balanced" on a tiny, skewed (GSM8K-dominated) label set is unstable; no cross-validation variance is reported.

5. Uncalibrated, hardcoded confidence. learned_router.py:81 returns `confidence=0.7` regardless of the model's predicted probability, and the cascade's confidence is the lexical heuristic above. Any ECE/calibration discussion (C8) is therefore vacuous, and the budget/escalation behavior is driven by a constant, not a signal.

### Reproducibility concerns
- Results are placeholders. By design ("results are placeholders"), the manuscript cannot be reproduced because the numbers do not yet exist. This alone blocks acceptance.
- Two data provenance issues prevent re-creation of even the existing baselines: the legacy logger truncated `response_text[:500]` (so F1 is unrecoverable from the published CSVs), and a `validation_problems` resume bug corrupted stats-JSON F1 (producing impossible F1<EM). The fix exists in code but the affected cells must be fully re-run; until then the released artifacts cannot reproduce the reported EM/F1.
- Mixed active/backup sources with `if len(recs) > len(best)` selection (training_data.py:40-44) means the oracle labels depend on whichever CSV happens to be longer at run time  -- non-deterministic across machines/checkouts.
- Hypothetical cost vector is a free parameter never frozen with a sensitivity study, so cost-based results are not reproducible in any externally meaningful sense.

### Questions to authors
1. Will you re-train and re-evaluate the learned router with GroupKFold on `problem_id` (or strictly cross-dataset: train on two, test on the third), and report the drop from the current per-example, label-stratified split? What is the test accuracy under the correct protocol?
2. Given that oracle labels are identical across the three roles, what information could the role one-hot possibly contribute to tier prediction  -- and if none, how do you reconcile this with the C4/C6 "workflow-aware" claims? Please report the tree's actual feature importances on role.
3. The multi-hop baselines are on mixed N (e.g., HotpotQA T3=48/200) and mixed sources. How can any paired test, oracle label, or QRR-vs-T4 be valid before all four tiers are re-run clean at N=200 on the same problems with untruncated F1?
4. The Tier-4 EM anomaly corrupts EM-based oracle labels for exactly the verbose-but-correct frontier answers. Will you re-derive oracle labels from F1 (or human-checked correctness) and report how many labels flip? What fraction of the current oracle/learned story survives?
5. Please run the full sensitivity analysis of all cost-based conclusions to the assumed price vector (especially the T4 8.0 output price). Do the savings/Pareto/WCG conclusions hold under reasonable alternative prices?
6. Why a depth-5 tree on 7 hand-crafted features (entity_count = capitalized words; estimated_hops = keyword//2) rather than a one-line complexity threshold? Please show, with grouped CV, per-dataset breakdown, and a paired test, that the learned router beats `complexity`  -- not just `random`.
7. The reported routing confidence is hardcoded 0.7 and the cascade confidence is a keyword heuristic. How can C8's calibration/ECE discussion be meaningful, and will you replace the constant with the model's predicted probability and report real calibration?
8. With N=200 (~+/-7pt CIs) and 15 routers x 3 datasets x 2 metrics, what multiple-comparison correction do you apply, and what is the achieved power for the one-sided WCG test?

---

## EMNLP Reviewer #1

### Summary & Recommendation
The paper proposes *per-agent* LLM tier routing inside a fixed Analyzer->Solver->Verifier pipeline, with a "Workflow Context Gain" (WCG) headline: workflow-aware routers (`adaptive`/`cascade`) supposedly beat a difficulty-only router (`complexity`) at matched cost. The accompanying freeze docs (`statistical_validation_plan.md`, `claim_evidence_matrix.md`) are unusually disciplined about *intended* rigor -- pre-registration, Holm-Bonferroni, paired bootstrap, EM+F1 honesty. I want to credit that. But intent is not evidence. As submitted, the central result does not exist (it is a placeholder), the one quantitative artifact that does exist (the learned router) is invalidated by a textbook train/test leak, the core "confidence" signal is a hardcoded constant / lexical heuristic, and the supporting baselines are offline simulations on mixed-N data riddled with a known EM anomaly. The gap between the methods-freeze ambition and the actual instrument is too large for a top-tier venue.

**Recommendation: Strong Reject. Severity ~4.7/5, reviewer confidence 4/5.** I would not be moved by a rebuttal that promises to run the experiments; I can only review what is here.

### Novelty concerns
The "per-agent routing" framing (C1) is positioned against RouteLLM/FrugalGPT/AutoMix/MasRouter as a new design point, but the realized method collapses toward a difficulty classifier and undercuts the novelty:
- The `learned` router's labels are *problem-level* (training_data.py lines 84-92 assign the same `int(tier)` to all three role rows). The role one-hot therefore carries zero information about the label, so a depth-5 tree cannot use role to reduce loss -- the "workflow-aware learned router" is, by construction, a difficulty -> tier map with three redundant copies of each problem. The headline distinction from `complexity` evaporates for the one data-driven component.
- C1 itself is explicitly a "feasibility/novelty claim ... None (no statistical comparison)" (claim_evidence_matrix.md C1 row). Novelty as a pure positioning argument, with the workflow signal demonstrably inert in the learned variant and untested elsewhere, is not enough for EMNLP. The reviewer's standing question (L11) stands: why a 7-feature tree (or four hand-tuned thresholds) over a one-line complexity cutoff? The paper provides no answer that survives the leakage and confidence issues below.

### Baseline concerns
- **Mixed-N, mixed-source baselines.** Per BASELINE_VALIDATION_REPORT.md S2, multi-hop tiers are assembled from active+backup CSVs at N in {48 (hotpot T3), 118 (hotpot T2), 199 (musique T4), 200}. `oracle_labels` and `simulate.load_tier_records` both pick "the most complete CSV available" and silently mix sources/N. Comparisons across tiers built on different problem subsets are not paired and not comparable; any oracle/savings number inherits this incoherence.
- **Offline simulation masquerading as result.** The flagship "oracle 98.5% EM @ \$0.0485" (C2) is a `simulate.py` estimate, not a live routed run. simulate.py's own docstring (lines 14-19) states the INDEPENDENCE ASSUMPTION: routed correctness is approximated by the *verifier-tier baseline correctness*, cost is summed per-tier baseline cost, and F1 is proxied by EM (line 128, `f1_flags.append(1.0 if is_correct else 0.0)`). This assumes the Analyzer/Solver tier choices have no effect on the final answer -- precisely the cross-agent interaction the paper claims to exploit. Using a routing-effect-free simulator to motivate a routing-effect paper is circular.
- **Hypothetical costs.** All tier prices are hypothetical (ROUTER_FINAL_SPEC.md S7); savings are ratios over assumed published prices. Fine if confined to ratios, but combined with T3/T4 sharing one GitHub token pool (R1) and offline cost summation, the "cost reduction" axis of the Pareto figure is doubly synthetic.

### Evaluation concerns
- **The Tier-4 EM anomaly poisons the labels, not just the headline.** T4 EM is *below* weaker tiers on both multi-hop sets (HotpotQA 37.5 vs 63.0/65.25/54.17; MuSiQue 25.63 vs 31.5/55.0/47.5). The authors attribute this to EM brittleness to verbose answers -- plausibly correct, which is exactly the problem: `oracle_labels` uses the brittle EM `correct` column (training_data.py line 45). A genuinely-best-but-verbose T4 answer scored 0 is mislabeled, so the "oracle" supervision the learned router and the oracle headroom (C2) both rest on is systematically wrong on the hard cases. F1 -- the metric the authors say is needed -- is PENDING for all multi-hop cells, so no current number can be reported honestly under the authors' own C8 rule ("no EM-only multi-hop claim").
- **label=4 fallback conflates 'unsolvable' with 'hardest'** (training_data.py lines 50-55): problems no tier solved are labeled T4, teaching the router to burn the most expensive tier on exactly the problems where it adds nothing. This biases over-provisioning and inflates apparent T4 demand.
- **WCG arms come from different regimes.** simulate.py lists `cascade`/`adaptive` as NOT_SIMULABLE (depend on generated-text confidence) while `complexity` is simulable. The headline matched-cost comparison therefore pits a live-only arm against a simulate-able arm; unless both are run live on identical problems, the WCG is not a controlled contrast.

### Statistical concerns (primary angle)
This is where the paper most clearly fails an EMNLP rigor bar.
1. **No data behind the headline.** C4 (WCG) is `Status: pending`; every routed-run cell in claim_evidence_matrix.md is `[X.X]/TBD-after-run`. There is nothing to test. A statistical plan, however careful, is not a result.
2. **Registered test != implemented test.** Section 8 pre-registers a *one-sided* primary (H1: WCG > 0). The only implemented engine, `paired_bootstrap_pvalue` (routing_metrics.py line 170), computes a *two-sided* p (centers diffs, counts `abs(s) >= abs(obs)`). McNemar/Wilcoxon/Holm/permutation are all "spec-only" -- i.e. not implemented, run "in an analysis notebook" that does not exist in the artifact. So the entire significance apparatus (multiple-comparison correction included) is aspirational.
3. **Underpowered for the effects claimed.** The authors concede ~+/-7 pt bootstrap half-width at N=200 and that only >= 8-10 pt EM effects are detectable per dataset (statistical_validation_plan.md S10). The ablation (C5) deltas and a plausible WCG are smaller than this. The paired-power hand-wave does not rescue this without the actual paired-difference variances, which cannot be known pre-run.
4. **Matched-cost selection is a forking path.** "matched (<=) cost" is enforced as a post-hoc filter on a noisy cost mean with no tolerance band, no CI on the cost gap, and no penalty for selecting the comparator. Choosing among {complexity, fixed_mixed, random} as the "best context-free at <= cost" comparator after seeing costs is a researcher-degrees-of-freedom problem that the Holm correction (applied only within fixed families) does not cover.
5. **Confidence is not a calibrated signal.** `extract_confidence` (signals.py 64-106) returns one of six constants from keyword matching; `LearnedRouter` hardcodes `confidence=0.7` (learned_router.py line 81) irrespective of the model's posterior. The cascade mechanism thresholds (tau=0.5/0.8) operate on this lexical staircase. ECE is spec-only and explicitly disclaimed ("No claim that confidence is calibrated"). The paper's causal story -- workflow *confidence* drives gains -- is therefore mechanistically untestable with the current signal; any observed WCG could be a lexical-cue artifact correlated with answer length/dataset.
6. **Leakage inflates the only reported model number.** `train_test_split(X, y, ..., stratify=y)` (train_router.py 53-55) splits per-example; with 3 near-duplicate role rows per problem and test_size=0.25, the same `problem_id` lands in both train and test. The reported `test_accuracy` is in-sample. There is no GroupKFold by problem, no cross-dataset OOD split, and oracle labels are derived from the same 200 problems used for live C6 eval -- so the held-out claim is unsupported twice over.

### Reproducibility concerns
- **Artifacts are placeholders by design.** claim_evidence_matrix.md is "FROZEN (... results are placeholders)"; master tables/figures are TBD. The repo documents *how* numbers would be produced, not the numbers. This is not reproducibility; it is a protocol.
- **Determinism does not equal validity.** seed=42, n_boot=10000 are fixed, but a deterministic in-sample accuracy and a deterministic two-sided bootstrap on absent data reproduce only the artifacts of the flaws above.
- **Pipeline brittleness undermines re-runs.** The legacy logger truncated `response_text[:500]`, breaking F1 recomputation on all backup CSVs and several active ones; the `validation_problems` resume bug corrupted stats-JSON F1. The fix exists but the clean multi-hop re-runs have not been done, so an independent party cannot today regenerate a single multi-hop F1 headline.

### Questions to authors
1. Run the WCG comparison live for `adaptive`/`cascade` AND `complexity` on identical N=200 problems, report effect size + paired CI + the *one-sided* test you registered (and fix `paired_bootstrap_pvalue`, or state which implemented function produces the registered p). Without this there is no headline.
2. Re-split the learned router by `problem_id` (GroupKFold) and report cross-dataset OOD accuracy. What is test accuracy when no test problem's siblings appear in train? Show feature importance -- does the tree ever use the role one-hot given problem-level labels?
3. Re-derive oracle labels from F1 (or partial credit), not EM, given your own Tier-4 anomaly. How many labels flip? Re-report C2 oracle headroom and C6 after relabeling.
4. Replace hardcoded `confidence=0.7` and the lexical staircase with a calibrated signal (e.g. token-level logprob/self-consistency) and report ECE before vs after. If WCG survives only with the lexical cue, the mechanism claim is unsupported.
5. Define "matched cost" operationally: tolerance band, CI on the cost gap, and how the comparator is chosen *without* peeking at quality. Show the WCG is robust to this choice.
6. Provide live (not simulated) cost/quality for the oracle and proposed routers; quantify how far the INDEPENDENCE ASSUMPTION simulator deviates from live runs on GSM8K where both can be computed.
7. State exact N and source CSV per cell used for every reported number; redo any cross-tier comparison on the intersection of problem_ids common to all tiers.

---

## NeurIPS Systems Reviewer #1

### Summary & Recommendation

The paper proposes per-agent LLM tier routing inside a fixed Analyzer->Solver->Verifier pipeline, with a four-tier model menu (Gemma-4B local, Llama-70B/Groq, Llama-405B/GitHub, GPT-4.1/GitHub), 15 router variants, and a headline "Workflow Context Gain" (WCG) claim that workflow signals beat difficulty-only routing. The engineering scaffolding is genuinely careful  -- a single shared code path for baselines and routers, a claim-evidence matrix, a freeze discipline, and an unusually honest baseline-validation report.

But as a *scientific* submission this is not close to ready, and several problems are not "needs more runs"  -- they are design-level defects that would invalidate the results even after the runs land. The headline claims (C3/C4/C5/C6) are entirely placeholder; the only verified numbers are GSM8K single-tier baselines and an *offline* oracle *estimate*. The learned router has a fatal train/test leakage bug and a circular labeling scheme. The cost story is hypothetical by the authors' own admission, and the infrastructure (free-tier rate limits, a shared T3/T4 token pool, provider drift on GitHub Models) confounds every latency/throughput number. This is currently an engineering artifact with a research narrative bolted on, not a finished experiment.

**Recommendation: Strong Reject. Severity ~4.6/5, reviewer confidence 4/5.** I would need to see this resubmitted with live results, grouped-by-problem evaluation, consistent-N baselines, and at least one second pipeline shape before it is reviewable as a contribution.

### Novelty concerns

- The framed novelty (C1)  -- routing *each agent invocation* rather than the whole query, using role/upstream-confidence/stage/budget  -- is a reasonable design point, but it is incremental over RouteLLM/FrugalGPT/AutoMix/MasRouter and is argued, not demonstrated. C1's "evidence" in 17_RESEARCH_CLAIMS.md is "argument + implementation," i.e. a related-work table plus the existence of an interface. That is positioning, not a result.
- The proposed `adaptive`/`cascade` methods are hand-tuned threshold heuristics (combined = 0.6*question + 0.4*context, thresholds (0.2,0.4,0.7), verifier -1 / solver +1, confidence cascade at tau=0.5/0.8, budget clamp). These are defensible as engineering but contain ~7 magic constants with no sensitivity analysis. A reviewer will ask why this is a NeurIPS contribution rather than a sensible production heuristic.
- The "learned" router does not add novelty over the `complexity` router because of the labeling collapse described below (L5): with a problem-level label identical across roles, the classifier cannot learn role-conditioned routing, so `learned` degenerates to a difficulty->tier map. The distinguishing claim of the paper (workflow context > difficulty) is therefore not instantiated by the learned variant at all.

### Baseline concerns

- **Mixed-N, mixed-source baselines (disqualifying for the multi-hop comparisons).** Per BASELINE_VALIDATION_REPORT.md Sec 2: HotpotQA T2 = 118/200, T3 = 48/200 (PARTIAL), T4 from a truncated *backup*; MuSiQue T4 = 199/200, with T2/T3 also from backup. Comparing EM, cost-per-task, and savings ratios across tiers measured on *different problem subsets* and *different N* is not a fair comparison. A 48/200 T3 cell cannot anchor any cost-quality or QRR claim against a 200/200 T1 cell.
- **The all-T4 reference is itself broken on multi-hop.** C3 and the WCG claim use `fixed_t4` as the quality ceiling, yet `fixed_t4` EM is *below* T1/T2/T3 on both multi-hop sets (HotpotQA 37.5 vs 63/65/54; MuSiQue 25.63 vs 31.5/55/47.5). "Quality Retention vs the all-Tier-4 ceiling" is meaningless when T4 is the floor; QRR > 100% is acknowledged but not resolved. The reference baseline must be fixed before any retention claim is interpretable.
- **Hypothetical costs.** ROUTER_FINAL_SPEC.md Sec 7 states all models are free in practice and prices are assigned hypothetically (T1 0.03/0.06 ... T4 2.00/8.00). Every "cost reduction factor" / "savings %" is therefore a function of an assumed price vector, not a measured quantity. The headline efficiency narrative is unfalsifiable as written; at minimum a sensitivity analysis over plausible price vectors is required, and the framing must stop implying deployment savings.

### Evaluation concerns

- **Headline claims are unmeasured.** C3 (retention@cost), C4 (WCG  -- the explicitly labeled headline), C5 (ablation), C6 (learned) are all status pending/placeholder. The paper currently has no live routed runs. C2's oracle number (98.5% EM @ $0.0485) is from `simulate_routing.py` *offline*, not a live mixed-tier execution; the authors' own out-of-scope list forbids treating simulator estimates as live results, yet the oracle headroom claim leans on exactly that.
- **One pipeline shape, no generality.** A single fixed Analyzer->Solver->Verifier topology, 3 QA/math benchmarks, N=200. There is no second workflow shape, no agent count variation, no tool-use or retrieval pipeline. The out-of-scope list concedes "no claim beyond the single pipeline shape," which is honest but also means the contribution does not generalize beyond one hand-built graph. For a systems venue this is the central weakness: the method may be entirely an artifact of this one topology's role->difficulty correlation.
- **No cross-dataset / OOD evaluation.** Training pools all three datasets and evaluates on the same three; there is no held-out dataset, so "generalizes across difficulty" (C7) is in-distribution interpolation, not generalization. The label distribution is dominated by the easiest dataset (GSM8K is mostly T1), so the pooled classifier's behavior is driven by dataset identity / answer length, not difficulty.
- **Latency is confounded, not measured.** Latency is logged as a sum-of-latency wall-clock *proxy* over free-tier APIs. T3 and T4 share the GitHub Models token pool (R1  -- the report explicitly says do not run them simultaneously), and free-tier throttling injects queueing delay uncorrelated with model compute. Any T3/T4 latency or throughput comparison is confounded by rate-limiting and provider drift; it cannot support an efficiency claim, even a secondary one.

### Statistical concerns

- **N=200 yields ~+/-7pt EM CIs at 50%** (the authors state this themselves). The WCG and ablation deltas the paper needs to demonstrate are plausibly within this band, so the headline result risks being statistically indistinguishable from zero. The plan to use a *one-sided* test for the primary WCG hypothesis (claim_evidence_matrix Sec 2) further weakens an already underpowered design and should be justified or dropped.
- **The learned-router test accuracy is statistically void** due to the per-example split leakage (next section): there is no valid held-out estimate to report a CI on. The plan to report `learned` test accuracy as evidence for C6 cannot stand.
- **Multiple comparisons.** 15 routers x 3 datasets x (EM, F1) with paired bootstrap tests is a large family; there is no mention of multiplicity correction. With underpowered N and many comparisons, false positives are likely.
- **Confidence is a lexical heuristic.** `extract_confidence` is lexical hedging/assertion cues, and the learned router hardcodes RoutingDecision.confidence = 0.7 (not the model's probability). Any ECE/calibration number is descriptive at best; reporting it alongside "confidence cascade" results risks implying a calibration property that does not exist.

### Reproducibility concerns

This is my core area and where the paper is weakest.

- **Free-tier rate limits + shared token pool (R1).** T3 (Llama-405B) and T4 (GPT-4.1) draw from one GitHub Models token pool; the report instructs not to run them concurrently. This means (a) runs are serialized and throttled, (b) latency is contaminated by queueing, and (c) anyone reproducing must own the same free-tier quota, which is not a stable, specifiable resource. Reproducibility on free-tier provider endpoints is essentially impossible to guarantee.
- **Provider drift.** GPT-4.1 and Llama-405B on GitHub Models are moving targets  -- model versions, prompt handling, and availability change without notice. The Tier-4 EM anomaly is explicitly hypothesized (Sec 4, hypothesis 3) to be partly "provider/prompt variance for GPT-4.1 on GitHub Models." A result that may be an artifact of an unversioned third-party endpoint is not reproducible.
- **Truncation / data-loss in the logged artifacts.** The legacy logger stored response_text[:500], so F1 is unrecoverable from all backup CSVs and several active ones; ALL multi-hop F1 is pending clean re-runs. The corpus the paper currently rests on is partially corrupted by its own admission.
- **Learned-router leakage (L1), the most serious single defect.** I verified in `train_router.py` (L53-55): `train_test_split(X, y, test_size=0.25, stratify=y)` with no `groups=` and no problem_id. In `training_data.py` (L84-92) each problem emits one row per role (ROLE_ORDER), all three sharing the *same* problem-level oracle label and near-identical features (role differs only in a one-hot). The split is therefore by example and stratified by label, so the same problem appears in both train and test. The reported test accuracy is effectively in-sample. **Severity: CRITICAL.** Fix requires GroupKFold / grouped split by problem_id (and ideally leave-one-dataset-out).
- **Circular oracle labels (L2).** `oracle_labels` is computed from the same baselines/problems on which the router is later evaluated; running `learned` on those 200 problems is in-sample evaluation. **Severity: CRITICAL/High.** Needs held-out-by-problem and cross-dataset evaluation.
- **Corrupted supervision via EM (L3/L4).** Labels use brittle EM `correct`; under the documented T4 EM anomaly, genuinely-best verbose answers are scored 0 and mislabeled. The `label=4` fallback conflates "hardest" with "no tier solved it," and those labels are drawn from partial/truncated multi-hop baselines on inconsistent N. The training signal is unreliable. **Severity: High.**
- **Role-collapse (L5).** Because the label is problem-level (identical across roles), the role one-hot carries no label-discriminative information; the tree cannot use role to predict tier. The "learned, workflow-aware" router collapses to a difficulty classifier, undercutting C6 vs `complexity`. **Severity: CRITICAL/High.**
- **Overfitting / unstable model (L6/L7/L9).** ~200 problems/dataset, depth-5 tree on ~7 numeric hand-features (entity_count = capitalized-word count; estimated_hops = keyword count //2; complexity_score = hand-weighted linear combo), skewed labels with class_weight='balanced' on tiny data, pooled across datasets with a label distribution dominated by the easiest dataset, while deployment is mixed-tier but labels come from uniform-tier baselines (distribution shift). The features may encode dataset identity (length) rather than difficulty. **Severity: High.**
- **No grouped CV / no OOD (L10).** No cross-dataset or OOD evaluation; the router can only be shown to memorize the difficulty->tier map of these three benchmarks. **Severity: High.**
- **The obvious reviewer objection (L11).** Why a depth-5 tree on 7 hand-features rather than a one-line complexity threshold? The paper must show `learned` beats `complexity` with significance, *grouped* CV, and a per-dataset breakdown. As implemented it cannot, because of L1/L5.

### Questions to authors

1. Will you re-run the learned router with a problem-grouped split (GroupKFold by problem_id) and, separately, leave-one-dataset-out? What is the test accuracy then, with a CI? (The current per-example split number must be retracted.)
2. The oracle labels are computed on the same 200 problems used for evaluation. How do you evaluate `learned`/`oracle` out-of-sample? Without this, C2/C6 are circular.
3. Given that the label is identical across the three roles, what evidence is there that the learned router uses the role feature at all? Please report feature_importances for the role one-hots.
4. How can WCG (C4) be valid when the `fixed_t4` "ceiling" is the multi-hop *floor* (EM 37.5/25.63)? What is the corrected quality reference?
5. Multi-hop baselines are at N = 118/48/199/200 from mixed active+backup sources. How are cross-tier and cost comparisons valid across different problem subsets and N? Will all cells be re-run clean at N=200 before any number is reported?
6. T3 and T4 share one token pool and run under free-tier throttling. How do you decouple model latency from queueing/rate-limit delay? Without isolation, every latency/throughput number is uninterpretable.
7. The Tier-4 EM anomaly may be GPT-4.1 provider/prompt drift on GitHub Models. What model/version pinning and prompt-fixing makes this reproducible by a third party who lacks your free-tier quota?
8. Costs are hypothetical. Will you provide a sensitivity analysis showing the savings claim is robust across plausible real price vectors, and stop framing ratios as deployment savings?
9. With N=200 (~+/-7pt EM CIs) and 15x3x2 comparisons, what is your statistical power for the headline WCG, and how do you correct for multiple comparisons? Why is the primary WCG test one-sided?
10. Beyond the single Analyzer->Solver->Verifier topology, what evidence is there that per-agent routing generalizes to any other pipeline shape? Can you show one additional workflow?
