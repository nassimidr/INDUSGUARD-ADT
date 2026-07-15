"""Sélection et disponibilité des pièces de rechange synthétiques."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PartsSelection:
    required_parts: tuple[str, ...]
    optional_parts: tuple[str, ...]
    quantities: dict[str, int]
    all_required_available: bool
    unavailable_parts: tuple[str, ...]


class SparePartsManager:
    def __init__(self, resources: dict[str, Any]) -> None:
        self.catalog = resources["spare_parts"]
        self.inventory = {name: int(value["quantity"]) for name, value in self.catalog.items()}

    def select(
        self, required: tuple[str, ...], optional: tuple[str, ...]
    ) -> PartsSelection:
        unknown = (set(required) | set(optional)) - set(self.catalog)
        if unknown:
            raise ValueError(f"Pièces inconnues : {sorted(unknown)}")
        unavailable = tuple(part for part in required if self.inventory.get(part, 0) < 1)
        return PartsSelection(
            required, optional, {part: 1 for part in required},
            not unavailable, unavailable,
        )

    def available(self, parts: tuple[str, ...]) -> tuple[bool, tuple[str, ...]]:
        missing = tuple(part for part in parts if self.inventory.get(part, 0) < 1)
        return not missing, missing

    def reserve(self, parts: tuple[str, ...]) -> None:
        available, missing = self.available(parts)
        if not available:
            raise ValueError(f"Pièces indisponibles : {missing}")
        for part in parts:
            self.inventory[part] -= 1

    def cost(self, parts: tuple[str, ...]) -> float:
        return sum(float(self.catalog[part]["unit_cost"]) for part in parts)

