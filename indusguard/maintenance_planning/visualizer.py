"""Dix visualisations de recommandation et planification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def create_maintenance_plots(
    recommendations: pd.DataFrame,
    orders: pd.DataFrame,
    schedule: pd.DataFrame,
    directory: str | Path,
) -> list[Path]:
    output = Path(directory); output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    paths.append(_bar(recommendations["priority"].value_counts(), output / "interventions_by_priority.png", "Interventions par priorité", "Nombre"))
    paths.append(_bar(recommendations["maintenance_strategy"].value_counts(), output / "interventions_by_strategy.png", "Interventions par stratégie", "Nombre"))

    planned = schedule[schedule["scheduled_start"].fillna("") != ""].copy()
    figure, axis = plt.subplots(figsize=(12, 6))
    if not planned.empty:
        planned["start"] = pd.to_datetime(planned["scheduled_start"])
        planned["end"] = pd.to_datetime(planned["scheduled_end"])
        origin = planned["start"].min()
        for position, (_, row) in enumerate(planned.iterrows()):
            left = (row["start"] - origin).total_seconds() / 3600
            width = (row["end"] - row["start"]).total_seconds() / 3600
            axis.barh(position, width, left=left, label=row["priority"] if position == 0 else None)
        axis.set_yticks(range(len(planned)), planned["equipment_id"])
    _decorate(axis, "Calendrier des interventions", "Heures depuis le début", "Équipement")
    paths.append(_save(figure, output / "maintenance_gantt.png"))

    paths.append(_bar(recommendations.set_index("equipment_id")["estimated_total_cost"], output / "cost_by_equipment.png", "Coût estimé par équipement", "Coût synthétique"))
    paths.append(_bar(recommendations.set_index("equipment_id")["estimated_duration_hours"], output / "duration_by_equipment.png", "Durée estimée par équipement", "Heures"))

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.scatter(recommendations["predicted_rul_steps"], recommendations["priority_score"], c=recommendations["priority_score"], cmap="viridis")
    _decorate(axis, "RUL contre priorité", "RUL prédite", "Score de priorité")
    paths.append(_save(figure, output / "rul_vs_priority.png"))
    paths.append(_bar(recommendations.set_index("equipment_id")["priority_score"], output / "priority_score_by_equipment.png", "Score de priorité", "Score 0-100"))

    resource_counts = schedule["assigned_resource"].str.split(",").explode().value_counts()
    resource_counts = resource_counts[resource_counts.index != ""]
    paths.append(_bar(resource_counts, output / "resource_distribution.png", "Répartition des ressources", "Affectations"))
    paths.append(_bar(orders["status"].value_counts(), output / "scheduled_vs_blocked.png", "Ordres planifiés et bloqués", "Nombre"))
    part_counts = recommendations["required_parts"].str.split(",").explode().value_counts()
    part_counts = part_counts[part_counts.index != ""]
    paths.append(_bar(part_counts, output / "required_spare_parts.png", "Pièces de rechange nécessaires", "Quantité"))
    return paths


def _bar(values: pd.Series, path: Path, title: str, ylabel: str) -> Path:
    figure, axis = plt.subplots(figsize=(9, 5)); values.plot.bar(ax=axis)
    _decorate(axis, title, "Catégorie", ylabel); return _save(figure, path)


def _decorate(axis: Any, title: str, xlabel: str, ylabel: str) -> None:
    axis.set_title(title); axis.set_xlabel(xlabel); axis.set_ylabel(ylabel); axis.grid(alpha=0.25)
    handles, labels = axis.get_legend_handles_labels()
    if handles and labels:
        axis.legend(loc="best")


def _save(figure: Any, path: Path) -> Path:
    figure.tight_layout(); figure.savefig(path, dpi=140); plt.close(figure); return path
