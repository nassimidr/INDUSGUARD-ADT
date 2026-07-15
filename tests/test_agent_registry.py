import pytest
from indusguard.multi_agent.agent_registry import AgentRegistry
def test_register_and_update(): r=AgentRegistry();r.register("sensor","sensor@localhost");r.update("sensor","ready");assert r.get("sensor@localhost").status=="ready"
def test_duplicate_rejected():
    r=AgentRegistry();r.register("sensor","sensor@localhost")
    with pytest.raises(ValueError):r.register("sensor","other@localhost")
