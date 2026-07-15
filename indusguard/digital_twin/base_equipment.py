"""Comportements partagés par les équipements de la ligne industrielle."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseEquipment(ABC):
    """Base reproductible d'un équipement instrumenté."""

    VALID_STATES = {"normal", "degradation", "critical"}

    def __init__(self, equipment_id: str, config: dict[str, Any], seed: int) -> None:
        if not equipment_id:
            raise ValueError("L'identifiant de l'équipement ne peut pas être vide.")
        if "normal" not in config or "noise" not in config:
            raise ValueError("Chaque équipement requiert les sections normal et noise.")
        self.equipment_id = equipment_id
        self.config = config
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.state = "normal"
        self.health_score = 100.0

    def reset(self) -> None:
        """Replace l'équipement dans son état initial reproductible."""
        self.rng = np.random.default_rng(self.seed)
        self.state = "normal"
        self.health_score = 100.0

    def set_state(self, state: str, intensity: float = 0.0) -> None:
        """Met à jour l'état et le score de santé selon une intensité [0, 1]."""
        if state not in self.VALID_STATES:
            raise ValueError(f"État invalide : {state}")
        self.state = state
        self.health_score = float(np.clip(100.0 - 80.0 * intensity, 0.0, 100.0))

    def apply_intensity(self, intensity: float) -> float:
        """Déduit l'état depuis l'intensité et retourne l'intensité bornée."""
        value = float(np.clip(intensity, 0.0, 1.0))
        state = "critical" if value >= 0.75 else "degradation" if value >= 0.25 else "normal"
        self.set_state(state, value)
        return value

    def noisy(self, value: float, sensor: str, minimum: float = 0.0) -> float:
        """Ajoute le bruit gaussien configuré et borne la mesure."""
        standard_deviation = float(self.config["noise"].get(sensor, 0.0))
        return max(minimum, float(value + self.rng.normal(0.0, standard_deviation)))

    @abstractmethod
    def generate_measurement(
        self, intensity: float, influences: dict[str, float] | None = None
    ) -> dict[str, float]:
        """Génère une mesure cohérente avec l'état courant."""

