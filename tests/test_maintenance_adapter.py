import pandas as pd
from indusguard.multi_agent.adapters.maintenance_adapter import MaintenanceAdapter
def test_maintenance_recommendation_fields():
    row=pd.read_csv("data/synthetic/industrial_line_scenario.csv").iloc[0].to_dict();d={"final_diagnosis":"normal","final_confidence":1,"severity":"none"};r={"predicted_rul_steps":100,"predicted_rul_hours":50,"rul_lower_bound":90,"rul_upper_bound":110,"prediction_confidence":.9,"risk_level":"low"};assert "required_skills" in MaintenanceAdapter(".").recommend(row,d,r)
