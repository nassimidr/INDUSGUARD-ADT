"""Conversion d'une RUL en niveau de risque configurable."""

from __future__ import annotations

from typing import Mapping


def assess_risk(rul_steps: float, thresholds: Mapping[str, float]) -> str:
    """Retourne low, medium, high ou critical."""
    if rul_steps <= float(thresholds["critical_max"]):
        return "critical"
    if rul_steps <= float(thresholds["high_max"]):
        return "high"
    if rul_steps <= float(thresholds["medium_max"]):
        return "medium"
    return "low"

