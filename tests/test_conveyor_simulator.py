from indusguard.digital_twin import ConveyorSimulator


CONFIG = {
    "normal": {"temperature": 43, "vibration": 1.5, "load": 45, "conveyor_speed": 1.8, "slip_rate": 1.5},
    "noise": {"temperature": 0, "vibration": 0, "load": 0, "conveyor_speed": 0, "slip_rate": 0},
}


def test_conveyor_follows_motor_and_overload() -> None:
    conveyor = ConveyorSimulator("C", CONFIG, 1)
    normal = conveyor.generate_measurement(0)
    faulty = conveyor.generate_measurement(0.8, {"overload": 1, "motor_speed_ratio": 0.8})
    assert conveyor.state == "critical"
    assert faulty["conveyor_speed"] < normal["conveyor_speed"]
    assert faulty["load"] > normal["load"]

