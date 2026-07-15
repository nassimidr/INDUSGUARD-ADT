"""Applique les modèles sauvegardés à un nouveau CSV de mesures."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from indusguard.anomaly_detection import ModelManager, ThresholdDetector, load_sensor_data
from train_anomaly_detector import load_config, prediction_frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Nouveau CSV (dataset configuré par défaut)")
    parser.add_argument("--output", type=Path, help="CSV de sortie optionnel")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        config = load_config(root / "configs" / "anomaly_detection.yaml")
        source = args.input or root / config["paths"]["data"]
        destination = args.output or root / config["paths"]["predictions"]
        data = load_sensor_data(source)
        threshold = ThresholdDetector(config["thresholds"]).predict(data)
        manager = ModelManager(config, root); manager.load()
        predictions = prediction_frame(data, threshold, manager.predict(data))
        destination.parent.mkdir(parents=True, exist_ok=True); predictions.to_csv(destination, index=False)
        important = predictions[
            predictions["threshold_prediction"] | predictions["isolation_forest_prediction"]
        ].nlargest(10, "anomaly_score")
        print(f"Prédiction terminée : {len(predictions)} mesures, {len(important)} anomalies importantes affichées")
        if not important.empty:
            print(important[["timestamp", "equipment_id", "anomaly_score", "anomaly_explanation"]].to_string(index=False))
        print(f"Fichier : {destination}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
        logging.exception("La prédiction a échoué : %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())
