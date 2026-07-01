"""
Learned Router
==============
A data-driven router that predicts the model tier for each agent call from
question features + agent role, using a small classifier trained offline on the
baseline results (see train_router.py / src/router/training_data.py).

Training labels are the "oracle tier": the cheapest tier that answered each
problem correctly in the baselines. The classifier therefore learns a cheap,
interpretable approximation of the oracle from features available at inference
time (no peeking at the answer).

The trained artifact is a pickle containing:
    {"model": <sklearn estimator>, "feature_names": [...], "classes": [...],
     "meta": {...}}

This router degrades gracefully: if the artifact or scikit-learn is missing it
raises a clear, actionable error instead of failing silently.
"""

from __future__ import annotations

import pickle
from pathlib import Path

from src.router.base_router import BaseRouter, RoutingDecision
from src.router.signals import router_feature_vector, FEATURE_NAMES
from src.utils.config import RESULTS_DIR

DEFAULT_MODEL_PATH = RESULTS_DIR / "routing" / "learned_router.pkl"


class LearnedRouter(BaseRouter):
    def __init__(self, model_path: str | Path | None = None):
        self._model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"Learned router artifact not found at {self._model_path}.\n"
                f"Train it first:  python train_router.py --datasets gsm8k hotpotqa musique"
            )
        try:
            with open(self._model_path, "rb") as f:
                bundle = pickle.load(f)
        except ModuleNotFoundError as e:  # scikit-learn not installed
            raise RuntimeError(
                "Could not unpickle the learned router (scikit-learn missing?). "
                "Install requirements:  pip install -r requirements.txt"
            ) from e

        self._model = bundle["model"]
        self._feature_names = bundle.get("feature_names", list(FEATURE_NAMES))
        self._classes = bundle.get("classes")
        self._meta = bundle.get("meta", {})

    def select_tier(
        self,
        question: str,
        agent_role: str,
        context: dict | None = None,
        upstream_output: str | None = None,
        upstream_confidence: float | None = None,
        cost_spent: float = 0.0,
        cost_budget: float = float("inf"),
        problem_id: int | None = None,
        dataset: str = "",
    ) -> RoutingDecision:
        x = [router_feature_vector(question, agent_role, context)]
        pred = int(self._model.predict(x)[0])
        base_tier = min(4, max(1, pred))

        # Real model confidence = posterior of the predicted class (fixes the
        # hardcoded-0.7 issue, L8). Enables ECE/reliability diagrams. Falls back to
        # 1.0 only if the estimator lacks predict_proba (e.g. a bare regressor).
        confidence = 1.0
        if hasattr(self._model, "predict_proba"):
            try:
                proba = self._model.predict_proba(x)[0]
                confidence = float(max(proba))
            except Exception:
                confidence = 0.0

        # Budget guard (records the executed tier honestly in reason/base_tier, L13).
        tier = base_tier
        budget_capped = False
        if cost_budget < float("inf") and (cost_budget - cost_spent) < 0.001 and tier > 1:
            tier = 1
            budget_capped = True

        reason = f"Learned classifier predicted T{pred} (p={confidence:.2f})"
        if budget_capped:
            reason += " [budget-capped to T1]"
        return RoutingDecision(
            tier=tier,
            router_name=self.name,
            agent_role=agent_role,
            reason=reason,
            confidence=confidence,
            base_tier=base_tier,   # pre-budget predicted tier; executed tier is `tier`
        )

    @property
    def name(self) -> str:
        return "learned"
