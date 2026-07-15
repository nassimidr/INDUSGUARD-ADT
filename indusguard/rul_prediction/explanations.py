"""Explications RUL basées sur les tendances réellement calculées."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def build_rul_explanation(
    row: pd.Series,
    predicted_rul: float,
    risk_level: str,
    responsible_features: Iterable[str],
) -> str:
    """Décrit la RUL et les tendances dominantes de la mesure."""
    trends: list[str] = []
    for feature in responsible_features:
        if not feature.endswith("_slope") or pd.isna(row.get(feature)):
            continue
        value = float(row[feature])
        sensor = feature.removesuffix("_slope")
        if abs(value) > 0.01:
            direction = "augmente" if value > 0 else "diminue"
            trends.append(f"{sensor} {direction} ({value:+.3f}/cycle)")
    trend_text = "; ".join(trends[:3]) or "les tendances récentes des capteurs confirment cette estimation"
    return (
        f"La durée de vie restante est estimée à {predicted_rul:.1f} cycles "
        f"avec un risque {risk_level}. {trend_text}."
    )
