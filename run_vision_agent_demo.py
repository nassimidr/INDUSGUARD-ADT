"""Real XMPP demonstration: SupervisorAgent requests an image analysis from VisionAgent."""
from __future__ import annotations

import asyncio
import json

import spade

from indusguard.multi_agent.adapters.persistence_adapter import PersistenceAdapter
from indusguard.multi_agent.agents import AlertAgent, HistorianAgent, SupervisorAgent, VisionAgent
from indusguard.multi_agent.config import load_multi_agent_config
from indusguard.multi_agent.metrics import MetricsCollector


async def main():
    config = load_multi_agent_config(); metrics = MetricsCollector()
    persistence = PersistenceAdapter(config.root / "outputs/vision/agent_demo")
    common = {"config": config, "metrics": metrics, "persistence": persistence}
    agents = [HistorianAgent(**common), AlertAgent(**common), SupervisorAgent(**common), VisionAgent(**common)]
    try:
        for agent in agents:
            await agent.start(auto_register=config.auto_register)
        supervisor = agents[2]
        request = await supervisor.send_fipa(
            "vision", "vision.analysis.request",
            {"image_path": "data/vision/demo/sample_belt_misalignment.png", "equipment_id": "CONVEYOR-001", "camera_id": "camera_01"},
            "request", "industrial-vision", equipment_id="CONVEYOR-001", equipment_type="conveyor",
        )
        deadline = asyncio.get_running_loop().time() + 30
        while supervisor.case_states.get(request.trace_id) != "vision_detected":
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError("VisionAgent did not publish a detection within 30 seconds.")
            await asyncio.sleep(0.1)
        print(json.dumps({
            "status": "VISION_XMPP_OK", "trace_id": request.trace_id,
            "equipment_id": request.equipment_id, "state": supervisor.case_states[request.trace_id],
            "vision_detections_produced": metrics.counters["vision_detections_produced"],
        }, indent=2))
    finally:
        for agent in reversed(agents):
            if agent.is_alive(): await agent.stop()
        persistence.close()


if __name__ == "__main__":
    spade.run(main(), embedded_xmpp_server=True)
