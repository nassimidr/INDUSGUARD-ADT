"""Entraînement, persistance et application des quatre modèles RUL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .baseline_estimator import HealthBaselineEstimator
from .feature_engineering import engineered_feature_names
from .preprocessing import split_by_trajectory
from .rul_regressor import RULRegressor


class RULModelManager:
    """Gère un modèle et une baseline par type d'équipement."""

    def __init__(self, config: dict[str, Any], project_root: str | Path) -> None:
        self.config = config
        self.project_root = Path(project_root)
        self.models_directory = self.project_root / config["paths"]["models_directory"]
        self.models: dict[str, RULRegressor] = {}
        self.baselines: dict[str, HealthBaselineEstimator] = {}
        self.train_runs: dict[str, frozenset[str]] = {}
        self.test_runs: dict[str, frozenset[str]] = {}

    def train(self, data: pd.DataFrame) -> None:
        """Sépare par trajectoire, entraîne et sauvegarde quatre forêts."""
        windows = self.config["feature_engineering"]["rolling_windows"]
        for equipment_type, base_features in self.config["features"].items():
            split = split_by_trajectory(
                data, equipment_type, self.config["model"]["test_size"],
                self.config["model"]["random_seed"],
            )
            features = engineered_feature_names(base_features, windows)
            target = split.train["rul_steps"]
            baseline = HealthBaselineEstimator().fit(split.train, target)
            model = RULRegressor(features, self.config["model"]).fit(split.train, target)
            model.save(self._model_path(equipment_type))
            self.models[equipment_type] = model
            self.baselines[equipment_type] = baseline
            self.train_runs[equipment_type] = split.train_runs
            self.test_runs[equipment_type] = split.test_runs
        self._save_metadata()

    def load(self) -> None:
        """Recharge les modèles et les identifiants de test persistés."""
        missing = [kind for kind in self.config["features"] if not self._model_path(kind).is_file()]
        if missing:
            raise FileNotFoundError(f"Modèles RUL absents : {missing}")
        self.models = {
            kind: RULRegressor.load(self._model_path(kind))
            for kind in self.config["features"]
        }
        metadata_path = self.models_directory / "split_metadata.json"
        if metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.train_runs = {kind: frozenset(values) for kind, values in metadata["train_runs"].items()}
            self.test_runs = {kind: frozenset(values) for kind, values in metadata["test_runs"].items()}

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Retourne prédiction ML, baseline et intervalle pour chaque ligne."""
        if not self.models:
            raise RuntimeError("Aucun modèle RUL disponible.")
        result = pd.DataFrame(index=data.index)
        for column in ["predicted_rul_steps", "rul_lower_bound", "rul_upper_bound", "baseline_rul_steps"]:
            result[column] = np.nan
        uncertainty = self.config["uncertainty"]
        for kind, model in self.models.items():
            mask = data["equipment_type"] == kind
            prediction, lower, upper = model.predict_with_interval(
                data.loc[mask], uncertainty["lower_percentile"], uncertainty["upper_percentile"]
            )
            result.loc[mask, "predicted_rul_steps"] = prediction
            result.loc[mask, "rul_lower_bound"] = lower
            result.loc[mask, "rul_upper_bound"] = upper
            if kind in self.baselines:
                result.loc[mask, "baseline_rul_steps"] = self.baselines[kind].predict(data.loc[mask])
        return result

    def evaluation_mask(self, data: pd.DataFrame) -> pd.Series:
        all_test_runs = set().union(*self.test_runs.values()) if self.test_runs else set()
        return data["asset_run_id"].isin(all_test_runs)

    def top_features(self, equipment_type: str, count: int = 3) -> tuple[str, ...]:
        importances = self.models[equipment_type].feature_importances()
        return tuple(list(importances)[:count])

    def _model_path(self, equipment_type: str) -> Path:
        return self.models_directory / f"{equipment_type}_rul_model.joblib"

    def _save_metadata(self) -> None:
        self.models_directory.mkdir(parents=True, exist_ok=True)
        metadata = {
            "train_runs": {kind: sorted(values) for kind, values in self.train_runs.items()},
            "test_runs": {kind: sorted(values) for kind, values in self.test_runs.items()},
        }
        (self.models_directory / "split_metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

