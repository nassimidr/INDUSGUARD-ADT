import json
from pathlib import Path

import pandas as pd
import yaml

from indusguard.maintenance_planning.evaluator import maintenance_metrics, validate_plan
from indusguard.maintenance_planning.planning_service import MaintenancePlanningService


def test_planning_service_creates_csv_and_metrics(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    config = yaml.safe_load((root / "configs" / "maintenance_planning.yaml").read_text(encoding="utf-8"))
    resources = yaml.safe_load((root / "configs" / "maintenance_resources.yaml").read_text(encoding="utf-8"))
    equipment = pd.DataFrame([{
        "timestamp": "2026-01-01T08:00:00", "equipment_id": "B1", "equipment_type": "bearing",
        "diagnosed_fault": "bearing_wear", "diagnosis_confidence": .9, "severity": "medium",
        "predicted_rul_steps": 40, "predicted_rul_hours": 20, "rul_lower_bound": 35,
        "rul_upper_bound": 45, "prediction_confidence": .85, "risk_level": "medium",
        "diagnosis_source": "test",
    }])
    service = MaintenancePlanningService(config, resources)
    recommendations, orders, schedule = service.plan(equipment)
    validate_plan(recommendations, orders, schedule)
    for name, frame in [("recommendations.csv", recommendations), ("orders.csv", orders), ("schedule.csv", schedule)]:
        frame.to_csv(tmp_path / name, index=False)
        assert (tmp_path / name).is_file()
    metrics = maintenance_metrics(recommendations, orders, schedule, service.scheduler.conflicts_detected, service.scheduler.conflicts_resolved)
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    assert metrics["recommendation_count"] == 1
    assert (tmp_path / "metrics.json").is_file()
