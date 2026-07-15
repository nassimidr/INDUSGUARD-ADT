"""Visualisations des performances et des anomalies détectées."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def create_detection_plots(data: pd.DataFrame, directory: str | Path) -> list[Path]:
    """Crée les six graphiques de synthèse de la phase 2."""
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    figure, axis = plt.subplots(figsize=(6, 5))
    matrix = confusion_matrix(data["is_anomaly"], data["isolation_forest_prediction"], labels=[False, True])
    ConfusionMatrixDisplay(matrix, display_labels=["Normal", "Anomalie"]).plot(ax=axis, colorbar=False)
    axis.set_title("Matrice de confusion - Isolation Forest")
    paths.append(_save(figure, output / "confusion_matrix.png"))

    figure, axis = plt.subplots(figsize=(11, 5))
    for kind, group in data.groupby("equipment_type"):
        axis.plot(group.index, group["anomaly_score"], label=kind, linewidth=1)
    _decorate(axis, "Score d'anomalie dans le temps", "Score")
    paths.append(_save(figure, output / "anomaly_scores_time.png"))

    figure, axis = plt.subplots(figsize=(11, 4))
    axis.scatter(data.index, data["is_anomaly"].astype(int), s=8, label="Réelle", alpha=0.65)
    axis.scatter(data.index, data["isolation_forest_prediction"].astype(int) + 0.04, s=8, label="Détectée", alpha=0.65)
    axis.set_yticks([0, 1], ["Normal", "Anomalie"]); _decorate(axis, "Anomalies réelles et détectées", "Classe")
    paths.append(_save(figure, output / "actual_vs_detected.png"))

    figure, axis = plt.subplots(figsize=(9, 5))
    for actual, group in data.groupby("is_anomaly"):
        axis.hist(group["anomaly_score"], bins=35, alpha=0.55, label="Anomalie" if actual else "Normal")
    _decorate(axis, "Distribution des scores d'anomalie", "Nombre")
    paths.append(_save(figure, output / "score_distribution.png"))

    comparison = data.groupby("equipment_type")[["is_anomaly", "threshold_prediction", "isolation_forest_prediction"]].mean()
    figure, axis = plt.subplots(figsize=(9, 5)); comparison.plot.bar(ax=axis)
    _decorate(axis, "Comparaison par équipement", "Proportion")
    paths.append(_save(figure, output / "equipment_comparison.png"))

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=False)
    sensor = {"motor": "current", "bearing": "vibration", "conveyor": "slip_rate", "pump": "flow_rate"}
    for axis, (kind, column) in zip(axes.flat, sensor.items()):
        group = data[data["equipment_type"] == kind]
        axis.plot(group.index, group[column], linewidth=1, label=column)
        anomalies = group[group["isolation_forest_prediction"]]
        axis.scatter(anomalies.index, anomalies[column], color="red", s=12, label="Détectée")
        _decorate(axis, f"{kind} - {column}", column)
    figure.tight_layout(); paths.append(_save(figure, output / "sensor_anomalies.png"))
    return paths


def _decorate(axis: Any, title: str, ylabel: str) -> None:
    axis.set_title(title); axis.set_xlabel("Index"); axis.set_ylabel(ylabel)
    axis.grid(alpha=0.25); axis.legend(loc="best")


def _save(figure: Any, path: Path) -> Path:
    figure.tight_layout(); figure.savefig(path, dpi=140); plt.close(figure)
    return path

