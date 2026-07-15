"""Gestion des quatre classificateurs de panne."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ml_fault_classifier import MLFaultClassifier
from .preprocessing import split_equipment_data


class FaultModelManager:
    """Entraîne, persiste et applique un modèle par équipement."""

    def __init__(self, config: dict[str, Any], project_root: str | Path) -> None:
        self.config = config
        self.project_root = Path(project_root)
        self.models_directory = self.project_root / config["paths"]["models_directory"]
        self.models: dict[str, MLFaultClassifier] = {}
        self.test_indices: set[int] = set()

    def train(self, data: pd.DataFrame) -> None:
        """Entraîne les modèles et mémorise uniquement les index de test."""
        self.test_indices.clear()
        for equipment_type, features in self.config["features"].items():
            split = split_equipment_data(
                data, equipment_type, features,
                float(self.config["model"]["test_size"]),
                int(self.config["model"]["random_seed"]),
            )
            model = MLFaultClassifier(features, self.config["model"]).fit(
                split.x_train, split.y_train
            )
            model.save(self._model_path(equipment_type))
            self.models[equipment_type] = model
            self.test_indices.update(int(index) for index in split.x_test.index)

    def load(self) -> None:
        """Recharge les modèles et signale clairement tout fichier absent."""
        missing = [kind for kind in self.config["features"] if not self._model_path(kind).is_file()]
        if missing:
            raise FileNotFoundError(f"Modèles de diagnostic absents : {missing}")
        self.models = {
            kind: MLFaultClassifier.load(self._model_path(kind))
            for kind in self.config["features"]
        }

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Retourne la classe et sa probabilité maximale pour chaque ligne."""
        if not self.models:
            raise RuntimeError("Aucun modèle de diagnostic disponible.")
        result = pd.DataFrame(index=data.index)
        result["ml_predicted_fault"] = "unknown_fault"
        result["ml_confidence"] = 0.0
        for kind, model in self.models.items():
            mask = data["equipment_type"] == kind
            predictions, confidence = model.predict(data.loc[mask])
            result.loc[mask, "ml_predicted_fault"] = predictions
            result.loc[mask, "ml_confidence"] = confidence
        result["ml_confidence"] = result["ml_confidence"].astype(float)
        return result

    def evaluation_mask(self, data: pd.DataFrame) -> pd.Series:
        return data.index.isin(self.test_indices)

    def _model_path(self, equipment_type: str) -> Path:
        return self.models_directory / f"{equipment_type}_fault_classifier.joblib"
