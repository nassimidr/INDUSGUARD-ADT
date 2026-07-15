import numpy as np
import pandas as pd

from indusguard.fault_diagnosis import MLFaultClassifier


def test_ml_classifier_trains_and_returns_confidence() -> None:
    rng = np.random.default_rng(42)
    data = pd.DataFrame({
        "temperature": np.r_[rng.normal(45, 1, 40), rng.normal(75, 1, 40)],
        "current": np.r_[rng.normal(15, 1, 40), rng.normal(28, 1, 40)],
    })
    target = pd.Series(["normal"] * 40 + ["motor_overheating"] * 40)
    model = MLFaultClassifier(["temperature", "current"], {"n_estimators": 30, "random_seed": 42})
    model.fit(data, target)
    prediction, confidence = model.predict(pd.DataFrame({"temperature": [80], "current": [30]}))
    assert prediction[0] == "motor_overheating"
    assert 0.5 <= confidence[0] <= 1.0

