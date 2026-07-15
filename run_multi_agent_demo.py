"""Démonstration XMPP: SensorAgent → AnomalyDetectionAgent → SupervisorAgent."""
from types import SimpleNamespace
import spade
from run_multi_agent_system import main

if __name__=="__main__":
    args=SimpleNamespace(scenario="normal",mode="embedded",speed=1000,max_measurements=1,equipment_id="MOTOR-001")
    spade.run(main(args),embedded_xmpp_server=True)
