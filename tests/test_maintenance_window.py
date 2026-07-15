from datetime import datetime

import pandas as pd

from indusguard.maintenance_planning.maintenance_window import calculate_window


CONFIG = {"rul_thresholds": {"immediate": 5}, "safety_margin": {"critical": .55, "low_confidence": .4, "default": .25}, "confidence_threshold": .6}


def test_window_deadline_precedes_estimated_failure() -> None:
    now = datetime(2026, 1, 1, 8)
    row = pd.Series({"timestamp": now, "predicted_rul_steps": 20, "predicted_rul_hours": 10, "severity": "high", "diagnosis_confidence": .9, "prediction_confidence": .9})
    window = calculate_window(row, CONFIG, now)
    assert window.start <= window.deadline
    assert window.maximum_delay_hours < row["predicted_rul_hours"]

