"""
Figure generation
==================
All paper/presentation figures, defined in docs/15_FIGURE_PLAN.md.

Two kinds:
  * SCHEMATIC figures (architecture, workflow, decision flow) are drawn from code
    and need no experiment data -- they can be produced any time.
  * DATA figures (Pareto, utilization, ablation, escalation) read the aggregated
    rows produced by aggregate_results.py / simulate_routing.py. They degrade
    gracefully (skip with a message) when the underlying data is missing.

Uses the non-interactive Agg backend so it runs headless on any machine.
Outputs PNG (+ PDF for vector figures) into results/figures/.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from src.utils.config import RESULTS_DIR

FIG_DIR = RESULTS_DIR / "figures"
TIER_COLORS = {1: "#e74c3c", 2: "#e67e22", 3: "#3498db", 4: "#2ecc71"}
TIER_LABELS = {1: "T1 Gemma 4B", 2: "T2 Llama 70B", 3: "T3 GPT-OSS 120B", 4: "T4 GPT-4.1"}


def _save(fig, name: str, also_pdf: bool = False):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    png = FIG_DIR / f"{name}.png"
    fig.savefig(png, dpi=200, bbox_inches="tight")
    if also_pdf:
        fig.savefig(FIG_DIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    return png


def _box(ax, xy, w, h, text, color="#ecf0f1", ec="#2c3e50", fontsize=10, tc="#2c3e50"):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                linewidth=1.6, edgecolor=ec, facecolor=color))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
            color=tc, weight="bold", wrap=True)


def _arrow(ax, p1, p2, color="#2c3e50"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16,
                                 linewidth=1.6, color=color))


# --------------------------------------------------------------------------- #
# Schematic figures (no data needed)
# --------------------------------------------------------------------------- #
def fig_architecture():
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.set_title("System Architecture: Context-Aware Router for Multi-Agent Pipelines",
                 fontsize=12, weight="bold")
    _box(ax, (0.3, 4.6), 2.2, 0.9, "Problem\n(question + context)", "#dfe6e9")
    _box(ax, (3.0, 4.6), 2.2, 0.9, "Signal Extractor\n(features, confidence)", "#fdebd0")
    _box(ax, (5.7, 4.6), 2.2, 0.9, "Router\n(select tier per agent)", "#d6eaf8")
    _box(ax, (8.0, 4.6), 1.7, 0.9, "Decision\nTier 1-4", "#d5f5e3")
    for x in (2.5, 5.2, 7.9):
        _arrow(ax, (x, 5.05), (x + 0.5, 5.05))
    # Model tiers
    for i, t in enumerate((1, 2, 3, 4)):
        _box(ax, (0.6 + i * 2.3, 2.6), 1.9, 0.8, TIER_LABELS[t], TIER_COLORS[t], tc="white")
    _arrow(ax, (8.85, 4.6), (8.85, 3.4))
    # Pipeline
    _box(ax, (1.2, 0.6), 2.2, 0.9, "Analyzer", "#ecf0f1")
    _box(ax, (4.0, 0.6), 2.2, 0.9, "Solver", "#ecf0f1")
    _box(ax, (6.8, 0.6), 2.2, 0.9, "Verifier -> Answer", "#ecf0f1")
    _arrow(ax, (3.4, 1.05), (4.0, 1.05)); _arrow(ax, (6.2, 1.05), (6.8, 1.05))
    ax.text(5.0, 2.15, "Router selects a tier independently for each agent call",
            ha="center", fontsize=9, style="italic", color="#7f8c8d")
    return _save(fig, "fig1_architecture", also_pdf=True)


def fig_workflow():
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.set_xlim(0, 9); ax.set_ylim(0, 3); ax.axis("off")
    ax.set_title("Multi-Agent Workflow (Analyzer -> Solver -> Verifier)", fontsize=12, weight="bold")
    steps = [("Analyzer\ndecompose / select facts", 0.4),
             ("Solver\nmulti-hop reasoning", 3.2),
             ("Verifier\ncheck + finalize answer", 6.0)]
    for text, x in steps:
        _box(ax, (x, 1.0), 2.5, 1.0, text, "#d6eaf8")
    _arrow(ax, (2.9, 1.5), (3.2, 1.5)); _arrow(ax, (5.7, 1.5), (6.0, 1.5))
    ax.text(4.5, 0.4, "upstream output + confidence feed the next routing decision",
            ha="center", fontsize=9, style="italic", color="#7f8c8d")
    return _save(fig, "fig2_workflow", also_pdf=True)


def fig_router_decision_flow():
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.set_xlim(0, 7.5); ax.set_ylim(0, 7); ax.axis("off")
    ax.set_title("Router Decision Flow (per agent call)", fontsize=12, weight="bold")
    _box(ax, (2.5, 6.0), 2.6, 0.7, "Incoming agent call", "#dfe6e9")
    _box(ax, (2.5, 4.8), 2.6, 0.7, "Complexity < floor?", "#fdebd0")
    _box(ax, (0.2, 3.6), 2.0, 0.7, "Tier 1", TIER_COLORS[1], tc="white")
    _box(ax, (2.5, 3.6), 2.6, 0.7, "Upstream confident?", "#fdebd0")
    _box(ax, (5.4, 3.6), 1.9, 0.7, "Role base tier", "#d6eaf8")
    _box(ax, (2.5, 2.2), 2.6, 0.7, "Escalate +1 tier", "#f9e79f")
    _box(ax, (2.5, 0.9), 2.6, 0.7, "Budget cap -> clamp", "#d5f5e3")
    _arrow(ax, (3.8, 6.0), (3.8, 5.5)); _arrow(ax, (3.8, 4.8), (3.8, 4.3))
    _arrow(ax, (2.5, 5.15), (2.2, 4.3)); ax.text(1.9, 4.55, "yes", fontsize=8)
    _arrow(ax, (5.1, 3.95), (5.4, 3.95)); ax.text(5.15, 4.05, "high", fontsize=8)
    _arrow(ax, (3.8, 3.6), (3.8, 2.9)); ax.text(3.9, 3.2, "low", fontsize=8)
    _arrow(ax, (3.8, 2.2), (3.8, 1.6))
    return _save(fig, "fig3_router_decision_flow", also_pdf=True)


# --------------------------------------------------------------------------- #
# Data figures
# --------------------------------------------------------------------------- #
def fig_pareto(rows: list[dict], dataset: str):
    pts = [r for r in rows if r.get("dataset") == dataset and r.get("n")]
    if not pts:
        return None
    fig, ax = plt.subplots(figsize=(7, 5))
    xs = [r["cost_per_task"] for r in pts]
    ys = [r["em"] for r in pts]
    for r in pts:
        is_router = not r["label"].startswith("baseline")
        ax.scatter(r["cost_per_task"], r["em"], s=90,
                   marker=("*" if r["label"] == "oracle" else ("o" if is_router else "s")),
                   color=("#8e44ad" if is_router else "#34495e"),
                   zorder=3, edgecolors="white")
        ax.annotate(r["label"], (r["cost_per_task"], r["em"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=8)
    # Pareto frontier (max EM at <= cost).
    order = sorted(zip(xs, ys), key=lambda t: t[0])
    fx, fy, best = [], [], -1
    for x, y in order:
        if y > best:
            fx.append(x); fy.append(y); best = y
    ax.step(fx, fy, where="post", color="#e67e22", linestyle="--", linewidth=1.5,
            label="Pareto frontier", zorder=2)
    ax.set_xscale("log")
    ax.set_xlabel("Cost per task (USD, log scale)")
    ax.set_ylabel("Exact Match (%)")
    ax.set_title(f"Cost vs Quality Pareto Frontier — {dataset}")
    ax.grid(True, alpha=0.3); ax.legend()
    return _save(fig, f"fig4_pareto_{dataset}", also_pdf=True)


def fig_model_utilization(rows: list[dict], dataset: str):
    pts = [r for r in rows if r.get("dataset") == dataset and r.get("tier_distribution")]
    if not pts:
        return None
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = [r["label"] for r in pts]
    bottoms = [0] * len(pts)
    for t in (1, 2, 3, 4):
        vals = [r["tier_distribution"].get(f"t{t}", 0) for r in pts]
        ax.bar(labels, vals, bottom=bottoms, color=TIER_COLORS[t], label=TIER_LABELS[t])
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_ylabel("Problems (by verifier tier)")
    ax.set_title(f"Model Utilization by Router — {dataset}")
    ax.legend(fontsize=8); plt.xticks(rotation=30, ha="right")
    return _save(fig, f"fig5_utilization_{dataset}")


def fig_ablation(rows: list[dict], dataset: str):
    pts = [r for r in rows if r.get("dataset") == dataset
           and ("ablation" in r["label"] or r["label"] in ("adaptive", "cascade", "complexity"))]
    if len(pts) < 2:
        return None
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = [r["label"] for r in pts]
    ax.bar(labels, [r["em"] for r in pts], color="#5dade2")
    ax.set_ylabel("Exact Match (%)")
    ax.set_title(f"Ablation: routing signals — {dataset}")
    plt.xticks(rotation=30, ha="right"); ax.grid(True, axis="y", alpha=0.3)
    return _save(fig, f"fig6_ablation_{dataset}")


def fig_escalation(rows: list[dict], dataset: str):
    pts = [r for r in rows if r.get("dataset") == dataset and r.get("escalation_rate") is not None
           and not r["label"].startswith("baseline")]
    if not pts:
        return None
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = [r["label"] for r in pts]
    ax.bar(labels, [r.get("escalation_rate", 0) for r in pts], color="#f5b041")
    ax.set_ylabel("Escalation rate (% of agent calls)")
    ax.set_title(f"Escalation Behaviour by Router — {dataset}")
    plt.xticks(rotation=30, ha="right"); ax.grid(True, axis="y", alpha=0.3)
    return _save(fig, f"fig7_escalation_{dataset}")


SCHEMATICS = [fig_architecture, fig_workflow, fig_router_decision_flow]
DATA_FIGURES = [fig_pareto, fig_model_utilization, fig_ablation, fig_escalation]
