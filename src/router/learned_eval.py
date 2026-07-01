"""
Rigorous learned-router evaluation harness
===========================================
Implements the publishability "minimum bar" from
docs/learned_router_risk_assessment.md so the learned-router claim (C6) is
defensible. Everything here is OFFLINE (sklearn + numpy only); the only external
need is the QUESTION TEXT (via `questions_provider` or the HF adapter) to build
features and to run the rule-based comparators.

What it produces (all written into learned_router_report.json by train_router.py):
  1. GROUPED CV (fixes L1/L14/L15): StratifiedGroupKFold by problem_id, repeated
     over >=5 seeds. Reports tier-prediction accuracy mean +/- std and effective
     N = #problems (NOT #rows).
  2. OOD (fixes L2/L10): leave-one-dataset-out -- train on k-1 datasets, test on
     the held-out one. Reports the in-distribution vs OOD gap.
  3. FAIR COMPARISON (fixes L11): learned vs complexity vs random vs a
     majority-tier baseline on the SAME held-out problems, with paired McNemar +
     paired-bootstrap significance on routing accuracy (predicted tier == oracle).
  4. ROLE EVIDENCE (fixes L5): role-feature importances of a final tree -- expected
     ~0, the honest evidence that the learned router is a difficulty classifier,
     not a workflow-aware one.
  5. DATASET-ID PROBE (fixes L6/L9): how well the 10 features predict dataset
     identity (high => features leak dataset/length, not intrinsic difficulty).
  6. CALIBRATION (fixes L8): ECE of out-of-fold predicted-class probabilities.
  7. REPRODUCIBILITY (fixes L16/L17): realized achievable class set + tier
     distribution; all estimators seeded.
"""

from __future__ import annotations

from collections import Counter

from src.router.signals import router_feature_vector, ROLE_ORDER, FEATURE_NAMES
from src.router.training_data import oracle_labels, DEFAULT_F1_THRESHOLD
from src.router import get_router
from src.evaluation import routing_metrics as RM

REPRESENTATIVE_ROLE = "solver"   # role used to read a single tier per problem for router comparison


def _new_estimator(model: str, max_depth: int, seed: int):
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.linear_model import LogisticRegression
    if model == "tree":
        return DecisionTreeClassifier(max_depth=max_depth, random_state=seed, class_weight="balanced")
    return LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed)


def build_problem_table(datasets, questions_provider=None, baselines_dir=None,
                        metric="em", f1_threshold=DEFAULT_F1_THRESHOLD, num_problems=200):
    """One record per labeled (solvable) problem with its question + oracle label."""
    problems = []
    for ds in datasets:
        labels = oracle_labels(ds, metric, f1_threshold, baselines_dir, restrict_intersection=True)
        if questions_provider:
            qmap = questions_provider(ds)
        else:
            from src.pipeline.dataset_adapters import get_adapter
            adapter = get_adapter(ds)
            qmap = {p.id: (p.question, adapter.format_context(p.context))
                    for p in adapter.load(num_problems)}
        for pid, tier in labels.items():
            if pid not in qmap:
                continue
            q, ctx = qmap[pid]
            problems.append({"pid": pid, "dataset": ds, "group": f"{ds}#{pid}",
                             "question": q, "context": ctx, "label": int(tier)})
    return problems


def _expand_rows(problems):
    """problem-level table -> (X, y, groups, dataset_ids) with one row per (problem, role)."""
    X, y, groups, dids = [], [], [], []
    for p in problems:
        for role in ROLE_ORDER:
            X.append(router_feature_vector(p["question"], role, p["context"]))
            y.append(p["label"])
            groups.append(p["group"])
            dids.append(p["dataset"])
    return X, y, groups, dids


