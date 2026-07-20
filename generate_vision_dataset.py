from __future__ import annotations

import argparse

from indusguard.vision import load_vision_config
from indusguard.vision.synthetic_generator import SyntheticVisionDatasetGenerator


def arguments():
    parser = argparse.ArgumentParser(description="Generate the offline synthetic Phase 8A dataset")
    parser.add_argument("--config", default="configs/vision.yaml")
    parser.add_argument("--count", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = arguments()
    config = load_vision_config(args.config)
    values = config.values["dataset"]
    generator = SyntheticVisionDatasetGenerator(
        config.path(values["root"]), seed=int(values["seed"]),
        width=int(values["image_width"]), height=int(values["image_height"]),
    )
    metadata = generator.generate(
        args.count, train_fraction=float(values["train_fraction"]),
        validation_fraction=float(values["validation_fraction"]),
    )
    print(metadata.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
