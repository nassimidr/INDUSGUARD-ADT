from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

@dataclass(frozen=True)
class DashboardConfig:
    root:Path; values:dict[str,Any]
    @property
    def database_url(self)->str:
        url=str(self.values["database"]["url"])
        if url.startswith("sqlite:///") and not Path(url[10:]).is_absolute():return "sqlite:///"+str((self.root/Path(url[10:])).resolve()).replace("\\","/")
        return url
    @property
    def timezone(self)->str:return str(self.values["app"]["timezone"])
    @property
    def allowed_scenarios(self)->set[str]:return set(self.values["runtime"]["allowed_scenarios"])

def load_dashboard_config(path:str|Path="configs/dashboard.yaml")->DashboardConfig:
    source=Path(path).resolve();values=yaml.safe_load(source.read_text(encoding="utf-8"))
    required={"app","api","database","websocket","dashboard","retention","runtime"}
    if required-set(values or {}):raise ValueError(f"Configuration dashboard incomplète: {sorted(required-set(values or {}))}")
    if not str(values["api"]["host"]) in {"127.0.0.1","localhost"}:raise ValueError("L'API locale doit écouter sur loopback par défaut.")
    return DashboardConfig(source.parent.parent,values)
