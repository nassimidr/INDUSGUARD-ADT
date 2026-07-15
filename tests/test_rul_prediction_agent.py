from spade.agent import Agent
from indusguard.multi_agent.agents.rul_prediction_agent import RULPredictionAgent
def test_rul_is_spade_agent(): assert issubclass(RULPredictionAgent,Agent)
