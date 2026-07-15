"""Registre canonique compatible avec les identifiants historiques et RUL."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

from .constants import EQUIPMENT_TYPES


class AssetRegistry:
    def __init__(self, path: str | Path = "configs/assets.yaml") -> None:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self.assets: dict[str, dict[str, Any]] = data["assets"]
        self.aliases: dict[str, str] = {}
        for canonical, item in self.assets.items():
            self.aliases[canonical.lower()] = canonical
            for alias in item.get("aliases", []):
                self.aliases[str(alias).lower()] = canonical

    def resolve(self, equipment_id: str) -> str:
        key = str(equipment_id).strip()
        direct = self.aliases.get(key.lower())
        if direct:
            return direct
        match = re.match(r"^(motor|bearing|conveyor|pump)(?:-rul)?[-_]?(\d+)$", key, re.I)
        if match:
            kind, number = match.groups()
            return f"{kind.upper()}-RUL-{int(number):03d}" if "rul" in key.lower() else f"{kind.upper()}-{int(number):03d}"
        run = re.match(r"^(motor|bearing|conveyor|pump)_run_(\d+)$", key, re.I)
        if run:
            return f"{run.group(1).upper()}-RUL-{int(run.group(2)):03d}"
        raise KeyError(f"Équipement inconnu: {equipment_id}")

    def validate(self, equipment_id: str) -> bool:
        try: self.resolve(equipment_id); return True
        except KeyError: return False

    def equipment_type(self, equipment_id: str) -> str:
        canonical = self.resolve(equipment_id)
        configured = self.assets.get(canonical, {}).get("equipment_type")
        kind = str(configured or canonical.split("-", 1)[0].lower())
        if kind not in EQUIPMENT_TYPES: raise KeyError(equipment_id)
        return kind

    def line_id(self, equipment_id: str) -> str:
        return str(self.assets.get(self.resolve(equipment_id), {}).get("line_id", "line_01"))

    def parent(self, equipment_id: str) -> str | None:
        return self.assets.get(self.resolve(equipment_id), {}).get("parent_equipment_id")

    def children(self, equipment_id: str) -> tuple[str, ...]:
        canonical = self.resolve(equipment_id)
        return tuple(k for k, v in self.assets.items() if v.get("parent_equipment_id") == canonical)
