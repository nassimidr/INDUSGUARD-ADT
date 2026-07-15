import json,pytest
from indusguard.multi_agent.schemas import AgentMessage

def sample(**overrides):
    values=dict(message_type="sensor.measurement",sender_agent="sensor@localhost",target_agent="anomaly@localhost",payload={},equipment_id="MOTOR-001",equipment_type="motor")
    values.update(overrides);return AgentMessage(**values)
def test_round_trip_and_ids(): m=sample();m.validate();assert AgentMessage.from_json(m.to_json()).trace_id==m.trace_id
def test_invalid_uuid_rejected():
    with pytest.raises(ValueError): sample(message_id="bad").validate()
def test_unknown_equipment_type_rejected():
    with pytest.raises(ValueError): sample(equipment_type="turbine").validate()
def test_size_limit():
    with pytest.raises(ValueError): sample(payload={"x":"a"*500}).validate(100)
