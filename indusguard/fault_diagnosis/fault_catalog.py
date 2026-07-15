"""Catalogue central et typé des pannes prises en charge."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FaultDefinition:
    """Décrit une panne, son équipement et ses symptômes principaux."""

    equipment_type: str
    symptoms: tuple[str, ...]
    sensors: tuple[str, ...]
    description: str


def _fault(equipment: str, symptoms: tuple[str, ...], description: str) -> FaultDefinition:
    return FaultDefinition(equipment, symptoms, symptoms, description)


FAULT_CATALOG: dict[str, FaultDefinition] = {
    "normal": _fault("all", (), "Aucun symptôme de panne significatif n'est observé."),
    "unknown_fault": _fault("all", (), "Une anomalie est détectée, mais sa cause reste incertaine."),
    "cascade_failure": _fault("multi", ("vibration", "temperature", "rpm", "conveyor_speed"), "Plusieurs équipements présentent une dégradation liée."),
    "motor_overheating": _fault("motor", ("temperature", "current", "load"), "Le moteur présente une surchauffe associée à son effort électrique."),
    "motor_overload": _fault("motor", ("load", "current", "temperature", "rpm"), "La charge et le courant moteur sont élevés tandis que le régime diminue."),
    "motor_speed_loss": _fault("motor", ("rpm", "current"), "Le régime moteur est inférieur au régime attendu."),
    "motor_electrical_fault": _fault("motor", ("current", "temperature"), "La consommation électrique du moteur est anormalement élevée."),
    "bearing_wear": _fault("bearing", ("vibration", "health_score", "temperature"), "La vibration augmente et le score de santé du roulement diminue."),
    "bearing_overheating": _fault("bearing", ("temperature", "vibration"), "Le roulement présente une température et une vibration excessives."),
    "bearing_severe_damage": _fault("bearing", ("vibration", "temperature", "health_score"), "Le roulement présente des signes de dommage mécanique critique."),
    "conveyor_overload": _fault("conveyor", ("load", "conveyor_speed", "vibration", "temperature"), "Le convoyeur est chargé au-delà de son régime nominal."),
    "conveyor_slippage": _fault("conveyor", ("slip_rate", "conveyor_speed"), "Le taux de glissement est élevé et la vitesse utile diminue."),
    "conveyor_speed_fault": _fault("conveyor", ("conveyor_speed", "slip_rate"), "La vitesse du convoyeur est anormalement basse."),
    "conveyor_motor_overheating": _fault("conveyor", ("temperature", "load", "vibration"), "Le moteur du convoyeur présente une surchauffe."),
    "pump_cavitation": _fault("pump", ("vibration", "pressure", "flow_rate"), "La pompe vibre et son débit baisse avec une pression perturbée."),
    "pump_blockage": _fault("pump", ("flow_rate", "pressure", "current"), "Une obstruction est probable : débit faible, pression et courant élevés."),
    "pump_leakage": _fault("pump", ("flow_rate", "pressure"), "Une fuite est probable car le débit et la pression sont faibles."),
    "pump_overheating": _fault("pump", ("temperature", "current"), "La pompe présente une température et un courant élevés."),
    "pump_bearing_fault": _fault("pump", ("vibration", "temperature"), "Le roulement de pompe présente une vibration excessive."),
}

ALL_FAULT_TYPES = frozenset(FAULT_CATALOG)
FAULTS_BY_EQUIPMENT: dict[str, tuple[str, ...]] = {
    equipment: tuple(
        name for name, definition in FAULT_CATALOG.items()
        if definition.equipment_type in {equipment, "all", "multi"}
    )
    for equipment in ("motor", "bearing", "conveyor", "pump")
}

