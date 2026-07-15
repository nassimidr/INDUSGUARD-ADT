"""Simulateur de la pompe industrielle."""

from __future__ import annotations

from .base_equipment import BaseEquipment


class PumpSimulator(BaseEquipment):
    """Produit des mesures de pompe, dont débit réduit en cas de panne."""

    def generate_measurement(
        self, intensity: float, influences: dict[str, float] | None = None
    ) -> dict[str, float]:
        intensity = self.apply_intensity(intensity)
        normal = self.config["normal"]
        return {
            "temperature": self.noisy(normal["temperature"] + 22 * intensity, "temperature"),
            "vibration": self.noisy(normal["vibration"] + 5.0 * intensity, "vibration"),
            "current": self.noisy(normal["current"] + 8.0 * intensity, "current"),
            "pressure": self.noisy(normal["pressure"] + 3.2 * intensity, "pressure"),
            "flow_rate": self.noisy(normal["flow_rate"] * (1 - 0.65 * intensity), "flow_rate"),
            "health_score": self.health_score,
        }

