from indusguard.digital_twin import PumpSimulator


CONFIG = {
    "normal": {"temperature": 46, "vibration": 1.6, "current": 14, "pressure": 5, "flow_rate": 120},
    "noise": {"temperature": 0, "vibration": 0, "current": 0, "pressure": 0, "flow_rate": 0},
}


def test_pump_anomaly_reduces_flow_and_increases_pressure() -> None:
    pump = PumpSimulator("P", CONFIG, 1)
    normal = pump.generate_measurement(0)
    critical = pump.generate_measurement(1)
    assert critical["flow_rate"] < normal["flow_rate"]
    assert critical["pressure"] > normal["pressure"]
    assert pump.state == "critical"

