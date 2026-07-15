import pandas as pd

from indusguard.anomaly_detection import ThresholdDetector


def test_threshold_detector_finds_obvious_anomaly() -> None:
    data = pd.DataFrame([
        {"equipment_type": "pump", "temperature": 90, "flow_rate": 20},
        {"equipment_type": "pump", "temperature": 45, "flow_rate": 120},
    ])
    detector = ThresholdDetector({"pump": {"temperature": {"max": 60}, "flow_rate": {"min": 80}}})
    result = detector.predict(data)
    assert bool(result.iloc[0]["threshold_prediction"])
    assert not bool(result.iloc[1]["threshold_prediction"])
    assert "temperature" in result.iloc[0]["detected_sensors"]
    assert result.iloc[0]["threshold_severity"] > 0

