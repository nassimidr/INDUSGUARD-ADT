"""Métriques supervisées réservées à l'évaluation des détecteurs."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support


def _metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, Any]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        actual.astype(bool), predicted.astype(bool), average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[False, True]).ravel()
    return {
        "accuracy": float(accuracy_score(actual, predicted)), "precision": float(precision),
        "recall": float(recall), "f1": float(f1), "true_positives": int(tp),
        "false_positives": int(fp), "false_negatives": int(fn), "true_negatives": int(tn),
    }


def evaluate_predictions(
    data: pd.DataFrame, prediction_column: str, mask: pd.Series | None = None
) -> dict[str, Any]:
    """Calcule les métriques globales et par type d'équipement."""
    evaluated = data.loc[mask] if mask is not None else data
    result: dict[str, Any] = {"global": _metrics(evaluated["is_anomaly"], evaluated[prediction_column])}
    result["by_equipment"] = {
        equipment_type: _metrics(group["is_anomaly"], group[prediction_column])
        for equipment_type, group in evaluated.groupby("equipment_type")
    }
    return result
