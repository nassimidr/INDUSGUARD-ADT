from pathlib import Path

import pandas as pd
import pytest

from indusguard.rul_prediction import RULTrajectoryGenerator


@pytest.fixture(scope="module")
def rul_data() -> pd.DataFrame:
    config = Path(__file__).parents[1] / "configs" / "rul_prediction.yaml"
    return RULTrajectoryGenerator(config).generate_dataset()


def test_complete_trajectories_decrease_to_zero(rul_data: pd.DataFrame) -> None:
    assert len(rul_data) >= 10_000
    for _, group in rul_data.groupby("asset_run_id"):
        if group["failure_occurred"].max() == 1:
            assert group.iloc[0]["rul_steps"] > group.iloc[-1]["rul_steps"]
            assert group.iloc[-1]["rul_steps"] == 0
            assert group["rul_steps"].diff().dropna().eq(-1).all()


def test_generator_is_reproducible(rul_data: pd.DataFrame) -> None:
    config = Path(__file__).parents[1] / "configs" / "rul_prediction.yaml"
    second = RULTrajectoryGenerator(config).generate_dataset()
    pd.testing.assert_frame_equal(rul_data.select_dtypes("number"), second.select_dtypes("number"))


def test_missing_phase_three_faults_and_sensor_degradation(rul_data: pd.DataFrame) -> None:
    missing_before = {"motor_electrical_fault", "conveyor_speed_fault", "pump_leakage", "pump_bearing_fault"}
    assert missing_before.issubset(set(rul_data["failure_type"]))
    electrical = rul_data[rul_data["failure_type"] == "motor_electrical_fault"].groupby("asset_run_id").first()
    electrical_end = rul_data[rul_data["failure_type"] == "motor_electrical_fault"].groupby("asset_run_id").last()
    assert (electrical_end["current"] > electrical["current"]).all()

