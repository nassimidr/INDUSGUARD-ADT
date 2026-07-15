"""Planificateur heuristique sans conflits de ressources."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from .spare_parts import SparePartsManager
from .work_order import WorkOrder


class MaintenanceScheduler:
    """Trie priorité/date limite puis attribue le premier créneau commun."""

    def __init__(self, resources: dict[str, Any], parts: SparePartsManager) -> None:
        self.resources = resources
        self.parts = parts
        self.conflicts_detected = 0
        self.conflicts_resolved = 0

    def schedule(self, orders: list[WorkOrder]) -> tuple[list[WorkOrder], list[dict[str, object]]]:
        if not orders:
            return orders, []
        start_reference = min(order.recommended_start for order in orders)
        availability = self._availability(start_reference)
        schedules: list[dict[str, object]] = []
        sorted_orders = sorted(orders, key=lambda order: (-order.priority_score, order.recommended_deadline))
        for order in sorted_orders:
            parts_ok, missing = self.parts.available(order.required_parts)
            order.parts_available = parts_ok
            if not parts_ok:
                order.status = "blocked"
                order.blocking_reason = "Pièces indisponibles : " + ", ".join(missing)
                schedules.append(self._schedule_record(order, "")); continue
            allocation = self._find_allocation(order, availability)
            if allocation is None:
                order.status = "blocked"
                order.blocking_reason = "Aucune ressource ou aucun créneau avant la date limite"
                schedules.append(self._schedule_record(order, "")); continue
            scheduled_start, scheduled_end, resource_ids = allocation
            self.parts.reserve(order.required_parts)
            for skill, resource_index in resource_ids:
                availability[skill][resource_index] = scheduled_end
            order.scheduled_start = scheduled_start; order.scheduled_end = scheduled_end
            order.assigned_skill = ",".join(f"{skill}_{index + 1}" for skill, index in resource_ids)
            order.status = "urgent" if order.priority in {"urgent", "critical"} else "scheduled"
            schedules.append(self._schedule_record(order, order.assigned_skill))
        return orders, schedules

    def _availability(self, start: datetime) -> dict[str, list[datetime]]:
        return {
            skill: [start] * int(values["available_count"])
            for skill, values in self.resources["technicians"].items()
        }

    def _find_allocation(
        self, order: WorkOrder, availability: dict[str, list[datetime]]
    ) -> tuple[datetime, datetime, list[tuple[str, int]]] | None:
        if any(not availability.get(skill) for skill in order.required_skills):
            return None
        chosen = [(skill, min(range(len(availability[skill])), key=availability[skill].__getitem__)) for skill in order.required_skills]
        resource_ready = max(availability[skill][index] for skill, index in chosen)
        candidate = max(order.recommended_start, resource_ready)
        if candidate > order.recommended_start:
            self.conflicts_detected += 1; self.conflicts_resolved += 1
        start = self._within_working_hours(candidate, order.estimated_duration_hours)
        end = start + timedelta(hours=order.estimated_duration_hours)
        if end > order.recommended_deadline:
            return None
        return start, end, chosen

    def _within_working_hours(self, candidate: datetime, duration: float) -> datetime:
        start_time = time.fromisoformat(self.resources["working_hours"]["start"])
        end_time = time.fromisoformat(self.resources["working_hours"]["end"])
        work_start = datetime.combine(candidate.date(), start_time)
        work_end = datetime.combine(candidate.date(), end_time)
        if candidate < work_start:
            candidate = work_start
        if candidate + timedelta(hours=duration) > work_end:
            candidate = datetime.combine(candidate.date() + timedelta(days=1), start_time)
        return candidate

    @staticmethod
    def _schedule_record(order: WorkOrder, resource: str) -> dict[str, object]:
        return {
            "work_order_id": order.work_order_id, "equipment_id": order.equipment_id,
            "scheduled_start": order.scheduled_start.isoformat() if order.scheduled_start else "",
            "scheduled_end": order.scheduled_end.isoformat() if order.scheduled_end else "",
            "assigned_resource": resource, "priority": order.priority, "status": order.status,
            "deadline_respected": bool(order.scheduled_end and order.scheduled_end <= order.recommended_deadline),
        }
