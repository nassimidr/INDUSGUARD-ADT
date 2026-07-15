from indusguard.digital_twin import MotorSimulator


CONFIG = {
    "normal": {"temperature": 48, "vibration": 1.8, "rpm": 1500, "current": 18, "load": 55},
    "noise": {"temperature": 0, "vibration": 0, "rpm": 0, "current": 0, "load": 0},
}


def test_motor_states_and_overload_dependency() -> None:
    motor = MotorSimulator("M", CONFIG, 1)
    normal = motor.generate_measurement(0)
    overloaded = motor.generate_measurement(0.6, {"conveyor_overload": 1})
    assert motor.state == "degradation"
    assert overloaded["current"] > normal["current"]
    assert overloaded["temperature"] > normal["temperature"]


def test_motor_is_reproducible() -> None:
    first = MotorSimulator("M", CONFIG, 7).generate_measurement(0.5)
    second = MotorSimulator("M", CONFIG, 7).generate_measurement(0.5)
    assert first == second

