"""Détection explicable fondée sur des seuils capteurs."""

from __future__ import annotations

from typing import Any

import pandas as pd


class ThresholdDetector:
    """Détecte les dépassements haut/bas propres à chaque équipement."""

    def __init__(self, thresholds: dict[str, dict[str, dict[str, float]]]) -> None:
        self.thresholds = thresholds

    def detect_row(self, row: pd.Series) -> tuple[bool, float, str, str]:
        """Retourne prédiction, sévérité, capteurs et explication d'une mesure."""
        equipment_type = str(row["equipment_type"])
        rules = self.thresholds.get(equipment_type, {})
        violations: list[tuple[str, float, float, str]] = []
        for sensor, rule in rules.items():
            value = row.get(sensor)
            if pd.isna(value):
                continue
            if "max" in rule and float(value) > float(rule["max"]):
                severity = min(1.0, (float(value) - rule["max"]) / max(abs(rule["max"]), 1.0) + 0.5)
                violations.append((sensor, severity, float(value), ">"))
            if "min" in rule and float(value) < float(rule["min"]):
                severity = min(1.0, (rule["min"] - float(value)) / max(abs(rule["min"]), 1.0) + 0.5)
                violations.append((sensor, severity, float(value), "<"))
        if not violations:
            return False, 0.0, "", "Aucun seuil dépassé"
        sensors = ",".join(item[0] for item in violations)
        explanation = "; ".join(
            f"{sensor}={value:.3f} {operator} seuil" for sensor, _, value, operator in violations
        )
        return True, max(item[1] for item in violations), sensors, explanation

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Applique les règles à toutes les lignes en conservant leur index."""
        results = [self.detect_row(row) for _, row in data.iterrows()]
        return pd.DataFrame(
            results,
            columns=["threshold_prediction", "threshold_severity", "detected_sensors", "anomaly_explanation"],
            index=data.index,
        )

