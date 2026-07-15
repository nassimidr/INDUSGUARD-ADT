import pandas as pd
from indusguard.multi_agent.adapters import AnomalyAdapter,DiagnosisAdapter,RULAdapter,MaintenanceAdapter
def test_business_chain_without_xmpp_server():
    row=pd.read_csv("data/synthetic/industrial_line_scenario.csv").iloc[0].to_dict();a=AnomalyAdapter(".").analyze(row);d=DiagnosisAdapter(".").diagnose(row,a);r=RULAdapter(".").predict(row);m=MaintenanceAdapter(".").recommend(row,d,r);assert m["maintenance_strategy"]=="monitor"
