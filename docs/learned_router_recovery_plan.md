# Learned-Router Recovery Plan

> Status: FROZEN (recovery protocol; no code is changed here — this is the plan).
> Source risks: [learned_router_risk_assessment.md](learned_router_risk_assessment.md) (L1, L2, L5 = Critical).
> Integrates with: [claim_evidence_matrix.md](claim_evidence_matrix.md) (C4, C6),
> [statistical_validation_plan.md](statistical_validation_plan.md),
> [experiment_execution_plan.md](experiment_execution_plan.md),
> [paper_tables_template.md](paper_tables_template.md) (T6), [RESULT_PROVENANCE_MAP.md](RESULT_PROVENANCE_MAP.md) (C6).

## Problem statement (the three Critical risks)

- **L1 (leakage).** `train_router.py` L53-55 uses `train_test_split(X, y, stratify=y)` — split is
  per-EXAMPLE, stratified by label, **not** grouped by `problem_id`. `build_training_data`
  (`src/router/training_data.py` L88-91) emits 3 rows per problem (one per agent role) that share an
  IDENTICAL label and differ only in a role one-hot, so a problem's near-duplicate rows fall on both
  sides of the split → the reported tier-prediction accuracy is inflated and meaningless.
- **L2 (in-sample / circularity).** `oracle_labels` is computed from the SAME baselines and the SAME
  200 problems the learned router is then evaluated on. There is no held-out partition, and the label
  definition (cheapest EM-correct tier) is circular with the metric the router is later scored against.
- **L5 (role-collapse).** The oracle label is PROBLEM-level (identical across the 3 roles), so the role
  one-hot is provably label-irrelevant; the tree's role importance is ~0 and the "learned workflow-aware"
  router mathematically reduces to a difficulty classifier == the rule-based `complexity` router. This
  guts the C4 (Workflow Context Gain) and C6 (learned beats rule-based) framing.

These are protocol/design defects, not data defects: each is closable without new modeling, and (for
L1/L5) without any API spend.

---

## The minimum fix set

### FIX-A — Group the split/CV by `problem_id`  (closes L1)
- **What changes.** Replace `train_test_split(X, y, stratify=y)` with a **grouped** scheme:
  `sklearn.model_selection.GroupKFold` (k=5) for cross-validated reporting, or `GroupShuffleSplit`
  for a single split — in both cases `groups = problem_id` so all 3 role-rows of a problem stay on the
  same side. `build_training_data` must also **return per-example groups** `(problem_id, dataset)`
  (today it returns only `X, y, feature_names, meta`). `train_router.py` then passes `groups=` to the
  splitter and reports CV mean ± std, not a single split number.
- **Why it restores validity.** Eliminates the near-duplicate-row leak; the tier-prediction accuracy
  becomes an honest generalization estimate. Stratification can be approximated with
  `StratifiedGroupKFold` to also balance tiers across folds.
- **Effort.** **S** (~1-2 h): a few lines in `training_data.py` (carry + return groups) and
  `train_router.py` (swap splitter, loop folds).
- **Depends on / API.** None. **Do now (offline).**
- **Acceptance.** Reported accuracy is grouped-CV mean ± std with `groups=problem_id`; assert BOTH
  (i) train/test `problem_id` disjointness per fold AND (ii) group cardinality —
  `#unique groups == #problems` and exactly 3 rows per group — so a silent group-keying bug (e.g.
  groups keyed by row index) cannot pass (i) while re-leaking.
- **Interaction with FIX-B.** If FIX-B takes the "drop the role one-hots" branch, `build_training_data`
  collapses to **1 row per problem**, which *independently* removes the near-duplicate mechanism that
  causes L1. In that case FIX-A simplifies to an ordinary problem-level split (still group-safe, but the
  duplicate-row hazard is gone by construction). Decide FIX-B's branch first; the two fixes are coupled.

### FIX-B — Reframe the learned router as a *learned difficulty router*  (closes L5, minimal & honest)
- **What changes.** Stop claiming the learned router is workflow/role-aware. Two concrete edits:
  (1) **Framing:** the learned router is a *learned, role-AGNOSTIC difficulty router*; the workflow-aware
  / per-agent claim (**C4**) rests on the RUNTIME routers `cascade` and `adaptive`, which genuinely
  consume agent role + upstream confidence during execution ([ROUTER_FINAL_SPEC.md](ROUTER_FINAL_SPEC.md)).
  (2) **Feature:** drop the 3 role one-hots from the learned feature vector (they are provably inert), OR
  keep them and **report their importance (~0)** as direct evidence for the reframe. Also fix the
  contradicting docstring in `training_data.py` L10-13.
