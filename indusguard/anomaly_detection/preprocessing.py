"""Chargement, validation et sélection des caractéristiques capteurs."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

FEATURE_MAP: dict[str, list[str]] = {
    "motor": ["temperature", "vibration", "rpm", "current", "load"],
    "bearing": ["temperature", "vibration", "rpm", "health_score"],
    "conveyor": ["temperature", "vibration", "load", "conveyor_speed", "slip_rate"],
    "pump": ["temperature", "vibration", "current", "pressure", "flow_rate"],
}

TARGET_COLUMNS = {"is_anomaly", "operating_state", "failure_type", "anomaly_severity"}


def load_sensor_data(path: str | Path) -> pd.DataFrame:
    """Charge un CSV de mesures et valide les colonnes structurelles."""
    csv_path = Path(path).expanduser().resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(f"Dataset introuvable : {csv_path}")
    data = pd.read_csv(csv_path, parse_dates=["timestamp"])
    required = {"timestamp", "equipment_id", "equipment_type"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Colonnes structurelles manquantes : {sorted(missing)}")
    return data


def equipment_features(
    data: pd.DataFrame, equipment_type: str, features: Mapping[str, Sequence[str]] | None = None
) -> pd.DataFrame:
    """Retourne uniquement les variables numériques autorisées d'un équipement."""
    mapping = features or FEATURE_MAP
    if equipment_type not in mapping:
        raise ValueError(f"Type d'équipement inconnu : {equipment_type}")
    selected = list(mapping[equipment_type])
    forbidden = TARGET_COLUMNS.intersection(selected)
    if forbidden:
        raise ValueError(f"La cible ne peut pas être une caractéristique : {sorted(forbidden)}")
    missing = set(selected) - set(data.columns)
    if missing:
        raise ValueError(f"Caractéristiques manquantes : {sorted(missing)}")
    subset = data.loc[data["equipment_type"] == equipment_type, selected].copy()
    return subset.apply(pd.to_numeric, errors="coerce")

