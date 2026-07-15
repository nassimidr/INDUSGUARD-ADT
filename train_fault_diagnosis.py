"""Entraîne, évalue et sauvegarde les modèles de diagnostic de phase 3."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from indusguard.anomaly_detection import ModelManager as AnomalyModelManager
from indusguard.anomaly_detection import ThresholdDetector
from indusguard.fault_diagnosis import DiagnosisService, FaultModelManager, RuleBasedDiagnoser
from indusguard.fault_diagnosis.evaluator import evaluate_diagnosis
from indusguard.fault_diagnosis.preprocessing import load_diagnosis_data
from indusguard.fault_diagnosis.visualizer import create_diagnosis_plots

LOGGER = logging.getLogger(__name__)


def load_yaml(path: Path) -> dict[str, Any]:
    """Charge une configuration YAML sous forme de dictionnaire."""
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError(f"Configuration invalide : {path}")
    return config


def anomaly_predictions(data: Any, anomaly_config: dict[str, Any], root: Path) -> Any:
    """Réutilise les deux détecteurs déjà entraînés en phase 2."""
    threshold = ThresholdDetector(anomaly_config["thresholds"]).predict(data)
    manager = AnomalyModelManager(anomaly_config, root)
    manager.load()
    return threshold.join(manager.predict(data))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        config = load_yaml(root / "configs" / "fault_diagnosis.yaml")
        anomaly_config = load_yaml(root / config["paths"]["anomaly_config"])
        data = load_diagnosis_data(root / config["paths"]["data"])
        anomaly = anomaly_predictions(data, anomaly_config, root)
        manager = FaultModelManager(config, root); manager.train(data)
        rules = RuleBasedDiagnoser(
            config["rules"], config["confidence"]["minimum_rule"]
        )
        service = DiagnosisService(
            rules, manager, config["confidence"]["minimum_final"]
        )
        diagnosis = service.diagnose(data, anomaly)
        destination = root / config["paths"]["predictions"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        diagnosis.to_csv(destination, index=False, encoding="utf-8")
        mask = manager.evaluation_mask(data)
        metrics = {
            "rule_based": evaluate_diagnosis(diagnosis, "rule_based_fault", mask),
            "machine_learning": evaluate_diagnosis(diagnosis, "ml_predicted_fault", mask),
            "hybrid": evaluate_diagnosis(diagnosis, "final_diagnosis", mask),
            "rare_classes": {
                name: int(count) for name, count in data["failure_type"].value_counts().items()
                if int(count) < 10
            },
            "evaluation_rows": int(mask.sum()),
        }
        metrics_path = root / config["paths"]["metrics"]
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        create_diagnosis_plots(diagnosis.loc[mask], root / config["paths"]["plots_directory"])
        summary = metrics["hybrid"]["global"]
        print("Entraînement du diagnostic terminé")
        print(f"Mesures d'évaluation : {metrics['evaluation_rows']}")
        print(f"Accuracy hybride : {summary['accuracy']:.3f}")
        print(f"F1 macro hybride : {summary['f1_macro']:.3f}")
        print(f"Modèles : {manager.models_directory.relative_to(root)}")
        print(f"Diagnostic : {destination.relative_to(root)}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
        LOGGER.exception("L'entraînement du diagnostic a échoué : %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

