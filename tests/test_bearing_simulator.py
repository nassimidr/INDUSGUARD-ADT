"""Tests du simulateur de roulement."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from indusguard.digital_twin import BearingSimulator


@pytest.fixture()
def simulator() -> BearingSimulator:
    """Crée un simulateur utilisant la configuration du projet."""
    config = Path(__file__).parents[1] / "configs" / "simulation.yaml"
    return BearingSimulator(config)


@pytest.fixture()
def dataset(simulator: BearingSimulator) -> pd.DataFrame:
    """Génère un jeu de données commun aux tests."""
    return simulator.generate_dataset()


def test_total_rows(dataset: pd.DataFrame) -> None:
    assert len(dataset) == 200


def test_exact_columns(dataset: pd.DataFrame) -> None:
    assert list(dataset.columns) == BearingSimulator.COLUMNS


def test_no_missing_values(dataset: pd.DataFrame) -> None:
    assert not dataset.isna().any().any()


def test_health_score_bounds(dataset: pd.DataFrame) -> None:
    assert dataset["health_score"].between(0, 100).all()


def test_load_bounds(dataset: pd.DataFrame) -> None:
    assert dataset["load_pct"].between(0, 100).all()


def test_vibrations_are_positive(dataset: pd.DataFrame) -> None:
    assert (dataset["vibration_rms_mm_s"] > 0).all()


def test_temperatures_are_positive(dataset: pd.DataFrame) -> None:
    assert (dataset["temperature_c"] > 0).all()


def test_timestamps_are_sorted(dataset: pd.DataFrame) -> None:
    assert dataset["timestamp"].is_monotonic_increasing


def test_timestamps_are_unique(dataset: pd.DataFrame) -> None:
    assert dataset["timestamp"].is_unique


def test_states_are_valid(dataset: pd.DataFrame) -> None:
    assert set(dataset["state"]) == {"normal", "degradation", "critique"}


@pytest.mark.parametrize(
    ("state", "expected"),
    [("normal", 100), ("degradation", 60), ("critique", 40)],
)
def test_period_measurement_count(
    dataset: pd.DataFrame, state: str, expected: int
) -> None:
    assert (dataset["state"] == state).sum() == expected


def test_fault_inactive_during_normal_period(dataset: pd.DataFrame) -> None:
    assert not dataset.loc[dataset["state"] == "normal", "fault_active"].any()


def test_fault_active_during_other_periods(dataset: pd.DataFrame) -> None:
    other = dataset["state"].isin(["degradation", "critique"])
    assert dataset.loc[other, "fault_active"].all()


def test_fault_type_matches_fault_status(dataset: pd.DataFrame) -> None:
    assert (dataset.loc[~dataset["fault_active"], "fault_type"] == "none").all()
    assert (
        dataset.loc[dataset["fault_active"], "fault_type"] == "bearing_wear"
    ).all()


def test_critical_vibration_mean_is_higher(dataset: pd.DataFrame) -> None:
    means = dataset.groupby("state")["vibration_rms_mm_s"].mean()
    assert means["critique"] > means["normal"]


def test_critical_temperature_mean_is_higher(dataset: pd.DataFrame) -> None:
    means = dataset.groupby("state")["temperature_c"].mean()
    assert means["critique"] > means["normal"]


def test_critical_health_mean_is_lower(dataset: pd.DataFrame) -> None:
    means = dataset.groupby("state")["health_score"].mean()
    assert means["critique"] < means["normal"]


def test_same_seed_produces_same_numeric_values(simulator: BearingSimulator) -> None:
    first = simulator.generate_dataset().select_dtypes(include="number")
    second = simulator.generate_dataset().select_dtypes(include="number")
    pd.testing.assert_frame_equal(first, second)


def test_save_uses_temporary_directory(
    simulator: BearingSimulator, dataset: pd.DataFrame, tmp_path: Path
) -> None:
    simulator.csv_path = tmp_path / "synthetic" / "scenario.csv"
    saved_path = simulator.save_dataset(dataset)
    assert saved_path.is_file()
    assert len(pd.read_csv(saved_path)) == 200


def test_invalid_configuration_has_clear_error(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(yaml.safe_dump({"project": {"name": "test"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="Sections manquantes"):
        BearingSimulator(config_path)
