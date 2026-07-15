from datetime import datetime, timedelta

from indusguard.maintenance_planning.scheduler import MaintenanceScheduler
from indusguard.maintenance_planning.spare_parts import SparePartsManager
from indusguard.maintenance_planning.work_order import WorkOrder


def order(identifier: str, part: str = "") -> WorkOrder:
    now = datetime(2026, 1, 1, 8)
    return WorkOrder(identifier, identifier, "bearing", "bearing_wear", "preventive_maintenance", "high", 60, now, now + timedelta(hours=12), 2, ("mechanic",), (part,) if part else (), True, 100)


def test_scheduler_avoids_conflicts_and_blocks_missing_parts() -> None:
    resources = {"working_hours": {"start": "08:00", "end": "18:00"}, "technicians": {"mechanic": {"available_count": 1}}, "spare_parts": {"sensor": {"quantity": 0, "unit_cost": 10}}}
    parts = SparePartsManager(resources); scheduler = MaintenanceScheduler(resources, parts)
    orders, _ = scheduler.schedule([order("A"), order("B"), order("C", "sensor")])
    planned = sorted([item for item in orders if item.status == "scheduled"], key=lambda item: item.scheduled_start)
    assert planned[0].scheduled_end <= planned[1].scheduled_start
    blocked = [item for item in orders if item.status == "blocked"]
    assert len(blocked) == 1 and "sensor" in blocked[0].blocking_reason