def grouped_cv(problems, model="tree", max_depth=5, seeds=(0, 1, 2, 3, 4), n_splits=5):
    """Repeated StratifiedGroupKFold by problem_id. Returns mean+/-std test accuracy
    and per-router routing accuracy (learned/complexity/random/majority) with
    paired significance, all on held-out-by-problem rows."""
    import numpy as np
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.metrics import accuracy_score

    X, y, groups, _ = _expand_rows(problems)
    X = np.array(X, dtype=float); y = np.array(y); groups = np.array(groups)
    by_group = {p["group"]: p for p in problems}

    fold_acc = []
    # Per-problem routing-correct flags, accumulated across seeds (held-out only).
    learned_correct, complexity_correct, random_correct, majority_correct = [], [], [], []
    ece_probs, ece_correct = [], []
    rng_random = get_router("random", seed=12345)
    rng_complexity = get_router("complexity")

    n_labels = len(set(y.tolist()))
    for seed in seeds:
        if n_labels < 2:
            break
        majority_tier = Counter(y.tolist()).most_common(1)[0][0]
        try:
            sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
            splits = list(sgkf.split(X, y, groups))
        except ValueError:
            # too few groups per class for this n_splits; reduce splits
            sgkf = StratifiedGroupKFold(n_splits=min(3, n_splits), shuffle=True, random_state=seed)
            splits = list(sgkf.split(X, y, groups))
        for tr, te in splits:
            clf = _new_estimator(model, max_depth, seed)
            clf.fit(X[tr], y[tr])
            fold_acc.append(accuracy_score(y[te], clf.predict(X[te])))
            # Problem-level routing comparison on held-out groups (seed 0 only to
            # avoid double-counting a problem across seeds).
            if seed == seeds[0]:
                seen = set()
                for i in te:
                    g = groups[i]
                    if g in seen:
                        continue
                    seen.add(g)
                    p = by_group[g]
                    oracle = p["label"]
                    feat = [router_feature_vector(p["question"], REPRESENTATIVE_ROLE, p["context"])]
                    lt = int(min(4, max(1, clf.predict(feat)[0])))
                    ct = rng_complexity.select_tier(p["question"], REPRESENTATIVE_ROLE, p["context"]).tier
                    rt = rng_random.select_tier(p["question"], REPRESENTATIVE_ROLE, p["context"]).tier
                    learned_correct.append(1.0 if lt == oracle else 0.0)
                    complexity_correct.append(1.0 if ct == oracle else 0.0)
                    random_correct.append(1.0 if rt == oracle else 0.0)
                    majority_correct.append(1.0 if majority_tier == oracle else 0.0)
                    if hasattr(clf, "predict_proba"):
                        proba = clf.predict_proba(feat)[0]
                        ece_probs.append(float(max(proba)))
                        ece_correct.append(1.0 if lt == oracle else 0.0)

    mean = float(np.mean(fold_acc)) if fold_acc else float("nan")
    std = float(np.std(fold_acc)) if fold_acc else float("nan")
    out = {
        "n_problems": len(problems),
        "n_rows": len(X),
        "n_folds_total": len(fold_acc),
        "n_seeds": len(seeds),
        "tier_pred_accuracy_mean": round(mean, 4),
        "tier_pred_accuracy_std": round(std, 4),
        "routing_accuracy": {
            "learned": round(RM.exact_match([c > 0 for c in learned_correct]) * 100, 2) if learned_correct else None,
            "complexity": round(RM.exact_match([c > 0 for c in complexity_correct]) * 100, 2) if complexity_correct else None,
            "random": round(RM.exact_match([c > 0 for c in random_correct]) * 100, 2) if random_correct else None,
            "majority_tier": round(RM.exact_match([c > 0 for c in majority_correct]) * 100, 2) if majority_correct else None,
        },
        "learned_vs_complexity": {
            "mcnemar": RM.mcnemar_test(learned_correct, complexity_correct) if learned_correct else None,
            "paired_bootstrap_greater_p": (round(RM.paired_bootstrap_pvalue(
                learned_correct, complexity_correct, alternative="greater"), 4) if learned_correct else None),
            "routing_acc_diff_ci": ({k: round(v, 4) if isinstance(v, float) else v
                                     for k, v in RM.paired_diff_ci(learned_correct, complexity_correct).items()}
                                    if learned_correct else None),
        },
        "calibration_ece": round(_ece(ece_probs, ece_correct), 4) if ece_probs else None,
    }
    return out