- **CAUTION — the rule-based `complexity` baseline is itself role-AWARE.** `complexity_router.py` holds
  per-role threshold vectors (L32-36) and selects by `agent_role` (L58), so it can route a problem's
  three roles to three tiers. The learned router (role-blind by L5) is therefore **strictly weaker by
  construction** than `complexity`, and is NOT its "counterpart." A naive "learned vs `complexity`"
  contest is apples-to-oranges and would make C6 fail for a mislabeled reason. **For C6, compare the
  learned router against a role-AGNOSTIC complexity variant** (a `ComplexityRouter` given a single shared
  threshold vector for all roles) on the SAME grouped folds — a like-for-like role-blind comparison.
- **Revised C6.** "A small classifier trained on oracle labels matches or beats a **role-agnostic**
  difficulty rule (single-threshold `complexity`) and the `random`/single-tier references at matched cost
  (cost-match point fixed on TRAIN folds; see FIX-C)." A learned-vs-rule comparison, not a workflow claim.
  **Do not** cite the learned router as C4 evidence, and do not pit it against role-aware `complexity`.
- **Why it restores validity.** Removes a structurally false claim AND a rigged-to-fail comparison; what
  remains (learned >= role-agnostic difficulty rule) is true-or-falsifiable and supported by FIX-A/FIX-C.
- **Effort.** **S** (~1-2 h): framing/doc edits + a 1-line feature change + a 1-line role-agnostic
  `complexity` comparator instance.
- **Depends on / API.** None. **Do now (offline).**
- **Acceptance.** No doc claims the learned router routes per-role; role importance reported ~0 (if kept);
  C4 in [claim_evidence_matrix.md](claim_evidence_matrix.md) lists only `cascade`/`adaptive`; the C6
  comparator is the role-agnostic `complexity` variant on identical folds.
