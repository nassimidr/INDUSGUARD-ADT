"""Service de prédiction RUL, confiance, risque et explication."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .explanations import build_rul_explanation
from .model_manager import RULModelManager
from .risk_assessment import assess_risk
from .uncertainty import technical_confidence


class RULPredictionService:
    """Produit le format de sortie stable de la phase 4."""

    OUTPUT_COLUMNS = [
        "timestamp", "asset_run_id", "cycle", "equipment_id", "equipment_type",
        "true_failure_type", "true_rul_steps", "predicted_rul_steps",
        "predicted_rul_hours", "rul_lower_bound", "rul_upper_bound",
        "prediction_error", "risk_level", "prediction_confidence",
        "responsible_features", "rul_explanation",
    ]

    def __init__(self, manager: RULModelManager, config: dict[str, Any]) -> None:
        self.manager = manager
        self.config = config

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prédit toutes les lignes, y compris les trajectoires incomplètes."""
        raw = self.manager.predict(data)
        rows: list[dict[str, Any]] = []
        interval_hours = float(self.config["simulation"]["interval_hours"])
        top_features = {
            kind: self.manager.top_features(kind) for kind in self.manager.models
        }
        for index, measurement in data.iterrows():
            predicted = max(0.0, float(raw.loc[index, "predicted_rul_steps"]))
            lower = max(0.0, float(raw.loc[index, "rul_lower_bound"]))
            upper = max(predicted, float(raw.loc[index, "rul_upper_bound"]))
            history = np.array([float(measurement["cycle"]) + 1.0])
            base_features = self.config["features"][measurement["equipment_type"]]
            missing = np.array([float(measurement[base_features].isna().mean())])
            confidence = technical_confidence(
                np.array([predicted]), np.array([lower]), np.array([upper]),
                history, missing,
            )[0]
            risk = assess_risk(predicted, self.config["risk_thresholds"])
            important = top_features[str(measurement["equipment_type"])]
            true_rul = measurement.get("rul_steps", np.nan)
            error = predicted - float(true_rul) if not pd.isna(true_rul) else np.nan
            rows.append({
                "timestamp": measurement["timestamp"],
                "asset_run_id": measurement["asset_run_id"],
                "cycle": measurement["cycle"],
                "equipment_id": measurement["equipment_id"],
                "equipment_type": measurement["equipment_type"],
                "true_failure_type": measurement["failure_type"],
                "true_rul_steps": true_rul,
                "predicted_rul_steps": round(predicted, 3),
                "predicted_rul_hours": round(predicted * interval_hours, 3),
                "rul_lower_bound": round(lower, 3),
                "rul_upper_bound": round(upper, 3),
                "prediction_error": round(error, 3) if not pd.isna(error) else np.nan,
                "risk_level": risk,
                "prediction_confidence": round(float(confidence), 4),
                "responsible_features": ",".join(important),
                "rul_explanation": build_rul_explanation(measurement, predicted, risk, important),
            })
        return pd.DataFrame(rows, columns=self.OUTPUT_COLUMNS, index=data.index)
