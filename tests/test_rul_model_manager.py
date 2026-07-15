from pathlib import Path

import pandas as pd

from indusguard.rul_prediction import RULModelManager
from indusguard.rul_prediction.feature_engineering import create_temporal_features


def test_rul_manager_saves_loads_and_keeps_groups_disjoint(tmp_path: Path) -> None:
    rows = []
    for run in range(8):
        for cycle in range(12):
            rows.append({
                "asset_run_id": f"motor_run_{run}", "equipment_type": "motor",
                "cycle": cycle, "failure_occurred": int(cycle == 11),
                "rul_steps": 11 - cycle, "health_score": 100 - cycle * 9,
            })
    data = create_temporal_features(pd.DataFrame(rows), {"motor": ["health_score"]}, [2], 2)
    config = {
        "features": {"motor": ["health_score"]},
        "feature_engineering": {"rolling_windows": [2]},
        "model": {"test_size": 0.25, "random_seed": 42, "n_estimators": 10},
        "uncertainty": {"lower_percentile": 10, "upper_percentile": 90},
        "paths": {"models_directory": "models"},
    }
    manager = RULModelManager(config, tmp_path); manager.train(data)
    assert manager.train_runs["motor"].isdisjoint(manager.test_runs["motor"])
    assert (tmp_path / "models" / "motor_rul_model.joblib").is_file()
    loaded = RULModelManager(config, tmp_path); loaded.load()
    prediction = loaded.predict(data)
    assert (prediction["predicted_rul_steps"] >= 0).all()

