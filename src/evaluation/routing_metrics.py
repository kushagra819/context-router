"""
Routing / Efficiency / Research metrics
=======================================
Formal, self-contained implementations of every metric defined in
docs/13_METRICS_AND_FORMULAS.md. Each function documents its formula so the doc
and the code can never silently drift apart.

Conventions
-----------
* "quality" is a fraction in [0,1] (EM or F1), unless a function says otherwise.
* "cost" is hypothetical USD (sum of per-call costs); see docs/03_MODEL_MATRIX.md.
* A problem's per-tier "correct" flags come from the baselines (CSV truth source).
* The oracle tier for a problem is the cheapest tier that answered it correctly.
"""

from __future__ import annotations

import math
import random as _random
from collections import Counter

TIERS = (1, 2, 3, 4)


# --------------------------------------------------------------------------- #
# Task metrics (means over problems)
# --------------------------------------------------------------------------- #
def exact_match(correct_flags: list[bool]) -> float:
    """EM / Accuracy = mean(correct).  Returns a fraction in [0,1]."""
    return sum(1 for c in correct_flags if c) / len(correct_flags) if correct_flags else 0.0


def mean_f1(f1_scores: list[float]) -> float:
    """Macro token-F1 = mean of per-problem F1."""
    return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0


# --------------------------------------------------------------------------- #
# Oracle / routing-quality metrics
# --------------------------------------------------------------------------- #
def oracle_tier(per_tier_correct: dict[int, bool]) -> int | None:
    """Cheapest tier that answered the problem correctly, or None if no tier did."""
    for t in TIERS:
        if per_tier_correct.get(t):
            return t
    return None


def routing_accuracy(chosen_tiers: list[int], oracle_tiers: list[int | None]) -> float:
    """
    Routing Accuracy = fraction of problems where the router's representative tier
    equals the oracle tier. Problems with no correct tier (oracle = None) are
    excluded from the denominator (no "right answer" exists to route to).
    """
    pairs = [(c, o) for c, o in zip(chosen_tiers, oracle_tiers) if o is not None]
    if not pairs:
        return 0.0
    return sum(1 for c, o in pairs if c == o) / len(pairs)


def over_provision_rate(chosen_tiers: list[int], oracle_tiers: list[int | None]) -> float:
    """
    Over-Provision Rate = fraction of problems where the router used a HIGHER
    (more expensive) tier than the oracle needed. Wasted capability.
    Excludes problems with no correct tier.
    """
    pairs = [(c, o) for c, o in zip(chosen_tiers, oracle_tiers) if o is not None]
    if not pairs:
        return 0.0
    return sum(1 for c, o in pairs if c > o) / len(pairs)


def under_provision_rate(
    chosen_tiers: list[int],
    oracle_tiers: list[int | None],
    correct_flags: list[bool] | None = None,
) -> float:
    """
    Under-Provision Rate = fraction of SOLVABLE problems where the router chose a
    tier STRICTLY BELOW the oracle tier (under-powered a winnable problem). This is
    the symmetric counterpart of over_provision_rate (chosen > oracle). Because the
    oracle is the cheapest CORRECT tier, chosen < oracle implies the chosen tier was
    incorrect by construction, so this isolates failures specifically caused by
    under-powering (not non-monotonic failures at/above the oracle tier).
    Denominator = solvable problems (oracle is not None). `correct_flags` is accepted
    for backward compatibility but no longer needed.
    """
    pairs = [(c, o) for c, o in zip(chosen_tiers, oracle_tiers) if o is not None]
    if not pairs:
        return 0.0
    return sum(1 for c, o in pairs if c < o) / len(pairs)


def escalation_rate(escalated_flags: list[bool]) -> float:
    """Escalation Rate = fraction of agent CALLS the router escalated above base tier."""
    return sum(1 for e in escalated_flags if e) / len(escalated_flags) if escalated_flags else 0.0


# --------------------------------------------------------------------------- #
# Efficiency metrics
# --------------------------------------------------------------------------- #
def cost_per_task(total_cost: float, n: int) -> float:
    return total_cost / n if n else 0.0


