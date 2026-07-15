"""Service hybride combinant détection, règles et Machine Learning."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .explanations import build_explanation, severity_for
from .fault_catalog import FAULT_CATALOG
from .model_manager import FaultModelManager
from .rule_based_diagnoser import RuleBasedDiagnoser


class DiagnosisService:
    """Produit un diagnostic final clair pour chaque mesure."""

    OUTPUT_COLUMNS = [
        "timestamp", "scenario_id", "equipment_id", "equipment_type",
        "operating_state", "is_anomaly", "true_failure_type",
        "rule_based_fault", "rule_based_confidence", "ml_predicted_fault",
        "ml_confidence", "final_diagnosis", "final_confidence", "severity",
        "responsible_sensors", "diagnosis_explanation",
        "threshold_prediction", "isolation_forest_prediction", "anomaly_score",
    ]

    def __init__(
        self,
        rule_diagnoser: RuleBasedDiagnoser,
        model_manager: FaultModelManager,
        minimum_confidence: float = 0.65,
    ) -> None:
        self.rule_diagnoser = rule_diagnoser
        self.model_manager = model_manager
        self.minimum_confidence = float(minimum_confidence)

    def diagnose(self, data: pd.DataFrame, anomaly_results: pd.DataFrame) -> pd.DataFrame:
        """Fusionne les résultats index par index et retourne le format final."""
        ml_results = self.model_manager.predict(data)
        rows: list[dict[str, Any]] = []
        for index, measurement in data.iterrows():
            anomaly = anomaly_results.loc[index]
            threshold_detected = bool(anomaly.get("threshold_prediction", False))
            forest_detected = bool(anomaly.get("isolation_forest_prediction", False))
            detected = (
                threshold_detected and forest_detected
            ) or measurement["operating_state"] in {"degradation", "critical"}
            rule = self.rule_diagnoser.diagnose(measurement, detected)
            ml_fault = str(ml_results.loc[index, "ml_predicted_fault"])
            ml_confidence = float(ml_results.loc[index, "ml_confidence"])
            final_fault, final_confidence = self._combine(
                detected, rule.predicted_fault, rule.confidence,
                ml_fault, ml_confidence,
            )
            sensors = self._responsible_sensors(final_fault, rule.responsible_sensors)
            rows.append({
                "timestamp": measurement["timestamp"],
                "scenario_id": measurement.get("scenario_id", "unknown"),
                "equipment_id": measurement["equipment_id"],
                "equipment_type": measurement["equipment_type"],
                "operating_state": measurement["operating_state"],
                "is_anomaly": measurement.get("is_anomaly", False),
                "true_failure_type": measurement.get("failure_type", "unknown"),
                "rule_based_fault": rule.predicted_fault,
                "rule_based_confidence": round(rule.confidence, 4),
                "ml_predicted_fault": ml_fault,
                "ml_confidence": round(ml_confidence, 4),
                "final_diagnosis": final_fault,
                "final_confidence": round(final_confidence, 4),
                "severity": severity_for(measurement, final_fault, final_confidence),
                "responsible_sensors": ",".join(sensors),
                "diagnosis_explanation": build_explanation(final_fault, sensors, measurement),
                "threshold_prediction": bool(anomaly.get("threshold_prediction", False)),
                "isolation_forest_prediction": bool(anomaly.get("isolation_forest_prediction", False)),
                "anomaly_score": float(anomaly.get("anomaly_score", 0.0)),
            })
        return pd.DataFrame(rows, columns=self.OUTPUT_COLUMNS, index=data.index)

    def _combine(
        self, detected: bool, rule_fault: str, rule_confidence: float,
        ml_fault: str, ml_confidence: float,
    ) -> tuple[str, float]:
        if not detected:
            return "normal", max(0.8, ml_confidence if ml_fault == "normal" else 0.8)
        valid_rule = rule_fault not in {"normal", "unknown_fault"}
        valid_ml = ml_fault not in {"normal", "unknown_fault"}
        if valid_rule and rule_fault == ml_fault:
            return rule_fault, min(1.0, (rule_confidence + ml_confidence) / 2 + 0.1)
        choices = [(rule_confidence, rule_fault)] if valid_rule else []
        if valid_ml:
            choices.append((ml_confidence, ml_fault))
        if not choices:
            uncertainty = max(rule_confidence, 1.0 - ml_confidence)
            return "unknown_fault", min(0.64, uncertainty)
        confidence, fault = max(choices)
        if confidence < self.minimum_confidence:
            return "unknown_fault", confidence
        return fault, confidence

    @staticmethod
    def _responsible_sensors(fault: str, rule_sensors: tuple[str, ...]) -> tuple[str, ...]:
        if rule_sensors:
            return rule_sensors
        return FAULT_CATALOG.get(fault, FAULT_CATALOG["unknown_fault"]).sensors
