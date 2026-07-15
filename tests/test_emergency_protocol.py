from indusguard.multi_agent.protocols.emergency_protocol import is_critical
def test_critical_conditions(): assert is_critical(strategy="emergency_shutdown") and is_critical(diagnosis="cascade_failure")
def test_normal_not_critical(): assert not is_critical(predicted_rul_steps=100)
