from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from indusguard.anomaly_detection import IsolationForestDetector


def sample_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({"temperature": rng.normal(40, 1, 120), "vibration": rng.normal(2, 0.1, 120)})


def test_isolation_forest_trains_and_detects_outlier() -> None:
    normal = sample_data()
    detector = IsolationForestDetector(["temperature", "vibration"], contamination=0.05, n_estimators=50)
    detector.fit(normal)
    test = pd.DataFrame({"temperature": [40, 100], "vibration": [2, 15]})
    predictions, scores = detector.predict(test)
    assert predictions.tolist() == [False, True]
    assert scores[1] > scores[0]


def test_isolation_forest_save_and_load(tmp_path: Path) -> None:
    detector = IsolationForestDetector(["temperature", "vibration"], n_estimators=30).fit(sample_data())
    path = detector.save(tmp_path / "model.joblib")
    loaded = IsolationForestDetector.load(path)
    first, _ = detector.predict(sample_data().head())
    second, _ = loaded.predict(sample_data().head())
    assert np.array_equal(first, second)


def test_isolation_forest_rejects_target() -> None:
    with pytest.raises(ValueError, match="cible"):
        IsolationForestDetector(["temperature", "is_anomaly"])
