from spade.agent import Agent
from indusguard.multi_agent.agents.anomaly_detection_agent import AnomalyDetectionAgent
def test_anomaly_is_spade_agent(): assert issubclass(AnomalyDetectionAgent,Agent)