def cost_reduction_factor(reference_cost: float, router_cost: float) -> float:
    """How many times cheaper the router is than the reference (e.g. all-Tier-4)."""
    return reference_cost / router_cost if router_cost > 0 else float("inf")


def cost_savings_pct(reference_cost: float, router_cost: float) -> float:
    """(1 - router/reference) * 100. Positive = cheaper than reference."""
    return (1 - router_cost / reference_cost) * 100 if reference_cost > 0 else 0.0


def throughput_per_min(n: int, total_latency_s: float) -> float:
    """Problems completed per minute (sum of per-problem latencies as wall-clock proxy)."""
    return n / (total_latency_s / 60.0) if total_latency_s > 0 else 0.0


def token_efficiency(correct_count: int, total_tokens: int) -> float:
    """Correct answers produced per 1M tokens consumed (quality-per-token)."""
    return correct_count / (total_tokens / 1_000_000) if total_tokens > 0 else 0.0


# --------------------------------------------------------------------------- #
# Research metrics
# --------------------------------------------------------------------------- #
def quality_retention_pct(router_quality: float, reference_quality: float) -> float:
    """router_quality / reference_quality * 100. 100% = matches the frontier ceiling."""
    return (router_quality / reference_quality) * 100 if reference_quality > 0 else 0.0


def workflow_context_gain(workflow_aware_quality: float, best_context_free_quality: float) -> float:
    """
    Workflow Context Gain (WCG) = quality(workflow-aware router) -
    quality(best context-free router) AT MATCHED (<=) COST.

    This isolates the value of the workflow-only signals (agent role, upstream
    confidence, workflow stage) from generic query-difficulty routing. Returns a
    quality-fraction delta (multiply by 100 for points). The caller is
    responsible for selecting the matched-cost comparators.
    """
    return workflow_aware_quality - best_context_free_quality


# --------------------------------------------------------------------------- #
# Statistical significance
# --------------------------------------------------------------------------- #
def bootstrap_ci(
    values: list[float],
    n_boot: int = 10_000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Percentile bootstrap (1-alpha) CI for the mean of `values`
    (e.g. per-problem correct flags as 0/1, or per-problem F1).
    Deterministic given `seed`.
    """
    if not values:
        return (0.0, 0.0)
    rng = _random.Random(seed)
    n = len(values)
    means = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot) - 1]
    return (lo, hi)


def paired_bootstrap_pvalue(
    a_flags: list[float],
    b_flags: list[float],
    n_boot: int = 10_000,
    seed: int = 42,
    alternative: str = "two-sided",
) -> float:
    """
    Paired bootstrap p-value for two systems on the SAME problems (aligned
    per-problem outcomes). H0: mean(a) == mean(b).

    `alternative`:
      * "two-sided" : H1 mean(a) != mean(b)           (count |s| >= |obs|)
      * "greater"   : H1 mean(a) >  mean(b)            (count  s  >=  obs)  -- the
                      registered one-sided primary for WCG > 0 (see
                      docs/statistical_validation_plan.md): pass a=workflow-aware,
                      b=context-free.
      * "less"      : H1 mean(a) <  mean(b)            (count  s  <=  obs)

    The bootstrap distribution is built under H0 by centering the per-problem
    differences. Deterministic given `seed`.
    """
    if len(a_flags) != len(b_flags) or not a_flags:
        return float("nan")
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(f"alternative must be two-sided|greater|less, got {alternative!r}")
    rng = _random.Random(seed)
    n = len(a_flags)
    diffs = [a - b for a, b in zip(a_flags, b_flags)]
    obs = sum(diffs) / n
    centered = [d - obs for d in diffs]
    count = 0
    for _ in range(n_boot):
        s = sum(centered[rng.randrange(n)] for _ in range(n)) / n
        if alternative == "two-sided":
            if abs(s) >= abs(obs):
                count += 1
        elif alternative == "greater":
            if s >= obs:
                count += 1
        else:  # less
            if s <= obs:
                count += 1
    return count / n_boot


def paired_diff_ci(
    a_flags: list[float],
    b_flags: list[float],
    n_boot: int = 10_000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Bootstrap CI for the paired mean difference mean(a) - mean(b), plus the
    point estimate. Use this to report (effect size, CI) for every comparison."""
    if len(a_flags) != len(b_flags) or not a_flags:
        return {"diff": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n": 0}
    rng = _random.Random(seed)
    n = len(a_flags)
    diffs = [a - b for a, b in zip(a_flags, b_flags)]
    obs = sum(diffs) / n
    means = []
    for _ in range(n_boot):
        means.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot) - 1]
    return {"diff": obs, "ci_low": lo, "ci_high": hi, "n": n}


