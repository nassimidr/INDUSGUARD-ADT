"""Lance la simulation multi-équipement de la phase 1B."""

from __future__ import annotations

import logging
from pathlib import Path

from indusguard.digital_twin import IndustrialLineSimulator


def main() -> int:
    """Génère, valide, enregistre et visualise la ligne industrielle."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = Path(__file__).resolve().parent / "configs" / "industrial_line.yaml"
    try:
        simulator = IndustrialLineSimulator(config)
        dataset = simulator.generate_dataset()
        simulator.save_dataset(dataset)
        simulator.create_plots(dataset)
        simulator.print_summary(dataset)
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError) as error:
        logging.exception("La simulation industrielle a échoué : %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

