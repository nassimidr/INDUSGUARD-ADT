"""Génère recommandations, ordres de travail et planning de maintenance."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from indusguard.maintenance_planning.evaluator import maintenance_metrics, validate_plan
from indusguard.maintenance_planning.planning_service import MaintenancePlanningService
from indusguard.maintenance_planning.preprocessing import (
    ANOMALY_REQUIRED, DIAGNOSIS_REQUIRED, RUL_REQUIRED, load_csv,
    merge_maintenance_sources,
)
from indusguard.maintenance_planning.visualizer import create_maintenance_plots

LOGGER = logging.getLogger(__name__)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError(f"Configuration invalide : {path}")
    return config


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        config = load_yaml(root / "configs" / "maintenance_planning.yaml")
        resources = load_yaml(root / config["paths"]["resources"])
        diagnosis = load_csv(root / config["paths"]["diagnosis"], DIAGNOSIS_REQUIRED)
        rul = load_csv(root / config["paths"]["rul"], RUL_REQUIRED)
        anomalies = load_csv(root / config["paths"]["anomalies"], ANOMALY_REQUIRED)
        equipment = merge_maintenance_sources(diagnosis, rul, anomalies)
        service = MaintenancePlanningService(config, resources)
        recommendations, orders, schedule = service.plan(equipment)
        validate_plan(recommendations, orders, schedule)
        for key, frame in [
            ("recommendations", recommendations), ("work_orders", orders), ("schedule", schedule)
        ]:
            path = root / config["paths"][key]
            path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(path, index=False, encoding="utf-8")
        metrics = maintenance_metrics(
            recommendations, orders, schedule,
            service.scheduler.conflicts_detected, service.scheduler.conflicts_resolved,
        )
        metrics_path = root / config["paths"]["metrics"]
        metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        create_maintenance_plots(
            recommendations, orders, schedule, root / config["paths"]["plots_directory"]
        )
        print("Plan de maintenance généré")
        print(f"Équipements analysés : {len(recommendations)}")
        for strategy, count in recommendations["maintenance_strategy"].value_counts().items():
            print(f"{strategy} : {count}")
        print("\nPriorités :")
        for priority, count in recommendations["priority"].value_counts().items():
            print(f"{priority} : {count}")
        print(f"\nOrdres planifiés : {metrics['scheduled_orders']}")
        print(f"Ordres bloqués : {metrics['blocked_orders']}")
        print(f"Coût total estimé : {metrics['total_estimated_cost']:.2f}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
        LOGGER.exception("La génération du plan a échoué : %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())

