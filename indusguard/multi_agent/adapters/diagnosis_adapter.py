"""Adaptateur Phase 3; diagnostic hybride sans réentraînement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from indusguard.fault_diagnosis.diagnosis_service import DiagnosisService
from indusguard.fault_diagnosis.model_manager import FaultModelManager
from indusguard.fault_diagnosis.rule_based_diagnoser import RuleBasedDiagnoser


class _SingleRowFaultModels:
    def __init__(self, manager: FaultModelManager) -> None: self.manager=manager
    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        result=pd.DataFrame(index=data.index,columns=["ml_predicted_fault","ml_confidence"])
        for kind in data["equipment_type"].unique():
            mask=data["equipment_type"]==kind
            predictions,confidence=self.manager.models[str(kind)].predict(data.loc[mask])
            result.loc[mask,"ml_predicted_fault"]=predictions; result.loc[mask,"ml_confidence"]=confidence
        result["ml_confidence"]=result["ml_confidence"].astype(float); return result


class DiagnosisAdapter:
    def __init__(self, root: str | Path) -> None:
        self.root=Path(root); config=yaml.safe_load((self.root/"configs/fault_diagnosis.yaml").read_text(encoding="utf-8"))
        manager=FaultModelManager(config,self.root); manager.load()
        rules=RuleBasedDiagnoser(config["rules"],config["confidence"]["minimum_rule"])
        self.service=DiagnosisService(rules,_SingleRowFaultModels(manager),config["confidence"]["minimum_final"])

    def diagnose(self, measurement: dict[str, Any], anomaly: dict[str, Any]) -> dict[str, Any]:
        frame=pd.DataFrame([measurement]); anomaly_frame=pd.DataFrame([anomaly])
        result=self.service.diagnose(frame,anomaly_frame).iloc[0]
        return {
            "rule_based_fault":str(result["rule_based_fault"]),
            "rule_based_confidence":float(result["rule_based_confidence"]),
            "ml_predicted_fault":str(result["ml_predicted_fault"]),
            "ml_confidence":float(result["ml_confidence"]),
            "final_diagnosis":str(result["final_diagnosis"]),
            "final_confidence":float(result["final_confidence"]),
            "severity":str(result["severity"]),
            "responsible_sensors":str(result["responsible_sensors"]),
            "diagnosis_explanation":str(result["diagnosis_explanation"]),
        }
