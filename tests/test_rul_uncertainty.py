import numpy as np

from indusguard.rul_prediction.uncertainty import prediction_interval, technical_confidence


def test_interval_contains_prediction_and_confidence_is_bounded() -> None:
    trees = np.array([[8, 18], [10, 20], [12, 22]], dtype=float)
    prediction, lower, upper = prediction_interval(trees, 10, 90)
    assert np.all(lower <= prediction)
    assert np.all(prediction <= upper)
    confidence = technical_confidence(prediction, lower, upper, np.array([20, 5]), np.zeros(2))
    assert np.all((confidence >= 0) & (confidence <= 1))

