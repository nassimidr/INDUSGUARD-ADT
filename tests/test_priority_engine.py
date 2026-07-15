import pandas as pd

from indusguard.maintenance_planning.priority_engine import PriorityEngine


CONFIG = {
    "priority_weights": {"severity": .25, "rul": .25, "risk": .2, "cascade": .1, "safety": .08, "production_impact": .07, "confidence": .05},
    "severity_scores": {"low": .25, "high": .75, "critical": 1},
    "risk_scores": {"low": .15, "high": .75, "critical": 1},
    "priority_thresholds": {"medium": 25, "high": 50, "urgent": 75, "critical": 90},
}


def test_priority_is_bounded_and_increases_when_rul_falls() -> None:
    engine = PriorityEngine(CONFIG)
    common = {"severity": "high", "risk_level": "high", "diagnosed_fault": "bearing_wear", "diagnosis_confidence": .9, "prediction_confidence": .9}
    high_rul = engine.calculate(pd.Series({**common, "predicted_rul_steps": 80}), True)
    low_rul = engine.calculate(pd.Series({**common, "predicted_rul_steps": 10}), True)
    assert 0 <= high_rul.score <= 100
    assert low_rul.score > high_rul.score
    critical = engine.calculate(pd.Series({**common, "severity": "critical", "predicted_rul_steps": 40}), True)
    assert critical.priority == "critical"