def leave_one_dataset_out(problems, model="tree", max_depth=5, seed=0):
    """Train on all-but-one dataset, evaluate tier-prediction accuracy on the
    held-out dataset (OOD). Reports the in-distribution vs OOD gap."""
    import numpy as np
    from sklearn.metrics import accuracy_score
    datasets = sorted({p["dataset"] for p in problems})
    results = {}
    for held in datasets:
        train_p = [p for p in problems if p["dataset"] != held]
        test_p = [p for p in problems if p["dataset"] == held]
        if not train_p or not test_p:
            continue
        Xtr, ytr, _, _ = _expand_rows(train_p)
        Xte, yte, _, _ = _expand_rows(test_p)
        clf = _new_estimator(model, max_depth, seed)
        clf.fit(np.array(Xtr, dtype=float), np.array(ytr))
        ood_acc = float(accuracy_score(yte, clf.predict(np.array(Xte, dtype=float))))
        # majority-tier-of-train baseline on the held-out set
        maj = Counter(ytr).most_common(1)[0][0]
        maj_acc = float(np.mean([1.0 if t == maj else 0.0 for t in yte]))
        results[held] = {"ood_accuracy": round(ood_acc, 4),
                         "majority_baseline_accuracy": round(maj_acc, 4),
                         "n_test_problems": len(test_p)}
    return results


def dataset_id_probe(problems, max_depth=5, seed=0):
    """Leakage probe: how well do the 10 features predict DATASET identity?
    High accuracy => features encode dataset/length, not intrinsic difficulty (L6)."""
    import numpy as np
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import cross_val_score
    X, _, _, dids = _expand_rows(problems)
    if len(set(dids)) < 2:
        return {"note": "single dataset; probe not applicable"}
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=seed)
    scores = cross_val_score(clf, np.array(X, dtype=float), np.array(dids), cv=5)
    baseline = max(Counter(dids).values()) / len(dids)
    return {"dataset_id_cv_accuracy": round(float(scores.mean()), 4),
            "majority_class_baseline": round(baseline, 4),
            "interpretation": "accuracy >> baseline => features leak dataset identity"}


def role_importances(problems, model="tree", max_depth=5, seed=0):
    """Final-model role-feature importances (or |coef|). Expected ~0 because oracle
    labels are role-invariant -> honest evidence of role-collapse (L5)."""
    import numpy as np
    X, y, _, _ = _expand_rows(problems)
    clf = _new_estimator(model, max_depth, seed).fit(np.array(X, dtype=float), np.array(y))
    if hasattr(clf, "feature_importances_"):
        imp = clf.feature_importances_
    else:
        imp = np.abs(clf.coef_).mean(axis=0)
        imp = imp / (imp.sum() or 1.0)
    importances = {name: round(float(v), 4) for name, v in zip(FEATURE_NAMES, imp)}
    role_keys = ("role_analyzer", "role_solver", "role_verifier")
    return {"importances": importances,
            "role_importance_sum": round(sum(importances[k] for k in role_keys), 4),
            "achievable_classes": sorted(int(c) for c in clf.classes_)}


def _ece(probs, correct, n_bins=10):
    """Expected Calibration Error of max-class probabilities vs correctness."""
    if not probs:
        return float("nan")
    bins = [[] for _ in range(n_bins)]
    for p, c in zip(probs, correct):
        idx = min(n_bins - 1, int(p * n_bins))
        bins[idx].append((p, c))
    n = len(probs)
    ece = 0.0
    for b in bins:
        if not b:
            continue
        conf = sum(p for p, _ in b) / len(b)
        acc = sum(c for _, c in b) / len(b)
        ece += (len(b) / n) * abs(conf - acc)
    return ece


def full_evaluation(datasets, questions_provider=None, baselines_dir=None,
                    metric="em", f1_threshold=DEFAULT_F1_THRESHOLD, num_problems=200,
                    model="tree", max_depth=5, seeds=(0, 1, 2, 3, 4)):
    """Run the whole battery and return a single report dict."""
    problems = build_problem_table(datasets, questions_provider, baselines_dir,
                                   metric, f1_threshold, num_problems)
    report = {
        "datasets": datasets, "metric": metric, "model": model, "max_depth": max_depth,
        "n_problems": len(problems),
        "label_distribution": {f"t{t}": sum(1 for p in problems if p["label"] == t) for t in (1, 2, 3, 4)},
        "grouped_cv": grouped_cv(problems, model, max_depth, seeds) if problems else None,
        "ood_leave_one_dataset_out": leave_one_dataset_out(problems, model, max_depth) if problems else None,
        "dataset_id_probe": dataset_id_probe(problems, max_depth) if problems else None,
        "role_evidence": role_importances(problems, model, max_depth) if problems else None,
    }
    return report
