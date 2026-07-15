"""Indicateurs et contrôles de cohérence du plan synthétique."""

from __future__ import annotations

from typing import Any

import pandas as pd


def validate_plan(
    recommendations: pd.DataFrame, orders: pd.DataFrame, schedule: pd.DataFrame
) -> None:
    """Lève une erreur lorsqu'une règle de sécurité logique est violée."""
    if not recommendations["priority_score"].between(0, 100).all():
        raise ValueError("Les scores de priorité doivent rester entre 0 et 100.")
    if (recommendations[["estimated_labor_cost", "estimated_parts_cost", "estimated_downtime_cost", "estimated_total_cost"]] < 0).any().any():
        raise ValueError("Les coûts doivent être positifs ou nuls.")
    critical = recommendations["severity"] == "critical"
    if recommendations.loc[critical, "priority"].isin(["low", "medium"]).any():
        raise ValueError("Une situation critique ne peut pas avoir une faible priorité.")
    low_rul = recommendations["predicted_rul_steps"] <= 5
    if (recommendations.loc[low_rul, "maintenance_strategy"] == "monitor").any():
        raise ValueError("Une RUL très faible ne peut pas conduire à monitor.")
    normal = recommendations["diagnosed_fault"] == "normal"
    if recommendations.loc[normal, "shutdown_required"].any():
        raise ValueError("Un équipement normal ne doit pas être arrêté en urgence.")
    planned = orders[orders["status"].isin(["scheduled", "urgent"])]
    if not planned.empty:
        starts = pd.to_datetime(planned["scheduled_start"])
        ends = pd.to_datetime(planned["scheduled_end"])
        if not (starts < ends).all():
            raise ValueError("Chaque début planifié doit précéder sa fin.")
        _validate_resource_conflicts(planned)


def maintenance_metrics(
    recommendations: pd.DataFrame,
    orders: pd.DataFrame,
    schedule: pd.DataFrame,
    conflicts_detected: int,
    conflicts_resolved: int,
) -> dict[str, Any]:
    planned = orders["status"].isin(["scheduled", "urgent"])
    blocked = orders["status"] == "blocked"
    respected = schedule.loc[schedule["status"].isin(["scheduled", "urgent"]), "deadline_respected"]
    return {
        "recommendation_count": int(len(recommendations)),
        "by_strategy": recommendations["maintenance_strategy"].value_counts().to_dict(),
        "by_priority": recommendations["priority"].value_counts().to_dict(),
        "shutdown_count": int(recommendations["shutdown_required"].sum()),
        "scheduled_orders": int(planned.sum()), "blocked_orders": int(blocked.sum()),
        "deadline_respected_pct": float(respected.mean() * 100) if len(respected) else 0.0,
        "total_estimated_cost": float(recommendations["estimated_total_cost"].sum()),
        "total_duration_hours": float(recommendations["estimated_duration_hours"].sum()),
        "orders_without_parts": int((~orders["parts_available"].astype(bool)).sum()),
        "low_confidence_recommendations": int((recommendations["recommendation_confidence"] < 0.6).sum()),
        "critical_recommendations": int((recommendations["priority"] == "critical").sum()),
        "resource_conflicts_detected": int(conflicts_detected),
        "resource_conflicts_resolved": int(conflicts_resolved),
        "blocking_reasons": orders.loc[blocked, "blocking_reason"].value_counts().to_dict(),
        "resources_used": schedule.loc[schedule["assigned_resource"] != "", "assigned_resource"].value_counts().to_dict(),
        "required_parts": _part_counts(recommendations["required_parts"]),
    }


def _validate_resource_conflicts(orders: pd.DataFrame) -> None:
    expanded = orders.assign(resource=orders["assigned_skill"].str.split(",")).explode("resource")
    for _, group in expanded.groupby("resource"):
        ordered = group.sort_values("scheduled_start")
        previous_end = None
        for _, row in ordered.iterrows():
            start = pd.Timestamp(row["scheduled_start"]); end = pd.Timestamp(row["scheduled_end"])
            if previous_end is not None and start < previous_end:
                raise ValueError("Deux ordres partagent la même ressource au même moment.")
            previous_end = end


def _part_counts(series: pd.Series) -> dict[str, int]:
    parts = series.str.split(",").explode(); parts = parts[parts.fillna("") != ""]
    return {str(name): int(count) for name, count in parts.value_counts().items()}

