from spade.agent import Agent
from indusguard.multi_agent.agents.maintenance_agent import MaintenanceAgent
def test_maintenance_is_spade_agent(): assert issubclass(MaintenanceAgent,Agent)
