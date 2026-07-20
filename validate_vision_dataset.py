from __future__ import annotations

import argparse
import json

from indusguard.vision.dataset import validate_yolo_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate YOLO labels, splits and leakage")
    parser.add_argument("--dataset", default="data/vision/dataset.yaml")
    args = parser.parse_args()
    print(json.dumps(validate_yolo_dataset(args.dataset), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
