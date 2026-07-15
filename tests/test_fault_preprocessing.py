import pandas as pd
import pytest

from indusguard.fault_diagnosis.preprocessing import select_features, split_equipment_data


def sample() -> pd.DataFrame:
    return pd.DataFrame({
        "equipment_type": ["motor"] * 12,
        "temperature": range(40, 52), "current": range(10, 22),
        "failure_type": ["normal"] * 6 + ["motor_overload"] * 6,
        "is_anomaly": [False] * 6 + [True] * 6,
    })


def test_feature_selection_and_stratified_split() -> None:
    selected = select_features(sample(), "motor", ["temperature", "current"])
    assert list(selected.columns) == ["temperature", "current"]
    split = split_equipment_data(sample(), "motor", selected.columns, 0.25, 42)
    assert set(split.y_test) == {"normal", "motor_overload"}


def test_target_leakage_is_rejected() -> None:
    with pytest.raises(ValueError, match="Fuite"):
        select_features(sample(), "motor", ["temperature", "failure_type"])

