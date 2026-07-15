from spade.agent import Agent
from indusguard.multi_agent.agents.fault_diagnosis_agent import FaultDiagnosisAgent
def test_diagnosis_is_spade_agent(): assert issubclass(FaultDiagnosisAgent,Agent)
