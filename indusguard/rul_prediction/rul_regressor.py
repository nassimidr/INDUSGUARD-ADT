"""Pipeline Random Forest de régression RUL."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from .preprocessing import validate_feature_columns
from .uncertainty import prediction_interval


class RULRegressor:
    """Régression RUL non négative avec intervalle empirique des arbres."""

    def __init__(self, features: Sequence[str], parameters: dict[str, Any]) -> None:
        self.features = validate_feature_columns(features)
        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("regressor", RandomForestRegressor(
                n_estimators=int(parameters.get("n_estimators", 120)),
                max_depth=parameters.get("max_depth"),
                min_samples_leaf=int(parameters.get("min_samples_leaf", 2)),
                random_state=int(parameters.get("random_seed", 42)),
                n_jobs=-1,
            )),
        ])
        self.is_fitted = False

    def fit(self, data: pd.DataFrame, target: pd.Series) -> "RULRegressor":
        if data.empty:
            raise ValueError("Le modèle RUL requiert des données.")
        self.pipeline.fit(data[self.features], target)
        self.is_fitted = True
        return self

    def predict(self, data: pd.DataFrame) -> np.ndarray:
        self._require_fitted()
        return np.clip(self.pipeline.predict(data[self.features]), 0, None)

    def predict_with_interval(
        self, data: pd.DataFrame, lower_percentile: float, upper_percentile: float
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        self._require_fitted()
        transformed = self.pipeline.named_steps["imputer"].transform(data[self.features])
        forest = self.pipeline.named_steps["regressor"]
        trees = np.vstack([tree.predict(transformed) for tree in forest.estimators_])
        return prediction_interval(trees, lower_percentile, upper_percentile)

    def feature_importances(self) -> dict[str, float]:
        self._require_fitted()
        values = self.pipeline.named_steps["regressor"].feature_importances_
        return dict(sorted(zip(self.features, values), key=lambda item: item[1], reverse=True))

    def save(self, path: str | Path) -> Path:
        destination = Path(path); destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, destination); return destination

    @classmethod
    def load(cls, path: str | Path) -> "RULRegressor":
        model = joblib.load(Path(path))
        if not isinstance(model, cls):
            raise TypeError("Le fichier ne contient pas un modèle RUL.")
        return model

    def _require_fitted(self) -> None:
        if not self.is_fitted:
            raise RuntimeError("Le modèle RUL doit être entraîné.")
