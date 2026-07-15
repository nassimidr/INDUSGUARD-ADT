"""Chargement et validation de la configuration multi-agents."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class MultiAgentConfig:
    root: Path
    values: dict[str, Any]

    @property
    def mode(self) -> str:
        return os.environ.get("INDUSGUARD_XMPP_MODE", self.values["runtime"]["mode"])

    @property
    def domain(self) -> str:
        return os.environ.get("INDUSGUARD_XMPP_DOMAIN", self.values["xmpp"]["domain"])

    @property
    def password(self) -> str:
        value=os.environ.get("INDUSGUARD_AGENT_PASSWORD")
        if value:return value
        if self.mode=="embedded":return "indusguard-local-dev"
        raise ValueError("INDUSGUARD_AGENT_PASSWORD est obligatoire en mode external.")

    @property
    def auto_register(self) -> bool:
        default = bool(self.values["runtime"]["auto_register"])
        return default if self.mode == "embedded" else os.environ.get("INDUSGUARD_AUTO_REGISTER", "false").lower() == "true"

    @property
    def agents(self) -> dict[str, dict[str, Any]]:
        output = {}
        for name, values in self.values["agents"].items():
            item = dict(values)
            local = str(item["jid"]).split("@", 1)[0]
            item["jid"] = os.environ.get(f"INDUSGUARD_{name.upper()}_JID", f"{local}@{self.domain}")
            output[name] = item
        return output

    @property
    def allowed_jids(self) -> set[str]:
        return {str(v["jid"]).lower() for v in self.agents.values() if v.get("enabled", True)}

    def jid(self, name: str) -> str:
        return str(self.agents[name]["jid"])


def load_multi_agent_config(path: str | Path = "configs/multi_agent.yaml") -> MultiAgentConfig:
    source = Path(path).resolve()
    values = yaml.safe_load(source.read_text(encoding="utf-8"))
    required = {"runtime", "xmpp", "agents", "simulation", "timeouts", "retries", "heartbeats", "idempotency", "messages", "outputs"}
    missing = required - set(values or {})
    if missing:
        raise ValueError(f"Sections de configuration absentes: {sorted(missing)}")
    if values["runtime"]["mode"] not in {"embedded", "external"}:
        raise ValueError("Le mode XMPP doit être embedded ou external.")
    for name, item in values["agents"].items():
        if "@" not in str(item.get("jid", "")):
            raise ValueError(f"JID invalide pour {name}.")
    return MultiAgentConfig(source.parent.parent, values)
