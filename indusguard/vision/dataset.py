from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

from .constants import INDUSTRIAL_DEFECT_CLASSES, SUPPORTED_EXTENSIONS
from .exceptions import VisionDatasetError


def validate_yolo_dataset(dataset_yaml: str | Path) -> dict:
    source = Path(dataset_yaml).resolve()
    if not source.is_file():
        raise VisionDatasetError(f"Dataset YAML not found: {source}")
    config = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    names = config.get("names")
    if list(names or []) != list(INDUSTRIAL_DEFECT_CLASSES):
        raise VisionDatasetError("Dataset classes do not match the controlled industrial vocabulary.")
    root = Path(config.get("path", source.parent))
    if not root.is_absolute():
        root = (source.parent / root).resolve()
    hashes: dict[str, str] = {}
    split_counts: dict[str, int] = {}
    split_annotations: dict[str, int] = {}
    class_counts = Counter()
    annotation_count = 0
    for split in ("train", "val", "test"):
        image_dir = root / str(config.get(split, f"images/{split}"))
        if not image_dir.is_dir():
            raise VisionDatasetError(f"Missing image split directory: {image_dir}")
        images = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS)
        split_counts[split] = len(images)
        split_annotations[split] = 0
        for image_path in images:
            digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
            if digest in hashes:
                raise VisionDatasetError(
                    f"Data leakage: {image_path} duplicates an image from split {hashes[digest]}."
                )
            hashes[digest] = split
            label_path = root / "labels" / split / f"{image_path.stem}.txt"
            if not label_path.is_file():
                raise VisionDatasetError(f"Missing YOLO label: {label_path}")
            for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) != 5:
                    raise VisionDatasetError(f"Invalid label format at {label_path}:{line_number}")
                class_id = int(parts[0])
                coordinates = [float(value) for value in parts[1:]]
                if class_id not in range(len(INDUSTRIAL_DEFECT_CLASSES)) or not all(0 <= value <= 1 for value in coordinates):
                    raise VisionDatasetError(f"Invalid label value at {label_path}:{line_number}")
                class_counts[INDUSTRIAL_DEFECT_CLASSES[class_id]] += 1
                annotation_count += 1
                split_annotations[split] += 1
    if not all(split_counts.values()):
        raise VisionDatasetError("Every dataset split must contain at least one image.")
    return {
        "dataset_yaml": source.as_posix(),
        "splits": split_counts,
        "split_annotations": split_annotations,
        "class_counts": dict(class_counts),
        "annotations": annotation_count,
        "unique_images": len(hashes),
    }


def load_manifest(path: str | Path) -> dict:
    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisionDatasetError(f"Invalid dataset manifest: {source}") from exc
