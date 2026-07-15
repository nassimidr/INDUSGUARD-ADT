"""Cycle de vie des modèles Isolation Forest par équipement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .isolation_forest_detector import IsolationForestDetector


class ModelManager:
    """Entraîne, sauvegarde, recharge et applique quatre modèles spécialisés."""

    def __init__(self, config: dict[str, Any], project_root: str | Path) -> None:
        self.config = config
        self.project_root = Path(project_root)
        self.models_directory = self.project_root / config["paths"]["models_directory"]
        self.models: dict[str, IsolationForestDetector] = {}
        self.training_indices: set[int] = set()

    def train(self, data: pd.DataFrame) -> None:
        """Entraîne chronologiquement sur une proportion des seules lignes normales."""
        forest = self.config["isolation_forest"]
        train_fraction = float(self.config["train_fraction"])
        self.training_indices.clear()
        for equipment_type, features in self.config["features"].items():
            subset = data[data["equipment_type"] == equipment_type]
            normal = subset[subset["operating_state"] == "normal"].sort_values("timestamp")
            train_size = max(10, int(len(normal) * train_fraction))
            training = normal.iloc[:train_size]
            detector = IsolationForestDetector(
                features, contamination=float(forest["contamination"]),
                random_state=int(forest["random_seed"]),
                n_estimators=int(forest["n_estimators"]),
            ).fit(training)
            detector.save(self.models_directory / f"{equipment_type}_isolation_forest.joblib")
            self.models[equipment_type] = detector
            self.training_indices.update(int(index) for index in training.index)

    def load(self) -> None:
        """Recharge tous les modèles configurés."""
        self.models = {
            equipment_type: IsolationForestDetector.load(
                self.models_directory / f"{equipment_type}_isolation_forest.joblib"
            )
            for equipment_type in self.config["features"]
        }

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Applique le modèle correspondant au type de chaque ligne."""
        if not self.models:
            raise RuntimeError("Aucun modèle disponible.")
        output = pd.DataFrame(index=data.index)
        output["isolation_forest_prediction"] = False
        output["anomaly_score"] = np.nan
        for equipment_type, detector in self.models.items():
            mask = data["equipment_type"] == equipment_type
            predictions, scores = detector.predict(data.loc[mask])
            output.loc[mask, "isolation_forest_prediction"] = predictions
            output.loc[mask, "anomaly_score"] = scores
        output["isolation_forest_prediction"] = output["isolation_forest_prediction"].astype(bool)
        return output

    def evaluation_mask(self, data: pd.DataFrame) -> pd.Series:
        """Exclut les lignes ayant servi à l'entraînement de l'évaluation."""
        return ~data.index.isin(self.training_indices)

