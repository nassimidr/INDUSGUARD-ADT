"""Simulateur du moteur électrique."""

from __future__ import annotations

from .base_equipment import BaseEquipment


class MotorSimulator(BaseEquipment):
    """Produit les capteurs moteur et applique les influences de la ligne."""

    def generate_measurement(
        self, intensity: float, influences: dict[str, float] | None = None
    ) -> dict[str, float]:
        intensity = self.apply_intensity(intensity)
        effects = influences or {}
        normal = self.config["normal"]
        overload = effects.get("conveyor_overload", 0.0)
        bearing_vibration = effects.get("bearing_vibration", 0.0)
        load = normal["load"] + 32.0 * overload + 10.0 * intensity
        current = normal["current"] + 0.17 * (load - normal["load"]) + 4.0 * intensity
        return {
            "temperature": self.noisy(normal["temperature"] + 18 * intensity + 10 * overload, "temperature"),
            "vibration": self.noisy(normal["vibration"] + 4.5 * intensity + bearing_vibration, "vibration"),
            "rpm": self.noisy(normal["rpm"] * (1 - 0.18 * intensity), "rpm", 1.0),
            "current": self.noisy(current, "current"),
            "load": min(100.0, self.noisy(load, "load")),
            "health_score": self.health_score,
        }

