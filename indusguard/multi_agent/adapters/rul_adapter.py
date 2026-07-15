"""Adaptateur Phase 4 avec historiques causaux séparés et bornés."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from indusguard.rul_prediction.feature_engineering import create_temporal_features
from indusguard.rul_prediction.model_manager import RULModelManager
from indusguard.rul_prediction.prediction_service import RULPredictionService


class _SingleTypeRULModels:
    def __init__(self, manager: RULModelManager) -> None:
        self.manager=manager; self.models=manager.models
    def predict(self,data:pd.DataFrame)->pd.DataFrame:
        import numpy as np
        result=pd.DataFrame(index=data.index)
        for column in ["predicted_rul_steps","rul_lower_bound","rul_upper_bound","baseline_rul_steps"]: result[column]=np.nan
        uncertainty=self.manager.config["uncertainty"]
        for kind in data["equipment_type"].unique():
            mask=data["equipment_type"]==kind; model=self.models[str(kind)]
            prediction,lower,upper=model.predict_with_interval(data.loc[mask],uncertainty["lower_percentile"],uncertainty["upper_percentile"])
            result.loc[mask,"predicted_rul_steps"]=prediction;result.loc[mask,"rul_lower_bound"]=lower;result.loc[mask,"rul_upper_bound"]=upper
        return result
    def top_features(self,kind:str,count:int=3): return self.manager.top_features(kind,count)


class RULAdapter:
    def __init__(self, root: str | Path, maximum_history: int = 100) -> None:
        self.root=Path(root); self.config=yaml.safe_load((self.root/"configs/rul_prediction.yaml").read_text(encoding="utf-8"))
        manager=RULModelManager(self.config,self.root); manager.load(); self.service=RULPredictionService(_SingleTypeRULModels(manager),self.config)
        self.histories: defaultdict[str, deque[dict[str,Any]]] = defaultdict(lambda: deque(maxlen=maximum_history))

    def predict(self, measurement: dict[str, Any]) -> dict[str, Any]:
        equipment_id=str(measurement["equipment_id"]); history=self.histories[equipment_id]
        row=dict(measurement); row.setdefault("cycle",len(history)); row["asset_run_id"]=equipment_id.lower().replace("-","_")
        row.setdefault("failure_type","unknown_fault"); row.setdefault("timestamp",pd.Timestamp.utcnow().isoformat())
        for sensors in self.config["features"].values():
            for sensor in sensors: row.setdefault(sensor,float("nan"))
        history.append(row)
        frame=pd.DataFrame(list(history))
        engineered=create_temporal_features(frame,self.config["features"],self.config["feature_engineering"]["rolling_windows"],self.config["feature_engineering"]["slope_window"])
        result=self.service.predict(engineered.tail(1)).iloc[0]
        return {
            "predicted_rul_steps":float(result["predicted_rul_steps"]),
            "predicted_rul_hours":float(result["predicted_rul_hours"]),
            "rul_lower_bound":float(result["rul_lower_bound"]),
            "rul_upper_bound":float(result["rul_upper_bound"]),
            "prediction_confidence":float(result["prediction_confidence"]),
            "risk_level":str(result["risk_level"]),
            "responsible_features":str(result["responsible_features"]),
            "rul_explanation":str(result["rul_explanation"]),
        }
