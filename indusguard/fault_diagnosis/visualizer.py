"""Graphiques de synthèse du diagnostic de pannes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, f1_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def create_diagnosis_plots(data: pd.DataFrame, directory: str | Path) -> list[Path]:
    """Crée les huit visualisations demandées."""
    output = Path(directory); output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    labels = sorted(set(data["true_failure_type"]) | set(data["final_diagnosis"]))
    figure, axis = plt.subplots(figsize=(12, 10))
    matrix = confusion_matrix(data["true_failure_type"], data["final_diagnosis"], labels=labels)
    ConfusionMatrixDisplay(matrix, display_labels=labels).plot(ax=axis, xticks_rotation=70, colorbar=False)
    axis.set_title("Matrice de confusion globale")
    paths.append(_save(figure, output / "global_confusion_matrix.png"))

    figure, axes = plt.subplots(2, 2, figsize=(14, 12))
    for axis, (kind, group) in zip(axes.flat, data.groupby("equipment_type")):
        local_labels = sorted(set(group["true_failure_type"]) | set(group["final_diagnosis"]))
        local = confusion_matrix(group["true_failure_type"], group["final_diagnosis"], labels=local_labels)
        ConfusionMatrixDisplay(local, display_labels=local_labels).plot(ax=axis, xticks_rotation=60, colorbar=False)
        axis.set_title(kind)
    paths.append(_save(figure, output / "equipment_confusion_matrices.png"))

    figure, axis = plt.subplots(figsize=(11, 6))
    data["final_diagnosis"].value_counts().plot.bar(ax=axis)
    _decorate(axis, "Répartition des diagnostics", "Nombre")
    paths.append(_save(figure, output / "fault_distribution.png"))

    f1_values = {
        kind: f1_score(group["true_failure_type"], group["final_diagnosis"], average="macro", zero_division=0)
        for kind, group in data.groupby("equipment_type")
    }
    figure, axis = plt.subplots(figsize=(8, 5)); pd.Series(f1_values).plot.bar(ax=axis)
    _decorate(axis, "F1 macro par équipement", "F1 macro")
    paths.append(_save(figure, output / "f1_by_equipment.png"))

    comparisons = {
        "Règles": (data["rule_based_fault"] == data["true_failure_type"]).mean(),
        "Machine Learning": (data["ml_predicted_fault"] == data["true_failure_type"]).mean(),
        "Hybride": (data["final_diagnosis"] == data["true_failure_type"]).mean(),
    }
    figure, axis = plt.subplots(figsize=(8, 5)); pd.Series(comparisons).plot.bar(ax=axis)
    _decorate(axis, "Comparaison des approches", "Accuracy")
    paths.append(_save(figure, output / "approach_comparison.png"))

    figure, axis = plt.subplots(figsize=(9, 5)); data["final_confidence"].hist(bins=25, ax=axis)
    _decorate(axis, "Confiance des diagnostics", "Nombre")
    paths.append(_save(figure, output / "diagnosis_confidence.png"))

    severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    figure, axis = plt.subplots(figsize=(12, 5))
    for kind, group in data.groupby("equipment_type"):
        axis.scatter(group.index, group["severity"].map(severity_order), s=8, label=kind)
    axis.set_yticks(list(severity_order.values()), list(severity_order.keys()))
    _decorate(axis, "Gravité des pannes dans le temps", "Gravité")
    paths.append(_save(figure, output / "severity_timeline.png"))

    sensors = data.assign(sensor=data["responsible_sensors"].str.split(",")).explode("sensor")
    sensors = sensors[sensors["sensor"].fillna("") != ""]
    pivot = pd.crosstab(sensors["final_diagnosis"], sensors["sensor"])
    figure, axis = plt.subplots(figsize=(12, 7)); pivot.plot.bar(stacked=True, ax=axis)
    _decorate(axis, "Capteurs responsables par type de panne", "Nombre")
    paths.append(_save(figure, output / "responsible_sensors.png"))
    return paths


def _decorate(axis: Any, title: str, ylabel: str) -> None:
    axis.set_title(title); axis.set_xlabel("Catégorie / index"); axis.set_ylabel(ylabel)
    axis.grid(alpha=0.25)
    handles, labels = axis.get_legend_handles_labels()
    if handles and labels:
        axis.legend(loc="best")


def _save(figure: Any, path: Path) -> Path:
    figure.tight_layout(); figure.savefig(path, dpi=140); plt.close(figure)
    return path
