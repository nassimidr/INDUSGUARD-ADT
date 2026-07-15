"""Caractéristiques temporelles calculées uniquement avec le passé."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


def engineered_feature_names(
    base_features: Sequence[str], windows: Sequence[int]
) -> list[str]:
    """Retourne les capteurs et noms de caractéristiques dérivées."""
    names = list(base_features)
    for sensor in base_features:
        for window in windows:
            names.extend([
                f"{sensor}_rolling_mean_{window}",
                f"{sensor}_rolling_std_{window}",
            ])
        names.append(f"{sensor}_slope")
    names.append("sensor_delta")
    return names


def create_temporal_features(
    data: pd.DataFrame,
    feature_map: Mapping[str, Sequence[str]],
    windows: Sequence[int],
    slope_window: int,
) -> pd.DataFrame:
    """Calcule rollings, écarts-types et pentes causales par trajectoire."""
    if any(int(window) <= 0 for window in windows) or int(slope_window) <= 1:
        raise ValueError("Les fenêtres temporelles doivent être positives.")
    output = data.sort_values(["asset_run_id", "cycle"]).copy()
    for equipment_type, sensors in feature_map.items():
        mask = output["equipment_type"] == equipment_type
        subset = output.loc[mask]
        groups = subset["asset_run_id"]
        deltas: list[pd.Series] = []
        for sensor in sensors:
            series = pd.to_numeric(subset[sensor], errors="coerce")
            grouped = series.groupby(groups, sort=False)
            for window in windows:
                rolling_mean = grouped.transform(
                    lambda values, size=int(window): values.rolling(size, min_periods=1).mean()
                )
                rolling_std = grouped.transform(
                    lambda values, size=int(window): values.rolling(size, min_periods=1).std(ddof=0)
                )
                output.loc[mask, f"{sensor}_rolling_mean_{window}"] = rolling_mean
                output.loc[mask, f"{sensor}_rolling_std_{window}"] = rolling_std.fillna(0.0)
            slope = grouped.diff(periods=int(slope_window) - 1) / (int(slope_window) - 1)
            output.loc[mask, f"{sensor}_slope"] = slope.fillna(0.0)
            deltas.append(grouped.diff().abs().fillna(0.0))
        output.loc[mask, "sensor_delta"] = pd.concat(deltas, axis=1).mean(axis=1)
    return output

