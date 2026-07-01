"""
Train + rigorously evaluate the learned router.

This does TWO things:
  1. Fits the DEPLOYED artifact on ALL labeled problems (it is the model the
     LearnedRouter loads at inference) and saves a pickle bundle.
  2. Runs the publishability evaluation battery (src/router/learned_eval.py) and
     writes a comprehensive `*_report.json`. The HEADLINE number is the
     GROUPED-by-problem CV accuracy (mean +/- std over seeds) -- NOT an in-sample
     or per-example-split accuracy, which would leak (see
     docs/learned_router_risk_assessment.md, L1).

Labels come from the baselines (oracle tier = cheapest correct tier). Use
`--metric f1` for F1-aware labels (recommended for the multi-hop sets, where EM
under-credits verbose frontier answers).

Example
-------
  python train_router.py --datasets gsm8k hotpotqa musique --model tree --max-depth 5 --metric f1

Requires scikit-learn + numpy (requirements.txt) and, to load questions, the HF
`datasets` package (API-free, one-time download). Output:
  results/routing/learned_router.pkl  (+ _report.json)
"""

import argparse
import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.router.training_data import build_training_data
from src.router.learned_router import DEFAULT_MODEL_PATH
from src.router.learned_eval import full_evaluation
from src.pipeline.dataset_adapters import available_datasets


def main():
    ap = argparse.ArgumentParser(description="Train + rigorously evaluate the learned router.")
    ap.add_argument("--datasets", nargs="+", default=available_datasets(), choices=available_datasets())
    ap.add_argument("--num-problems", type=int, default=200)
    ap.add_argument("--model", choices=["tree", "logreg"], default="tree")
    ap.add_argument("--max-depth", type=int, default=5)
    ap.add_argument("--metric", choices=["em", "f1"], default="f1",
                    help="Oracle-label correctness metric (f1 recommended for multi-hop).")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--out", default=str(DEFAULT_MODEL_PATH))
    args = ap.parse_args()

    import numpy as np
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.linear_model import LogisticRegression

    print(f"Building training data from baselines for {args.datasets} (metric={args.metric}) ...")
    X, y, groups, dataset_ids, feature_names, meta = build_training_data(
        args.datasets, args.num_problems, metric=args.metric)
    if not X:
        print("No training examples found. Run/validate the baselines first.")
        sys.exit(1)
    print(f"  {meta['n_examples']} rows | {meta['n_problems']} problems | "
          f"labels {meta['label_distribution']}")

    # --- Deployed artifact: fit on ALL labeled data (seeded). ---
    seed0 = args.seeds[0]
    if args.model == "tree":
        clf = DecisionTreeClassifier(max_depth=args.max_depth, random_state=seed0, class_weight="balanced")
    else:
        clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed0)
    clf.fit(np.array(X, dtype=float), np.array(y))

    # --- Honest evaluation battery (grouped CV / OOD / comparison / probes). ---
    print("Running grouped-CV / OOD / fair-comparison battery ...")
    evaluation = full_evaluation(
        args.datasets, metric=args.metric, num_problems=args.num_problems,
        model=args.model, max_depth=args.max_depth, seeds=tuple(args.seeds))

    gcv = evaluation.get("grouped_cv") or {}
    print(f"  GROUPED-CV tier accuracy: {gcv.get('tier_pred_accuracy_mean')} "
          f"+/- {gcv.get('tier_pred_accuracy_std')}  (effective N={gcv.get('n_problems')} problems)")
    ra = gcv.get("routing_accuracy", {})
    print(f"  Routing accuracy (vs oracle): learned={ra.get('learned')}  "
          f"complexity={ra.get('complexity')}  random={ra.get('random')}  majority={ra.get('majority_tier')}")
    role_ev = evaluation.get("role_evidence", {})
    print(f"  Role-feature importance sum (expect ~0 => difficulty clf): "
          f"{role_ev.get('role_importance_sum')}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": clf,
        "feature_names": feature_names,
        "classes": [int(c) for c in clf.classes_],
        "meta": {**meta, "model_type": args.model, "max_depth": args.max_depth,
                 "seeds": args.seeds,
                 "deployed_fit": "all labeled problems (in-sample fit; see report for held-out CV)"},
    }
    with open(out_path, "wb") as f:
        pickle.dump(bundle, f)

    report = {
        "out": str(out_path),
        "label_metric": args.metric,
        "label_distribution": meta["label_distribution"],
        "per_dataset_label_meta": meta["per_dataset"],
        "evaluation": evaluation,
        "honesty_note": (
            "Headline accuracy is the GROUPED-by-problem CV mean+/-std, not the "
            "in-sample fit. The learned router is a data-driven DIFFICULTY classifier: "
            "oracle labels are problem-level, so role-feature importance is ~0 (reported "
            "above). Workflow-awareness is the contribution of the rule-based cascade/"
            "adaptive routers, which consume role + upstream confidence at inference."),
    }
    report_path = out_path.with_name(out_path.stem + "_report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  Saved model  -> {out_path}")
    print(f"  Saved report -> {report_path}")


if __name__ == "__main__":
    main()
