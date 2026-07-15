from indusguard.multi_agent.message_factory import MessageFactory

def test_factory_fipa_metadata_and_json():
    e,m=MessageFactory().build(sender="sensor@localhost",target="anomaly@localhost",message_type="sensor.measurement",payload={},performative="inform",ontology="sensor-monitoring")
    assert m.get_metadata("trace-id")==e.trace_id and m.get_metadata("language")=="json-utf8"
def test_parent_preserves_trace_correlation_conversation():
    f=MessageFactory();p,_=f.build(sender="sensor@localhost",target="anomaly@localhost",message_type="sensor.measurement",payload={},performative="inform",ontology="sensor-monitoring")
    c,_=f.build(sender="anomaly@localhost",target="diagnosis@localhost",message_type="diagnosis.request",payload={},performative="request",ontology="fault-diagnosis",parent=p)
    assert (c.trace_id,c.correlation_id,c.conversation_id)==(p.trace_id,p.correlation_id,p.conversation_id)
def test_template_routes_message_type():
    f=MessageFactory();_,message=f.build(sender="sensor@localhost",target="anomaly@localhost",message_type="sensor.measurement",payload={},performative="inform",ontology="sensor-monitoring")
    assert f.template(message_type="sensor.measurement",performative="inform").match(message)
