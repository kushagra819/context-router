"""
Training-data builder + oracle-label logic for the learned router
=================================================================
Turns the baselines into supervised examples for predicting a model tier, and
provides the SINGLE canonical definition of the per-problem "oracle tier" reused
by `OracleRouter`, `simulate`, and the metrics layer.

Oracle tier (per problem)
-------------------------
The cheapest tier whose baseline answer is "correct" under a chosen metric:
  * metric="em"  -> the EM `correct` flag (default; always available).
  * metric="f1"  -> token-F1 >= `f1_threshold` (soft match; needs the f1 column).
Problems that NO tier solves are *unsolvable*: they carry no valid "cheapest
correct tier", so they are EXCLUDED from the training labels (returning them as
T4 would teach the router to burn the most expensive tier on problems where it
provably cannot help -- the L4 "hardest vs unsolvable" confound). The OracleRouter
routes such problems to T1 (cheapest), since no tier succeeds and spending more is
wasted -- so both consumers treat "unsolvable" coherently.

Comparability
-------------
Cross-tier labels are only meaningful on problems present at EVERY tier. We
restrict to the intersection of problem_ids across all four tiers (the same rule
`simulate.common_problem_ids` uses), and report the dropped-N so the label
construction is fully auditable. This removes the mixed-N / mixed-source confound.

Role and the learned router
---------------------------
We emit one example per (problem, role) so the feature vector carries the role
one-hot, but the oracle label is PROBLEM-LEVEL (uniform-tier baselines give us no
per-role sufficiency signal). The learned router is therefore, by construction, a
data-driven *difficulty* classifier; `train_router.py` reports the role-feature
importance (expected ~0) as honest evidence rather than claiming the learned
router is workflow-aware. Workflow-awareness is the contribution of the *rule-based*
`cascade`/`adaptive` routers, which consume role + upstream confidence at inference.

`questions_provider` lets callers inject {pid: (question, context_str)} so the
builder (and its tests) run without downloading the HF datasets.
"""

from __future__ import annotations

from pathlib import Path

from src.router.signals import router_feature_vector, FEATURE_NAMES, ROLE_ORDER
from src.evaluation.csv_io import per_problem_records
from src.utils.config import RESULTS_DIR

TIERS = (1, 2, 3, 4)
DEFAULT_F1_THRESHOLD = 0.6


# --------------------------------------------------------------------------- #
# Source selection + correctness
# --------------------------------------------------------------------------- #
def _best_records(dataset: str, tier: int, baselines_dir: Path | None = None) -> dict[int, dict]:
    """Per-problem records for (dataset, tier), preferring the more complete CSV
    (active over backup). This is the one place the active/backup choice is made."""
    base = baselines_dir or (RESULTS_DIR / "baselines")
    backup = base.parent / "baselines_backup"
    fname = f"{dataset}_baseline_tier{tier}.csv"
    best: dict[int, dict] = {}
    for path in (base / fname, backup / fname):
        if path.exists():
            recs = per_problem_records(path)
            if len(recs) > len(best):
                best = recs
    return best


def _is_correct(rec: dict, metric: str, f1_threshold: float) -> bool:
    """Correctness of one per-problem record under the chosen metric."""
    if metric == "f1":
        f1 = rec.get("f1")
        if f1 is None:
            # No F1 available (legacy/truncated cell) -> fall back to EM so the
            # tier is not silently dropped from the 'cheapest correct' search.
            return bool(rec.get("correct"))
        return float(f1) >= f1_threshold
    return bool(rec.get("correct"))


def tier_correctness(
    dataset: str,
    metric: str = "em",
    f1_threshold: float = DEFAULT_F1_THRESHOLD,
    baselines_dir: Path | None = None,
    restrict_intersection: bool = True,
) -> tuple[dict[int, dict[int, bool]], list[int], dict]:
    """Return ({tier: {pid: correct_bool}}, eligible_pids, meta).

    `eligible_pids` is the intersection of problem_ids present at all four tiers
    when restrict_intersection=True (the only set on which cross-tier oracle
    labels are comparable), else their union.
    """
    recs_by_tier = {t: _best_records(dataset, t, baselines_dir) for t in TIERS}
    pid_sets = [set(recs_by_tier[t].keys()) for t in TIERS]
    union = sorted(set().union(*pid_sets)) if any(pid_sets) else []
    inter = sorted(set.intersection(*pid_sets)) if all(pid_sets) else []
    eligible = inter if restrict_intersection else union

    correct = {
        t: {pid: _is_correct(recs_by_tier[t][pid], metric, f1_threshold)
            for pid in recs_by_tier[t]}
        for t in TIERS
    }
    meta = {
        "metric": metric,
        "f1_threshold": f1_threshold if metric == "f1" else None,
        "n_per_tier": {f"t{t}": len(recs_by_tier[t]) for t in TIERS},
        "n_union": len(union),
        "n_intersection": len(inter),
        "n_eligible": len(eligible),
        "restricted_to_intersection": restrict_intersection,
    }
    return correct, eligible, meta


def cheapest_correct_tier(per_tier_correct: dict[int, dict[int, bool]], pid: int) -> int | None:
    """Cheapest tier with correct==True for `pid`, or None if no tier solved it."""
    for t in TIERS:
        if per_tier_correct.get(t, {}).get(pid):
            return t
    return None


