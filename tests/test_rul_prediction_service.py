import pandas as pd

from indusguard.rul_prediction.prediction_service import RULPredictionService


class StubManager:
    models = {"bearing": object()}

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "predicted_rul_steps": [8.0], "rul_lower_bound": [5.0],
            "rul_upper_bound": [12.0], "baseline_rul_steps": [10.0],
        }, index=data.index)

    def top_features(self, equipment_type: str, count: int = 3) -> tuple[str, ...]:
        return ("vibration_slope", "health_score_slope")


def test_prediction_service_creates_complete_non_negative_output() -> None:
    data = pd.DataFrame([{
        "timestamp": "2026-01-01", "asset_run_id": "bearing_current", "cycle": 30,
        "equipment_id": "B", "equipment_type": "bearing", "failure_type": "bearing_wear",
        "rul_steps": float("nan"), "temperature": 55, "vibration": 6, "rpm": 1450,
        "health_score": 45, "vibration_slope": 0.2, "health_score_slope": -0.8,
    }])
    config = {
        "simulation": {"interval_hours": 0.5},
        "features": {"bearing": ["temperature", "vibration", "rpm", "health_score"]},
        "risk_thresholds": {"critical_max": 10, "high_max": 25, "medium_max": 50},
    }
    result = RULPredictionService(StubManager(), config).predict(data)
    assert list(result.columns) == RULPredictionService.OUTPUT_COLUMNS
    assert result.iloc[0]["predicted_rul_steps"] == 8
    assert result.iloc[0]["risk_level"] == "critical"
    assert result.iloc[0]["rul_lower_bound"] <= 8 <= result.iloc[0]["rul_upper_bound"]
    assert pd.isna(result.iloc[0]["prediction_error"])
    assert result.iloc[0]["rul_explanation"]
