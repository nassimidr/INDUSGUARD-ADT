"""Baseline RUL fondée sur la santé et sa vitesse de diminution."""

from __future__ import annotations

import numpy as np
import pandas as pd


class HealthBaselineEstimator:
    """Extrapole la RUL depuis la santé, bornée par la durée observée."""

    def __init__(self) -> None:
        self.maximum_rul = 0.0

    def fit(self, data: pd.DataFrame, target: pd.Series) -> "HealthBaselineEstimator":
        if target.empty:
            raise ValueError("La baseline requiert des cibles RUL.")
        self.maximum_rul = float(target.max())
        return self

    def predict(self, data: pd.DataFrame) -> np.ndarray:
        if self.maximum_rul <= 0:
            raise RuntimeError("La baseline doit être entraînée.")
        health = pd.to_numeric(data["health_score"], errors="coerce").fillna(100).clip(0, 100)
        scaled = health.to_numpy() / 100.0 * self.maximum_rul
        if "health_score_slope" not in data:
            return np.clip(scaled, 0, self.maximum_rul)
        decline = -pd.to_numeric(data["health_score_slope"], errors="coerce").fillna(0).to_numpy()
        extrapolated = np.divide(
            health.to_numpy(), decline,
            out=scaled.copy(), where=decline > 0.15,
        )
        prediction = 0.65 * scaled + 0.35 * np.clip(extrapolated, 0, self.maximum_rul)
        return np.clip(prediction, 0, self.maximum_rul)

