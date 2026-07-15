from spade.agent import Agent
from indusguard.multi_agent.agents.supervisor_agent import SupervisorAgent
def test_supervisor_is_spade_agent(): assert issubclass(SupervisorAgent,Agent)