- **Cheaper role-aware path (intermediate rung, before full ablation).** Per-`(problem, role)` supervision
  can be *approximated* from EXISTING mixed-tier trajectory logs that `cascade`/`adaptive` already write
  to `results/routing/` (which role's tier co-occurs with success/failure) — weaker than ablation labels
  but role-bearing and **zero extra API**. List as the first future-work option.
- **Out of scope (future work, NOT minimal).** True per-`(problem, role)` oracle labels via per-agent
  ablation runs (vary one agent's tier, hold others fixed) — many extra live runs. Future work only.

### FIX-C — Evaluate the learned router OUT-OF-SAMPLE  (reduces L2)
The model that routes a problem must never have been fit on that problem. Use k-fold cross-fitting by
`problem_id`: partition problems into k=5 folds; for each fold, recompute `oracle_labels` and **fit the
classifier on the other 4 folds only**, then evaluate the held-out fold. Two evaluation rungs:

- **C-1a (REQUIRED, OFFLINE, no API): held-out TIER-PREDICTION accuracy.** The metric "did the model
  predict the oracle tier" needs NO live runs — all four uniform-tier baselines already exist for every
  problem, so the held-out tier-prediction accuracy (vs `complexity`-role-agnostic / `random` / oracle)
  is a pure offline computation over the grouped folds. This is the cheapest valid out-of-sample number
  and belongs in Phase 0.
- **C-1b (RECOMMENDED, LIVE, API): held-out END-TASK quality/cost under mixed-tier routing.** To report
  the router's actual EM/F1/cost when it executes its (mixed-tier) choices, route each held-out fold
  **live** and log to `results/routing/`. This needs `run_experiment.py` to accept a problem subset — add
  a `--problem-ids`/`--fold` argument so a run executes only the held-out ids (a modest, isolated flag).
- **C-2 (RECOMMENDED headline): leave-one-dataset-out (LODO).** Train on 2 datasets, evaluate on the 3rd.
  Strongest evidence of transferable difficulty signal vs memorization. **Depends on the multi-hop
  baselines being COMPLETE AND of consistent N / untruncated** (else L4's completeness confound — `label=4`
  when a tier's row is missing/truncated — leaks a data-artifact into the labels). Gate on the
  intersection of fully-present problems across all 4 tiers, not merely "baselines exist."
- **Matched-cost selection (no leak).** Wherever C6/WCG uses "at matched cost," the cost-matching
  operating point (tier budget / threshold) MUST be chosen on the TRAIN folds and applied unchanged to
  the held-out fold. Never tune it, the model, or `max_depth` on the test fold.
- **Residual leak to DISCLOSE (do not hide).** Cross-fitting removes leakage of the *fitted model* across
  folds, but the oracle *label is still defined from each held-out problem's own EM outcome*
  (`training_data.py` L48-55). So this protocol fixes ESTIMATOR generalization, not the target's
  in-vivo origin. State the honest claim precisely: "the model predicts the cheapest-sufficient tier of
  UNSEEN problems," NOT "leak-free generalization." A strictly leak-free target would require a label
  source not derived from the eval problems' answers (future work).
- **Effort.** **M** (~0.5-1 day eng for the fold flag + orchestration; C-1b/C-2 add held-out LIVE runs).
- **Depends on / API.** C-1a none (offline). C-1b needs held-out live runs (**API**). C-2 additionally
  needs the 8 multi-hop baselines done + N-consistent ([experiment_execution_plan.md](experiment_execution_plan.md) Phase 1).
- **Acceptance.** Every reported learned number comes from problems whose labels did not enter the fitted
  model; harness asserts per-fold `problem_id` disjointness; matched-cost point provably set on train only.

### SUPPORTING (SHOULD — cheap, strengthens C6; not strictly required to be valid)
- Report grouped-CV tier-prediction accuracy **per dataset** (not just pooled) to expose dataset bias (L9).
- Compare learned vs `complexity` vs `random` vs `oracle` with **paired bootstrap + Holm correction**
  ([statistical_validation_plan.md](statistical_validation_plan.md)); the publishable C6 result is
  "learned significantly ≥ complexity at matched cost," else report the null honestly.
- Use F1-aware oracle labels once clean multi-hop F1 exists (mitigates L3); until then, state EM-label caveat.
- Calibration: either expose `predict_proba` and report ECE, or **drop** any calibration claim for the
  learned router (the hardcoded `confidence=0.7` is not a calibrated probability — L8).

---

## Prioritized plan (by scientific validity gained, then least engineering effort)

| Rank | Fix | Closes | Scientific validity gained | Effort | Depends on | API? |
|:----:|-----|:------:|----------------------------|:------:|------------|:----:|
| 1 | **FIX-A** group split by problem_id | L1 | Very high — makes any reported accuracy meaningful | S | none | No |
| 2 | **FIX-B** reframe as role-agnostic learned difficulty router (+ role-agnostic `complexity` comparator) | L5 | Very high — removes a false claim AND a rigged comparison | S | none | No |
| 3 | **FIX-C-1a** held-out TIER-PREDICTION (grouped cross-fit, OFFLINE) | L2 (reduce) | Very high — out-of-sample, zero API | S–M | fold flag (offline) | No |
| 4 | **FIX-C-1b** held-out END-TASK eval (live mixed-tier) | L2 (reduce) | Very high — real EM/F1/cost out-of-sample | M | fold flag + live runs | Yes |
| 5 | **FIX-C-2** leave-one-dataset-out | L2 + generalization | High — cross-distribution transfer | M | N-consistent multi-hop baselines | Yes |
| 6 | SUPPORTING: paired sig vs role-agnostic `complexity` + per-dataset + problem-level clustering | C6 | High — the actual C6 test, validly | S | ranks 1-4 done | No* |
| 7 | SUPPORTING: F1-aware labels / ECE-or-drop | L3, L8 | Medium | S–M | clean F1 | No* |

\* analysis-only once the runs in ranks 1-5 exist.

Ranks 1-3 are pure validity-per-hour wins (OFFLINE, hours, close/reduce two Criticals with zero API) —
do them first. Rank 4 is the first item needing API; rank 5 is gated on N-consistent baseline re-runs.

---

## Publishable floor (the strict required subset)

To state the learned-router result honestly, **FIX-A + FIX-B + FIX-C-1a** are MANDATORY (all OFFLINE):
- FIX-A so the number is not leaked across the split;
- FIX-C-1a so the (tier-prediction) number is out-of-sample;
- FIX-B so the claim it supports (C6, role-agnostic learned difficulty routing) is the claim the design
  can bear, and so the C6 comparator is the role-agnostic `complexity` variant (like-for-like).
- **Plus:** when any C6 significance is reported, problem-level clustering / effective-N = #problems is
  REQUIRED (the paired bootstrap is invalid if it treats the 3 rows/problem as i.i.d.).

FIX-C-1b (live end-task), FIX-C-2 (LODO) and the other SUPPORTING items are **recommended** (they make the
result strong rather than merely admissible). True per-agent learned labels are **future work**.

If the home-machine budget is tight: the learned router can be **demoted to a secondary result**
reported with the OFFLINE mandatory set only (FIX-A + FIX-B + FIX-C-1a, tier-prediction held-out), while
C4 stands on `cascade`/`adaptive`. The paper does not require the learned router for its headline.

---

## Reframing decision (explicit)

The learned router is hereby scoped as a **role-agnostic learned difficulty router**. (It is NOT a
"counterpart" of the default `complexity` router, which is role-AWARE via per-role thresholds; C6 must
compare the learned router against a role-AGNOSTIC `complexity` variant, like for like.) The
**workflow-aware contribution (C4, Workflow Context Gain) rests on `cascade` and `adaptive`**, which use
agent role and upstream confidence at run time. The learned router's role in the paper is to answer C6:
*can a cheap learned model recover the cost-quality benefit of role-agnostic difficulty routing (and the
oracle headroom) from features available before execution?*

---

## Knock-on doc edits (apply after the runs land)

- [claim_evidence_matrix.md](claim_evidence_matrix.md): C4 experiment column → `cascade`/`adaptive` only
  (remove any learned-router mention); restate C6/C6a as learned-vs-`complexity` difficulty routing.
- [statistical_validation_plan.md](statistical_validation_plan.md): add "all learned-router metrics use
  grouped (problem-level) resampling / cross-fitting"; C6 test = paired bootstrap learned-vs-complexity + Holm.
- [paper_tables_template.md](paper_tables_template.md) T6: footnote that learned-router cells are
  grouped-CV / held-out, and that role-importance ~0 is reported.
- [experiment_execution_plan.md](experiment_execution_plan.md): insert FIX-A/B (Phase 0, offline) and a
  cross-fit/LODO learned-router phase (after baselines); note the `--fold`/`--problem-ids` prerequisite.
- [17_RESEARCH_CLAIMS.md](17_RESEARCH_CLAIMS.md) C6: reword to "learned difficulty router" + grouped/held-out.
- [RESULT_PROVENANCE_MAP.md](RESULT_PROVENANCE_MAP.md) C6 chain: experiment = cross-fit folds; raw logs =
  per-fold `results/routing/*.csv`; note the disjoint-`problem_id` guarantee.
- [learned_router_risk_assessment.md](learned_router_risk_assessment.md): mark L1/L2/L5 "mitigation
  adopted — see recovery plan"; mark L3/L8/L9/L10 partially addressed by SUPPORTING + FIX-C-2.

---

## Leakage-closure proof sketch

- **L1 closed** iff the fitted model never trains on any row whose `problem_id` is in the evaluation
  partition. `GroupKFold(groups=problem_id)` guarantees fold-disjointness over `problem_id`; since all
  rows of a problem share its `problem_id`, the 3 role-rows move together → no near-duplicate leak.
  Verify with an assertion: `set(train_pids) ∩ set(test_pids) == {}` per fold.
- **L2 REDUCED, not fully closed (state this honestly).** Cross-fitting (C-1) makes each routed
  problem's *prediction* come from a model fit WITHOUT that problem in the training partition, so the
  ESTIMATOR no longer leaks across folds. **But the oracle TARGET is still defined from each held-out
  problem's own EM outcome** (`training_data.py` L48-55), so the metric grades against a label distilled
  from the test problem's answer key. The defensible claim is therefore "predicts the cheapest-sufficient
  tier of UNSEEN problems," not "leak-free generalization." Fully closing the definitional leak needs a
  label source not derived from the eval answers (future work). **Pitfalls to avoid (and state in
  methods):** (i) do NOT compute one global classifier and merely re-split for reporting — refit labels +
  model per fold; (ii) do NOT select hyperparameters (max_depth, model type) on the test fold (fix a
  priori or use a nested inner split); (iii) set any matched-cost operating point on TRAIN folds only.
  LODO (C-2) additionally removes test-DATASET label influence — but only on N-consistent baselines.
- **L5 closed** by construction of the *claim*, not the data: because the oracle label is role-invariant,
  no labelling/feature trick makes the current learned router role-aware without per-agent labels (future
  work). FIX-B closes L5 by retiring the false claim, comparing only against a role-AGNOSTIC `complexity`
  variant (the role-aware `complexity` would be an unfair, stronger opponent), assigning C4 to the routers
  that legitimately use role/confidence at run time, and reporting role-importance ~0 to make it auditable.
- **L9 (named residual threat, not closed here).** The oracle labels come from UNIFORM-tier baselines,
  while the deployed/held-out router produces MIXED-tier trajectories (e.g. analyzer@T1 -> solver@T3) that
  are outside the label-generating distribution. Cross-fitting does nothing for this. Treat L9 as an
  explicit validity threat to C6 in the Limitations, not a footnote; FIX-C-1b's live mixed-tier eval
  measures the real outcome under that shift, and the "cheaper role-aware path" (FIX-B) would partly
  address it with existing mixed-tier logs.
