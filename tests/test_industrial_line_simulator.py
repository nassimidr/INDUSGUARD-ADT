from pathlib import Path

import pandas as pd
import pytest

from indusguard.digital_twin import IndustrialLineSimulator


@pytest.fixture(scope="module")
def line_data() -> pd.DataFrame:
    simulator = IndustrialLineSimulator(Path(__file__).parents[1] / "configs" / "industrial_line.yaml")
    return simulator.generate_dataset()


def test_line_dataset_shape_and_columns(line_data: pd.DataFrame) -> None:
    assert len(line_data) == 2000
    assert list(line_data.columns) == IndustrialLineSimulator.COLUMNS
    assert set(line_data["equipment_type"]) == {"motor", "bearing", "conveyor", "pump"}


def test_line_has_normal_and_anomalous_periods(line_data: pd.DataFrame) -> None:
    assert set(line_data["is_anomaly"]) == {False, True}
    assert {"normal", "degradation", "critical"}.issubset(set(line_data["operating_state"]))
    assert (line_data.loc[~line_data["is_anomaly"], "failure_type"] == "normal").all()
    assert line_data.loc[line_data["is_anomaly"], "failure_type"].nunique() >= 8


def test_line_is_numerically_reproducible(line_data: pd.DataFrame) -> None:
    simulator = IndustrialLineSimulator(Path(__file__).parents[1] / "configs" / "industrial_line.yaml")
    other = simulator.generate_dataset()
    pd.testing.assert_frame_equal(line_data, other)


def test_dependencies_are_visible(line_data: pd.DataFrame) -> None:
    motors = line_data[line_data["equipment_type"] == "motor"]
    normal_current = motors[motors["scenario_id"] == "scenario_1_normal"]["current"].mean()
    overload_current = motors[motors["scenario_id"] == "scenario_3_overload"]["current"].tail(20).mean()
    assert overload_current > normal_current
    pumps = line_data[line_data["equipment_type"] == "pump"]
    normal_flow = pumps[pumps["scenario_id"] == "scenario_1_normal"]["flow_rate"].mean()
    anomaly_flow = pumps[pumps["scenario_id"] == "scenario_4_pump"]["flow_rate"].tail(20).mean()
    assert anomaly_flow < normal_flow
