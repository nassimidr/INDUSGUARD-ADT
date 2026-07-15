"""Calcul transparent du score et du niveau de priorité."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PriorityResult:
    score: float
    priority: str
    components: dict[str, float]


class PriorityEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.weights = config["priority_weights"]
        self.severity_scores = config["severity_scores"]
        self.risk_scores = config["risk_scores"]
        self.thresholds = config["priority_thresholds"]

    def calculate(self, row: pd.Series, shutdown_required: bool) -> PriorityResult:
        rul = max(0.0, float(row["predicted_rul_steps"]))
        components = {
            "severity": float(self.severity_scores.get(str(row["severity"]), 0.5)),
            "rul": float(np.clip(1.0 - rul / 100.0, 0.0, 1.0)),
            "risk": float(self.risk_scores.get(str(row["risk_level"]), 0.5)),
            "cascade": float(str(row["diagnosed_fault"]) == "cascade_failure"),
            "safety": float(shutdown_required),
            "production_impact": float(shutdown_required),
            "confidence": (float(row["diagnosis_confidence"]) + float(row["prediction_confidence"])) / 2,
        }
        score = float(np.clip(sum(components[name] * self.weights[name] for name in self.weights) * 100, 0, 100))
        if (
            str(row["severity"]) == "critical"
            or str(row["diagnosed_fault"]) == "cascade_failure"
            or rul <= 5
        ):
            score = max(score, float(self.thresholds["critical"]))
        return PriorityResult(round(score, 3), self._label(score), components)

    def _label(self, score: float) -> str:
        if score >= self.thresholds["critical"]:
            return "critical"
        if score >= self.thresholds["urgent"]:
            return "urgent"
        if score >= self.thresholds["high"]:
            return "high"
        if score >= self.thresholds["medium"]:
            return "medium"
        return "low"
