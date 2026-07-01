"""
Offline smoke tests (no API, no network, no third-party deps required).

Run directly:        python tests/test_offline.py
Or with pytest:      pytest tests/test_offline.py

These exercise the whole orchestration path with MockModel + the stdlib
analysis stack, so the home machine can verify the code works before spending
any API quota.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.router import get_router, list_routers
from src.router.signals import router_feature_vector, FEATURE_NAMES, extract_confidence
from src.models.registry import ModelRegistry
from src.pipeline.dataset_adapters import get_adapter, Problem
from src.pipeline.routed_pipeline import RoutedPipeline
from src.evaluation import routing_metrics as RM


def test_router_factory():
    names = list_routers()
    assert {"oracle", "random", "fixed_t1", "fixed_mixed", "complexity",
            "cascade", "adaptive"}.issubset(set(names))
    for n in ["random", "fixed_t1", "fixed_t4", "fixed_mixed", "complexity", "cascade", "adaptive"]:
        r = get_router(n)
        d = r.select_tier(question="What is 2+2?", agent_role="solver")
        assert d.tier in (1, 2, 3, 4)
    print(f"[ok] router factory: {len(names)} routers -> {names}")


def test_feature_vector():
    v = router_feature_vector("Who directed the film and when was it released?", "solver", "ctx " * 100)
    assert len(v) == len(FEATURE_NAMES)
    assert v[FEATURE_NAMES.index("role_solver")] == 1.0
    print(f"[ok] feature vector length {len(v)} matches FEATURE_NAMES")


def test_confidence_signal():
    assert extract_confidence("The answer is clearly 5. Final Answer: 5") > 0.6
    assert extract_confidence("I'm not sure, it might be ambiguous") < 0.5
    print("[ok] confidence extraction monotonic")


def test_mock_pipeline():
    adapter = get_adapter("gsm8k")
    registry = ModelRegistry(mock=True)
    pipe = RoutedPipeline(adapter, registry)
    problems = [
        Problem(id=0, question="What is 2+2?", context=None, ground_truth="4"),
        Problem(id=1, question="If a train travels 60 miles in 2 hours, what is its speed?",
                context=None, ground_truth="30"),
    ]
    for router_name in ["fixed_t1", "fixed_mixed", "complexity", "cascade", "adaptive", "random"]:
        router = get_router(router_name)
        for p in problems:
            res = pipe.run_problem(p, router)
            assert len(res.calls) == 3
            assert res.tier_path[0] in (1, 2, 3, 4)
            assert res.total_cost >= 0.0
    print("[ok] mock pipeline runs all routers x problems, 3 calls each")


def test_fixed_mixed_tier_path():
    adapter = get_adapter("hotpotqa")
    registry = ModelRegistry(mock=True)
    pipe = RoutedPipeline(adapter, registry)
    p = Problem(id=0, question="Who is older, A or B?",
                context={"title": ["A", "B"], "sentences": [["A born 1950."], ["B born 1960."]]},
                ground_truth="A")
    res = pipe.run_problem(p, get_router("fixed_mixed"))
    # default fixed_mixed: analyzer->2, solver->4, verifier->1
    assert res.tier_path == [2, 4, 1], res.tier_path
    print(f"[ok] fixed_mixed tier path = {res.tier_path}")


def test_routing_metrics():
    chosen = [1, 2, 4, 3]
    oracle = [1, 3, 4, None]
    correct = [True, False, True, False]
    assert abs(RM.routing_accuracy(chosen, oracle) - (2 / 3)) < 1e-9
    assert RM.cost_reduction_factor(10.0, 2.0) == 5.0
    assert abs(RM.cost_savings_pct(10.0, 2.0) - 80.0) < 1e-9
    assert abs(RM.quality_retention_pct(0.9, 0.97) - 92.78) < 0.1
    lo, hi = RM.bootstrap_ci([1, 1, 1, 0, 0], n_boot=2000)
    assert 0.0 <= lo <= hi <= 1.0
    print("[ok] routing metrics + bootstrap CI")


def test_offline_simulation_gsm8k():
    """GSM8K has all 4 tiers complete -> content-free routers are simulable offline."""
    from src.evaluation.simulate import simulate
    try:
        for name in ["oracle", "fixed_t1", "fixed_t4", "fixed_mixed", "random"]:
            out = simulate(name, "gsm8k")
            s = out["summary"]
            assert 0 <= s["em"] <= 100 and s["n"] > 0
            print(f"     sim {name:12} EM={s['em']:5.1f}%  cost=${s['total_cost_usd']:.4f}  "
                  f"route_acc={s['routing_accuracy']:.1f}%  tiers={s['tier_distribution']}")
        print("[ok] offline GSM8K simulation for content-free routers")
    except RuntimeError as e:
        print(f"[skip] GSM8K simulation ({e})")


def test_runner_glue_mock():
    """Run the full experiment driver offline with a synthetic dataset (no `datasets` dep)."""
    import src.pipeline.experiment as EXP
    from src.pipeline.dataset_adapters import GSM8KAdapter, Problem

    class SyntheticGSM8K(GSM8KAdapter):
        def load(self, num_problems):
            return [Problem(id=i, question=f"What is {i}+{i}?", context=None,
                            ground_truth=str(2 * i)) for i in range(num_problems)]

    orig = EXP.get_adapter
    EXP.get_adapter = lambda name: SyntheticGSM8K()
    try:
        stats = EXP.run_experiment("gsm8k", "cascade", num_problems=4, mock=True)
    finally:
        EXP.get_adapter = orig

    from src.utils.config import RESULTS_DIR
    csv_path = RESULTS_DIR / "_mock" / "gsm8k_cascade.csv"
    assert csv_path.exists(), csv_path
    from src.evaluation.csv_io import read_rows
    rows = read_rows(csv_path)
    assert len(rows) == 4 * 3, len(rows)            # 4 problems x 3 agents
    assert "confidence" in rows[0] and "routing_reason" in rows[0]
    assert stats["session_processed"] == 4
    print(f"[ok] experiment driver wrote {len(rows)} rows with full schema")


def test_learned_router_roundtrip():
    """Train -> save -> load -> predict, using synthetic questions (no `datasets` dep)."""
    try:
        from sklearn.tree import DecisionTreeClassifier
    except ImportError:
        print("[skip] learned router (scikit-learn not installed)")
        return
    import pickle
    from src.router.training_data import build_training_data
    from src.router.learned_router import LearnedRouter
    from src.utils.config import RESULTS_DIR

    def synthetic_questions(dataset):
        # short question -> easy (low tier label tendency); long -> harder
        return {i: (("word " * (i % 40 + 1)).strip(), "ctx " * (i % 20)) for i in range(200)}

    X, y, groups, dataset_ids, names, meta = build_training_data(
        ["gsm8k"], questions_provider=synthetic_questions)
    assert len(X) == len(y) == len(groups) == len(dataset_ids) > 0 and len(X[0]) == len(names)
    assert meta["n_problems"] == len(set(groups))
    clf = DecisionTreeClassifier(max_depth=4, random_state=0).fit(X, y)

    out = RESULTS_DIR / "routing" / "learned_router_test.pkl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump({"model": clf, "feature_names": names,
                     "classes": [int(c) for c in clf.classes_], "meta": meta}, f)
    try:
        lr = LearnedRouter(model_path=out)
        d = lr.select_tier(question="word word word", agent_role="solver")
        assert d.tier in (1, 2, 3, 4)
        print(f"[ok] learned router roundtrip (predicted T{d.tier}, labels={meta['label_distribution']})")
    finally:
        out.unlink(missing_ok=True)


def test_robust_answer_extraction():
    """Markdown-bold / verbose Final-Answer recovery (the Tier-4 anomaly fix)."""
    from src.evaluation.metrics import extract_hotpotqa_answer, normalize_answer
    cases = [
        ("...\n**Final Answer:** Greenwich Village, New York City", "greenwich village new york city"),
        ("blah\n**Final Answer:**\n3,677 people", "3677 people"),
        ("reasoning Final Answer: Terry Richardson", "terry richardson"),
        ("text **Final Answer:** **yes**", "yes"),
    ]
    for txt, exp in cases:
        got = normalize_answer(extract_hotpotqa_answer(txt))
        assert got == exp, f"{got!r} != {exp!r}"
    print("[ok] robust answer extraction (Markdown/verbose)")


def test_statistics():
    """One-sided vs two-sided bootstrap, McNemar, Holm, paired-diff CI, matched-cost WCG."""
    from src.evaluation import routing_metrics as RM
    a = [1, 1, 1, 0, 1, 1, 0, 1, 1, 1]
    b = [0, 1, 0, 0, 1, 0, 0, 1, 0, 1]
    p2 = RM.paired_bootstrap_pvalue(a, b, n_boot=4000, alternative="two-sided")
    pg = RM.paired_bootstrap_pvalue(a, b, n_boot=4000, alternative="greater")
    assert pg <= p2 + 1e-9 and 0 <= pg <= 1
    mc = RM.mcnemar_test(a, b)
    assert mc["n_discordant"] == 4 and abs(mc["p_value"] - 0.125) < 1e-9
    holm = RM.holm_bonferroni({"x": 0.01, "y": 0.04, "z": 0.2})
    assert holm["x"]["reject"] and not holm["z"]["reject"]
    ci = RM.paired_diff_ci(a, b)
    assert ci["ci_low"] <= ci["diff"] <= ci["ci_high"]
    cands = [{"name": "complexity", "quality": 0.61, "cost": 0.5},
             {"name": "fixed_mixed", "quality": 0.58, "cost": 0.9}]
    wcg = RM.workflow_context_gain_matched(0.64, 0.55, cands)
    assert wcg["comparator"] == "complexity" and abs(wcg["wcg"] - 0.03) < 1e-9
    print("[ok] statistics: one-sided bootstrap / McNemar / Holm / paired-CI / matched-cost WCG")


def test_query_level_router():
    """query_level assigns the SAME tier to all 3 roles of a problem (per-query control)."""
    r = get_router("query_level")
    tiers = {role: r.select_tier("Who directed the film and when?", role, context="ctx " * 50,
                                 problem_id=7, dataset="hotpotqa").tier for role in
             ("analyzer", "solver", "verifier")}
    assert len(set(tiers.values())) == 1, tiers
    assert "query_level" in list_routers()
    print(f"[ok] query_level router: one tier per query {set(tiers.values())}")


def test_logprob_confidence():
    """Pipeline uses CALIBRATED logprob confidence (exp(mean_logprob)) when available."""
    import math
    from src.router.signals import confidence_from_logprob
    assert confidence_from_logprob(None) is None
    assert abs(confidence_from_logprob(0.0) - 1.0) < 1e-9
    assert abs(confidence_from_logprob(-0.5) - math.exp(-0.5)) < 1e-9
    adapter = get_adapter("gsm8k")
    registry = ModelRegistry(mock=True)
    pipe = RoutedPipeline(adapter, registry)
    res = pipe.run_problem(Problem(id=0, question="What is 2+2?", context=None, ground_truth="4"),
                           get_router("cascade"))
    for call in res.calls:
        assert call.confidence_source == "logprob"          # MockModel emits mean_logprob
        assert call.response.mean_logprob is not None
        assert abs(call.confidence - math.exp(call.response.mean_logprob)) < 1e-6
    print("[ok] calibrated logprob confidence path (source=logprob, conf=exp(mean_logprob))")


def test_under_provision_symmetric():
    """under_provision_rate counts chosen < oracle (symmetric to over_provision)."""
    chosen = [1, 4, 2, 3]
    oracle = [3, 2, 2, None]
    assert abs(RM.under_provision_rate(chosen, oracle) - (1 / 3)) < 1e-9   # only (1<3)
    assert abs(RM.over_provision_rate(chosen, oracle) - (1 / 3)) < 1e-9    # only (4>2)
    print("[ok] under/over-provision symmetric definitions")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    print(f"Running {len(tests)} offline smoke tests...\n")
    for t in tests:
        t()
    print(f"\nAll {len(tests)} offline smoke tests passed.")


if __name__ == "__main__":
    main()
