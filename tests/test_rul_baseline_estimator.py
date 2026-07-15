import pandas as pd

from indusguard.rul_prediction import HealthBaselineEstimator


def test_health_baseline_decreases_with_health() -> None:
    data = pd.DataFrame({"health_score": [100, 50, 10], "health_score_slope": [0, -1, -2]})
    model = HealthBaselineEstimator().fit(data, pd.Series([100, 50, 0]))
    prediction = model.predict(data)
    assert prediction[0] > prediction[1] > prediction[2] >= 0

