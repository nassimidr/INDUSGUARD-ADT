"""Préparation sans fuite des données de diagnostic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd
from sklearn.model_selection import train_test_split

FORBIDDEN_FEATURES = {
    "failure_type", "is_anomaly", "operating_state",
    "anomaly_severity", "scenario_id",
}
REQUIRED_COLUMNS = {
    "timestamp", "scenario_id", "equipment_id", "equipment_type",
    "operating_state", "is_anomaly", "failure_type",
}


@dataclass(frozen=True)
class DiagnosisSplit:
    """Jeux d'entraînement et de test avec leurs index d'origine."""

    x_train: pd.DataFrame
    x_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series


def load_diagnosis_data(path: str | Path) -> pd.DataFrame:
    """Charge et valide le dataset industriel étiqueté."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Dataset de diagnostic introuvable : {source}")
    data = pd.read_csv(source, parse_dates=["timestamp"])
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Colonnes de diagnostic manquantes : {sorted(missing)}")
    if data["failure_type"].isna().any():
        raise ValueError("Les étiquettes de panne ne peuvent pas être vides.")
    return data


def select_features(
    data: pd.DataFrame, equipment_type: str, features: Sequence[str]
) -> pd.DataFrame:
    """Sélectionne les capteurs d'un équipement et interdit toute cible."""
    feature_list = list(features)
    forbidden = FORBIDDEN_FEATURES.intersection(feature_list)
    if forbidden:
        raise ValueError(f"Fuite de données interdite : {sorted(forbidden)}")
    missing = set(feature_list) - set(data.columns)
    if missing:
        raise ValueError(f"Capteurs manquants : {sorted(missing)}")
    subset = data.loc[data["equipment_type"] == equipment_type, feature_list]
    return subset.apply(pd.to_numeric, errors="coerce")


def split_equipment_data(
    data: pd.DataFrame,
    equipment_type: str,
    features: Sequence[str],
    test_size: float,
    random_state: int,
) -> DiagnosisSplit:
    """Crée une séparation stratifiée lorsque chaque classe le permet."""
    subset = data[data["equipment_type"] == equipment_type]
    x_values = select_features(data, equipment_type, features)
    target = subset["failure_type"]
    counts = target.value_counts()
    stratify = target if len(counts) > 1 and int(counts.min()) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x_values,
        target,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
    return DiagnosisSplit(x_train, x_test, y_train, y_test)

