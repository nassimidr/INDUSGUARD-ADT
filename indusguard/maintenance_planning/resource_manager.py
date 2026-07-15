"""Sélection des compétences, outils et coûts de main-d'œuvre."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResourceSelection:
    skills: tuple[str, ...]
    technician_count: int
    average_hourly_cost: float
    expertise: tuple[str, ...]
    protective_equipment: tuple[str, ...]
    tools: tuple[str, ...]


class ResourceManager:
    def __init__(self, resources: dict[str, Any]) -> None:
        self.resources = resources

    def select(self, equipment_type: str, skills: tuple[str, ...]) -> ResourceSelection:
        technicians = self.resources["technicians"]
        unknown = set(skills) - set(technicians)
        if unknown:
            raise ValueError(f"Compétences inconnues : {sorted(unknown)}")
        costs = [float(technicians[skill]["hourly_cost"]) for skill in skills]
        expertise = tuple(str(technicians[skill]["expertise"]) for skill in skills)
        tools = tuple(self.resources.get("tools", {}).get(equipment_type, []))
        return ResourceSelection(
            skills=skills, technician_count=max(1, len(skills)),
            average_hourly_cost=sum(costs) / max(len(costs), 1),
            expertise=expertise,
            protective_equipment=("EPI réglementaires", "équipement de consignation"),
            tools=tools,
        )

    def safety_instructions(self, equipment_type: str) -> tuple[str, ...]:
        return tuple(self.resources["safety_instructions"].get(equipment_type, []))

