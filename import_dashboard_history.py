"""Importe les artefacts historiques des phases 1 a 6 dans SQLite."""
from __future__ import annotations

import json

from indusguard.dashboard.config import load_dashboard_config
from indusguard.dashboard.database import build_engine, initialize_database, session_factory
from indusguard.dashboard.historical_importer import HistoricalImporter


if __name__ == "__main__":
    config = load_dashboard_config(); engine = build_engine(config); initialize_database(engine)
    with session_factory(engine)() as session:
        print(json.dumps(HistoricalImporter(config.root, session).run(), ensure_ascii=False, indent=2))
