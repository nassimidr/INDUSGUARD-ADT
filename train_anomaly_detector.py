"""Entraîne et évalue les détecteurs d'anomalies de la phase 2."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from indusguard.anomaly_detection import ModelManager, ThresholdDetector, evaluate_predictions, load_sensor_data
from indusguard.anomaly_detection.visualizer import create_detection_plots


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("Configuration de détection invalide.")
    return config


def prediction_frame(data: pd.DataFrame, threshold: pd.DataFrame, forest: pd.DataFrame) -> pd.DataFrame:
    """Assemble le format stable demandé pour les prédictions."""
    columns = ["timestamp", "equipment_id", "equipment_type", "operating_state", "is_anomaly"]
    return pd.concat([data[columns], threshold, forest], axis=1)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        config = load_config(root / "configs" / "anomaly_detection.yaml")
        data = load_sensor_data(root / config["paths"]["data"])
        threshold = ThresholdDetector(config["thresholds"]).predict(data)
        manager = ModelManager(config, root); manager.train(data)
        forest = manager.predict(data)
        predictions = prediction_frame(data, threshold, forest)
        destination = root / config["paths"]["predictions"]
        destination.parent.mkdir(parents=True, exist_ok=True); predictions.to_csv(destination, index=False)
        evaluation_data = pd.concat([data, threshold, forest], axis=1)
        mask = manager.evaluation_mask(data)
        metrics = {
            "threshold": evaluate_predictions(evaluation_data, "threshold_prediction", mask),
            "isolation_forest": evaluate_predictions(evaluation_data, "isolation_forest_prediction", mask),
        }
        metrics_path = destination.with_name("metrics.json")
        metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        create_detection_plots(evaluation_data.loc[mask], root / config["paths"]["plots_directory"])
        print("Entraînement terminé")
        print(json.dumps(metrics["isolation_forest"]["global"], indent=2))
        print(f"Prédictions : {destination.relative_to(root)}")
        print(f"Modèles : {manager.models_directory.relative_to(root)}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
        logging.exception("L'entraînement a échoué : %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())

