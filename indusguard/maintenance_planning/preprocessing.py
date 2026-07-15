"""Chargement et fusion déterministe des sorties des phases 2 à 4."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DIAGNOSIS_REQUIRED = {
    "timestamp", "equipment_type", "final_diagnosis", "final_confidence",
    "severity", "responsible_sensors", "diagnosis_explanation",
}
RUL_REQUIRED = {
    "timestamp", "asset_run_id", "equipment_id", "equipment_type",
    "true_failure_type", "true_rul_steps", "predicted_rul_steps",
    "predicted_rul_hours", "rul_lower_bound", "rul_upper_bound",
    "risk_level", "prediction_confidence",
}
ANOMALY_REQUIRED = {
    "timestamp", "equipment_type", "threshold_prediction",
    "isolation_forest_prediction", "anomaly_score",
}


def load_csv(path: str | Path, required: set[str]) -> pd.DataFrame:
    """Charge un CSV, valide ses colonnes et convertit son timestamp."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Fichier source introuvable : {source}")
    data = pd.read_csv(source, parse_dates=["timestamp"])
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Colonnes de maintenance manquantes : {sorted(missing)}")
    return data


def merge_maintenance_sources(
    diagnosis: pd.DataFrame, rul: pd.DataFrame, anomalies: pd.DataFrame
) -> pd.DataFrame:
    """Construit le parc courant à partir des trajectoires RUL incomplètes."""
    incomplete_runs = rul.loc[rul["true_rul_steps"].isna(), "asset_run_id"].unique()
    current = rul[rul["asset_run_id"].isin(incomplete_runs)].copy()
    if current.empty:
        current = rul.copy()
    current = (
        current.sort_values(["asset_run_id", "cycle"])
        .groupby("asset_run_id", as_index=False)
        .tail(1)
        .drop_duplicates("equipment_id")
    )
    records: list[dict[str, object]] = []
    for _, asset in current.iterrows():
        equipment_type = str(asset["equipment_type"])
        expected_fault = str(asset["true_failure_type"])
        candidates = diagnosis[diagnosis["equipment_type"] == equipment_type]
        matching = candidates[candidates["final_diagnosis"] == expected_fault]
        if not matching.empty:
            selected = matching.sort_values("final_confidence").iloc[-1]
            fault = str(selected["final_diagnosis"])
            diagnosis_confidence = float(selected["final_confidence"])
            severity = str(selected["severity"])
            sensors = selected.get("responsible_sensors", "")
            diagnosis_explanation = selected.get("diagnosis_explanation", "")
            diagnosis_source = "phase_3_exact_match"
        else:
            fault = expected_fault
            diagnosis_confidence = 0.58
            severity = _severity_from_risk(str(asset["risk_level"]))
            sensors = ""
            diagnosis_explanation = "Panne issue de la trajectoire synthétique RUL, sans classe équivalente en phase 3."
            diagnosis_source = "rul_synthetic_fallback"
        anomaly_pool = anomalies[anomalies["equipment_type"] == equipment_type]
        anomaly = anomaly_pool.sort_values("anomaly_score").iloc[-1]
        record = asset.to_dict()
        record.update({
            "diagnosed_fault": fault, "diagnosis_confidence": diagnosis_confidence,
            "severity": severity, "responsible_sensors": "" if pd.isna(sensors) else sensors,
            "diagnosis_explanation": diagnosis_explanation,
            "diagnosis_source": diagnosis_source,
            "threshold_prediction": bool(anomaly["threshold_prediction"]),
            "isolation_forest_prediction": bool(anomaly["isolation_forest_prediction"]),
            "anomaly_score": float(anomaly["anomaly_score"]),
        })
        records.append(record)
    merged = pd.DataFrame(records).sort_values(["equipment_type", "equipment_id"])
    if merged["equipment_id"].duplicated().any():
        raise ValueError("Un équipement ne peut apparaître qu'une fois dans le parc courant.")
    return merged.reset_index(drop=True)


def _severity_from_risk(risk: str) -> str:
    return {"low": "low", "medium": "medium", "high": "high", "critical": "critical"}.get(risk, "medium")

