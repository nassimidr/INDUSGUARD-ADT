import pandas as pd

from indusguard.maintenance_planning.maintenance_catalog import MaintenanceCatalog
from indusguard.maintenance_planning.recommendation_engine import RecommendationEngine


def catalog() -> MaintenanceCatalog:
    base = {"secondary_actions": [], "skills": [], "required_parts": [], "optional_parts": [], "duration_hours": 1, "inspection_required": False}
    return MaintenanceCatalog({
        "normal": {**base, "strategy": "monitor", "action": "Monitor", "shutdown_required": False},
        "unknown_fault": {**base, "strategy": "inspect", "action": "Inspect", "shutdown_required": False},
        "cascade_failure": {**base, "strategy": "emergency_shutdown", "action": "Stop", "shutdown_required": True},
        "bearing_wear": {**base, "strategy": "preventive_maintenance", "action": "Lubricate", "shutdown_required": True},
        "bearing_severe_damage": {**base, "strategy": "component_replacement", "action": "Replace", "shutdown_required": True},
    })


def row(fault: str, severity: str, rul: float, confidence: float = 0.9, risk: str = "low") -> pd.Series:
    return pd.Series({"diagnosed_fault": fault, "severity": severity, "predicted_rul_steps": rul, "diagnosis_confidence": confidence, "prediction_confidence": confidence, "risk_level": risk})


def test_normal_light_severe_cascade_and_low_confidence() -> None:
    engine = RecommendationEngine(catalog(), 0.6)
    assert engine.recommend(row("normal", "none", 100)).strategy == "monitor"
    assert engine.recommend(row("bearing_wear", "low", 70)).strategy == "inspect"
    assert engine.recommend(row("bearing_severe_damage", "high", 8)).strategy == "component_replacement"
    assert engine.recommend(row("cascade_failure", "critical", 30)).strategy == "emergency_shutdown"
    assert engine.recommend(row("bearing_wear", "medium", 40, 0.4)).strategy == "inspect"

