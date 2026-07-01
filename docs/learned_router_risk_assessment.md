> Status: FROZEN (risk assessment; no code changes)

# Learned Router -- Risk Assessment (ACL/EMNLP Reviewer Audit)

Scope: ONLY the learned router subsystem:
`src/router/learned_router.py`, `src/router/training_data.py`,
`src/router/signals.py`, `train_router.py`, and the roundtrip test
`tests/test_offline.py::test_learned_router_roundtrip`.
Supporting label source confirmed in `src/evaluation/csv_io.py::per_problem_records`.

This document audits the learned router against claims C6 (learned approximates
oracle / beats random + rule-based) and C4 (Workflow Context Gain, the headline).
It assesses every item in the seed checklist (L1-L11), adds further risks
(L12-L17), assigns severities, and ends with a ranked summary and a
"minimum bar to publish" checklist. Documentation/analysis only; no code is
proposed or changed here.

---

## How the pipeline actually works (as implemented)

1. `oracle_labels(dataset)` reads `{dataset}_baseline_tier{1..4}.csv` (with a
   `baselines_backup` fallback chosen by `len(recs) > len(best)`), takes the
   verifier-row `correct` boolean per problem, and assigns each problem the
   CHEAPEST tier with `correct == True`; if none is correct -> label `4`
   (`training_data.py` lines 31-56).
2. `correct` is the CSV `correct` column = baseline Exact Match
   (`csv_io.py` line 79: `str(vrow.get("correct","")).strip().lower()=="true"`).
   F1 is read but NEVER used for labels.
3. `build_training_data` emits ONE row per (problem, role): for each problem it
   loops `for role in ROLE_ORDER` and appends `router_feature_vector(question,
   role, context)` with the SAME problem-level `tier` label for all three roles
   (`training_data.py` lines 84-92).
4. Features = 10 dims from `signals.router_feature_vector`: `word_count`,
   `entity_count` (capitalized-word heuristic), `estimated_hops`
   (`hop_count // 2`, clamped 1-4), `has_comparison`, `has_temporal`,
   `complexity_score` (hand-weighted linear combo), `context_complexity`
   (`min(1, ctx_words/2000)`), and 3 role one-hots
   (`signals.py` lines 113-147).
5. `train_router.py` fits `DecisionTreeClassifier(max_depth=5,
   class_weight="balanced")` (or LogisticRegression) on a
   `train_test_split(X, y, test_size=0.25, stratify=y)` split -- BY EXAMPLE,
   STRATIFIED BY LABEL -- and reports tier-prediction train/test accuracy to
   `_report.json` (lines 53-95).
6. At inference `LearnedRouter.select_tier` builds the feature vector, predicts a
   tier, clamps to 1-4, applies a budget guard, and returns
   `RoutingDecision(confidence=0.7)` -- a HARDCODED constant, not the model's
   predicted probability (`learned_router.py` lines 67-83).

---

## Risk register

### L1 -- Per-EXAMPLE (not per-PROBLEM) split leaks problems across train/test
- ID: L1
- Title: train_test_split is by example, so the same problem is in train and test
- Severity: CRITICAL
- Evidence: `train_router.py` lines 53-55 split `X, y` with no `groups`
  argument. `build_training_data` (`training_data.py` lines 88-91) emits 3 rows
  per problem (one per role) that share the SAME label and near-identical
  features (only the 3 role one-hot bits differ; all 7 question/context features
  are byte-identical across the 3 rows). `train_test_split` shuffles rows
  independently, so for a typical problem >=1 of its 3 rows lands in train and
  >=1 in test. The "test" set therefore contains rows whose label and 7/10
  features were also seen in training.
- Why it matters to an ACL reviewer: the reported `test_accuracy` in
  `_report.json` is not an estimate of generalization to unseen problems; it is
  a near-duplicate retrieval score. Any claim that the learned router
  "approximates the oracle" (C6) built on this number is invalid. This is the
  single most damaging methodological flaw and a guaranteed desk-level
  objection.
- Mitigation: re-evaluate with GroupKFold / GroupShuffleSplit grouped by
  `problem_id` (and ideally by dataset). Report grouped CV mean +/- std, never
  the per-example split number. State explicitly in the paper that the original
  split was per-example and was discarded.

