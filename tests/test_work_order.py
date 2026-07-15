from datetime import datetime, timedelta

from indusguard.maintenance_planning.work_order import WorkOrder


def test_work_order_contains_required_fields() -> None:
    now = datetime(2026, 1, 1, 8)
    order = WorkOrder("WO-1", "B1", "bearing", "bearing_wear", "preventive_maintenance", "high", 60, now, now + timedelta(hours=8), 2, ("mechanic",), ("bearing",), True, 1000)
    record = order.to_record()
    for column in ["work_order_id", "equipment_id", "priority_score", "recommended_deadline", "required_parts", "status"]:
        assert column in record

