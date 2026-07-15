"""Prédit la RUL des trajectoires complètes ou en cours."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from indusguard.rul_prediction import RULModelManager
from indusguard.rul_prediction.prediction_service import RULPredictionService
from indusguard.rul_prediction.preprocessing import incomplete_run_ids, load_rul_data
from train_rul_models import load_config, prepare_features

LOGGER = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Dataset de trajectoires à analyser")
    parser.add_argument("--output", type=Path, help="CSV de prédictions à produire")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        config = load_config(root / "configs" / "rul_prediction.yaml")
        source = args.input or root / config["paths"]["dataset"]
        destination = args.output or root / config["paths"]["predictions"]
        data = load_rul_data(source); engineered = prepare_features(data, config)
        manager = RULModelManager(config, root); manager.load()
        predictions = RULPredictionService(manager, config).predict(engineered)
        destination.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(destination, index=False, encoding="utf-8")
        incomplete = incomplete_run_ids(data)
        current = predictions[predictions["asset_run_id"].isin(incomplete)]
        latest = current.sort_values("cycle").groupby("asset_run_id").tail(1)
        print("Prédiction RUL terminée")
        print(f"Équipements analysés : {len(latest)}")
        for risk in ["low", "medium", "high", "critical"]:
            print(f"Risque {risk} : {int((latest['risk_level'] == risk).sum())}")
        priorities = latest.sort_values("predicted_rul_steps").head(10)
        print("\nÉquipements prioritaires :")
        for _, row in priorities.iterrows():
            print(f"\n{row['asset_run_id']}")
            print(f"RUL estimée : {row['predicted_rul_steps']:.1f} cycles")
            print(f"Risque : {row['risk_level']}")
            print(f"Intervalle : {row['rul_lower_bound']:.1f} à {row['rul_upper_bound']:.1f} cycles")
        print(f"\nFichier : {destination}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
        LOGGER.exception("La prédiction RUL a échoué : %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())