def oracle_labels(
    dataset: str,
    metric: str = "em",
    f1_threshold: float = DEFAULT_F1_THRESHOLD,
    baselines_dir: Path | None = None,
    restrict_intersection: bool = True,
    include_unsolvable: bool = False,
) -> dict[int, int]:
    """{problem_id: cheapest correct tier}. Unsolvable problems are excluded by
    default (include_unsolvable=False); set include_unsolvable=True to map them to
    T1 (the OracleRouter convention)."""
    correct, eligible, _ = tier_correctness(
        dataset, metric, f1_threshold, baselines_dir, restrict_intersection)
    labels: dict[int, int] = {}
    for pid in eligible:
        tier = cheapest_correct_tier(correct, pid)
        if tier is None:
            if include_unsolvable:
                labels[pid] = 1  # no tier helps -> spend the least (OracleRouter convention)
            continue
        labels[pid] = tier
    return labels


def label_report(dataset: str, baselines_dir: Path | None = None) -> dict:
    """Diagnostic comparison of EM vs F1 oracle labels (for the paper's honesty
    section): label distributions, unsolvable rate, and EM-vs-F1 label agreement."""
    em_correct, eligible, em_meta = tier_correctness(dataset, "em", baselines_dir=baselines_dir)
    f1_correct, _, f1_meta = tier_correctness(dataset, "f1", baselines_dir=baselines_dir)
    em_lab, f1_lab, agree, unsolv_em, unsolv_f1 = {}, {}, 0, 0, 0
    for pid in eligible:
        e = cheapest_correct_tier(em_correct, pid)
        f = cheapest_correct_tier(f1_correct, pid)
        em_lab[pid] = e
        f1_lab[pid] = f
        if e is None:
            unsolv_em += 1
        if f is None:
            unsolv_f1 += 1
        if e == f:
            agree += 1
    n = len(eligible)
    dist = lambda d: {f"t{t}": sum(1 for v in d.values() if v == t) for t in TIERS}
    return {
        "dataset": dataset,
        "n_eligible": n,
        "n_intersection": em_meta["n_intersection"],
        "n_per_tier": em_meta["n_per_tier"],
        "em_label_distribution": dist(em_lab),
        "f1_label_distribution": dist(f1_lab),
        "unsolvable_em": unsolv_em,
        "unsolvable_f1": unsolv_f1,
        "em_f1_label_agreement_pct": round(100 * agree / n, 2) if n else None,
    }


# --------------------------------------------------------------------------- #
# Feature builder
# --------------------------------------------------------------------------- #
def _questions_via_adapter(dataset: str, num_problems: int) -> dict[int, tuple[str, str]]:
    from src.pipeline.dataset_adapters import get_adapter
    adapter = get_adapter(dataset)
    out = {}
    for p in adapter.load(num_problems):
        out[p.id] = (p.question, adapter.format_context(p.context))
    return out


def build_training_data(
    datasets: list[str],
    num_problems: int = 200,
    questions_provider=None,
    baselines_dir: Path | None = None,
    metric: str = "em",
    f1_threshold: float = DEFAULT_F1_THRESHOLD,
    restrict_intersection: bool = True,
):
    """Return (X, y, groups, dataset_ids, feature_names, meta).

    * groups       : problem_id per row (for GroupKFold by problem -- fixes leakage).
    * dataset_ids  : dataset name per row (for leave-one-dataset-out OOD eval).
    Unsolvable problems are excluded. One row per (problem, role).
    """
    X: list[list[float]] = []
    y: list[int] = []
    groups: list[str] = []          # globally-unique "dataset#pid" so groups don't collide
    dataset_ids: list[str] = []
    counts: dict[str, int] = {}
    per_dataset_meta: dict[str, dict] = {}

    for dataset in datasets:
        labels = oracle_labels(dataset, metric, f1_threshold, baselines_dir,
                               restrict_intersection, include_unsolvable=False)
        _, eligible, dmeta = tier_correctness(dataset, metric, f1_threshold,
                                              baselines_dir, restrict_intersection)
        qmap = (questions_provider(dataset) if questions_provider
                else _questions_via_adapter(dataset, num_problems))
        n = 0
        for pid, tier in labels.items():
            if pid not in qmap:
                continue
            question, context = qmap[pid]
            for role in ROLE_ORDER:
                X.append(router_feature_vector(question, role, context))
                y.append(int(tier))
                groups.append(f"{dataset}#{pid}")
                dataset_ids.append(dataset)
                n += 1
        counts[dataset] = n
        dmeta["n_labeled_problems"] = len(labels)
        dmeta["n_unsolvable_excluded"] = len(eligible) - len(labels)
        per_dataset_meta[dataset] = dmeta

    meta = {
        "datasets": datasets,
        "metric": metric,
        "f1_threshold": f1_threshold if metric == "f1" else None,
        "n_examples": len(X),
        "n_problems": len(set(groups)),
        "examples_per_dataset": counts,
        "label_distribution": {f"t{t}": y.count(t) for t in TIERS},
        "feature_names": list(FEATURE_NAMES),
        "per_dataset": per_dataset_meta,
    }
    return X, y, groups, dataset_ids, list(FEATURE_NAMES), meta
