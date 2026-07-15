"""Entraîne et évalue les quatre modèles de durée de vie restante."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from indusguard.rul_prediction import RULModelManager
from indusguard.rul_prediction.evaluator import evaluate_rul
from indusguard.rul_prediction.feature_engineering import create_temporal_features
from indusguard.rul_prediction.preprocessing import complete_run_ids, load_rul_data
from indusguard.rul_prediction.risk_assessment import assess_risk
from indusguard.rul_prediction.visualizer import create_rul_plots

LOGGER = logging.getLogger(__name__)


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("Configuration RUL invalide.")
    return config


def prepare_features(data: Any, config: dict[str, Any]) -> Any:
    feature_config = config["feature_engineering"]
    return create_temporal_features(
        data, config["features"], feature_config["rolling_windows"],
        feature_config["slope_window"],
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        config = load_config(root / "configs" / "rul_prediction.yaml")
        data = load_rul_data(root / config["paths"]["dataset"])
        engineered = prepare_features(data, config)
        manager = RULModelManager(config, root); manager.train(engineered)
        mask = manager.evaluation_mask(engineered)
        test = engineered.loc[mask].copy()
        test = test.join(manager.predict(test))
        test["risk_level"] = test["predicted_rul_steps"].map(
            lambda value: assess_risk(value, config["risk_thresholds"])
        )
        metrics = {
            "machine_learning": evaluate_rul(test, "predicted_rul_steps"),
            "baseline": evaluate_rul(test, "baseline_rul_steps"),
            "complete_trajectories": len(complete_run_ids(data)),
            "test_trajectories": int(test["asset_run_id"].nunique()),
            "train_runs": {kind: sorted(values) for kind, values in manager.train_runs.items()},
            "test_runs": {kind: sorted(values) for kind, values in manager.test_runs.items()},
            "feature_importance": {
                kind: model.feature_importances() for kind, model in manager.models.items()
            },
        }
        metrics_path = root / config["paths"]["metrics"]
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        create_rul_plots(test, manager, root / config["paths"]["plots_directory"])
        ml = metrics["machine_learning"]["global"]
        baseline = metrics["baseline"]["global"]
        print("Entraînement RUL terminé")
        print(f"Trajectoires train : {sum(len(v) for v in manager.train_runs.values())}")
        print(f"Trajectoires test : {metrics['test_trajectories']}")
        print(f"MAE baseline : {baseline['mae']:.3f} cycles")
        print(f"MAE Random Forest : {ml['mae']:.3f} cycles")
        print(f"RMSE Random Forest : {ml['rmse']:.3f} cycles")
        print(f"R² Random Forest : {ml['r2']:.3f}")
        print(f"Modèles : {manager.models_directory.relative_to(root)}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
        LOGGER.exception("L'entraînement RUL a échoué : %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())
