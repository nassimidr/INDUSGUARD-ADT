import pytest
from indusguard.multi_agent.message_factory import MessageFactory
from indusguard.multi_agent.message_validator import MessageValidator

def make():
    e,m=MessageFactory().build(sender="sensor@localhost",target="anomaly@localhost",message_type="sensor.measurement",payload={},performative="inform",ontology="sensor-monitoring");m.sender="sensor@localhost";return e,m
def test_valid_message(): e,m=make();assert MessageValidator({"sensor@localhost"}).validate(m).message_id==e.message_id
def test_unknown_sender_rejected():
    _,m=make()
    with pytest.raises(ValueError): MessageValidator({"other@localhost"}).validate(m)
