"""Diagnostique les causes probables dans un nouveau fichier de mesures."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from indusguard.fault_diagnosis import DiagnosisService, FaultModelManager, RuleBasedDiagnoser
from indusguard.fault_diagnosis.preprocessing import load_diagnosis_data
from train_fault_diagnosis import anomaly_predictions, load_yaml

LOGGER = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="CSV industriel à diagnostiquer")
    parser.add_argument("--output", type=Path, help="CSV de diagnostic à produire")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        config = load_yaml(root / "configs" / "fault_diagnosis.yaml")
        anomaly_config = load_yaml(root / config["paths"]["anomaly_config"])
        source = args.input or root / config["paths"]["data"]
        destination = args.output or root / config["paths"]["predictions"]
        data = load_diagnosis_data(source)
        anomaly = anomaly_predictions(data, anomaly_config, root)
        manager = FaultModelManager(config, root); manager.load()
        rules = RuleBasedDiagnoser(config["rules"], config["confidence"]["minimum_rule"])
        diagnosis = DiagnosisService(
            rules, manager, config["confidence"]["minimum_final"]
        ).diagnose(data, anomaly)
        destination.parent.mkdir(parents=True, exist_ok=True)
        diagnosis.to_csv(destination, index=False, encoding="utf-8")
        faults = diagnosis[diagnosis["final_diagnosis"] != "normal"]
        important = faults.nlargest(10, "final_confidence")
        print("Diagnostic terminé")
        print(f"Mesures analysées : {len(diagnosis)}")
        print(f"Anomalies détectées : {int((diagnosis['threshold_prediction'] | diagnosis['isolation_forest_prediction']).sum())}")
        print(f"Pannes diagnostiquées : {int((faults['final_diagnosis'] != 'unknown_fault').sum())}")
        print(f"Diagnostics inconnus : {int((diagnosis['final_diagnosis'] == 'unknown_fault').sum())}")
        for kind, group in faults.groupby("equipment_type"):
            print(f"\n{kind.capitalize()} :")
            for fault, count in group["final_diagnosis"].value_counts().items():
                print(f"- {fault} : {count}")
        if not important.empty:
            print("\nDiagnostics importants :")
            print(important[["equipment_id", "final_diagnosis", "severity", "final_confidence"]].to_string(index=False))
        print(f"\nFichier : {destination}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError, RuntimeError) as error:
        LOGGER.exception("Le diagnostic a échoué : %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
