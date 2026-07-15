"""Métriques de régression RUL globales et segmentées."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, float | int]:
    """Calcule les métriques demandées sans masquer les mauvaises valeurs."""
    valid = actual.notna() & predicted.notna()
    y_true = actual[valid].astype(float)
    y_pred = predicted[valid].astype(float)
    if y_true.empty:
        return {"rows": 0}
    error = (y_pred - y_true).abs()
    positive = y_true > 0
    mape = float((error[positive] / y_true[positive]).mean() * 100) if positive.any() else 0.0
    return {
        "rows": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)),
        "median_absolute_error": float(error.median()),
        "mape_positive_pct": mape,
        "within_5_cycles_pct": float((error <= 5).mean() * 100),
        "within_10_cycles_pct": float((error <= 10).mean() * 100),
        "within_20_cycles_pct": float((error <= 20).mean() * 100),
    }


def evaluate_rul(data: pd.DataFrame, prediction_column: str) -> dict[str, Any]:
    """Évalue globalement, par équipement, panne et niveau de RUL."""
    evaluated = data[data["rul_steps"].notna()].copy()
    evaluated["rul_level"] = pd.cut(
        evaluated["rul_steps"], [-1, 10, 25, 50, np.inf],
        labels=["0-10", "11-25", "26-50", ">50"],
    )
    return {
        "global": regression_metrics(evaluated["rul_steps"], evaluated[prediction_column]),
        "by_equipment": {
            name: regression_metrics(group["rul_steps"], group[prediction_column])
            for name, group in evaluated.groupby("equipment_type")
        },
        "by_failure_type": {
            name: regression_metrics(group["rul_steps"], group[prediction_column])
            for name, group in evaluated.groupby("failure_type")
        },
        "by_rul_level": {
            str(name): regression_metrics(group["rul_steps"], group[prediction_column])
            for name, group in evaluated.groupby("rul_level", observed=True)
        },
    }

