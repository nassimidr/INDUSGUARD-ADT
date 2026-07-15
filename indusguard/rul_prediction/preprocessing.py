"""Chargement et séparation étanche des trajectoires RUL."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

TARGET_COLUMNS = {
    "rul_steps", "rul_hours", "failure_occurred", "degradation_progress",
    "cycle_final", "failure_timestamp", "true_remaining_cycles",
    "operating_state", "is_anomaly", "failure_type", "anomaly_severity",
}
REQUIRED_COLUMNS = {
    "timestamp", "asset_run_id", "cycle", "equipment_id", "equipment_type",
    "failure_type", "failure_occurred", "rul_steps", "rul_hours",
    "degradation_progress",
}


@dataclass(frozen=True)
class TrajectorySplit:
    """Lignes d'entraînement/test et identifiants de trajectoire disjoints."""

    train: pd.DataFrame
    test: pd.DataFrame
    train_runs: frozenset[str]
    test_runs: frozenset[str]


def load_rul_data(path: str | Path) -> pd.DataFrame:
    """Charge, valide et trie le dataset RUL."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Dataset RUL introuvable : {source}")
    data = pd.read_csv(source, parse_dates=["timestamp"])
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Colonnes RUL manquantes : {sorted(missing)}")
    return data.sort_values(["asset_run_id", "cycle"]).reset_index(drop=True)


def complete_run_ids(data: pd.DataFrame) -> frozenset[str]:
    """Identifie les trajectoires ayant effectivement atteint la panne."""
    status = data.groupby("asset_run_id")["failure_occurred"].max()
    return frozenset(status[status.eq(1)].index.astype(str))


def incomplete_run_ids(data: pd.DataFrame) -> frozenset[str]:
    status = data.groupby("asset_run_id")["failure_occurred"].max()
    return frozenset(status[status.eq(0)].index.astype(str))


def validate_feature_columns(features: Sequence[str]) -> list[str]:
    """Interdit explicitement toute cible ou information future."""
    columns = list(features)
    forbidden = TARGET_COLUMNS.intersection(columns)
    if forbidden:
        raise ValueError(f"Fuite de cible RUL interdite : {sorted(forbidden)}")
    return columns


def split_by_trajectory(
    data: pd.DataFrame, equipment_type: str, test_size: float, random_state: int
) -> TrajectorySplit:
    """Sépare les trajectoires complètes avec GroupShuffleSplit."""
    complete = complete_run_ids(data)
    subset = data[
        (data["equipment_type"] == equipment_type)
        & data["asset_run_id"].isin(complete)
    ].copy()
    if subset["asset_run_id"].nunique() < 4:
        raise ValueError("Au moins quatre trajectoires complètes sont requises.")
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=float(test_size), random_state=int(random_state)
    )
    train_index, test_index = next(
        splitter.split(subset, groups=subset["asset_run_id"])
    )
    train = subset.iloc[train_index].copy()
    test = subset.iloc[test_index].copy()
    train_runs = frozenset(train["asset_run_id"].astype(str).unique())
    test_runs = frozenset(test["asset_run_id"].astype(str).unique())
    if train_runs.intersection(test_runs):
        raise RuntimeError("Une trajectoire apparaît dans train et test.")
    return TrajectorySplit(train, test, train_runs, test_runs)

