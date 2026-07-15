from spade.agent import Agent
from indusguard.multi_agent.agents.resource_agent import ResourceAgent
def test_resource_is_spade_agent(): assert issubclass(ResourceAgent,Agent)
