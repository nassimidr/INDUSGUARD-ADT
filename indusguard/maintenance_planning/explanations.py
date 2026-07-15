"""Explications factuelles des recommandations de maintenance."""

from __future__ import annotations

import pandas as pd


def recommendation_confidence(row: pd.Series, consistency: float) -> float:
    """Confiance technique, non calibrée statistiquement."""
    diagnosis = float(row["diagnosis_confidence"])
    rul = float(row["prediction_confidence"])
    width = float(row["rul_upper_bound"]) - float(row["rul_lower_bound"])
    uncertainty = max(0.0, 1.0 - width / max(float(row["predicted_rul_steps"]) + 10.0, 10.0))
    completeness = 1.0 - float(row.isna().mean())
    return round(max(0.0, min(1.0, 0.35 * diagnosis + 0.35 * rul + 0.15 * consistency + 0.10 * uncertainty + 0.05 * completeness)), 4)


def build_recommendation_explanation(
    row: pd.Series, action: str, priority: str, confidence: float
) -> str:
    return (
        f"{action} est recommandé avec une priorité {priority}, car le diagnostic "
        f"indique {row['diagnosed_fault']} (confiance {float(row['diagnosis_confidence']):.0%}) "
        f"et la RUL est estimée à {float(row['predicted_rul_steps']):.1f} cycles "
        f"avec un risque {row['risk_level']}. Confiance technique de la recommandation : {confidence:.0%}."
    )
