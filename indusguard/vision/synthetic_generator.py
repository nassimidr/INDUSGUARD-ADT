from __future__ import annotations

import json
import random
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml
from PIL import Image, ImageDraw

from .constants import DATASET_NAME, INDUSTRIAL_DEFECT_CLASSES
from .schemas import VisionDatasetMetadata


class SyntheticVisionDatasetGenerator:
    """Generate stylized conveyor images and YOLO labels without network access."""

    def __init__(self, root: str | Path, *, seed: int = 42, width: int = 640, height: int = 480) -> None:
        self.root = Path(root).resolve()
        self.seed = seed
        self.width = width
        self.height = height
        if self.root.parent == self.root:
            raise ValueError("The dataset root cannot be a filesystem root.")
        if width < 480 or height < 360:
            raise ValueError("Synthetic conveyor images must be at least 480x360 pixels.")

    def generate(
        self,
        total_images: int = 60,
        *,
        train_fraction: float = 0.70,
        validation_fraction: float = 0.15,
        clean: bool = True,
    ) -> VisionDatasetMetadata:
        if total_images < 12:
            raise ValueError("At least 12 images are required for balanced train/val/test splits.")
        if train_fraction <= 0 or validation_fraction <= 0 or train_fraction + validation_fraction >= 1:
            raise ValueError("Dataset split fractions are invalid.")
        if clean:
            for directory in (self.root / "images", self.root / "labels", self.root / "demo"):
                if directory.exists() and directory.parent == self.root and directory.name in {"images", "labels", "demo"}:
                    shutil.rmtree(directory)
        rng = random.Random(self.seed)
        indices = list(range(total_images))
        rng.shuffle(indices)
        train_end = round(total_images * train_fraction)
        val_end = train_end + round(total_images * validation_fraction)
        assignments = {
            **{index: "train" for index in indices[:train_end]},
            **{index: "val" for index in indices[train_end:val_end]},
            **{index: "test" for index in indices[val_end:]},
        }
        records = []
        class_counts = Counter()
        normal_images = 0
        categories: tuple[str | None, ...] = (*INDUSTRIAL_DEFECT_CLASSES, None)
        for index in range(total_images):
            defect = categories[index % len(categories)]
            split = assignments[index]
            image, boxes = self._render(rng, defect, index)
            stem = f"conveyor_{index:05d}"
            image_dir = self.root / "images" / split
            label_dir = self.root / "labels" / split
            image_dir.mkdir(parents=True, exist_ok=True)
            label_dir.mkdir(parents=True, exist_ok=True)
            image_path = image_dir / f"{stem}.png"
            label_path = label_dir / f"{stem}.txt"
            image.save(image_path, format="PNG")
            label_path.write_text("\n".join(self._yolo_line(name, box) for name, box in boxes), encoding="utf-8")
            if defect is None:
                normal_images += 1
            for name, _ in boxes:
                class_counts[name] += 1
            records.append({
                "image_id": stem,
                "split": split,
                "image_path": image_path.relative_to(self.root).as_posix(),
                "label_path": label_path.relative_to(self.root).as_posix(),
                "defects": [name for name, _ in boxes],
            })
        self._write_dataset_yaml()
        manifest = {
            "dataset_name": DATASET_NAME,
            "seed": self.seed,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "image_width": self.width,
            "image_height": self.height,
            "records": records,
            "parameters": {
                "total_images": total_images,
                "train_fraction": train_fraction,
                "validation_fraction": validation_fraction,
                "test_fraction": 1 - train_fraction - validation_fraction,
                "generator": "Pillow procedural conveyor renderer",
            },
        }
        (self.root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        split_counts = Counter(record["split"] for record in records)
        metadata = VisionDatasetMetadata(
            dataset_name=DATASET_NAME,
            seed=self.seed,
            generated_at=datetime.now(timezone.utc),
            image_width=self.width,
            image_height=self.height,
            total_images=total_images,
            splits=dict(split_counts),
            class_counts={name: class_counts[name] for name in INDUSTRIAL_DEFECT_CLASSES},
            normal_images=normal_images,
            generation_parameters=manifest["parameters"],
        )
        (self.root / "dataset_metadata.json").write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
        self._write_demo_images(records)
        return metadata

    def _render(self, rng: random.Random, defect: str | None, image_index: int) -> tuple[Image.Image, list[tuple[str, tuple[int, int, int, int]]]]:
        image = Image.new("RGB", (self.width, self.height), (24, 33, 43))
        draw = ImageDraw.Draw(image)
        draw.rectangle((30, 70, self.width - 30, self.height - 50), fill=(63, 73, 81), outline=(155, 166, 174), width=5)
        belt = (105, 105, self.width - 105, self.height - 85)
        draw.rectangle(belt, fill=(39, 47, 52), outline=(185, 195, 202), width=4)
        for y in range(125, self.height - 90, 55):
            draw.line((110, y, self.width - 110, y), fill=(86, 98, 105), width=3)
        boxes: list[tuple[str, tuple[int, int, int, int]]] = []
        if defect == "belt_misalignment":
            offset = rng.randint(25, 55)
            polygon = [(105 + offset, 105), (self.width - 105, 105), (self.width - 105 - offset, self.height - 85), (105, self.height - 85)]
            draw.polygon(polygon, fill=(47, 58, 64), outline=(245, 173, 66), width=7)
            boxes.append((defect, (95, 95, self.width - 95, self.height - 75)))
        elif defect == "obstacle":
            w, h = rng.randint(70, 125), rng.randint(60, 100)
            x = rng.randint(150, self.width - 150 - w)
            y = rng.randint(145, self.height - 120 - h)
            box = (x, y, x + w, y + h)
            draw.rounded_rectangle(box, radius=8, fill=(190, 52, 52), outline=(255, 210, 210), width=4)
            boxes.append((defect, box))
        elif defect == "material_accumulation":
            x, y = rng.randint(150, 350), rng.randint(170, 280)
            points = []
            for _ in range(rng.randint(5, 9)):
                radius = rng.randint(18, 34)
                cx, cy = x + rng.randint(-55, 55), y + rng.randint(-35, 35)
                ellipse = (cx - radius, cy - radius, cx + radius, cy + radius)
                draw.ellipse(ellipse, fill=(184, 139, 71), outline=(236, 204, 142), width=3)
                points.append(ellipse)
            box = (min(p[0] for p in points), min(p[1] for p in points), max(p[2] for p in points), max(p[3] for p in points))
            boxes.append((defect, box))
        draw.text((42, 25), f"INDUSGUARD synthetic conveyor | {defect or 'normal'} | {image_index:05d}", fill=(220, 230, 236))
        return image, boxes

    def _yolo_line(self, name: str, box: tuple[int, int, int, int]) -> str:
        x1, y1, x2, y2 = box
        class_id = INDUSTRIAL_DEFECT_CLASSES.index(name)
        x_center = ((x1 + x2) / 2) / self.width
        y_center = ((y1 + y2) / 2) / self.height
        width = (x2 - x1) / self.width
        height = (y2 - y1) / self.height
        return f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"

    def _write_dataset_yaml(self) -> None:
        content = {
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "names": list(INDUSTRIAL_DEFECT_CLASSES),
        }
        (self.root / "dataset.yaml").write_text(yaml.safe_dump(content, sort_keys=False), encoding="utf-8")

    def _write_demo_images(self, records: Iterable[dict]) -> None:
        demo = self.root / "demo"
        demo.mkdir(parents=True, exist_ok=True)
        chosen: set[str] = set()
        for record in records:
            defects = record["defects"]
            label = defects[0] if defects else "normal"
            if label in chosen:
                continue
            chosen.add(label)
            source = self.root / record["image_path"]
            shutil.copy2(source, demo / f"sample_{label}.png")