### L2 -- Label/eval circularity: oracle labels derived from the same problems used to evaluate
- ID: L2
- Title: In-sample evaluation -- labels and downstream eval share the 200 problems
- Severity: CRITICAL
- Evidence: `oracle_labels` (`training_data.py` 31-56) is computed from the SAME
  baseline CSVs (`results/baselines/*tier{1..4}.csv`) that the routed pipeline
  is run and scored on. There is no held-out problem partition anywhere in
  `train_router.py` or `training_data.py`; `num_problems` defaults to 200 and the
  full set is consumed (lines 81-92). When `LearnedRouter` is then run over those
  same 200 problems and scored against the oracle, training labels and the
  evaluation oracle are the identical signal.
- Why it matters to an ACL reviewer: routing-accuracy / quality-retention /
  cost-savings reported on the training problems is in-sample. The router has
  effectively memorized the difficulty->tier map of these exact problems. C6 and
  C7 (generalization) cannot be supported in-sample.
- Mitigation: define a held-out-by-problem split (train labels on a disjoint set
  of problem_ids from those used for routing eval), OR cross-dataset eval (train
  on 2 datasets, evaluate routing on the third). Report both. Document that
  oracle headroom (C2) and learned routing eval must use disjoint problem sets.

### L3 -- Brittle EM oracle labels + Tier-4 EM anomaly mislabels good answers
- ID: L3
- Title: Oracle label = EM-correct only; ignores F1/partial credit
- Severity: High
- Evidence: labels use the boolean `correct` column = EM
  (`csv_io.py` line 79; `training_data.py` line 45). F1 is read into the record
  (`csv_io.py` 89-95) but never consulted by `oracle_labels`. The project's
  KNOWN ANOMALY is that Tier-4 (GPT-4.1) EM is LOWER than weaker tiers on
  multi-hop because verbose answers fail EM. So a T4 answer that is genuinely
  correct-but-verbose is scored `correct=False`, removing T4 from the "cheapest
  correct" search and biasing labels toward lower tiers (or toward the label-4
  fallback when ALL tiers EM-fail a solvable problem).
- Why it matters to an ACL reviewer: the supervision target is systematically
  wrong on exactly the multi-hop datasets (HotpotQA, MuSiQue) that motivate the
  workflow framing. The router is being taught a distorted notion of "which tier
  is sufficient." C8 (honesty) explicitly commits to reporting F1; labels built
  on EM-only contradict that commitment.
- Mitigation: produce F1-aware oracle labels (e.g. tier is "correct" if F1 >=
  threshold, or cheapest tier within delta of best F1) and report label
  agreement EM-vs-F1. Ablate router results under both label definitions. Tie
  this to the existing T4-anomaly note in BASELINE_VALIDATION_REPORT.md.

### L4 -- Label=4 fallback conflates "hardest" with "unsolvable" on inconsistent N
- ID: L4
- Title: No-correct-tier -> label 4, computed over mismatched per-tier problem sets
- Severity: High
- Evidence: `oracle_labels` sets `label = 4` whenever no tier is EM-correct
  (`training_data.py` lines 50-55). Crucially, per-tier `correct` maps are built
  independently per file and the code picks whichever of base/backup has MORE
  records (`len(recs) > len(best)`, lines 40-44). Per the project state the
  multi-hop baselines are on MIXED N / sources (T2/T3 partial/clean; T4 truncated
  backup; MuSiQue T4 N=199). So a problem may be present for T1 but absent for
  T3/T4, or T4 may be truncated. A truncated/absent higher tier cannot
  contribute a `correct=True`, so the "cheapest correct" search and the
  label-4 fallback are computed over inconsistent problem sets. The label-4
  bucket therefore mixes genuinely-hard problems with problems that are merely
  missing/truncated at the tier that would have solved them.
- Why it matters to an ACL reviewer: label noise that is correlated with data
  completeness (a confound), not with true difficulty. "Send hard problems to
  T4" becomes "send problems with incomplete logging to T4." Undermines C2/C6
  and is hard to defend under questioning.
