from __future__ import annotations

import argparse
import json

from indusguard.vision import load_vision_config
from indusguard.vision.evaluator import evaluate_yolo_model


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate custom Phase 8A weights on a YOLO split")
    parser.add_argument("--config", default="configs/vision.yaml")
    parser.add_argument("--weights", default="outputs/vision/models/best.pt")
    parser.add_argument("--dataset", default="data/vision/dataset.yaml")
    parser.add_argument("--split", choices=["train", "val", "test"], default="test")
    args = parser.parse_args()
    try:
        result = evaluate_yolo_model(load_vision_config(args.config), args.weights, args.dataset, split=args.split)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"Vision evaluation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
