"""Estimation synthétique des coûts d'intervention."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CostEstimate:
    labor_cost: float
    parts_cost: float
    downtime_cost: float
    total_cost: float
    delayed_risk_cost: float


def estimate_cost(
    duration_hours: float,
    technician_count: int,
    average_hourly_cost: float,
    parts_cost: float,
    shutdown_required: bool,
    resources: dict[str, Any],
    priority_score: float,
) -> CostEstimate:
    """Calcule des montants synthétiques positifs et reproductibles."""
    labor = duration_hours * technician_count * average_hourly_cost
    downtime = duration_hours * float(resources["production_loss_per_hour"]) if shutdown_required else 0.0
    total = labor + parts_cost + downtime
    delayed = total * float(resources["delayed_risk_multiplier"]) * priority_score / 100.0
    return CostEstimate(*[round(value, 2) for value in (labor, parts_cost, downtime, total, delayed)])

