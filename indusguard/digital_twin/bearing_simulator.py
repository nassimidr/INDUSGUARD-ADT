"""Simulateur simple de données synthétiques pour un roulement industriel."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .base_equipment import BaseEquipment


class BearingSimulator:
    """Génère un scénario reproductible d'usure progressive d'un roulement."""

    COLUMNS = [
        "timestamp",
        "equipment_id",
        "vibration_rms_mm_s",
        "temperature_c",
        "speed_rpm",
        "load_pct",
        "health_score",
        "state",
        "fault_active",
        "fault_type",
    ]
    REQUIRED_SECTIONS = {
        "project",
        "simulation",
        "normal_state",
        "degradation_state",
        "critical_state",
        "output",
    }

    def __init__(self, config_path: str | Path) -> None:
        """Charge la configuration et prépare le générateur et les sorties."""
        self.config_path = Path(config_path).expanduser().resolve()
        self.config = self.load_config()
        self.project_root = self.config_path.parent.parent
        simulation = self.config["simulation"]
        self.rng = np.random.default_rng(simulation["random_seed"])
        self.csv_path = self.project_root / self.config["output"]["csv_path"]
        self.plots_directory = (
            self.project_root / self.config["output"]["plots_directory"]
        )

    def load_config(self) -> dict[str, Any]:
        """Lit le YAML et vérifie ses sections et paramètres essentiels."""
        if not self.config_path.is_file():
            raise FileNotFoundError(
                f"Fichier de configuration introuvable : {self.config_path}"
            )
        try:
            with self.config_path.open("r", encoding="utf-8") as stream:
                config = yaml.safe_load(stream)
        except yaml.YAMLError as error:
            raise ValueError(f"Configuration YAML incorrecte : {error}") from error
        except OSError as error:
            raise OSError(f"Impossible de lire la configuration : {error}") from error

        if not isinstance(config, dict):
            raise ValueError("La configuration YAML doit contenir un objet principal.")
        missing = self.REQUIRED_SECTIONS - config.keys()
        if missing:
            raise ValueError(
                "Sections manquantes dans la configuration : "
                + ", ".join(sorted(missing))
            )

        required_keys = {
            "simulation": {
                "total_measurements",
                "normal_end_index",
                "degradation_end_index",
                "interval_seconds",
                "random_seed",
                "equipment_id",
            },
            "normal_state": {
                "vibration_mean",
                "vibration_std",
                "temperature_mean",
                "temperature_std",
                "speed_mean",
                "speed_std",
                "load_mean",
                "load_std",
                "health_min",
                "health_max",
            },
            "degradation_state": {
                "vibration_start",
                "vibration_end",
                "temperature_start",
                "temperature_end",
                "health_start",
                "health_end",
            },
            "critical_state": {
                "vibration_start",
                "vibration_end",
                "temperature_start",
                "temperature_end",
                "health_start",
                "health_end",
            },
            "output": {"csv_path", "plots_directory"},
        }
        for section, keys in required_keys.items():
            if not isinstance(config[section], dict):
                raise ValueError(f"La section '{section}' doit être un objet YAML.")
            absent = keys - config[section].keys()
            if absent:
                raise ValueError(
                    f"Paramètres manquants dans '{section}' : "
                    + ", ".join(sorted(absent))
                )

        sim = config["simulation"]
        if not 0 < sim["normal_end_index"] < sim["degradation_end_index"] < sim["total_measurements"]:
            raise ValueError("Les limites des trois périodes sont incohérentes.")
        if sim["interval_seconds"] <= 0:
            raise ValueError("L'intervalle entre les mesures doit être positif.")
        return config

    def _operating_values(self, count: int) -> tuple[np.ndarray, np.ndarray]:
        """Génère une vitesse et une charge autour du régime nominal."""
        normal = self.config["normal_state"]
        speed = self.rng.normal(normal["speed_mean"], normal["speed_std"], count)
        load = self.rng.normal(normal["load_mean"], normal["load_std"], count)
        return np.clip(speed, 0.01, None), np.clip(load, 0.0, 100.0)

    def _period_frame(
        self,
        vibration: np.ndarray,
        temperature: np.ndarray,
        health: np.ndarray,
        state: str,
        fault_active: bool,
    ) -> pd.DataFrame:
        """Assemble les mesures d'une période dans un tableau."""
        count = len(vibration)
        speed, load = self._operating_values(count)
        return pd.DataFrame(
            {
                "equipment_id": self.config["simulation"]["equipment_id"],
                "vibration_rms_mm_s": np.clip(vibration, 0.001, None),
                "temperature_c": np.clip(temperature, 0.01, None),
                "speed_rpm": speed,
                "load_pct": load,
                "health_score": np.clip(health, 0.0, 100.0),
                "state": state,
                "fault_active": fault_active,
                "fault_type": "bearing_wear" if fault_active else "none",
            }
        )

    def generate_normal_period(self) -> pd.DataFrame:
        """Génère la période de fonctionnement normal."""
        count = self.config["simulation"]["normal_end_index"]
        normal = self.config["normal_state"]
        vibration = self.rng.normal(
            normal["vibration_mean"], normal["vibration_std"], count
        )
        temperature = self.rng.normal(
            normal["temperature_mean"], normal["temperature_std"], count
        )
        health = self.rng.uniform(normal["health_min"], normal["health_max"], count)
        return self._period_frame(vibration, temperature, health, "normal", False)

    def generate_degradation_period(self) -> pd.DataFrame:
        """Génère une dégradation progressive avec un léger bruit."""
        sim = self.config["simulation"]
        count = sim["degradation_end_index"] - sim["normal_end_index"]
        state = self.config["degradation_state"]
        vibration = np.linspace(state["vibration_start"], state["vibration_end"], count)
        vibration += self.rng.normal(0.0, 0.12, count)
        temperature = np.linspace(
            state["temperature_start"], state["temperature_end"], count
        )
        temperature += self.rng.normal(0.0, 0.5, count)
        health = np.linspace(state["health_start"], state["health_end"], count)
        health += self.rng.normal(0.0, 0.8, count)
        return self._period_frame(
            vibration, temperature, health, "degradation", True
        )

    def generate_critical_period(self) -> pd.DataFrame:
        """Génère la période critique du roulement."""
        sim = self.config["simulation"]
        count = sim["total_measurements"] - sim["degradation_end_index"]
        state = self.config["critical_state"]
        vibration = np.linspace(state["vibration_start"], state["vibration_end"], count)
        vibration += self.rng.normal(0.0, 0.15, count)
        temperature = np.linspace(
            state["temperature_start"], state["temperature_end"], count
        )
        temperature += self.rng.normal(0.0, 0.6, count)
        health = np.linspace(state["health_start"], state["health_end"], count)
        health += self.rng.normal(0.0, 0.8, count)
        vibration = np.clip(vibration, state["vibration_start"], state["vibration_end"])
        temperature = np.clip(
            temperature, state["temperature_start"], state["temperature_end"]
        )
        health = np.clip(health, state["health_end"], state["health_start"])
        return self._period_frame(vibration, temperature, health, "critique", True)

    def generate_dataset(self) -> pd.DataFrame:
        """Génère et réunit les trois périodes dans un DataFrame."""
        self.rng = np.random.default_rng(self.config["simulation"]["random_seed"])
        frames = [
            self.generate_normal_period(),
            self.generate_degradation_period(),
            self.generate_critical_period(),
        ]
        dataset = pd.concat(frames, ignore_index=True)
        sim = self.config["simulation"]
        timestamps = pd.date_range(
            start=datetime.now().replace(microsecond=0),
            periods=sim["total_measurements"],
            freq=pd.Timedelta(seconds=sim["interval_seconds"]),
        )
        dataset.insert(0, "timestamp", timestamps)
        decimals = {
            "vibration_rms_mm_s": 3,
            "temperature_c": 2,
            "speed_rpm": 2,
            "load_pct": 2,
            "health_score": 2,
        }
        dataset = dataset.round(decimals)
        return dataset[self.COLUMNS]

    def validate_dataset(self, dataset: pd.DataFrame) -> None:
        """Vérifie la structure, les valeurs et la cohérence du jeu de données."""
        expected_rows = self.config["simulation"]["total_measurements"]
        if len(dataset) != expected_rows:
            raise ValueError(f"Le jeu de données doit contenir exactement {expected_rows} lignes.")
        if list(dataset.columns) != self.COLUMNS:
            raise ValueError("Les colonnes du jeu de données sont absentes ou mal ordonnées.")
        if dataset.isna().any().any():
            raise ValueError("Le jeu de données contient des valeurs manquantes.")
        if not dataset["timestamp"].is_monotonic_increasing:
            raise ValueError("Les timestamps ne sont pas triés.")
        if dataset["timestamp"].duplicated().any():
            raise ValueError("Les timestamps contiennent des doublons.")
        for column in ["vibration_rms_mm_s", "temperature_c", "speed_rpm"]:
            if (dataset[column] <= 0).any():
                raise ValueError(f"La colonne '{column}' doit être strictement positive.")
        for column in ["load_pct", "health_score"]:
            if not dataset[column].between(0, 100).all():
                raise ValueError(f"La colonne '{column}' doit rester entre 0 et 100.")
        if not set(dataset["state"]).issubset({"normal", "degradation", "critique"}):
            raise ValueError("Le jeu de données contient un état non autorisé.")

        normal = dataset["state"] == "normal"
        faulty = dataset["state"].isin(["degradation", "critique"])
        if dataset.loc[normal, "fault_active"].any():
            raise ValueError("Un défaut est actif pendant la période normale.")
        if not dataset.loc[faulty, "fault_active"].all():
            raise ValueError("Le défaut doit être actif hors de la période normale.")
        if not (dataset.loc[normal, "fault_type"] == "none").all():
            raise ValueError("Le type de défaut normal doit être 'none'.")
        if not (dataset.loc[faulty, "fault_type"] == "bearing_wear").all():
            raise ValueError("Le défaut actif doit être de type 'bearing_wear'.")

    def save_dataset(self, dataset: pd.DataFrame) -> Path:
        """Enregistre le jeu de données au format CSV UTF-8."""
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        dataset.to_csv(self.csv_path, index=False, encoding="utf-8")
        return self.csv_path

    def create_plots(self, dataset: pd.DataFrame) -> list[Path]:
        """Crée les trois graphiques séparés du scénario."""
        self.plots_directory.mkdir(parents=True, exist_ok=True)
        normal_end = self.config["simulation"]["normal_end_index"]
        degradation_end = self.config["simulation"]["degradation_end_index"]
        plots = [
            ("vibration_rms_mm_s", "Évolution des vibrations", "Vibration RMS (mm/s)", "vibration.png"),
            ("temperature_c", "Évolution de la température", "Température (°C)", "temperature.png"),
            ("health_score", "Évolution du score de santé", "Score de santé", "health_score.png"),
        ]
        paths: list[Path] = []
        measurements = np.arange(1, len(dataset) + 1)
        for column, title, ylabel, filename in plots:
            figure, axis = plt.subplots(figsize=(10, 5))
            axis.plot(measurements, dataset[column], label=ylabel, linewidth=1.6)
            axis.axvline(normal_end + 1, color="orange", linestyle="--", label="Début dégradation")
            axis.axvline(degradation_end + 1, color="red", linestyle="--", label="Début état critique")
            axis.set_title(title)
            axis.set_xlabel("Numéro de mesure")
            axis.set_ylabel(ylabel)
            axis.grid(alpha=0.25)
            axis.legend()
            figure.tight_layout()
            path = self.plots_directory / filename
            figure.savefig(path, dpi=150)
            plt.close(figure)
            paths.append(path)
        return paths

    def print_summary(self, dataset: pd.DataFrame) -> None:
        """Affiche un résumé lisible de la simulation."""
        counts = dataset["state"].value_counts()
        relative_csv = self.csv_path.relative_to(self.project_root)
        relative_plots = [
            (self.plots_directory / name).relative_to(self.project_root)
            for name in ["vibration.png", "temperature.png", "health_score.png"]
        ]
        print("=" * 50)
        print(f"{self.config['project']['name']} — Simulation terminée")
        print("=" * 50)
        print(f"\nÉquipement : {self.config['simulation']['equipment_id']}")
        print(f"Nombre total de mesures : {len(dataset)}")
        print(f"\nMesures normales : {counts.get('normal', 0)}")
        print(f"Mesures en dégradation : {counts.get('degradation', 0)}")
        print(f"Mesures critiques : {counts.get('critique', 0)}")
        print(f"\nVibration minimale : {dataset['vibration_rms_mm_s'].min():.3f} mm/s")
        print(f"Vibration maximale : {dataset['vibration_rms_mm_s'].max():.3f} mm/s")
        print(f"\nTempérature minimale : {dataset['temperature_c'].min():.2f} °C")
        print(f"Température maximale : {dataset['temperature_c'].max():.2f} °C")
        print(f"\nScore de santé initial : {dataset['health_score'].iloc[0]:.2f}")
        print(f"Score de santé final : {dataset['health_score'].iloc[-1]:.2f}")
        print(f"\nFichier CSV :\n{relative_csv.as_posix()}")
        print("\nGraphiques :")
        for path in relative_plots:
            print(path.as_posix())
        print("\n" + "=" * 50)


class LineBearingSimulator(BaseEquipment):
    """Adaptation multi-équipement du roulement historique de la phase 1."""

    def generate_measurement(
        self, intensity: float, influences: dict[str, float] | None = None
    ) -> dict[str, float]:
        """Génère température, vibration, régime et santé du roulement."""
        intensity = self.apply_intensity(intensity)
        normal = self.config["normal"]
        return {
            "temperature": self.noisy(
                normal["temperature"] + 28.0 * intensity, "temperature"
            ),
            "vibration": self.noisy(
                normal["vibration"] + 7.0 * intensity, "vibration"
            ),
            "rpm": self.noisy(
                normal["rpm"] * (1.0 - 0.12 * intensity), "rpm", 1.0
            ),
            "health_score": self.health_score,
        }
