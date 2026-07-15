"""Dix graphiques de validation et d'explicabilité RUL."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .model_manager import RULModelManager


def create_rul_plots(
    data: pd.DataFrame, manager: RULModelManager, directory: str | Path
) -> list[Path]:
    """Crée les dix visualisations demandées à partir du jeu de test."""
    output = Path(directory); output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    figure, axis = plt.subplots(figsize=(7, 6))
    axis.scatter(data["rul_steps"], data["predicted_rul_steps"], s=8, alpha=0.4)
    maximum = max(data["rul_steps"].max(), data["predicted_rul_steps"].max())
    axis.plot([0, maximum], [0, maximum], "r--", label="Prédiction parfaite")
    _decorate(axis, "RUL réelle contre prédite", "RUL réelle", "RUL prédite")
    paths.append(_save(figure, output / "actual_vs_predicted.png"))

    run = data["asset_run_id"].iloc[0]; trajectory = data[data["asset_run_id"] == run]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(trajectory["cycle"], trajectory["rul_steps"], label="Réelle")
    axis.plot(trajectory["cycle"], trajectory["predicted_rul_steps"], label="Prédite")
    _decorate(axis, f"Évolution RUL - {run}", "Cycle", "RUL")
    paths.append(_save(figure, output / "trajectory_rul.png"))

    errors = data.assign(absolute_error=(data["predicted_rul_steps"] - data["rul_steps"]).abs())
    figure, axis = plt.subplots(figsize=(9, 5)); errors.boxplot(column="absolute_error", by="equipment_type", ax=axis)
    axis.get_figure().suptitle(""); _decorate(axis, "Erreur par équipement", "Équipement", "Erreur absolue")
    paths.append(_save(figure, output / "error_by_equipment.png"))

    mae_fault = errors.groupby("failure_type")["absolute_error"].mean().sort_values()
    figure, axis = plt.subplots(figsize=(11, 6)); mae_fault.plot.bar(ax=axis)
    _decorate(axis, "MAE par type de panne", "Panne", "MAE")
    paths.append(_save(figure, output / "mae_by_fault.png"))

    figure, axis = plt.subplots(figsize=(8, 5)); (data["predicted_rul_steps"] - data["rul_steps"]).hist(bins=35, ax=axis)
    _decorate(axis, "Distribution des erreurs", "Erreur signée", "Nombre")
    paths.append(_save(figure, output / "error_distribution.png"))

    comparison = pd.Series({
        "Baseline": (data["baseline_rul_steps"] - data["rul_steps"]).abs().mean(),
        "Random Forest": errors["absolute_error"].mean(),
    })
    figure, axis = plt.subplots(figsize=(7, 5)); comparison.plot.bar(ax=axis)
    _decorate(axis, "Baseline contre Machine Learning", "Méthode", "MAE")
    paths.append(_save(figure, output / "baseline_comparison.png"))

    figure, axes = plt.subplots(2, 2, figsize=(14, 10))
    for axis, kind in zip(axes.flat, manager.models):
        importance = pd.Series(manager.models[kind].feature_importances()).head(10).sort_values()
        importance.plot.barh(ax=axis); axis.set_title(kind); axis.grid(alpha=0.25)
    paths.append(_save(figure, output / "feature_importance.png"))

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(trajectory["cycle"], trajectory["predicted_rul_steps"], label="Prédiction")
    axis.fill_between(trajectory["cycle"], trajectory["rul_lower_bound"], trajectory["rul_upper_bound"], alpha=0.25, label="Percentiles arbres")
    _decorate(axis, "Intervalle empirique le long d'une trajectoire", "Cycle", "RUL")
    paths.append(_save(figure, output / "uncertainty_trajectory.png"))

    figure, axis = plt.subplots(figsize=(7, 5)); data["risk_level"].value_counts().plot.bar(ax=axis)
    _decorate(axis, "Répartition des niveaux de risque", "Risque", "Nombre")
    paths.append(_save(figure, output / "risk_distribution.png"))

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(trajectory["cycle"], trajectory["health_score"], label="Santé")
    axis.plot(trajectory["cycle"], trajectory["rul_steps"], label="RUL réelle")
    _decorate(axis, "Évolution des capteurs avec la RUL", "Cycle", "Valeur")
    paths.append(_save(figure, output / "sensors_with_rul.png"))
    return paths


def _decorate(axis: Any, title: str, xlabel: str, ylabel: str) -> None:
    axis.set_title(title); axis.set_xlabel(xlabel); axis.set_ylabel(ylabel); axis.grid(alpha=0.25)
    handles, labels = axis.get_legend_handles_labels()
    if handles and labels:
        axis.legend(loc="best")


def _save(figure: Any, path: Path) -> Path:
    figure.tight_layout(); figure.savefig(path, dpi=140); plt.close(figure); return path