def mcnemar_test(a_flags: list[float], b_flags: list[float], exact: bool = True) -> dict:
    """
    Exact (or continuity-corrected) McNemar test for two classifiers on the SAME
    problems, using only the DISCORDANT pairs (a wrong & b right vs a right & b
    wrong). This is the standard paired test for binary correctness and does NOT
    assume i.i.d. rows. Returns {n01, n10, n_discordant, p_value, statistic}.

    * exact=True  : two-sided exact binomial p with p=0.5 (recommended for small
                    discordant counts -- our N is small).
    * exact=False : continuity-corrected chi-square approximation.
    """
    if len(a_flags) != len(b_flags) or not a_flags:
        return {"n01": 0, "n10": 0, "n_discordant": 0, "p_value": float("nan"), "statistic": float("nan")}
    n01 = sum(1 for a, b in zip(a_flags, b_flags) if a < b)   # a wrong, b right
    n10 = sum(1 for a, b in zip(a_flags, b_flags) if a > b)   # a right, b wrong
    nd = n01 + n10
    if nd == 0:
        return {"n01": 0, "n10": 0, "n_discordant": 0, "p_value": 1.0, "statistic": 0.0}
    if exact:
        k = min(n01, n10)
        tail = sum(math.comb(nd, i) for i in range(k + 1)) * (0.5 ** nd)
        p = min(1.0, 2.0 * tail)
        return {"n01": n01, "n10": n10, "n_discordant": nd, "p_value": p, "statistic": float(k)}
    stat = (abs(n01 - n10) - 1) ** 2 / nd
    p = _chi2_sf_1df(stat)
    return {"n01": n01, "n10": n10, "n_discordant": nd, "p_value": p, "statistic": stat}


def _chi2_sf_1df(x: float) -> float:
    """Survival function of chi-square with 1 dof = 2*(1 - Phi(sqrt(x)))."""
    if x <= 0:
        return 1.0
    from statistics import NormalDist
    return 2.0 * (1.0 - NormalDist().cdf(math.sqrt(x)))


