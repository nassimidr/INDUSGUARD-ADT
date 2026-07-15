"""Incertitude empirique issue des arbres du Random Forest."""

from __future__ import annotations

import numpy as np


def prediction_interval(
    tree_predictions: np.ndarray, lower_percentile: float, upper_percentile: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Retourne moyenne et percentiles des prédictions des arbres."""
    if tree_predictions.ndim != 2 or tree_predictions.shape[0] == 0:
        raise ValueError("Les prédictions doivent avoir la forme arbres × mesures.")
    prediction = np.clip(tree_predictions.mean(axis=0), 0, None)
    lower = np.clip(np.percentile(tree_predictions, lower_percentile, axis=0), 0, None)
    upper = np.clip(np.percentile(tree_predictions, upper_percentile, axis=0), 0, None)
    lower = np.minimum(lower, prediction)
    upper = np.maximum(upper, prediction)
    return prediction, lower, upper


def technical_confidence(
    prediction: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    history_cycles: np.ndarray,
    missing_fraction: np.ndarray,
    history_target: int = 20,
) -> np.ndarray:
    """Estime une confiance technique non calibrée entre 0 et 1."""
    relative_width = (upper - lower) / np.maximum(prediction + 10.0, 10.0)
    interval_score = np.clip(1.0 - relative_width, 0.0, 1.0)
    history_score = np.clip(history_cycles / max(history_target, 1), 0.2, 1.0)
    completeness = np.clip(1.0 - missing_fraction, 0.2, 1.0)
    return np.clip(interval_score * history_score * completeness, 0.0, 1.0)

