import pandas as pd
from indusguard.multi_agent.adapters import AnomalyAdapter,DiagnosisAdapter
def test_diagnosis_fields():
    row=pd.read_csv("data/synthetic/industrial_line_scenario.csv").iloc[0].to_dict();a=AnomalyAdapter(".").analyze(row);r=DiagnosisAdapter(".").diagnose(row,a);assert r["final_diagnosis"]=="normal"