- Mitigation: restrict label construction to the intersection of problem_ids
  present (and untruncated) across ALL four tiers; report how many problems are
  dropped and the label-4 rate before/after. Re-run on clean, consistent-N
  baselines once the legacy 500-char truncation is fixed. Document the N per
  tier per dataset alongside the label distribution.

### L5 -- Role one-hots cannot help: the "learned" router collapses to a difficulty classifier
- ID: L5
- Title: Problem-level label makes role features label-irrelevant -> role-collapse
- Severity: CRITICAL
- Evidence: each problem's 3 rows differ ONLY in the role one-hot bits but carry
  the IDENTICAL label (`training_data.py` lines 84-91; label `tier` is fixed
  before the role loop). The three role rows are thus (features that move, label
  that does not move). Any classifier minimizing error has zero incentive to
  split on role -- splitting on `role_*` cannot reduce label impurity because the
  label is invariant to role within a problem. The expected outcome is that the
  tree's `feature_importances_` for `role_analyzer/solver/verifier` are ~0, i.e.
  the learned router reduces to a pure difficulty classifier identical in spirit
  to the rule-based `complexity` router. The code's OWN docstring asserts the
  opposite -- `training_data.py` lines 10-13 claim "one example is emitted per
  (problem, agent_role): the role is a feature, so the classifier *can* learn
  role-conditioned behaviour" -- a claim directly contradicted by the role-invariant
  label it then constructs (lines 84-91). This self-contradiction is a ready-made
  reviewer hook.
- Why it matters to an ACL reviewer: this directly guts the headline C4
  (Workflow Context Gain) and C6 framing. The paper's novelty is PER-AGENT /
  workflow-aware routing; but the learned router, by construction of its labels,
  cannot route different roles to different tiers and cannot learn anything the
  one-line complexity threshold doesn't. A reviewer will say "your learned
  router is a difficulty classifier wearing a role one-hot it provably ignores."
- Mitigation (analysis-level): (a) report `feature_importances_` / logreg
  coefficients for the role features and show whether they are ~0; (b) construct
  ROLE-SPECIFIC oracle labels (cheapest tier sufficient FOR THAT ROLE's
  sub-task) so role carries label signal -- present this as the corrected
  experimental design; (c) explicitly position the learned router vs complexity
  and report whether per-agent variation actually occurs at inference. Do not
  claim workflow-awareness for the learned router until role demonstrably changes
  its output.

### L6 -- Crude hand-engineered features; no semantics; may encode dataset identity
- ID: L6
- Title: Heuristic features proxy length/dataset, not difficulty
- Severity: High
- Evidence: `entity_count` is "capitalized word not after sentence-end"
  (`signals.py` 24-27) -- a casing heuristic, not NER; `estimated_hops =
  hop_count // 2` from a fixed keyword list (lines 30-35); `complexity_score` is
  a hand-weighted linear combination of the others (lines 46-52);
  `context_complexity = min(1, ctx_words/2000)` (line 174). There are no
  embeddings or semantic features. GSM8K (no context, short numeric prompts),
  HotpotQA and MuSiQue have systematically different `word_count`,
  `entity_count` and `context_complexity` ranges, so these features largely
  encode WHICH DATASET a problem came from rather than its intrinsic difficulty.
- Why it matters to an ACL reviewer: when datasets are pooled (default
  `--datasets gsm8k hotpotqa musique`) and each dataset has a dominant label
  (GSM8K mostly T1), a classifier can hit high accuracy by inferring dataset
  identity from length and predicting that dataset's modal tier -- a shortcut,
  not difficulty modeling. Hurts C6 (is it really learning?) and C7 (it will not
  transfer to a dataset whose length distribution differs).
- Mitigation: report a feature-vs-dataset mutual-information / dataset-id
  classification probe (how well do the 10 features predict dataset?); report
  per-dataset performance; and run the cross-dataset OOD eval from L10. Frame the
  features honestly as cheap heuristics, and contextualize accuracy against a
  dataset-modal-tier baseline.

