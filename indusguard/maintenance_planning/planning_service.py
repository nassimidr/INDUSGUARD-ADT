"""Orchestration complète de la recommandation à la planification."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd

from .cost_estimator import estimate_cost
from .explanations import build_recommendation_explanation, recommendation_confidence
from .maintenance_catalog import MaintenanceCatalog
from .maintenance_window import calculate_window
from .priority_engine import PriorityEngine
from .recommendation_engine import RecommendationEngine
from .resource_manager import ResourceManager
from .scheduler import MaintenanceScheduler
from .spare_parts import SparePartsManager
from .work_order import WorkOrder


class MaintenancePlanningService:
    """Produit recommandations, ordres de travail et planning sans conflit."""

    RECOMMENDATION_COLUMNS = [
        "timestamp", "equipment_id", "equipment_type", "diagnosed_fault",
        "diagnosis_confidence", "severity", "predicted_rul_steps",
        "predicted_rul_hours", "rul_lower_bound", "rul_upper_bound",
        "rul_confidence", "risk_level", "maintenance_strategy",
        "recommended_action", "secondary_actions", "priority", "priority_score",
        "recommended_start", "recommended_deadline", "maximum_delay_hours",
        "estimated_duration_hours", "required_skills", "required_parts",
        "shutdown_required", "inspection_required", "safety_instructions",
        "estimated_labor_cost", "estimated_parts_cost", "estimated_downtime_cost",
        "estimated_total_cost", "recommendation_confidence",
        "recommendation_explanation", "priority_components",
        "delayed_intervention_risk_cost", "diagnosis_source",
    ]

    def __init__(self, config: dict[str, Any], resources: dict[str, Any]) -> None:
        self.config = config
        self.resources_config = resources
        self.catalog = MaintenanceCatalog(config["catalog"])
        self.recommendation_engine = RecommendationEngine(
            self.catalog, config["confidence_threshold"]
        )
        self.priority_engine = PriorityEngine(config)
        self.resource_manager = ResourceManager(resources)
        self.parts_manager = SparePartsManager(resources)
        self.scheduler = MaintenanceScheduler(resources, self.parts_manager)

    def plan(
        self, equipment: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Analyse chaque actif et planifie les ordres triés par criticité."""
        reference = pd.to_datetime(equipment["timestamp"]).max().to_pydatetime()
        recommendations: list[dict[str, object]] = []
        orders: list[WorkOrder] = []
        for sequence, (_, row) in enumerate(equipment.iterrows(), start=1):
            definition = self.catalog.get(str(row["diagnosed_fault"]))
            recommendation = self.recommendation_engine.recommend(row)
            priority = self.priority_engine.calculate(row, recommendation.shutdown_required)
            window = calculate_window(row, self.config, reference)
            resources = self.resource_manager.select(str(row["equipment_type"]), definition.skills)
            parts = self.parts_manager.select(definition.required_parts, definition.optional_parts)
            costs = estimate_cost(
                definition.duration_hours, resources.technician_count,
                resources.average_hourly_cost, self.parts_manager.cost(definition.required_parts),
                recommendation.shutdown_required, self.resources_config, priority.score,
            )
            confidence = recommendation_confidence(row, recommendation.consistency)
            safety = self.resource_manager.safety_instructions(str(row["equipment_type"]))
            record = {
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat(),
                "equipment_id": row["equipment_id"], "equipment_type": row["equipment_type"],
                "diagnosed_fault": row["diagnosed_fault"],
                "diagnosis_confidence": round(float(row["diagnosis_confidence"]), 4),
                "severity": row["severity"],
                "predicted_rul_steps": row["predicted_rul_steps"],
                "predicted_rul_hours": row["predicted_rul_hours"],
                "rul_lower_bound": row["rul_lower_bound"], "rul_upper_bound": row["rul_upper_bound"],
                "rul_confidence": row["prediction_confidence"], "risk_level": row["risk_level"],
                "maintenance_strategy": recommendation.strategy,
                "recommended_action": recommendation.action,
                "secondary_actions": " | ".join(recommendation.secondary_actions),
                "priority": priority.priority, "priority_score": priority.score,
                "recommended_start": window.start.isoformat(),
                "recommended_deadline": window.deadline.isoformat(),
                "maximum_delay_hours": window.maximum_delay_hours,
                "estimated_duration_hours": definition.duration_hours,
                "required_skills": ",".join(resources.skills),
                "required_parts": ",".join(parts.required_parts),
                "shutdown_required": recommendation.shutdown_required,
                "inspection_required": recommendation.inspection_required,
                "safety_instructions": " | ".join(safety),
                "estimated_labor_cost": costs.labor_cost,
                "estimated_parts_cost": costs.parts_cost,
                "estimated_downtime_cost": costs.downtime_cost,
                "estimated_total_cost": costs.total_cost,
                "recommendation_confidence": confidence,
                "recommendation_explanation": build_recommendation_explanation(
                    row, recommendation.action, priority.priority, confidence
                ),
                "priority_components": json.dumps(priority.components, ensure_ascii=False),
                "delayed_intervention_risk_cost": costs.delayed_risk_cost,
                "diagnosis_source": row["diagnosis_source"],
            }
            recommendations.append(record)
            status = "urgent" if priority.priority in {"urgent", "critical"} else "proposed"
            orders.append(WorkOrder(
                work_order_id=f"WO-{reference:%Y%m%d}-{sequence:03d}",
                equipment_id=str(row["equipment_id"]), equipment_type=str(row["equipment_type"]),
                diagnosed_fault=str(row["diagnosed_fault"]),
                maintenance_strategy=recommendation.strategy,
                priority=priority.priority, priority_score=priority.score,
                recommended_start=window.start, recommended_deadline=window.deadline,
                estimated_duration_hours=definition.duration_hours,
                required_skills=resources.skills, required_parts=parts.required_parts,
                shutdown_required=recommendation.shutdown_required,
                estimated_total_cost=costs.total_cost, status=status,
            ))
        scheduled_orders, schedule = self.scheduler.schedule(orders)
        recommendation_frame = pd.DataFrame(recommendations, columns=self.RECOMMENDATION_COLUMNS)
        work_order_frame = pd.DataFrame([order.to_record() for order in scheduled_orders])
        schedule_frame = pd.DataFrame(schedule)
        return recommendation_frame, work_order_frame, schedule_frame

