"""Génération d'explications basées sur les capteurs observés."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from .fault_catalog import FAULT_CATALOG


def build_explanation(fault: str, sensors: Iterable[str], row: pd.Series) -> str:
    """Explique un diagnostic avec les valeurs réellement disponibles."""
    definition = FAULT_CATALOG.get(fault, FAULT_CATALOG["unknown_fault"])
    observations = []
    for sensor in sensors:
        value: Any = row.get(sensor)
        if not pd.isna(value):
            observations.append(f"{sensor}={float(value):.2f}")
    if fault == "normal":
        return definition.description
    if observations:
        return f"{definition.description} Mesures observées : {', '.join(observations)}."
    return definition.description


def severity_for(row: pd.Series, fault: str, confidence: float) -> str:
    """Combine état, santé, confiance et caractère en cascade."""
    if fault == "normal":
        return "none"
    state = str(row.get("operating_state", "normal"))
    health = float(row.get("health_score", 100.0))
    if state == "critical" or health < 30:
        return "critical"
    if fault == "cascade_failure" or health < 50 or confidence >= 0.9:
        return "high"
    if state == "degradation" or confidence >= 0.75:
        return "medium"
    return "low"

