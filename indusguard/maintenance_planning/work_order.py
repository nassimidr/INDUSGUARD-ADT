"""Structure d'un ordre de travail de maintenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


WORK_ORDER_STATUSES = {"proposed", "scheduled", "blocked", "urgent", "completed", "cancelled"}


@dataclass
class WorkOrder:
    work_order_id: str
    equipment_id: str
    equipment_type: str
    diagnosed_fault: str
    maintenance_strategy: str
    priority: str
    priority_score: float
    recommended_start: datetime
    recommended_deadline: datetime
    estimated_duration_hours: float
    required_skills: tuple[str, ...]
    required_parts: tuple[str, ...]
    shutdown_required: bool
    estimated_total_cost: float
    status: str = "proposed"
    blocking_reason: str = ""
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    assigned_skill: str = ""
    parts_available: bool = True

    def __post_init__(self) -> None:
        if self.status not in WORK_ORDER_STATUSES:
            raise ValueError(f"Statut d'ordre invalide : {self.status}")
        if self.estimated_duration_hours <= 0:
            raise ValueError("La durée d'un ordre doit être positive.")

    def to_record(self) -> dict[str, object]:
        record = asdict(self)
        for key in ("recommended_start", "recommended_deadline", "scheduled_start", "scheduled_end"):
            value = record[key]
            record[key] = value.isoformat() if value else ""
        record["required_skills"] = ",".join(self.required_skills)
        record["required_parts"] = ",".join(self.required_parts)
        return record

