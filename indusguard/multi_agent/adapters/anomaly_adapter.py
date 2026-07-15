"""Adaptateur Phase 2; modèles chargés une seule fois."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from indusguard.anomaly_detection.model_manager import ModelManager
from indusguard.anomaly_detection.threshold_detector import ThresholdDetector


class AnomalyAdapter:
    def __init__(self, root: str | Path) -> None:
        self.root=Path(root); self.config=yaml.safe_load((self.root/"configs/anomaly_detection.yaml").read_text(encoding="utf-8"))
        self.threshold=ThresholdDetector(self.config["thresholds"])
        self.models=ModelManager(self.config,self.root); self.models.load()

    def analyze(self, measurement: dict[str, Any]) -> dict[str, Any]:
        frame=pd.DataFrame([measurement]); threshold=self.threshold.predict(frame).iloc[0]
        kind=str(measurement["equipment_type"])
        predictions,scores=self.models.models[kind].predict(frame)
        detected=bool(threshold["threshold_prediction"] or predictions[0])
        return {
            "is_anomaly": detected,
            "threshold_prediction": bool(threshold["threshold_prediction"]),
            "threshold_severity": float(threshold["threshold_severity"]),
            "isolation_forest_prediction": bool(predictions[0]),
            "anomaly_score": float(scores[0]),
            "detected_sensors": str(threshold["detected_sensors"]),
            "anomaly_explanation": str(threshold["anomaly_explanation"]),
        }
