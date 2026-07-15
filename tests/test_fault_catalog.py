from indusguard.fault_diagnosis.fault_catalog import ALL_FAULT_TYPES, FAULTS_BY_EQUIPMENT


def test_catalog_contains_required_faults() -> None:
    required = {
        "normal", "unknown_fault", "cascade_failure", "motor_overload",
        "motor_overheating", "bearing_wear", "bearing_severe_damage",
        "conveyor_slippage", "pump_cavitation", "pump_blockage", "pump_leakage",
    }
    assert required.issubset(ALL_FAULT_TYPES)
    assert "motor_overload" in FAULTS_BY_EQUIPMENT["motor"]
    assert "pump_cavitation" in FAULTS_BY_EQUIPMENT["pump"]

