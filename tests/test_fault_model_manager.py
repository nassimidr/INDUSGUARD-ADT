from pathlib import Path

import pandas as pd

from indusguard.fault_diagnosis import FaultModelManager


def test_manager_saves_and_loads_model(tmp_path: Path) -> None:
    data = pd.DataFrame({
        "equipment_type": ["motor"] * 20,
        "temperature": list(range(40, 50)) + list(range(70, 80)),
        "current": [15] * 10 + [28] * 10,
        "failure_type": ["normal"] * 10 + ["motor_overheating"] * 10,
    })
    config = {
        "features": {"motor": ["temperature", "current"]},
        "model": {"test_size": 0.25, "random_seed": 42, "n_estimators": 20},
        "paths": {"models_directory": "models"},
    }
    manager = FaultModelManager(config, tmp_path); manager.train(data)
    assert (tmp_path / "models" / "motor_fault_classifier.joblib").is_file()
    loaded = FaultModelManager(config, tmp_path); loaded.load()
    assert len(loaded.predict(data)) == len(data)

