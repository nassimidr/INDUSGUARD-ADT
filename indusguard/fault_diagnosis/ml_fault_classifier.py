"""Classificateur supervisé interprétable des types de pannes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from .preprocessing import FORBIDDEN_FEATURES


class MLFaultClassifier:
    """Pipeline médiane + Random Forest pour un équipement."""

    def __init__(self, features: Sequence[str], parameters: dict[str, Any]) -> None:
        self.features = list(features)
        if FORBIDDEN_FEATURES.intersection(self.features):
            raise ValueError("Les cibles ne peuvent pas être utilisées par le modèle.")
        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", RandomForestClassifier(
                n_estimators=int(parameters.get("n_estimators", 150)),
                max_depth=parameters.get("max_depth"),
                min_samples_leaf=int(parameters.get("min_samples_leaf", 2)),
                class_weight="balanced",
                random_state=int(parameters.get("random_seed", 42)),
                n_jobs=-1,
            )),
        ])
        self.is_fitted = False

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "MLFaultClassifier":
        if features.empty or target.nunique() < 2:
            raise ValueError("Au moins deux classes sont requises pour l'entraînement.")
        self.pipeline.fit(features[self.features], target)
        self.is_fitted = True
        return self

    def predict(self, features: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        if not self.is_fitted:
            raise RuntimeError("Le classificateur doit être entraîné.")
        probabilities = self.pipeline.predict_proba(features[self.features])
        classes = self.pipeline.named_steps["classifier"].classes_
        best = probabilities.argmax(axis=1)
        return classes[best], probabilities[np.arange(len(best)), best]

    def save(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, destination)
        return destination

    @classmethod
    def load(cls, path: str | Path) -> "MLFaultClassifier":
        model = joblib.load(Path(path))
        if not isinstance(model, cls):
            raise TypeError("Le fichier ne contient pas un classificateur de panne.")
        return model

