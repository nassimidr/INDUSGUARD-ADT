"""Orchestration des équipements et des dépendances de la ligne."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import yaml

from .bearing_simulator import LineBearingSimulator
from .conveyor_simulator import ConveyorSimulator
from .motor_simulator import MotorSimulator
from .pump_simulator import PumpSimulator
from .scenarios import ScenarioState, scenario_state

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LOGGER = logging.getLogger(__name__)


class IndustrialLineSimulator:
    """Simule quatre équipements couplés sur un ou plusieurs scénarios."""

    COLUMNS = [
        "timestamp", "scenario_id", "equipment_id", "equipment_type",
        "operating_state", "is_anomaly", "health_score", "temperature",
        "vibration", "rpm", "current", "load", "pressure", "flow_rate",
        "conveyor_speed", "slip_rate", "failure_type", "anomaly_severity",
        "simulation_step",
    ]

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path).expanduser().resolve()
        self.project_root = self.config_path.parent.parent
        self.config = self._load_config()
        simulation = self.config["simulation"]
        if int(simulation["steps_per_scenario"]) <= 0:
            raise ValueError("steps_per_scenario doit être positif.")
        if float(simulation["interval_seconds"]) <= 0:
            raise ValueError("interval_seconds doit être positif.")
        self.output_path = self.project_root / self.config["output"]["csv_path"]
        self.plots_directory = self.project_root / self.config["output"]["plots_directory"]
        self.equipment: dict[str, Any] = {}

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.is_file():
            raise FileNotFoundError(f"Configuration introuvable : {self.config_path}")
        with self.config_path.open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        required = {"simulation", "scenarios", "equipment", "dependencies", "output"}
        if not isinstance(config, dict):
            raise ValueError("La configuration doit être un objet YAML.")
        missing = required - set(config)
        if missing:
            raise ValueError(f"Sections de configuration manquantes : {sorted(missing)}")
        return config

    def _build_equipment(self, scenario_index: int) -> None:
        seed = int(self.config["simulation"]["random_seed"]) + scenario_index * 100
        equipment = self.config["equipment"]
        self.equipment = {
            "motor": MotorSimulator("MOTOR-001", equipment["motor"], seed + 1),
            "bearing": LineBearingSimulator("BEARING-001", equipment["bearing"], seed + 2),
            "conveyor": ConveyorSimulator("CONVEYOR-001", equipment["conveyor"], seed + 3),
            "pump": PumpSimulator("PUMP-001", equipment["pump"], seed + 4),
        }

    def _selected_scenarios(self) -> list[dict[str, str]]:
        requested = self.config["simulation"].get("scenario", "all")
        scenarios = self.config["scenarios"]
        selected = scenarios if requested == "all" else [item for item in scenarios if item["id"] == requested]
        if not selected:
            raise ValueError(f"Scénario non configuré : {requested}")
        return selected

    def _measurement_rows(
        self, state: ScenarioState, scenario_id: str, step: int, timestamp: datetime
    ) -> list[dict[str, Any]]:
        dependencies = self.config["dependencies"]
        bearing = self.equipment["bearing"].generate_measurement(state.bearing)
        bearing_effect = max(0.0, bearing["vibration"] - self.config["equipment"]["bearing"]["normal"]["vibration"])
        motor_intensity = min(
            1.0,
            state.motor
            + state.bearing * dependencies["bearing_to_motor_degradation"]
            + state.conveyor_overload * 0.65,
        )
        motor = self.equipment["motor"].generate_measurement(
            motor_intensity,
            {
                "conveyor_overload": state.conveyor_overload * dependencies["conveyor_to_motor_load"],
                "bearing_vibration": bearing_effect * dependencies["bearing_to_motor_vibration"],
            },
        )
        nominal_rpm = self.config["equipment"]["motor"]["normal"]["rpm"]
        conveyor_intensity = min(1.0, state.conveyor + motor_intensity * dependencies["motor_to_conveyor_degradation"])
        conveyor = self.equipment["conveyor"].generate_measurement(
            conveyor_intensity,
            {"overload": state.conveyor_overload, "motor_speed_ratio": motor["rpm"] / nominal_rpm},
        )
        pump = self.equipment["pump"].generate_measurement(state.pump)
        values = {"motor": motor, "bearing": bearing, "conveyor": conveyor, "pump": pump}
        intensities = {"motor": motor_intensity, "bearing": state.bearing, "conveyor": conveyor_intensity, "pump": state.pump}
        return [self._row(name, values[name], intensities[name], scenario_id, step, timestamp) for name in values]

    def _row(
        self, equipment_type: str, values: dict[str, float], intensity: float,
        scenario_id: str, step: int, timestamp: datetime,
    ) -> dict[str, Any]:
        equipment = self.equipment[equipment_type]
        anomaly = equipment.state != "normal"
        row: dict[str, Any] = {column: np.nan for column in self.COLUMNS}
        row.update({
            "timestamp": timestamp, "scenario_id": scenario_id,
            "equipment_id": equipment.equipment_id, "equipment_type": equipment_type,
            "operating_state": equipment.state, "is_anomaly": anomaly,
            "health_score": round(values["health_score"], 3),
            "failure_type": self._failure_type(
                equipment_type, scenario_id, values, anomaly
            ),
            "anomaly_severity": round(float(intensity), 3), "simulation_step": step,
        })
        row.update({key: round(float(value), 3) for key, value in values.items() if key != "health_score"})
        return row

    @staticmethod
    def _failure_type(
        equipment_type: str,
        scenario_id: str,
        values: dict[str, float],
        anomaly: bool,
    ) -> str:
        """Attribue une panne cohérente avec le scénario et les capteurs."""
        if not anomaly:
            return "normal"
        if scenario_id == "scenario_5_cascade":
            return "cascade_failure"
        if equipment_type == "bearing":
            if values["health_score"] < 40 or values["vibration"] > 7.0:
                return "bearing_severe_damage"
            if values["temperature"] > 55.0:
                return "bearing_overheating"
            return "bearing_wear"
        if equipment_type == "motor":
            if values["temperature"] > 68.0:
                return "motor_overheating"
            if values["current"] > 27.0:
                return "motor_electrical_fault"
            if values["load"] > 78.0:
                return "motor_overload"
            return "motor_speed_loss"
        if equipment_type == "conveyor":
            if values["temperature"] > 58.0:
                return "conveyor_motor_overheating"
            if values["slip_rate"] > 11.0:
                return "conveyor_slippage"
            if values["conveyor_speed"] < 1.35:
                return "conveyor_speed_fault"
            return "conveyor_overload"
        if values["temperature"] > 65.0:
            return "pump_overheating"
        if values["pressure"] > 7.0 and values["flow_rate"] < 75.0:
            return "pump_blockage"
        if values["vibration"] > 2.7 and values["flow_rate"] < 105.0:
            return "pump_cavitation"
        return "pump_bearing_fault"

    def generate_dataset(self) -> pd.DataFrame:
        """Génère un dataset long : une ligne par équipement et par pas."""
        rows: list[dict[str, Any]] = []
        steps = int(self.config["simulation"]["steps_per_scenario"])
        interval = timedelta(seconds=float(self.config["simulation"]["interval_seconds"]))
        start = datetime.fromisoformat(self.config["simulation"].get("start_timestamp", "2026-01-01T00:00:00"))
        for scenario_index, scenario in enumerate(self._selected_scenarios()):
            self._build_equipment(scenario_index)
            for step in range(steps):
                state = scenario_state(scenario["type"], step, steps)
                timestamp = start + interval * (scenario_index * steps + step)
                rows.extend(self._measurement_rows(state, scenario["id"], step, timestamp))
        dataset = pd.DataFrame(rows, columns=self.COLUMNS)
        self.validate_dataset(dataset)
        return dataset

    def validate_dataset(self, dataset: pd.DataFrame) -> None:
        """Valide la structure et les invariants du dataset multi-équipement."""
        expected = len(self._selected_scenarios()) * int(self.config["simulation"]["steps_per_scenario"]) * 4
        if len(dataset) != expected or list(dataset.columns) != self.COLUMNS:
            raise ValueError("Taille ou colonnes du dataset industriel incorrectes.")
        if set(dataset["equipment_type"]) != {"motor", "bearing", "conveyor", "pump"}:
            raise ValueError("Les quatre types d'équipement sont requis.")
        if not dataset["health_score"].between(0, 100).all():
            raise ValueError("Les scores de santé doivent être compris entre 0 et 100.")
        if not set(dataset["operating_state"]).issubset({"normal", "degradation", "critical"}):
            raise ValueError("État d'équipement invalide.")
        if not (dataset.loc[~dataset["is_anomaly"], "failure_type"] == "normal").all():
            raise ValueError("Les mesures normales doivent porter l'étiquette normal.")
        if (dataset.loc[dataset["is_anomaly"], "failure_type"] == "normal").any():
            raise ValueError("Une mesure anormale doit porter une panne explicite.")

    def save_dataset(self, dataset: pd.DataFrame) -> Path:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        dataset.to_csv(self.output_path, index=False, encoding="utf-8")
        return self.output_path

    def create_plots(self, dataset: pd.DataFrame) -> list[Path]:
        """Crée les sept vues opérationnelles demandées."""
        self.plots_directory.mkdir(parents=True, exist_ok=True)
        plot_specs = [
            ("temperature", None, "Températures", "Température (°C)", "temperatures.png"),
            ("vibration", None, "Vibrations", "Vibration (mm/s)", "vibrations.png"),
            ("health_score", None, "Scores de santé", "Score", "health_scores.png"),
            ("current", "motor", "Courant et charge du moteur", "Valeur", "motor_current_load.png"),
            ("conveyor_speed", "conveyor", "Vitesse et charge du convoyeur", "Valeur", "conveyor_speed_load.png"),
            ("pressure", "pump", "Pression et débit de la pompe", "Valeur", "pump_pressure_flow.png"),
        ]
        paths: list[Path] = []
        for primary, equipment_type, title, ylabel, filename in plot_specs:
            subset = dataset if equipment_type is None else dataset[dataset["equipment_type"] == equipment_type]
            figure, axis = plt.subplots(figsize=(11, 5))
            for kind, group in subset.groupby("equipment_type"):
                if group[primary].notna().any():
                    axis.plot(group.index, group[primary], label=f"{kind} - {primary}", linewidth=1.2)
            secondary = {"current": "load", "conveyor_speed": "load", "pressure": "flow_rate"}.get(primary)
            if secondary:
                axis.plot(subset.index, subset[secondary], label=secondary, linewidth=1.2)
            self._decorate(axis, title, ylabel)
            path = self.plots_directory / filename
            figure.tight_layout(); figure.savefig(path, dpi=140); plt.close(figure); paths.append(path)
        figure, axis = plt.subplots(figsize=(11, 5))
        mapping = {"normal": 0, "degradation": 1, "critical": 2}
        for kind, group in dataset.groupby("equipment_type"):
            axis.plot(group.index, group["operating_state"].map(mapping), label=kind, linewidth=1.2)
        axis.set_yticks(list(mapping.values()), list(mapping.keys()))
        self._decorate(axis, "Chronologie des états", "État")
        path = self.plots_directory / "operating_states.png"
        figure.tight_layout(); figure.savefig(path, dpi=140); plt.close(figure); paths.append(path)
        return paths

    @staticmethod
    def _decorate(axis: Any, title: str, ylabel: str) -> None:
        axis.set_title(title); axis.set_xlabel("Index de mesure"); axis.set_ylabel(ylabel)
        axis.grid(alpha=0.3); axis.legend(loc="best")

    def print_summary(self, dataset: pd.DataFrame) -> None:
        counts = dataset["operating_state"].value_counts()
        print("Simulation terminée")
        print(f"Nombre total de mesures : {len(dataset)}")
        print(f"Mesures normales : {counts.get('normal', 0)}")
        print(f"Mesures en dégradation : {counts.get('degradation', 0)}")
        print(f"Mesures critiques : {counts.get('critical', 0)}")
        print(f"Anomalies générées : {int(dataset['is_anomaly'].sum())}")
        print(f"Fichier CSV : {self.output_path.relative_to(self.project_root)}")
        print(f"Graphiques : {self.plots_directory.relative_to(self.project_root)}")
