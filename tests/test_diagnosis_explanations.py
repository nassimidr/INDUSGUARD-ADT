import pandas as pd

from indusguard.fault_diagnosis.explanations import build_explanation, severity_for


def test_explanation_uses_observed_values() -> None:
    row = pd.Series({"vibration": 6.2, "health_score": 42, "operating_state": "degradation"})
    explanation = build_explanation("bearing_wear", ["vibration", "health_score"], row)
    assert "vibration=6.20" in explanation
    assert "health_score=42.00" in explanation
    assert severity_for(row, "bearing_wear", 0.92) == "high"


def test_critical_state_produces_critical_severity() -> None:
    row = pd.Series({"operating_state": "critical", "health_score": 20})
    assert severity_for(row, "pump_blockage", 0.8) == "critical"

