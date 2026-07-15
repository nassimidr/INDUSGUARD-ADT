"""Catalogue central et typé des interventions de maintenance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MAINTENANCE_STRATEGIES = frozenset({
    "monitor", "inspect", "preventive_maintenance", "component_replacement",
    "corrective_maintenance", "emergency_shutdown",
})


@dataclass(frozen=True)
class MaintenanceDefinition:
    """Décrit l'intervention de référence associée à une panne."""

    strategy: str
    action: str
    secondary_actions: tuple[str, ...]
    skills: tuple[str, ...]
    required_parts: tuple[str, ...]
    optional_parts: tuple[str, ...]
    duration_hours: float
    shutdown_required: bool
    inspection_required: bool


class MaintenanceCatalog:
    """Convertit le catalogue YAML en définitions validées."""

    def __init__(self, entries: dict[str, dict[str, Any]]) -> None:
        self.entries = {
            fault: MaintenanceDefinition(
                strategy=value["strategy"], action=value["action"],
                secondary_actions=tuple(value.get("secondary_actions", [])),
                skills=tuple(value.get("skills", [])),
                required_parts=tuple(value.get("required_parts", [])),
                optional_parts=tuple(value.get("optional_parts", [])),
                duration_hours=float(value["duration_hours"]),
                shutdown_required=bool(value["shutdown_required"]),
                inspection_required=bool(value["inspection_required"]),
            )
            for fault, value in entries.items()
        }
        invalid = {entry.strategy for entry in self.entries.values()} - MAINTENANCE_STRATEGIES
        if invalid:
            raise ValueError(f"Stratégies de maintenance invalides : {sorted(invalid)}")
        for required in ("normal", "unknown_fault", "cascade_failure"):
            if required not in self.entries:
                raise ValueError(f"Entrée obligatoire absente du catalogue : {required}")

    def get(self, fault: str) -> MaintenanceDefinition:
        """Retourne une définition prudente si la panne est inconnue."""
        return self.entries.get(fault, self.entries["unknown_fault"])

