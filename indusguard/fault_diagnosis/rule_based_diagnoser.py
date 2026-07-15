"""Diagnostic métier fondé sur des symptômes configurables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .fault_catalog import ALL_FAULT_TYPES


@dataclass(frozen=True)
class RuleDiagnosis:
    """Résultat explicable d'un diagnostic par règles."""

    predicted_fault: str
    confidence: float
    responsible_sensors: tuple[str, ...]


class RuleBasedDiagnoser:
    """Compare une mesure à des règles pondérées définies en YAML."""

    def __init__(self, rules: dict[str, list[dict[str, Any]]], minimum_confidence: float = 0.65) -> None:
        self.rules = rules
        self.minimum_confidence = float(minimum_confidence)
        configured = {rule["fault"] for group in rules.values() for rule in group}
        unknown = configured - ALL_FAULT_TYPES
        if unknown:
            raise ValueError(f"Pannes inconnues dans les règles : {sorted(unknown)}")

    def diagnose(self, row: pd.Series, anomaly_detected: bool) -> RuleDiagnosis:
        """Retourne la meilleure règle ou normal/unknown_fault."""
        if not anomaly_detected and row.get("operating_state", "normal") == "normal":
            return RuleDiagnosis("normal", 1.0, ())
        candidates: list[tuple[float, str, tuple[str, ...]]] = []
        for rule in self.rules.get(str(row["equipment_type"]), []):
            matched: list[str] = []
            matched_weight = 0.0
            total_weight = 0.0
            for condition in rule["conditions"]:
                weight = float(condition.get("weight", 1.0))
                total_weight += weight
                value = row.get(condition["sensor"])
                if self._matches(value, condition):
                    matched.append(condition["sensor"])
                    matched_weight += weight
            if len(matched) >= int(rule.get("min_matches", 2)):
                ratio = matched_weight / max(total_weight, 1.0)
                confidence = min(0.98, 0.5 + 0.48 * ratio)
                candidates.append((confidence, rule["fault"], tuple(dict.fromkeys(matched))))
        if not candidates:
            return RuleDiagnosis("unknown_fault", 0.5, ())
        confidence, fault, sensors = max(candidates, key=lambda item: item[0])
        if confidence < self.minimum_confidence:
            return RuleDiagnosis("unknown_fault", confidence, sensors)
        return RuleDiagnosis(fault, confidence, sensors)

    @staticmethod
    def _matches(value: Any, condition: dict[str, Any]) -> bool:
        if pd.isna(value):
            return False
        numeric = float(value)
        return (
            ("min" not in condition or numeric >= float(condition["min"]))
            and ("max" not in condition or numeric <= float(condition["max"]))
        )

