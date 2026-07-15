"""Lance l'API locale du tableau de bord INDUSGUARD-ADT."""
from __future__ import annotations

import uvicorn

from indusguard.dashboard.config import load_dashboard_config


if __name__ == "__main__":
    config = load_dashboard_config()
    uvicorn.run("indusguard.dashboard.main:app", host=config.values["api"]["host"], port=int(config.values["api"]["port"]), reload=False)
