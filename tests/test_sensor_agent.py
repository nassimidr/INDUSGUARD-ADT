from spade.agent import Agent
from indusguard.multi_agent.agents.sensor_agent import SensorAgent
def test_sensor_is_spade_agent(): assert issubclass(SensorAgent,Agent)
