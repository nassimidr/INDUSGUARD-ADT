"""Pipeline Isolation Forest pour un type d'équipement."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .preprocessing import TARGET_COLUMNS


class IsolationForestDetector:
    """Encapsule nettoyage, standardisation et détection non supervisée."""

    def __init__(
        self, features: Sequence[str], contamination: float = 0.08,
        random_state: int = 42, n_estimators: int = 200,
    ) -> None:
        self.features = list(features)
        if TARGET_COLUMNS.intersection(self.features):
            raise ValueError("Une cible ne peut pas être utilisée comme caractéristique.")
        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", IsolationForest(
                contamination=contamination, random_state=random_state,
                n_estimators=n_estimators, n_jobs=-1,
            )),
        ])
        self.is_fitted = False

    def fit(self, data: pd.DataFrame) -> "IsolationForestDetector":
        """Entraîne le pipeline sur les seules caractéristiques déclarées."""
        if data.empty:
            raise ValueError("Aucune donnée disponible pour l'entraînement.")
        self.pipeline.fit(data[self.features])
        self.is_fitted = True
        return self

    def predict(self, data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Retourne les anomalies booléennes et un score croissant avec l'anomalie."""
        if not self.is_fitted:
            raise RuntimeError("Le modèle doit être entraîné avant la prédiction.")
        raw = self.pipeline.predict(data[self.features])
        scores = -self.pipeline.decision_function(data[self.features])
        return raw == -1, scores

    def save(self, path: str | Path) -> Path:
        """Sérialise le détecteur complet."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, destination)
        return destination

    @classmethod
    def load(cls, path: str | Path) -> "IsolationForestDetector":
        """Recharge et valide un détecteur sérialisé."""
        detector = joblib.load(Path(path))
        if not isinstance(detector, cls):
            raise TypeError("Le fichier ne contient pas un détecteur Isolation Forest.")
        return detector

