import numpy as np
import pandas as pd

from indusguard.rul_prediction import RULRegressor


def test_rul_regressor_trains_and_never_predicts_negative() -> None:
    data = pd.DataFrame({"health_score": np.linspace(100, 0, 80), "vibration_slope": np.linspace(0, 1, 80)})
    target = pd.Series(np.linspace(79, 0, 80))
    model = RULRegressor(data.columns, {"n_estimators": 20, "random_seed": 42}).fit(data, target)
    prediction = model.predict(data)
    assert (prediction >= 0).all()
    assert prediction[0] > prediction[-1]

