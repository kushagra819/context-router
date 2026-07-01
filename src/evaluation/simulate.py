"""
Offline routing simulation
===========================
Estimate a router's cost/quality from the BASELINE CSVs alone -- no API calls.

Why this is possible (and the assumption it makes)
--------------------------------------------------
The baselines record, for every problem and every tier, each agent's cost and
whether that tier answered the problem correctly. A router only chooses *which
tier runs each agent*. So we can replay the router's tier choices and read the
cost/correctness straight from the baselines, under one explicit assumption:

    INDEPENDENCE ASSUMPTION: a routed pipeline's correctness is approximated by
    the baseline correctness of the tier assigned to the VERIFIER (the agent that
    emits the final answer), and its cost is the sum of each agent's per-tier
    baseline cost.

This is the same precomputed-response methodology used by routing papers
(e.g. RouteLLM). It is an ESTIMATE; the live runs (run_experiment.py) confirm it.
Routers whose decisions depend on generated text (cascade/adaptive use upstream
*confidence*) cannot be faithfully simulated and are skipped unless live.

Content-free routers (oracle, random, fixed_*, fixed_mixed) need no question
text. complexity/learned additionally need the question, supplied via `questions`.
"""

from __future__ import annotations

from pathlib import Path

from src.evaluation.csv_io import per_problem_records, ROLES
from src.evaluation import routing_metrics as RM
from src.router import get_router
from src.utils.config import RESULTS_DIR

CONTENT_FREE = {"oracle", "random", "fixed_t1", "fixed_t2", "fixed_t3", "fixed_t4", "fixed_mixed"}
NEEDS_QUESTION = {"complexity", "learned", "query_level"}
NOT_SIMULABLE = {"cascade", "adaptive"}  # depend on generated-text confidence

TIERS = (1, 2, 3, 4)


def load_tier_records(dataset: str, baselines_dir: Path | None = None) -> dict[int, dict[int, dict]]:
    """For each tier, load per-problem records from the most complete CSV available."""
    base = baselines_dir or (RESULTS_DIR / "baselines")
    backup = base.parent / "baselines_backup"
    out: dict[int, dict[int, dict]] = {}
    for tier in TIERS:
        fname = f"{dataset}_baseline_tier{tier}.csv"
        candidates = [base / fname, backup / fname]
        best: dict[int, dict] = {}
        for path in candidates:
            if path.exists():
                recs = per_problem_records(path)
                if len(recs) > len(best):
                    best = recs
        out[tier] = best
    return out


def common_problem_ids(tier_records: dict[int, dict[int, dict]]) -> list[int]:
    """Problem ids present at EVERY tier (so cost/correctness is defined for any choice)."""
    sets = [set(recs.keys()) for recs in tier_records.values() if recs]
    if len(sets) < len(TIERS):
        return []
    common = set.intersection(*sets) if sets else set()
    return sorted(common)


def simulate(router_name: str, dataset: str, questions: dict[int, str] | None = None,
             baselines_dir: Path | None = None, **router_kwargs) -> dict:
    """
    Simulate one router on one dataset. Returns a dict with per-problem arrays and
    a `summary` of aggregated metrics. Raises if the router cannot be simulated.
    """
    if router_name in NOT_SIMULABLE:
        raise ValueError(
            f"Router '{router_name}' depends on generated-text confidence and cannot be "
            f"simulated offline; run it live with run_experiment.py."
        )
    if router_name in NEEDS_QUESTION and not questions:
        raise ValueError(
            f"Router '{router_name}' needs question text; pass `questions` (load the dataset)."
        )

    tier_records = load_tier_records(dataset, baselines_dir)
    pids = common_problem_ids(tier_records)
    if not pids:
        raise RuntimeError(
            f"No problems present at all 4 tiers for '{dataset}'. "
            f"Run/complete the baselines first."
        )

    router = get_router(router_name, **router_kwargs)

    chosen, oracle_t, correct_flags, f1_flags = [], [], [], []
    costs, in_tokens, out_tokens, latencies, escalations = [], [], [], [], []

    for pid in pids:
        per_tier_correct = {t: bool(tier_records[t][pid]["correct"]) for t in TIERS}
        otier = RM.oracle_tier(per_tier_correct)
        q = (questions or {}).get(pid, "")

        upstream = None
        tiers_for_roles = {}
        n_escalated = 0
        for role in ROLES:
            d = router.select_tier(
                question=q, agent_role=role, context=None,
                upstream_output=upstream, problem_id=pid, dataset=dataset,
            )
            tiers_for_roles[role] = d.tier
            if d.escalated:
                n_escalated += 1
            upstream = "(simulated upstream output)"  # presence only; confidence not modelled

        verifier_tier = tiers_for_roles["verifier"]
        prob_cost = sum(tier_records[tiers_for_roles[r]][pid]["roles"][r]["cost"] for r in ROLES)
        prob_tokens_in = sum(
            tier_records[tiers_for_roles[r]][pid]["roles"][r].get("tokens", 0) for r in ROLES
        )
        prob_lat = sum(tier_records[tiers_for_roles[r]][pid]["latency"] / 3.0 for r in ROLES)

        chosen.append(verifier_tier)
        oracle_t.append(otier)
        is_correct = per_tier_correct[verifier_tier]
        correct_flags.append(is_correct)
        f1_flags.append(1.0 if is_correct else 0.0)  # EM proxy; live runs report true F1
        costs.append(prob_cost)
        in_tokens.append(prob_tokens_in)
        out_tokens.append(0)
        latencies.append(prob_lat)
        escalations.append(n_escalated)

    n = len(pids)
    total_cost = sum(costs)
    total_tokens = sum(in_tokens) + sum(out_tokens)
    correct_count = sum(1 for c in correct_flags if c)

    summary = {
        "router": router_name,
        "dataset": dataset,
        "n": n,
        "mode": "simulation",
        "is_estimate": True,
        "estimate_note": ("OFFLINE ESTIMATE under the independence assumption (routed "
                          "correctness ~= verifier-tier baseline correctness; F1 proxied by EM). "
                          "NOT a live result; cascade/adaptive are not simulable. Quantify the "
                          "sim-vs-live gap on GSM8K once live routed runs exist."),
        "em": round(RM.exact_match(correct_flags) * 100, 2),
        "correct": correct_count,
        "total_cost_usd": round(total_cost, 6),
        "cost_per_task": round(RM.cost_per_task(total_cost, n), 6),
        "avg_latency_s": round(sum(latencies) / n, 2) if n else 0.0,
        "routing_accuracy": round(RM.routing_accuracy(chosen, oracle_t) * 100, 2),
        "over_provision_rate": round(RM.over_provision_rate(chosen, oracle_t) * 100, 2),
        "under_provision_rate": round(RM.under_provision_rate(chosen, oracle_t, correct_flags) * 100, 2),
        "escalation_rate": round(RM.escalation_rate([e > 0 for e in escalations]) * 100, 2),
        "token_efficiency": round(RM.token_efficiency(correct_count, total_tokens), 2),
        "tier_distribution": _tier_dist(chosen),
    }
    return {
        "summary": summary,
        "problem_ids": pids,
        "chosen_tiers": chosen,
        "oracle_tiers": oracle_t,
        "correct_flags": correct_flags,
        "costs": costs,
    }


def _tier_dist(tiers: list[int]) -> dict[str, int]:
    return {f"t{t}": sum(1 for x in tiers if x == t) for t in TIERS}
