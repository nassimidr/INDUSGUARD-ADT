import pandas as pd

from indusguard.fault_diagnosis import RuleBasedDiagnoser


RULES = {
    "motor": [{"fault": "motor_overload", "min_matches": 2, "conditions": [
        {"sensor": "load", "min": 80}, {"sensor": "current", "min": 24}, {"sensor": "rpm", "max": 1400},
    ]}],
    "bearing": [{"fault": "bearing_wear", "min_matches": 2, "conditions": [
        {"sensor": "vibration", "min": 4}, {"sensor": "health_score", "max": 70},
    ]}],
    "conveyor": [{"fault": "conveyor_slippage", "min_matches": 2, "conditions": [
        {"sensor": "slip_rate", "min": 10}, {"sensor": "conveyor_speed", "max": 1.5},
    ]}],
    "pump": [{"fault": "pump_cavitation", "min_matches": 2, "conditions": [
        {"sensor": "vibration", "min": 3}, {"sensor": "flow_rate", "max": 90}, {"sensor": "pressure", "max": 7},
    ]}],
}


def _diagnose(equipment: str, **values: float) -> str:
    row = pd.Series({"equipment_type": equipment, "operating_state": "degradation", **values})
    return RuleBasedDiagnoser(RULES).diagnose(row, True).predicted_fault


def test_obvious_equipment_faults() -> None:
    assert _diagnose("motor", load=90, current=28, rpm=1300) == "motor_overload"
    assert _diagnose("bearing", vibration=6, health_score=50) == "bearing_wear"
    assert _diagnose("conveyor", slip_rate=18, conveyor_speed=1.1) == "conveyor_slippage"
    assert _diagnose("pump", vibration=5, flow_rate=60, pressure=6) == "pump_cavitation"


def test_normal_and_unknown_results() -> None:
    detector = RuleBasedDiagnoser(RULES)
    normal = pd.Series({"equipment_type": "motor", "operating_state": "normal", "load": 55})
    uncertain = pd.Series({"equipment_type": "motor", "operating_state": "degradation", "load": 60, "current": 19, "rpm": 1490})
    assert detector.diagnose(normal, False).predicted_fault == "normal"
    assert detector.diagnose(uncertain, True).predicted_fault == "unknown_fault"

