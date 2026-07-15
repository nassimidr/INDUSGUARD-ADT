"""Adaptateur Phase 5 produisant la recommandation avant Contract Net."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from indusguard.maintenance_planning.planning_service import MaintenancePlanningService


class MaintenanceAdapter:
    def __init__(self, root: str | Path) -> None:
        self.root=Path(root)
        self.config=yaml.safe_load((self.root/"configs/maintenance_planning.yaml").read_text(encoding="utf-8"))
        self.resources=yaml.safe_load((self.root/"configs/maintenance_resources.yaml").read_text(encoding="utf-8"))

    def recommend(self, measurement: dict[str,Any], diagnosis: dict[str,Any], rul: dict[str,Any]) -> dict[str,Any]:
        row={
            "timestamp":measurement["timestamp"], "equipment_id":measurement["equipment_id"],
            "equipment_type":measurement["equipment_type"], "diagnosed_fault":diagnosis["final_diagnosis"],
            "diagnosis_confidence":diagnosis["final_confidence"], "severity":diagnosis["severity"],
            **rul, "diagnosis_source":"phase_6_hybrid",
        }
        recommendations,_,_=MaintenancePlanningService(self.config,self.resources).plan(pd.DataFrame([row]))
        result=recommendations.iloc[0]
        split=lambda value: [x.strip() for x in str(value).split(",") if x.strip()]
        return {
            "maintenance_strategy":str(result["maintenance_strategy"]),
            "recommended_action":str(result["recommended_action"]),
            "secondary_actions":[x.strip() for x in str(result["secondary_actions"]).split("|") if x.strip()],
            "priority":str(result["priority"]), "priority_score":float(result["priority_score"]),
            "recommended_start":str(result["recommended_start"]), "recommended_deadline":str(result["recommended_deadline"]),
            "estimated_duration_hours":float(result["estimated_duration_hours"]),
            "required_skills":split(result["required_skills"]), "required_parts":split(result["required_parts"]),
            "shutdown_required":bool(result["shutdown_required"]), "estimated_total_cost":float(result["estimated_total_cost"]),
            "recommendation_confidence":float(result["recommendation_confidence"]),
            "recommendation_explanation":str(result["recommendation_explanation"]),
        }
