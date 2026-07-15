import pandas as pd
import pytest

from indusguard.rul_prediction.preprocessing import split_by_trajectory, validate_feature_columns


def test_group_split_has_no_shared_trajectory() -> None:
    rows = []
    for run in range(8):
        for cycle in range(5):
            rows.append({"asset_run_id": f"motor_{run}", "equipment_type": "motor", "failure_occurred": int(cycle == 4), "cycle": cycle, "rul_steps": 4 - cycle})
    split = split_by_trajectory(pd.DataFrame(rows), "motor", 0.25, 42)
    assert split.train_runs.isdisjoint(split.test_runs)


def test_rul_targets_are_forbidden_features() -> None:
    with pytest.raises(ValueError, match="Fuite"):
        validate_feature_columns(["temperature", "rul_steps", "failure_occurred"])

