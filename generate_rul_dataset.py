"""Génère le dataset synthétique de trajectoires RUL."""

from __future__ import annotations

import logging
from pathlib import Path

from indusguard.rul_prediction import RULTrajectoryGenerator


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(__file__).resolve().parent
    try:
        generator = RULTrajectoryGenerator(root / "configs" / "rul_prediction.yaml")
        dataset = generator.generate_dataset(); generator.save_dataset(dataset)
        complete = dataset.groupby("asset_run_id")["failure_occurred"].max()
        counts = dataset.groupby("equipment_type")["asset_run_id"].nunique()
        print("Dataset RUL généré")
        print(f"Nombre total de lignes : {len(dataset)}")
        print(f"Trajectoires complètes : {int(complete.sum())}")
        print(f"Trajectoires incomplètes : {int((complete == 0).sum())}")
        for kind, count in counts.items():
            print(f"{kind.capitalize()} : {count} trajectoires")
        print(f"Fichier : {generator.output_path.relative_to(root)}")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError) as error:
        logging.exception("La génération RUL a échoué : %s", error); return 1


if __name__ == "__main__":
    raise SystemExit(main())