def holm_bonferroni(pvalues: dict[str, float], alpha: float = 0.05) -> dict[str, dict]:
    """
    Holm-Bonferroni step-down correction over a family of comparisons.
    Input: {comparison_name: p_value}. Output: {name: {p, p_adjusted, reject}}.
    Controls family-wise error rate at `alpha`. (See statistical_validation_plan.md §6.)
    """
    items = [(k, v) for k, v in pvalues.items() if v == v]  # drop NaN
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    out: dict[str, dict] = {}
    prev_adj = 0.0
    for i, (name, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        adj = max(adj, prev_adj)   # enforce monotonicity (step-down)
        prev_adj = adj
        out[name] = {"p": p, "p_adjusted": adj, "reject": adj <= alpha}
    for k, v in pvalues.items():
        if v != v:
            out[k] = {"p": float("nan"), "p_adjusted": float("nan"), "reject": False}
    return out


def benjamini_hochberg(pvalues: dict[str, float], alpha: float = 0.05) -> dict[str, dict]:
    """Benjamini-Hochberg FDR control over a family. Output mirrors holm_bonferroni."""
    items = [(k, v) for k, v in pvalues.items() if v == v]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    out: dict[str, dict] = {}
    min_adj = 1.0
    for i in range(m - 1, -1, -1):
        name, p = items[i]
        adj = min(min_adj, p * m / (i + 1))
        min_adj = adj
        out[name] = {"p": p, "p_adjusted": adj, "reject": adj <= alpha}
    for k, v in pvalues.items():
        if v != v:
            out[k] = {"p": float("nan"), "p_adjusted": float("nan"), "reject": False}
    return out


def min_detectable_effect_proportion(
    n: int, baseline: float = 0.5, alpha: float = 0.05, power: float = 0.8,
    one_sided: bool = False,
) -> float:
    """
    Minimum detectable EFFECT (absolute change in proportion) for an UNPAIRED
    two-proportion comparison at sample size `n` per arm -- a conservative
    reference for "is N big enough?". Paired tests (mcnemar/paired bootstrap) are
    strictly more powerful, so the achievable MDE is no worse than this.
    Normal approximation (uses statistics.NormalDist; no scipy needed).
    """
    from statistics import NormalDist
    if n <= 0:
        return float("nan")
    nd = NormalDist()
    z_a = nd.inv_cdf(1 - (alpha if one_sided else alpha / 2))
    z_b = nd.inv_cdf(power)
    # Solve (z_a+z_b)*sqrt(2 p (1-p) / n) for delta (approx, equal-variance).
    var = baseline * (1 - baseline)
    return (z_a + z_b) * math.sqrt(2 * var / n)


# --------------------------------------------------------------------------- #
# Workflow Context Gain -- operational matched-cost protocol
# --------------------------------------------------------------------------- #
def select_matched_cost_comparator(
    workflow_cost: float,
    candidates: list[dict],
    tolerance_frac: float = 0.05,
) -> dict | None:
    """
    Pick the context-free comparator for a matched-cost WCG, OPERATIONALLY and
    WITHOUT peeking at quality differences (fixes the forking-path concern,
    reviewer S-wcg): among context-free routers whose mean cost is <= the
    workflow-aware router's cost * (1 + tolerance_frac), return the CHEAPEST-
    eligible... no -- the HIGHEST-COST eligible one (the strongest comparator the
    cost budget allows), breaking ties by name for determinism.

    `candidates`: list of {"name", "quality", "cost"} for context-free routers
    (e.g. complexity, fixed_mixed, random, fixed_t*). Returns the chosen dict or
    None if none fit the budget.
    """
    budget = workflow_cost * (1 + tolerance_frac)
    eligible = [c for c in candidates if c["cost"] <= budget]
    if not eligible:
        return None
    # Strongest comparator the budget allows = the one closest to (<=) the budget.
    return sorted(eligible, key=lambda c: (-c["cost"], c["name"]))[0]


def workflow_context_gain_matched(
    workflow_quality: float,
    workflow_cost: float,
    candidates: list[dict],
    tolerance_frac: float = 0.05,
) -> dict:
    """
    Workflow Context Gain with the matched-cost comparator chosen operationally.
    WCG = quality(workflow-aware) - quality(best context-free router at <= matched
    cost). Returns the gain, the chosen comparator, and the realized cost gap so
    the match is auditable. A positive WCG means the workflow-only signals (role,
    upstream confidence, stage) buy quality beyond difficulty-only routing.
    """
    comp = select_matched_cost_comparator(workflow_cost, candidates, tolerance_frac)
    if comp is None:
        return {"wcg": float("nan"), "comparator": None, "reason": "no context-free router within cost budget"}
    return {
        "wcg": workflow_quality - comp["quality"],
        "comparator": comp["name"],
        "comparator_quality": comp["quality"],
        "comparator_cost": comp["cost"],
        "workflow_quality": workflow_quality,
        "workflow_cost": workflow_cost,
        "cost_gap_frac": (comp["cost"] - workflow_cost) / workflow_cost if workflow_cost else float("nan"),
        "tolerance_frac": tolerance_frac,
    }
