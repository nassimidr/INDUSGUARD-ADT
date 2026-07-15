"""Simulateur du convoyeur."""

from __future__ import annotations

from .base_equipment import BaseEquipment


class ConveyorSimulator(BaseEquipment):
    """Produit les capteurs convoyeur dépendants du moteur."""

    def generate_measurement(
        self, intensity: float, influences: dict[str, float] | None = None
    ) -> dict[str, float]:
        intensity = self.apply_intensity(intensity)
        effects = influences or {}
        normal = self.config["normal"]
        overload = effects.get("overload", 0.0)
        motor_speed_ratio = effects.get("motor_speed_ratio", 1.0)
        load = normal["load"] + 45.0 * overload + 10.0 * intensity
        return {
            "temperature": self.noisy(normal["temperature"] + 15 * intensity + 9 * overload, "temperature"),
            "vibration": self.noisy(normal["vibration"] + 3.5 * intensity + 1.5 * overload, "vibration"),
            "load": min(100.0, self.noisy(load, "load")),
            "conveyor_speed": self.noisy(normal["conveyor_speed"] * motor_speed_ratio * (1 - 0.22 * intensity), "conveyor_speed"),
            "slip_rate": min(100.0, self.noisy(normal["slip_rate"] + 16 * intensity + 12 * overload, "slip_rate")),
            "health_score": self.health_score,
        }

