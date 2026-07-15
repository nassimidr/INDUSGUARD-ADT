"""Point d'entrée de la première phase d'INDUSGUARD-ADT."""

from __future__ import annotations

import logging
from pathlib import Path

from indusguard.digital_twin import BearingSimulator


def main() -> int:
    """Exécute la génération, la validation et les exports."""
    config_path = Path(__file__).resolve().parent / "configs" / "simulation.yaml"
    try:
        simulator = BearingSimulator(config_path)
        dataset = simulator.generate_dataset()
        simulator.validate_dataset(dataset)
        simulator.save_dataset(dataset)
        simulator.create_plots(dataset)
        simulator.print_summary(dataset)
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError) as error:
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s : %(message)s")
        logging.error("La simulation a échoué : %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