### L7 -- Overfitting risk: tiny, skewed data; depth-5 tree; unstable balanced weighting
- ID: L7
- Title: ~200 problems/dataset, depth-5 tree on 7 numeric features, skewed labels
- Severity: High
- Evidence: `num_problems` defaults to 200 (`train_router.py` line 33);
  effectively ~200 distinct problems per dataset (the 3 role rows are
  near-duplicates, so effective independent sample size is the problem count, not
  `n_examples`). `DecisionTreeClassifier(max_depth=5)` can express up to ~32
  leaves over only ~7 informative numeric features (lines 57-59). GSM8K labels
  are dominated by T1, so several tier classes are tiny;
  `class_weight="balanced"` upweights rare classes, which on a handful of T3/T4
  examples produces high-variance, dataset-specific splits.
- Why it matters to an ACL reviewer: with this few effective samples and skewed
  classes, both the depth-5 tree and the per-example split (L1) inflate apparent
  performance and the model is unlikely to be stable across seeds/folds.
  Reviewers expect variance estimates, not a single split number.
- Mitigation: report grouped CV mean +/- std across multiple seeds; report a
  learning curve vs N; compare depth-5 against a depth-1/2 stump and against the
  complexity rule; report the confusion matrix and per-class support (T3/T4
  counts). State effective sample size = #problems, not #rows.

### L8 -- Uncalibrated outputs and hardcoded confidence; no abstention/ECE
- ID: L8
- Title: confidence=0.7 is a constant, not the model probability
- Severity: Medium
- Evidence: `LearnedRouter.select_tier` returns
  `RoutingDecision(confidence=0.7)` unconditionally (`learned_router.py` line
  82); `predict_proba` is never called. There is no calibration step, no ECE
  measurement, and no abstention/threshold. The logged `confidence` column for
  this router is therefore a constant carrying no information.
