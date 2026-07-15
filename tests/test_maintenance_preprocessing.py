import pandas as pd

from indusguard.maintenance_planning.preprocessing import merge_maintenance_sources


def test_merge_selects_latest_incomplete_asset_without_duplicates() -> None:
    diagnosis = pd.DataFrame([{"equipment_type": "bearing", "final_diagnosis": "bearing_wear", "final_confidence": 0.9, "severity": "medium", "responsible_sensors": "vibration", "diagnosis_explanation": "wear"}])
    rul = pd.DataFrame([
        {"timestamp": "2026-01-01", "asset_run_id": "b1", "cycle": 1, "equipment_id": "B1", "equipment_type": "bearing", "true_failure_type": "bearing_wear", "true_rul_steps": float("nan"), "predicted_rul_steps": 60, "predicted_rul_hours": 30, "rul_lower_bound": 50, "rul_upper_bound": 70, "risk_level": "low", "prediction_confidence": 0.8},
        {"timestamp": "2026-01-02", "asset_run_id": "b1", "cycle": 2, "equipment_id": "B1", "equipment_type": "bearing", "true_failure_type": "bearing_wear", "true_rul_steps": float("nan"), "predicted_rul_steps": 50, "predicted_rul_hours": 25, "rul_lower_bound": 45, "rul_upper_bound": 55, "risk_level": "medium", "prediction_confidence": 0.85},
    ])
    anomalies = pd.DataFrame([{"equipment_type": "bearing", "threshold_prediction": True, "isolation_forest_prediction": True, "anomaly_score": 0.3}])
    merged = merge_maintenance_sources(diagnosis, rul, anomalies)
    assert len(merged) == 1
    assert merged.iloc[0]["predicted_rul_steps"] == 50
    assert merged.iloc[0]["diagnosed_fault"] == "bearing_wear"

