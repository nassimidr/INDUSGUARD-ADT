import pandas as pd

from indusguard.fault_diagnosis import DiagnosisService, RuleBasedDiagnoser


class StubManager:
    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "ml_predicted_fault": ["motor_overload", "normal"],
            "ml_confidence": [0.9, 0.95],
        }, index=data.index)


def test_hybrid_service_output_structure() -> None:
    rules = {"motor": [{"fault": "motor_overload", "min_matches": 2, "conditions": [
        {"sensor": "load", "min": 80}, {"sensor": "current", "min": 24},
    ]}]}
    data = pd.DataFrame([
        {"timestamp": "2026-01-01", "scenario_id": "s", "equipment_id": "M", "equipment_type": "motor", "operating_state": "degradation", "is_anomaly": True, "failure_type": "motor_overload", "load": 90, "current": 28, "health_score": 60},
        {"timestamp": "2026-01-02", "scenario_id": "s", "equipment_id": "M", "equipment_type": "motor", "operating_state": "normal", "is_anomaly": False, "failure_type": "normal", "load": 55, "current": 18, "health_score": 100},
    ])
    anomaly = pd.DataFrame({
        "threshold_prediction": [True, False], "isolation_forest_prediction": [True, False], "anomaly_score": [0.4, -0.2],
    })
    service = DiagnosisService(RuleBasedDiagnoser(rules), StubManager())
    result = service.diagnose(data, anomaly)
    assert list(result.columns) == DiagnosisService.OUTPUT_COLUMNS
    assert result.iloc[0]["final_diagnosis"] == "motor_overload"
    assert result.iloc[0]["severity"] in {"medium", "high"}
    assert result.iloc[1]["final_diagnosis"] == "normal"
    assert result.iloc[0]["diagnosis_explanation"]
