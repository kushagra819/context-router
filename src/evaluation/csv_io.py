"""
CSV I/O helpers
===============
Shared, dependency-free readers for the experiment logs. CSV files are the
source of truth (ADR-001); these helpers de-duplicate resume artifacts and
expose per-problem records that every analysis tool reuses.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

ROLES = ("analyzer", "solver", "verifier")


def read_rows(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def dedup_by_problem_role(rows: list[dict]) -> dict[tuple[int, str], dict]:
    """Keep the LAST row for each (problem_id, agent_role); handles resume dupes."""
    out: dict[tuple[int, str], dict] = {}
    for r in rows:
        try:
            pid = int(float(r.get("problem_id", "")))
        except (ValueError, TypeError):
            continue
        role = (r.get("agent_role") or "").strip()
        out[(pid, role)] = r
    return out


def _f(row: dict, key: str, default=0.0) -> float:
    try:
        v = row.get(key, default)
        return float(v) if v not in (None, "") else float(default)
    except (ValueError, TypeError):
        return float(default)


def _i(row: dict, key: str, default=0) -> int:
    try:
        v = row.get(key, default)
        return int(float(v)) if v not in (None, "") else int(default)
    except (ValueError, TypeError):
        return int(default)


def per_problem_records(path: Path) -> dict[int, dict]:
    """
    Collapse an experiment CSV into one record per COMPLETE problem
    (all 3 agent roles present, verifier not an [ERROR]).

    Each record:
        {
          "correct": bool, "f1": float|None,
          "cost": float, "input_tokens": int, "output_tokens": int, "latency": float,
          "tiers": {role: tier}, "escalations": int,
          "roles": {role: {"cost":..., "tier":..., "tokens":...}},
        }
    """
    by_key = dedup_by_problem_role(read_rows(path))
    pids = sorted({pid for (pid, _) in by_key})
    out: dict[int, dict] = {}
    for pid in pids:
        roles_present = {r for (p, r) in by_key if p == pid}
        if not set(ROLES).issubset(roles_present):
            continue
        vrow = by_key.get((pid, "verifier"))
        if vrow is None or "[ERROR]" in str(vrow.get("response_text", "")):
            continue

        rec = {
            "correct": str(vrow.get("correct", "")).strip().lower() == "true",
            "f1": None,
            "cost": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "latency": 0.0,
            "tiers": {},
            "escalations": 0,
            "roles": {},
        }
        # F1 may be stored per-row (new schema); take verifier's value if present.
        f1v = vrow.get("f1")
        if f1v not in (None, ""):
            try:
                rec["f1"] = float(f1v)
            except (ValueError, TypeError):
                rec["f1"] = None

        for role in ROLES:
            r = by_key.get((pid, role))
            if not r:
                continue
            cost = _f(r, "cost_usd")
            itok = _i(r, "input_tokens")
            otok = _i(r, "output_tokens")
            tier = _i(r, "tier")
            rec["cost"] += cost
            rec["input_tokens"] += itok
            rec["output_tokens"] += otok
            rec["latency"] += _f(r, "latency_s")
            rec["tiers"][role] = tier
            rec["roles"][role] = {"cost": cost, "tier": tier, "tokens": itok + otok}
            ef = r.get("escalated_from")
            if ef not in (None, "", "None"):
                rec["escalations"] += 1
        out[pid] = rec
    return out
