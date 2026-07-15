"""Sélection explicable d'une stratégie de maintenance."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .maintenance_catalog import MaintenanceCatalog


@dataclass(frozen=True)
class Recommendation:
    strategy: str
    action: str
    secondary_actions: tuple[str, ...]
    shutdown_required: bool
    inspection_required: bool
    consistency: float


class RecommendationEngine:
    """Combine panne, gravité, RUL, risque et confiance."""

    def __init__(self, catalog: MaintenanceCatalog, confidence_threshold: float) -> None:
        self.catalog = catalog
        self.confidence_threshold = float(confidence_threshold)

    def recommend(self, row: pd.Series) -> Recommendation:
        fault = str(row["diagnosed_fault"])
        definition = self.catalog.get(fault)
        rul = float(row["predicted_rul_steps"])
        severity = str(row["severity"])
        risk = str(row["risk_level"])
        confidence = min(float(row["diagnosis_confidence"]), float(row["prediction_confidence"]))
        if fault == "normal" and risk == "low":
            strategy = "monitor"
        elif fault == "cascade_failure" or severity == "critical" or rul <= 5:
            strategy = "emergency_shutdown"
        elif confidence < self.confidence_threshold:
            strategy = "inspect"
        elif rul <= 20 and severity in {"high", "critical"}:
            strategy = "component_replacement"
        elif severity == "high" or risk in {"high", "critical"} or rul <= 50:
            strategy = "preventive_maintenance"
        elif severity in {"low", "medium"}:
            strategy = "inspect"
        else:
            strategy = definition.strategy
        shutdown = definition.shutdown_required or strategy == "emergency_shutdown"
        inspection = definition.inspection_required or strategy == "inspect"
        consistency = 1.0 if strategy == definition.strategy else 0.8
        return Recommendation(
            strategy, definition.action, definition.secondary_actions,
            shutdown, inspection, consistency,
        )

