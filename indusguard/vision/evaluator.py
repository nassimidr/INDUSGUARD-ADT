from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import VisionConfig
from .dataset import validate_yolo_dataset
from .exceptions import VisionModelUnavailableError


def evaluate_yolo_model(
    config: VisionConfig,
    weights: str | Path,
    dataset_yaml: str | Path,
    *,
    split: str = "test",
) -> dict[str, Any]:
    weights_path = Path(weights).resolve()
    if not weights_path.is_file():
        raise VisionModelUnavailableError(f"Custom vision weights not found: {weights_path}")
    dataset = validate_yolo_dataset(dataset_yaml)
    from ultralytics import YOLO

    model = YOLO(str(weights_path))
    configured_device = str(config.values["model"].get("device", "auto"))
    try:
        import torch
        device = "0" if configured_device == "auto" and torch.cuda.is_available() else "cpu" if configured_device == "auto" else configured_device
    except ImportError:
        device = "cpu" if configured_device == "auto" else configured_device
    started = time.perf_counter()
    metrics = model.val(
        data=str(Path(dataset_yaml).resolve()),
        split=split,
        imgsz=int(config.values["model"]["image_size"]),
        device=device,
        project=str(config.path("outputs/vision/reports")),
        name=f"evaluation_{split}",
        exist_ok=True,
        plots=True,
        verbose=False,
    )
    elapsed = time.perf_counter() - started
    names = model.names if isinstance(model.names, dict) else dict(enumerate(model.names))
    maps = list(getattr(metrics.box, "maps", []))
    by_class = {
        str(names[index]): {"map50_95": float(maps[index]) if index < len(maps) else None}
        for index in range(len(names))
    }
    try:
        displayed_weights = weights_path.relative_to(config.root).as_posix()
    except ValueError:
        displayed_weights = weights_path.as_posix()
    output = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "weights": displayed_weights,
        "split": split,
        "images": dataset["splits"][split],
        "annotations": dataset["split_annotations"][split],
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "map50": float(metrics.box.map50),
        "map50_95": float(metrics.box.map),
        "per_class": by_class,
        "average_inference_ms": float(getattr(metrics, "speed", {}).get("inference", 0.0)),
        "wall_seconds": elapsed,
    }
    metrics_path = config.path("outputs/vision/metrics/vision_metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    report = config.path("outputs/vision/reports/vision_evaluation.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Vision model evaluation\n\n"
        f"- Weights: `{output['weights']}`\n"
        f"- Split: `{split}` ({output['images']} images)\n"
        f"- Precision: {output['precision']:.6f}\n"
        f"- Recall: {output['recall']:.6f}\n"
        f"- mAP50: {output['map50']:.6f}\n"
        f"- mAP50-95: {output['map50_95']:.6f}\n"
        f"- Average inference: {output['average_inference_ms']:.3f} ms\n\n"
        "These metrics are measured on the generated synthetic test split and do not establish industrial validity.\n",
        encoding="utf-8",
    )
    return output
