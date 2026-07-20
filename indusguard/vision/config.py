from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .constants import INDUSTRIAL_DEFECT_CLASSES


@dataclass(frozen=True)
class VisionConfig:
    root: Path
    values: dict[str, Any]

    def path(self, value: str | Path) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (self.root / path).resolve()

    @property
    def classes(self) -> tuple[str, ...]:
        return tuple(self.values["classes"])


def load_vision_config(path: str | Path = "configs/vision.yaml") -> VisionConfig:
    source = Path(path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    values = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    required = {"enabled", "mode", "model", "classes", "camera", "outputs", "agent", "training", "dataset"}
    missing = required - set(values)
    if missing:
        raise ValueError(f"Vision configuration sections missing: {sorted(missing)}")
    if values["mode"] not in {"demo", "camera"}:
        raise ValueError("Vision mode must be 'demo' or 'camera'.")
    classes = tuple(values["classes"])
    if not classes or len(classes) != len(set(classes)):
        raise ValueError("Vision classes must be non-empty and unique.")
    unknown = set(classes) - set(INDUSTRIAL_DEFECT_CLASSES)
    if unknown:
        raise ValueError(f"Unsupported configured vision classes: {sorted(unknown)}")
    for key in ("confidence_threshold", "iou_threshold"):
        value = float(values["model"][key])
        if not 0 <= value <= 1:
            raise ValueError(f"model.{key} must be between 0 and 1.")
    return VisionConfig(source.parent.parent, values)
