import pytest

from indusguard.maintenance_planning.maintenance_catalog import MaintenanceCatalog


def test_catalog_validates_and_returns_unknown_fallback() -> None:
    entries = {
        "normal": {"strategy": "monitor", "action": "Surveiller", "duration_hours": 1, "shutdown_required": False, "inspection_required": False},
        "unknown_fault": {"strategy": "inspect", "action": "Inspecter", "duration_hours": 1, "shutdown_required": False, "inspection_required": True},
        "cascade_failure": {"strategy": "emergency_shutdown", "action": "Arrêter", "duration_hours": 2, "shutdown_required": True, "inspection_required": True},
    }
    catalog = MaintenanceCatalog(entries)
    assert catalog.get("normal").strategy == "monitor"
    assert catalog.get("not_known").strategy == "inspect"


def test_invalid_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="Stratégies"):
        MaintenanceCatalog({
            "normal": {"strategy": "bad", "action": "x", "duration_hours": 1, "shutdown_required": False, "inspection_required": False},
            "unknown_fault": {"strategy": "inspect", "action": "x", "duration_hours": 1, "shutdown_required": False, "inspection_required": True},
            "cascade_failure": {"strategy": "emergency_shutdown", "action": "x", "duration_hours": 1, "shutdown_required": True, "inspection_required": True},
        })

