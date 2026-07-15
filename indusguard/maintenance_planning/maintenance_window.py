"""Calcul de la fenêtre d'intervention avant la panne estimée."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class MaintenanceWindow:
    start: datetime
    deadline: datetime
    maximum_delay_hours: float


def calculate_window(
    row: pd.Series, config: dict[str, Any], reference_time: datetime
) -> MaintenanceWindow:
    """Applique une marge accrue lorsque la confiance est faible."""
    current = max(pd.Timestamp(row["timestamp"]).to_pydatetime(), reference_time)
    rul_hours = max(0.0, float(row["predicted_rul_hours"]))
    confidence = min(float(row["diagnosis_confidence"]), float(row["prediction_confidence"]))
    if str(row["severity"]) == "critical" or float(row["predicted_rul_steps"]) <= config["rul_thresholds"]["immediate"]:
        margin = config["safety_margin"]["critical"]
        start_delay = 0.0
    elif confidence < config["confidence_threshold"]:
        margin = config["safety_margin"]["low_confidence"]
        start_delay = min(2.0, rul_hours * 0.1)
    else:
        margin = config["safety_margin"]["default"]
        start_delay = min(8.0, rul_hours * 0.15)
    maximum_delay = max(0.0, rul_hours * (1.0 - margin))
    deadline = current + timedelta(hours=maximum_delay)
    start = min(current + timedelta(hours=start_delay), deadline)
    return MaintenanceWindow(start, deadline, round(maximum_delay, 3))
