from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from indusguard.multi_agent.agents import VisionAgent
from indusguard.multi_agent.adapters.persistence_adapter import PersistenceAdapter
from indusguard.multi_agent.config import load_multi_agent_config
from indusguard.multi_agent.message_factory import MessageFactory
from indusguard.multi_agent.metrics import MetricsCollector
from indusguard.multi_agent.schemas import AgentMessage
from indusguard.vision.schemas import VisionInferenceRequest
from indusguard.vision.service import VisionService
from tests.vision_helpers import fake_detector, make_image, temporary_vision_config


def test_vision_agent_is_registered_spade_agent(tmp_path):
    config = load_multi_agent_config()
    agent = VisionAgent(config=config, metrics=MetricsCollector(), persistence=PersistenceAdapter(tmp_path))
    assert agent.agent_name == "vision" and str(agent.jid).startswith("vision@localhost")


def test_fipa_factory_preserves_vision_trace_and_equipment():
    trace_id = str(uuid4())
    parent = AgentMessage("vision.analysis.request", "supervisor@localhost", "vision@localhost", {},
                          equipment_id="CONVEYOR-001", equipment_type="conveyor", trace_id=trace_id)
    envelope, message = MessageFactory().build(
        sender="vision@localhost", target="supervisor@localhost", message_type="vision.detection",
        payload={"defect_type": "obstacle"}, performative="inform", ontology="industrial-vision", parent=parent,
    )
    assert envelope.trace_id == trace_id and envelope.equipment_id == "CONVEYOR-001"
    assert message.get_metadata("ontology") == "industrial-vision"


@pytest.mark.asyncio
async def test_vision_agent_processes_request_and_publishes_detection(tmp_path):
    vision_config = temporary_vision_config(tmp_path)
    image = make_image(tmp_path / "demo" / "agent.png")
    detector, _ = fake_detector(vision_config)
    service = VisionService(vision_config, detector)
    agent = VisionAgent(config=load_multi_agent_config(), metrics=MetricsCollector(),
                        persistence=PersistenceAdapter(tmp_path / "events"), service=service)
    agent.send_fipa = AsyncMock(); agent.emit_historian = AsyncMock()
    trace_id = str(uuid4())
    envelope = AgentMessage(
        "vision.analysis.request", "supervisor@localhost", "vision@localhost",
        VisionInferenceRequest(image_path=str(image), equipment_id="CONVEYOR-001", camera_id="camera_01").model_dump(),
        equipment_id="CONVEYOR-001", equipment_type="conveyor", trace_id=trace_id,
    )
    await agent.process(envelope, None)
    assert any(call.args[1] == "vision.detection" for call in agent.send_fipa.await_args_list)
    payload = next(call.args[2] for call in agent.send_fipa.await_args_list if call.args[1] == "vision.detection")
    assert payload["trace_id"] == trace_id and payload["equipment_id"] == "CONVEYOR-001"
