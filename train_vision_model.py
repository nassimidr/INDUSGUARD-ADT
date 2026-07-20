from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from indusguard.vision import load_vision_config
from indusguard.vision.dataset import validate_yolo_dataset


def arguments():
    parser = argparse.ArgumentParser(description="Train a custom YOLOv8 Phase 8A detector")
    parser.add_argument("--config", default="configs/vision.yaml")
    parser.add_argument("--dataset", default="data/vision/dataset.yaml")
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--quick", action="store_true", help="Use one epoch and a small batch for technical validation")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    config = load_vision_config(args.config)
    dataset = validate_yolo_dataset(args.dataset)
    training = config.values["training"]
    seed = int(training["seed"])
    random.seed(seed); np.random.seed(seed)
    try:
        import torch
        from ultralytics import YOLO

        torch.manual_seed(seed)
        if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
        epochs = 1 if args.quick else int(args.epochs or training["epochs"])
        batch = min(4, int(training["batch_size"])) if args.quick else int(training["batch_size"])
        base_weights = str(config.values["model"]["fallback_weights"])
        run_directory = config.path("outputs/vision/training")
        model = YOLO(base_weights)
        configured_device = str(config.values["model"].get("device", "auto"))
        device = "0" if configured_device == "auto" and torch.cuda.is_available() else "cpu" if configured_device == "auto" else configured_device
        results = model.train(
            data=str(Path(args.dataset).resolve()), epochs=epochs, batch=batch,
            imgsz=int(training["image_size"]), patience=int(training["patience"]),
            seed=seed, deterministic=True, workers=int(training.get("workers", 0)),
            device=device,
            project=str(run_directory), name="phase8a", exist_ok=True, plots=True, verbose=False,
        )
        source_weights = Path(results.save_dir) / "weights" / "best.pt"
        destination = config.path(config.values["model"]["weights_path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_weights, destination)
        history_path = Path(results.save_dir) / "results.csv"
        with history_path.open(encoding="utf-8") as history_file:
            epochs_completed = sum(1 for _ in csv.DictReader(history_file))
        def portable(path: str | Path) -> str:
            resolved = Path(path).resolve()
            try:
                return resolved.relative_to(config.root).as_posix()
            except ValueError:
                return resolved.as_posix()

        dataset_summary = dict(dataset)
        dataset_summary["dataset_yaml"] = portable(dataset_summary["dataset_yaml"])
        parameters = {
            "trained_at": datetime.now(timezone.utc).isoformat(), "seed": seed,
            "epochs_requested": epochs, "epochs_completed": epochs_completed,
            "batch_size": batch, "image_size": int(training["image_size"]), "base_weights": base_weights, "device": device,
            "dataset": portable(args.dataset), "dataset_summary": dataset_summary,
            "custom_weights": portable(destination), "training_run": portable(results.save_dir),
        }
        parameter_path = config.path("outputs/vision/models/training_parameters.json")
        parameter_path.write_text(json.dumps(parameters, indent=2), encoding="utf-8")
        print(json.dumps(parameters, indent=2))
        return 0
    except Exception as exc:
        print(f"Vision training failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
