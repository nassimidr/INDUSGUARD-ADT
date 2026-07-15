from indusguard.maintenance_planning.spare_parts import SparePartsManager


def test_parts_selection_and_reservation() -> None:
    manager = SparePartsManager({"spare_parts": {"bearing": {"quantity": 1, "unit_cost": 100}, "sensor": {"quantity": 0, "unit_cost": 20}}})
    assert manager.select(("bearing",), ()).all_required_available
    manager.reserve(("bearing",))
    assert not manager.select(("bearing",), ()).all_required_available
    assert not manager.select(("sensor",), ()).all_required_available

