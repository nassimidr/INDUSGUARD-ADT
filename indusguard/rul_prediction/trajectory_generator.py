"""Génération reproductible de trajectoires complètes et incomplètes."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


class RULTrajectoryGenerator:
    """Simule la vie de quatre types d'équipement jusqu'à la panne."""

    COLUMNS = [
        "timestamp", "asset_run_id", "cycle", "equipment_id",
        "equipment_type", "failure_type", "temperature", "vibration",
        "rpm", "current", "load", "pressure", "flow_rate",
        "conveyor_speed", "slip_rate", "health_score", "failure_occurred",
        "rul_steps", "rul_hours", "degradation_progress", "simulation_step",
        "scenario_id",
    ]
    SENSOR_COLUMNS = [
        "temperature", "vibration", "rpm", "current", "load", "pressure",
        "flow_rate", "conveyor_speed", "slip_rate", "health_score",
    ]

    BASELINES: dict[str, dict[str, float]] = {
        "motor": {"temperature": 48, "vibration": 1.8, "rpm": 1500, "current": 18, "load": 55},
        "bearing": {"temperature": 40, "vibration": 2.0, "rpm": 1500},
        "conveyor": {"temperature": 43, "vibration": 1.5, "load": 45, "conveyor_speed": 1.8, "slip_rate": 1.5},
        "pump": {"temperature": 46, "vibration": 1.6, "current": 14, "pressure": 5, "flow_rate": 120},
    }
    NOISE = {
        "temperature": 0.6, "vibration": 0.1, "rpm": 8.0,
        "current": 0.25, "load": 0.8, "pressure": 0.07,
        "flow_rate": 0.9, "conveyor_speed": 0.02, "slip_rate": 0.15,
        "health_score": 0.5,
    }
    EFFECTS: dict[str, dict[str, float]] = {
        "motor_overheating": {"temperature": 48, "current": 9, "load": 16, "vibration": 2},
        "motor_overload": {"temperature": 32, "current": 15, "load": 45, "rpm": -300, "vibration": 4},
        "motor_speed_loss": {"temperature": 15, "current": 7, "rpm": -650, "vibration": 4},
        "motor_electrical_fault": {"temperature": 28, "current": 22, "load": 8, "vibration": 3},
        "bearing_wear": {"temperature": 27, "vibration": 8, "rpm": -160},
        "bearing_overheating": {"temperature": 52, "vibration": 6, "rpm": -100},
        "bearing_severe_damage": {"temperature": 46, "vibration": 13, "rpm": -280},
        "conveyor_overload": {"temperature": 32, "vibration": 5, "load": 52, "conveyor_speed": -0.55, "slip_rate": 13},
        "conveyor_slippage": {"temperature": 18, "vibration": 3, "load": 20, "conveyor_speed": -1.05, "slip_rate": 32},
        "conveyor_speed_fault": {"temperature": 12, "vibration": 2, "conveyor_speed": -1.35, "slip_rate": 18},
        "conveyor_motor_overheating": {"temperature": 52, "vibration": 6, "load": 25, "conveyor_speed": -0.35},
        "pump_cavitation": {"temperature": 20, "vibration": 9, "pressure": -2.2, "flow_rate": -60, "current": 5},
        "pump_blockage": {"temperature": 28, "vibration": 5, "pressure": 5, "flow_rate": -105, "current": 16},
        "pump_leakage": {"temperature": 10, "vibration": 2, "pressure": -4.2, "flow_rate": -75, "current": 2},
        "pump_overheating": {"temperature": 52, "vibration": 4, "pressure": 1, "flow_rate": -30, "current": 15},
        "pump_bearing_fault": {"temperature": 28, "vibration": 11, "pressure": 1, "flow_rate": -25, "current": 6},
    }

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path).expanduser().resolve()
        self.project_root = self.config_path.parent.parent
        with self.config_path.open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        if not isinstance(config, dict):
            raise ValueError("La configuration RUL doit être un objet YAML.")
        self.config = config
        self.output_path = self.project_root / config["paths"]["dataset"]
        self.rng = np.random.default_rng(int(config["simulation"]["random_seed"]))

    def generate_dataset(self) -> pd.DataFrame:
        """Génère toutes les trajectoires configurées dans un dataset unique."""
        self.rng = np.random.default_rng(int(self.config["simulation"]["random_seed"]))
        rows: list[dict[str, Any]] = []
        run_offset = 0
        simulation = self.config["simulation"]
        complete_count = int(simulation["complete_runs_per_equipment"])
        incomplete_count = int(simulation["incomplete_runs_per_equipment"])
        for equipment_type, faults in self.config["failure_types"].items():
            for run_number in range(1, complete_count + 1):
                fault = faults[(run_number - 1) % len(faults)]
                length = self._random_length()
                rows.extend(self._trajectory(equipment_type, fault, run_number, length, length, True, run_offset))
                run_offset += length
            for extra in range(1, incomplete_count + 1):
                run_number = complete_count + extra
                fault = faults[(run_number - 1) % len(faults)]
                full_length = self._random_length()
                fraction = self.rng.uniform(
                    simulation["incomplete_min_fraction"], simulation["incomplete_max_fraction"]
                )
                observed_length = max(20, int(full_length * fraction))
                rows.extend(self._trajectory(equipment_type, fault, run_number, full_length, observed_length, False, run_offset))
                run_offset += observed_length
        dataset = pd.DataFrame(rows, columns=self.COLUMNS)
        self.validate_dataset(dataset)
        return dataset

    def _random_length(self) -> int:
        simulation = self.config["simulation"]
        return int(self.rng.integers(
            int(simulation["min_trajectory_length"]),
            int(simulation["max_trajectory_length"]) + 1,
        ))

    def _trajectory(
        self, equipment_type: str, fault: str, run_number: int,
        full_length: int, observed_length: int, complete: bool, time_offset: int,
    ) -> list[dict[str, Any]]:
        simulation = self.config["simulation"]
        interval_hours = float(simulation["interval_hours"])
        start = datetime.fromisoformat(simulation["start_timestamp"])
        run_id = f"{equipment_type}_run_{run_number:03d}"
        rows: list[dict[str, Any]] = []
        for cycle in range(observed_length):
            fraction = cycle / max(full_length - 1, 1)
            progress = float(fraction ** 1.55)
            values = self._sensor_values(equipment_type, fault, progress, cycle)
            failure = int(complete and cycle == full_length - 1)
            rul_steps = float(full_length - 1 - cycle) if complete else np.nan
            row = {column: np.nan for column in self.COLUMNS}
            row.update(values)
            row.update({
                "timestamp": start + timedelta(hours=(time_offset + cycle) * interval_hours),
                "asset_run_id": run_id, "cycle": cycle,
                "equipment_id": f"{equipment_type.upper()}-RUL-{run_number:03d}",
                "equipment_type": equipment_type, "failure_type": fault,
                "failure_occurred": failure, "rul_steps": rul_steps,
                "rul_hours": rul_steps * interval_hours if complete else np.nan,
                "degradation_progress": round(progress, 6),
                "simulation_step": cycle, "scenario_id": f"rul_{fault}",
            })
            rows.append(row)
        return rows

    def _sensor_values(
        self, equipment_type: str, fault: str, progress: float, cycle: int
    ) -> dict[str, float]:
        baseline = self.BASELINES[equipment_type]
        effects = self.EFFECTS[fault]
        values: dict[str, float] = {}
        for sensor, nominal in baseline.items():
            oscillation = 0.0
            if fault == "pump_cavitation" and sensor in {"pressure", "flow_rate"}:
                oscillation = np.sin(cycle * 0.7) * progress * (0.8 if sensor == "pressure" else 5.0)
            value = nominal + effects.get(sensor, 0.0) * progress + oscillation
            minimum = 0.01 if sensor not in {"load", "slip_rate"} else 0.0
            values[sensor] = round(max(minimum, value + self.rng.normal(0, self.NOISE[sensor])), 3)
        health = 100.0 - 100.0 * progress + self.rng.normal(0, self.NOISE["health_score"])
        values["health_score"] = round(float(np.clip(health, 0, 100)), 3)
        return values

    def validate_dataset(self, dataset: pd.DataFrame) -> None:
        """Vérifie structure, RUL décroissante, pannes finales et trajectoires."""
        if list(dataset.columns) != self.COLUMNS:
            raise ValueError("Les colonnes du dataset RUL sont incorrectes.")
        minimum_rows = 10_000
        if len(dataset) < minimum_rows:
            raise ValueError(f"Le dataset RUL doit contenir au moins {minimum_rows} lignes.")
        for _, group in dataset.groupby("asset_run_id", sort=False):
            group = group.sort_values("cycle")
            if not group["cycle"].is_monotonic_increasing:
                raise ValueError("Les cycles doivent être triés.")
            complete = group["failure_occurred"].eq(1).any()
            if complete:
                if group["failure_occurred"].sum() != 1 or group.iloc[-1]["rul_steps"] != 0:
                    raise ValueError("Une trajectoire complète doit finir avec RUL=0 et une panne.")
                if not group["rul_steps"].diff().dropna().eq(-1).all():
                    raise ValueError("La RUL doit diminuer exactement d'un cycle.")
            elif group[["rul_steps", "rul_hours"]].notna().any().any():
                raise ValueError("Une trajectoire incomplète ne doit pas exposer sa RUL réelle.")

    def save_dataset(self, dataset: pd.DataFrame) -> Path:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        dataset.to_csv(self.output_path, index=False, encoding="utf-8")
        return self.output_path

