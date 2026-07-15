import pandas as pd
import pytest

from indusguard.anomaly_detection.preprocessing import equipment_features


def test_preprocessing_selects_features_without_target() -> None:
    data = pd.DataFrame({
        "equipment_type": ["motor"], "temperature": [50], "vibration": [2],
        "rpm": [1500], "current": [18], "load": [55], "is_anomaly": [False],
    })
    features = equipment_features(data, "motor")
    assert list(features.columns) == ["temperature", "vibration", "rpm", "current", "load"]
    assert "is_anomaly" not in features


def test_preprocessing_rejects_target_feature() -> None:
    data = pd.DataFrame({"equipment_type": ["motor"], "is_anomaly": [False]})
    with pytest.raises(ValueError, match="cible"):
        equipment_features(data, "motor", {"motor": ["is_anomaly"]})