- Why it matters to an ACL reviewer: any downstream analysis that uses
  `confidence` (e.g. confidence-gated escalation, reliability diagrams, the
  spec's ECE metric) is meaningless for the learned router. If the paper reports
  ECE or confidence-based behavior, it cannot include the learned router
  honestly without this fix.
- Mitigation: either expose `max(predict_proba)` and measure ECE / plot a
  reliability diagram, or explicitly document that the learned router emits a
  constant confidence and EXCLUDE it from any confidence/ECE analysis. Do not
  report a confidence-conditioned result for this router.

### L9 -- Dataset bias: pooled training dominated by easiest dataset; uniform-tier labels vs mixed-tier deployment
- ID: L9
- Title: Pooled label distribution skewed by GSM8K; train/deploy distribution shift
- Severity: High
- Evidence: `build_training_data` pools all passed datasets into one X/y with no
  reweighting (`training_data.py` 79-92); `meta["label_distribution"]` is a
  single pooled histogram (line 98). GSM8K (highest baseline EM, mostly
  T1-solvable) contributes a large block of T1 labels, dominating the pooled
  prior. Separately, the labels come from UNIFORM-tier baselines (every problem
  was run end-to-end at a single fixed tier), whereas the deployed learned router
  produces MIXED-tier trajectories (different tiers per agent within one
  problem). The label-generating distribution differs from the deployment
  distribution.
- Why it matters to an ACL reviewer: the pooled prior biases predictions toward
  T1; per-dataset behavior is hidden behind the pooled number; and the
  uniform->mixed shift means a "cheapest correct tier" learned from uniform runs
  is not guaranteed valid for a mixed pipeline (an analyzer at T1 feeding a
  solver at T3 is never observed in the label-generating data). Threatens C3, C6,
  C7.
- Mitigation: report per-dataset label distributions and per-dataset router
  metrics (not just pooled); ablate pooled vs per-dataset training; and
  explicitly discuss the uniform-baseline -> mixed-deployment distribution shift
  as a validity threat, ideally validating a sample of mixed trajectories.

### L10 -- No cross-dataset / OOD evaluation
- ID: L10
- Title: No held-out dataset; cannot support C7 generalization
- Severity: High
- Evidence: `train_router.py` always trains and tests on the same pooled
  datasets via one random split (lines 47-55). Nothing trains on a subset of
  datasets and evaluates on an unseen one. Combined with L6 (features proxy
  dataset identity), the model most likely memorizes the per-benchmark
  difficulty->tier map.
- Why it matters to an ACL reviewer: C7 explicitly claims cross-dataset
  generalization; with no OOD experiment that claim is unfounded. Reviewers
  routinely require leave-one-dataset-out for any "generalizes" claim.
- Mitigation: leave-one-dataset-out experiments (train GSM8K+HotpotQA ->
  evaluate MuSiQue, and rotations); report the OOD drop vs in-distribution and vs
  the complexity rule on the same OOD set.

### L11 -- Reviewer objection: why a depth-5 tree over a one-line complexity threshold?
- ID: L11
- Title: Learned router must demonstrably beat the rule baseline with rigor
- Severity: High (framing/headline-critical)
- Evidence: features are a hand-weighted `complexity_score` plus its own
  ingredients (`signals.py` 46-52), and the labels are problem-level difficulty
  (L5). A depth-5 tree over these is at risk of being a more complicated
  re-derivation of the `complexity` router with no added value, and the current
  evaluation (per-example split, in-sample, single seed, pooled) cannot show
  otherwise.
- Why it matters to an ACL reviewer: the core question for any "learned beats
  rule-based" claim (C6) is a fair, powered comparison. Without grouped CV,
  per-dataset breakdown, significance testing, and an explicit complexity
  baseline on the SAME folds, the contribution is not demonstrated.
- Mitigation: head-to-head learned vs complexity vs random vs oracle on grouped
  CV folds; paired significance test (McNemar / paired bootstrap from
  `routing_metrics.py`) on routing accuracy AND end-task quality/cost;
  per-dataset table; report effect size and CIs. If learned does not beat
  complexity significantly, report that honestly (supports C8).

### L12 -- Misleading `dict | None` context type hint (latent, not a live bug)
- ID: L12
- Title: context type annotation does not match what callers actually pass; parity unverified
- Severity: Low
- Evidence: TRAINING passes `context` as a formatted STRING
  (`adapter.format_context(...)`, `training_data.py` line 64). LIVE INFERENCE in
  the real pipeline ALSO passes a string: `routed_pipeline.py` sets
  `router_context = problem.formatted_context or None` and calls
  `select_tier(context=router_context, ...)`, so BOTH train and serve hit the
  `str` branch of `extract_context_complexity` (`signals.py`) and the
  `context_complexity` feature is computed CONSISTENTLY. The roundtrip test calls
  `select_tier(question=..., agent_role='solver')` with no `context` (defaults to
  `None` -> 0.0). The only latent issue is cosmetic: every `select_tier` signature
  annotates `context: dict | None` (`base_router.py`) while every caller passes
  `str | None`, and `extract_context_complexity` also has a `dict` branch (for a
  raw HotpotQA context dict) that the pipeline never exercises.
- Why it matters to an ACL reviewer: this is NOT a live train/serve skew (corrected
  from an earlier draft that wrongly claimed inference passes a dict). But the
  mismatched type hint invites a future caller to pass a raw HotpotQA `context`
  dict directly, which WOULD silently take the dict branch and change the feature;
  a reviewer diffing signatures against call sites will note the annotation is wrong.
- Mitigation (doc/analysis-level): state in the methods that the router always
  receives the formatted-context STRING; correct the `context: dict | None`
  annotation to `str | None` (or normalize at the boundary) when code work resumes;
  report the train-vs-serve distribution of `context_complexity` to confirm parity.

### L13 -- reason/base_tier reports raw prediction while tier is clamped/budget-overridden
- ID: L13
- Title: Logged routing_reason and base_tier can disagree with the executed tier
- Severity: Low
- Evidence: `select_tier` computes `tier = min(4, max(1, pred))` and may then set
  `tier = 1` under the budget guard, but returns `reason=f"Learned classifier
  predicted T{pred}"` and `base_tier=pred` (`learned_router.py` 68-83) -- both
  carrying the UNCLAMPED, pre-budget `pred`. If the model ever predicts outside
  1-4 (possible for LogisticRegression label space, or future class sets) or the
  budget guard fires, the logged reason/base_tier misstates what executed.
- Why it matters to an ACL reviewer: provenance/honesty (C8). Post-hoc analyses
  that read `routing_reason`/`base_tier`/`escalated_from` may attribute a tier
  that did not run. Minor but it is a data-integrity nit a careful reviewer (or
  the artifact reviewer) can catch.
- Mitigation: when reporting, derive executed tier from the `tier` column, not
  from `routing_reason`/`base_tier`; document that `base_tier` is the
  pre-clamp/pre-budget prediction.

### L14 -- Stratify-by-label split is incompatible with grouped evaluation and hides rare-class fragility
- ID: L14
- Title: stratify=y enforces label balance across the leaky split, masking variance
- Severity: Medium
- Evidence: `train_test_split(..., stratify=y)` (`train_router.py` 54-55)
  guarantees each tier label appears in both train and test in proportion. Given
  only a few T3/T4 problems, stratification can place near-duplicate role rows of
  the SAME rare-class problem on both sides (compounding L1), and it produces a
  single optimistic test number with no variance estimate.
- Why it matters to an ACL reviewer: stratified-by-label + per-example is exactly
  the configuration that maximally inflates reported accuracy for rare classes.
  Reviewers expect grouped, repeated CV with variance, not one stratified split.
- Mitigation: replace with repeated GroupKFold (group=problem_id); report
  per-class support and confusion matrix so rare-class behavior is visible rather
  than smoothed by stratification.

### L15 -- No deduplication / problem-identity check; near-duplicate rows counted as independent
- ID: L15
- Title: n_examples (3x problems) is reported as the sample size
- Severity: Medium
- Evidence: `meta["n_examples"] = len(X)` (`training_data.py` 95-98) equals
  3 * #problems because of the per-role expansion (lines 88-91); `train_router.py`
  prints `n_examples` as the dataset size (line 51). The three rows per problem
  are near-duplicates (7/10 features identical, label identical).
- Why it matters to an ACL reviewer: stating "N=600 training examples" when there
  are ~200 independent problems overstates statistical power and data scale, and
  invalidates any CI / significance computed treating rows as i.i.d.
- Mitigation: always report effective sample size = number of distinct problems;
  any CI/test must account for the 3-rows-per-problem clustering (cluster by
  problem_id).

### L16 -- Single global label space; class set depends on data presence
- ID: L16
- Title: clf.classes_ / bundle["classes"] can omit tiers absent from training
- Severity: Low
- Evidence: `classes = [int(c) for c in clf.classes_]` (`train_router.py` line
  79) reflects only labels PRESENT in `y`. If a dataset (e.g. clean GSM8K) yields
  no T2/T3 oracle labels, those tiers are absent from `classes_` and the model
  can never predict them; the inference clamp `min(4,max(1,pred))`
  (`learned_router.py` 69) cannot reintroduce a missing interior tier.
- Why it matters to an ACL reviewer: a router that structurally cannot emit T2 or
  T3 is a silent capability gap; cost/quality trade-offs will look artificially
  bimodal. Reviewers comparing tier distributions across routers will notice.
- Mitigation: report the achievable class set per trained model and the realized
  tier distribution; if interior tiers are unreachable, disclose it and discuss
  impact on cost-quality Pareto claims.

### L17 -- Determinism/reproducibility gaps in the logreg path and label-source selection
- ID: L17
- Title: Non-seeded LogisticRegression and base/backup file race weaken reproducibility
- Severity: Low
- Evidence: the tree gets `random_state=args.seed` but `LogisticRegression(...)`
  is constructed WITHOUT a `random_state` (`train_router.py` lines 57-61);
  `oracle_labels` silently prefers whichever of `baselines/` vs
  `baselines_backup/` has more records per tier (`training_data.py` 40-44), so
  labels depend on transient file state rather than a pinned snapshot.
- Why it matters to an ACL reviewer: reproducibility (artifact evaluation, C8).
  Two runs can yield different labels (different backup contents) or different
  logreg solutions, and the paper cannot claim a fixed result.
- Mitigation: pin the exact baseline snapshot used for labels (hash/manifest);
  document the base-vs-backup selection; seed all estimators; report results over
  multiple seeds.

---

## Ranked severity summary

| Rank | ID  | Title (short)                                              | Severity |
|------|-----|-----------------------------------------------------------|----------|
| 1    | L1  | Per-example split leaks problems across train/test        | Critical |
| 2    | L2  | In-sample eval: labels share the 200 eval problems        | Critical |
| 3    | L5  | Problem-level label -> role-collapse to difficulty clf    | Critical |
| 4    | L3  | EM-only oracle labels + T4 EM anomaly mislabel answers     | High     |
| 5    | L4  | label=4 conflates hard with unsolvable on inconsistent N  | High     |
| 6    | L6  | Crude features proxy dataset identity, not difficulty      | High     |
| 7    | L7  | Tiny skewed data + depth-5 tree -> overfitting             | High     |
| 8    | L9  | Pooled bias + uniform-vs-mixed distribution shift          | High     |
| 9    | L10 | No cross-dataset / OOD evaluation                          | High     |
| 10   | L11 | Must beat complexity rule with grouped CV + significance   | High     |
| 11   | L8  | Hardcoded confidence=0.7; no ECE/abstention                | Medium   |
| 12   | L14 | stratify=y hides rare-class fragility, no variance         | Medium   |
| 13   | L15 | n_examples (3x problems) overstates sample size            | Medium   |
| 14   | L12 | Misleading dict|None context type hint (latent, not live)  | Low      |
| 15   | L13 | reason/base_tier disagree with executed tier               | Low      |
| 16   | L16 | classes_ may omit unreachable interior tiers               | Low      |
| 17   | L17 | Non-seeded logreg + base/backup label race                 | Low      |

Totals: **Critical 3 (L1, L2, L5), High 7, Medium 3, Low 4.**

Counts: Critical 3, High 8, Medium 3, Low 3 (total 17).

---

## Minimum bar to make the learned-router results publishable

1. GROUPED EVALUATION (fixes L1, L14, L15): all learned-router numbers come from
   repeated GroupKFold grouped by `problem_id`; report mean +/- std over >=5
   seeds; report effective N = #problems, not #rows.
2. OUT-OF-SAMPLE / OOD (fixes L2, L10): train labels and evaluate routing on
   DISJOINT problem sets; add leave-one-dataset-out cross-dataset results with
   the in-distribution-vs-OOD gap.
3. FAIR BASELINE COMPARISON (fixes L11): learned vs complexity vs random vs
   oracle on the SAME folds, with a paired significance test (McNemar / paired
   bootstrap) and CIs on routing accuracy, end-task quality, and cost.
4. PER-DATASET REPORTING (fixes L6, L9): per-dataset label distributions, per
   dataset router metrics, pooled-vs-per-dataset ablation, and a dataset-id
   probe showing how much features leak dataset identity.
5. LABEL VALIDITY (fixes L3, L4): F1-aware oracle labels reported alongside
   EM-only, with EM-vs-F1 label agreement; restrict labels to the intersection
   of problems present and untruncated across all four tiers; report dropped-N
   and label-4 rate before/after; re-run on clean, consistent-N baselines.
6. ROLE-AWARENESS EVIDENCE (fixes L5): report role-feature importances /
   coefficients; demonstrate (or retract) that the learned router actually routes
   roles differently; if claiming workflow-awareness, use role-specific oracle
   labels so role carries label signal.
7. CALIBRATION HONESTY (fixes L8): either expose predict_proba and report ECE +
   reliability diagram, or exclude the learned router from all confidence/ECE
   analysis and state the constant-0.7 limitation.
8. TRAIN/SERVE PARITY (fixes L12): verify every feature (esp.
   context_complexity) is computed identically at train and inference; document
   the exact context object at each path; report the per-feature train-vs-serve
   distribution.
9. REPRODUCIBILITY (fixes L13, L16, L17): pin the baseline snapshot used for
   labels (hash/manifest); seed all estimators; report the achievable class set
   and realized tier distribution; derive executed tier from the `tier` column,
   not `routing_reason`/`base_tier`.

Until items 1-3 (the three Critical fixes) are satisfied, the current
`test_accuracy` in `learned_router_report.json` must NOT be cited as evidence
for C6 or C7. The fix is experimental/analytical (re-run the evaluation), not a
new model.
