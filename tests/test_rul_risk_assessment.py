from indusguard.rul_prediction.risk_assessment import assess_risk


THRESHOLDS = {"critical_max": 10, "high_max": 25, "medium_max": 50}


def test_risk_levels_follow_rul_thresholds() -> None:
    assert assess_risk(5, THRESHOLDS) == "critical"
    assert assess_risk(18, THRESHOLDS) == "high"
    assert assess_risk(40, THRESHOLDS) == "medium"
    assert assess_risk(80, THRESHOLDS) == "low"

