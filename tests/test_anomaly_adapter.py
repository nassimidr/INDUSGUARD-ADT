import pandas as pd
from indusguard.multi_agent.adapters.anomaly_adapter import AnomalyAdapter
def test_normal_measurement(): r=AnomalyAdapter(".").analyze(pd.read_csv("data/synthetic/industrial_line_scenario.csv").iloc[0].to_dict());assert set(["is_anomaly","anomaly_score","detected_sensors"])<=set(r)
