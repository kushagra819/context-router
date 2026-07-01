"""
Confidence-signal validation
============================
The cascade/adaptive routers escalate when the UPSTREAM agent's `extract_confidence`
(a lexical hedging/assertion score) is low. Reviewers correctly demand evidence
that this signal actually correlates with correctness before any "confidence
cascade works" claim. This module measures, OFFLINE from the baseline responses:

  * AUC of upstream confidence predicting final correctness (0.5 = no signal),
  * mean confidence | correct vs | incorrect (separation),
  * point-biserial correlation,
  * ECE (calibration of the confidence value vs empirical accuracy).

Computed on cells with untruncated `response_text` + `ground_truth`. If AUC is
near 0.5, the honest move is to soften the confidence-cascade claim (or replace
the signal); if AUC > ~0.6 the cascade has an empirical basis. Pure stdlib.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

from src.router.signals import extract_confidence, confidence_from_logprob
from src.evaluation.metrics import hotpotqa_check_correct, extract_hotpotqa_answer
from src.utils.config import RESULTS_DIR

ROLES = ("analyzer", "solver", "verifier")


def _auc(scores: list[float], labels: list[int]) -> float | None:
    """ROC-AUC via the Mann-Whitney rank statistic (handles ties)."""
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # average rank (1-based)
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    sum_pos = sum(ranks[i] for i in range(len(scores)) if labels[i] == 1)
    return (sum_pos - pos * (pos + 1) / 2.0) / (pos * neg)


def _ece(scores: list[float], labels: list[int], n_bins: int = 10) -> float | None:
    if not scores:
        return None
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for s, y in zip(scores, labels):
        bins[min(n_bins - 1, int(s * n_bins))].append((s, y))
    n = len(scores)
    ece = 0.0
    for b in bins:
        if not b:
            continue
        conf = sum(s for s, _ in b) / len(b)
        acc = sum(y for _, y in b) / len(b)
        ece += len(b) / n * abs(conf - acc)
    return ece


def validate_cell(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or "ground_truth" not in rows[0]:
        return None
    by_key = {}
    for r in rows:
        try:
            pid = int(float(r.get("problem_id", "")))
        except (ValueError, TypeError):
            continue
        by_key[(pid, (r.get("agent_role") or "").strip())] = r
    pids = sorted({p for (p, _) in by_key})

    # upstream confidence = SOLVER's confidence (what the verifier's routing sees);
    # outcome = final correctness. Recompute LEXICAL confidence from text (don't trust
    # the column). Also score CALIBRATED logprob confidence when the run logged it.
    conf_solver, conf_verifier, correct = [], [], []
    lp_solver, lp_correct = [], []   # calibrated logprob-confidence (new-schema runs only)
    for pid in pids:
        v = by_key.get((pid, "verifier"))
        s = by_key.get((pid, "solver"))
        if not v or not s:
            continue
        vtext = v.get("response_text") or ""
        stext = s.get("response_text") or ""
        if len(vtext) <= 1 or "[ERROR]" in vtext:
            continue
        gt = (v.get("ground_truth") or "").strip()
        if not gt:
            continue
        ok = 1 if hotpotqa_check_correct(extract_hotpotqa_answer(vtext), gt) else 0
        conf_solver.append(extract_confidence(stext))
        conf_verifier.append(extract_confidence(vtext))
        correct.append(ok)
        # Calibrated confidence from the solver's logged mean_logprob, if present.
        mlp = s.get("mean_logprob")
        if mlp not in (None, "", "None"):
            try:
                c = confidence_from_logprob(float(mlp))
                if c is not None:
                    lp_solver.append(c)
                    lp_correct.append(ok)
            except (ValueError, TypeError):
                pass

    n = len(correct)
    if n == 0:
        return None
    cpos = [c for c, ok in zip(conf_solver, correct) if ok]
    cneg = [c for c, ok in zip(conf_solver, correct) if not ok]
    out = {
        "cell": path.stem, "n": n, "accuracy": round(sum(correct) / n, 3),
        "auc_solver_conf_vs_final_correct": (round(_auc(conf_solver, correct), 3)
                                             if _auc(conf_solver, correct) is not None else None),
        "auc_verifier_conf_vs_correct": (round(_auc(conf_verifier, correct), 3)
                                         if _auc(conf_verifier, correct) is not None else None),
        "mean_solver_conf_when_correct": round(sum(cpos) / len(cpos), 3) if cpos else None,
        "mean_solver_conf_when_incorrect": round(sum(cneg) / len(cneg), 3) if cneg else None,
        "ece_verifier_conf": (round(_ece(conf_verifier, correct), 3)
                              if _ece(conf_verifier, correct) is not None else None),
    }
    # Calibrated logprob-confidence comparison (populated once runs log mean_logprob).
    if lp_solver:
        auc_lp = _auc(lp_solver, lp_correct)
        out["auc_logprob_conf_vs_correct"] = round(auc_lp, 3) if auc_lp is not None else None
        out["ece_logprob_conf"] = (round(_ece(lp_solver, lp_correct), 3)
                                   if _ece(lp_solver, lp_correct) is not None else None)
        out["n_logprob"] = len(lp_solver)
    return out


def run(baselines_dir: Path | None = None) -> dict:
    base = baselines_dir or (RESULTS_DIR / "baselines")
    cells = []
    for ds in ("hotpotqa", "musique"):
        for t in (1, 2, 3, 4):
            r = validate_cell(base / f"{ds}_baseline_tier{t}.csv")
            if r:
                cells.append(r)
    aucs = [c["auc_solver_conf_vs_final_correct"] for c in cells
            if c["auc_solver_conf_vs_final_correct"] is not None]
    return {
        "cells": cells,
        "mean_auc_solver_conf": round(sum(aucs) / len(aucs), 3) if aucs else None,
        "interpretation": ("AUC ~0.5 => the lexical confidence carries little signal about "
                           "correctness; >0.6 => a usable escalation signal. Report honestly."),
    }
