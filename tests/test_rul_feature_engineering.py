import pandas as pd

from indusguard.rul_prediction.feature_engineering import create_temporal_features


def test_temporal_features_never_use_future_values() -> None:
    data = pd.DataFrame({
        "asset_run_id": ["run"] * 6, "cycle": range(6), "equipment_type": ["bearing"] * 6,
        "temperature": [10, 11, 12, 13, 14, 15], "health_score": [100, 95, 90, 85, 80, 75],
    })
    first = create_temporal_features(data, {"bearing": ["temperature", "health_score"]}, [3], 3)
    modified = data.copy(); modified.loc[5, "temperature"] = 10_000
    second = create_temporal_features(modified, {"bearing": ["temperature", "health_score"]}, [3], 3)
    pd.testing.assert_series_equal(
        first.loc[:4, "temperature_rolling_mean_3"],
        second.loc[:4, "temperature_rolling_mean_3"],
    )
    assert first.loc[2, "temperature_rolling_mean_3"] == 11

