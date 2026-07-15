import pandas as pd
from indusguard.multi_agent.adapters.rul_adapter import RULAdapter
def test_rul_history_is_separate():
    rows=pd.read_csv("data/synthetic/industrial_line_scenario.csv");a=RULAdapter(".");a.predict(rows.iloc[0].to_dict());a.predict(rows.iloc[1].to_dict());assert len(a.histories)==2 and all(len(v)==1 for v in a.histories.values())
