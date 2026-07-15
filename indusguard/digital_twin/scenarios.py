"""Définition des profils de panne de la ligne industrielle."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioState:
    """Intensités de panne appliquées à un pas de simulation."""

    bearing: float = 0.0
    motor: float = 0.0
    conveyor: float = 0.0
    pump: float = 0.0
    conveyor_overload: float = 0.0


def progressive(step: int, total_steps: int, start_fraction: float) -> float:
    """Retourne une rampe de 0 à 1 commençant à la fraction donnée."""
    start = int(total_steps * start_fraction)
    if step < start:
        return 0.0
    return min(1.0, (step - start + 1) / max(1, total_steps - start))


def scenario_state(scenario_type: str, step: int, total_steps: int) -> ScenarioState:
    """Construit les intensités et dépendances d'un scénario configurable."""
    ramp = progressive(step, total_steps, 0.35)
    if scenario_type == "normal":
        return ScenarioState()
    if scenario_type == "bearing_degradation":
        return ScenarioState(bearing=ramp)
    if scenario_type == "conveyor_overload":
        return ScenarioState(conveyor=0.65 * ramp, conveyor_overload=ramp)
    if scenario_type == "pump_anomaly":
        return ScenarioState(pump=ramp)
    if scenario_type == "cascade_failure":
        bearing = progressive(step, total_steps, 0.20)
        motor = 0.75 * progressive(step, total_steps, 0.45)
        conveyor = 0.65 * progressive(step, total_steps, 0.65)
        return ScenarioState(bearing=bearing, motor=motor, conveyor=conveyor)
    raise ValueError(f"Type de scénario inconnu : {scenario_type}")
