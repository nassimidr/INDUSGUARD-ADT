"""Métriques multiclasses du diagnostic de panne."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.metrics import precision_recall_fscore_support


def _evaluate(actual: pd.Series, predicted: pd.Series) -> dict[str, Any]:
    precision, recall, f1_macro, _ = precision_recall_fscore_support(
        actual, predicted, average="macro", zero_division=0
    )
    _, _, f1_weighted, _ = precision_recall_fscore_support(
        actual, predicted, average="weighted", zero_division=0
    )
    labels = sorted(set(actual) | set(predicted))
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision_macro": float(precision), "recall_macro": float(recall),
        "f1_macro": float(f1_macro), "f1_weighted": float(f1_weighted),
        "unknown_count": int((predicted == "unknown_fault").sum()),
        "labels": labels,
        "confusion_matrix": confusion_matrix(actual, predicted, labels=labels).tolist(),
        "by_class": classification_report(actual, predicted, labels=labels, output_dict=True, zero_division=0),
    }


def evaluate_diagnosis(
    data: pd.DataFrame, prediction_column: str, mask: pd.Series | None = None
) -> dict[str, Any]:
    """Calcule les métriques globales et par équipement."""
    evaluated = data.loc[mask] if mask is not None else data
    return {
        "global": _evaluate(evaluated["true_failure_type"], evaluated[prediction_column]),
        "by_equipment": {
            kind: _evaluate(group["true_failure_type"], group[prediction_column])
            for kind, group in evaluated.groupby("equipment_type")
        },
    }
