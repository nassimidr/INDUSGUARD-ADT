import hashlib

from indusguard.vision.dataset import validate_yolo_dataset
from indusguard.vision.synthetic_generator import SyntheticVisionDatasetGenerator


def test_synthetic_dataset_is_reproducible_split_and_leak_free(tmp_path):
    first = tmp_path / "first" / "vision"; second = tmp_path / "second" / "vision"
    one = SyntheticVisionDatasetGenerator(first, seed=17, width=640, height=480).generate(20)
    two = SyntheticVisionDatasetGenerator(second, seed=17, width=640, height=480).generate(20)
    result = validate_yolo_dataset(first / "dataset.yaml")
    assert sum(one.splits.values()) == 20 and one.splits == two.splits
    assert result["unique_images"] == 20 and result["annotations"] == 15
    first_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((first / "images").rglob("*.png"))]
    second_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((second / "images").rglob("*.png"))]
    assert first_hashes == second_hashes
    assert (first / "demo" / "sample_normal.png").is_file()
