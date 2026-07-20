from PIL import Image
import pytest

from indusguard.vision.exceptions import InvalidImageError
from indusguard.vision.preprocessing import load_and_preprocess_image
from tests.vision_helpers import make_image


@pytest.mark.parametrize("mode", ["RGB", "L", "RGBA"])
def test_supported_images_are_converted_to_rgb(tmp_path, mode):
    image = make_image(tmp_path / f"image_{mode}.png", mode)
    processed = load_and_preprocess_image(image)
    assert processed.image.mode == "RGB"
    assert (processed.width, processed.height) == (120, 90)


def test_missing_corrupt_extension_and_small_images_are_rejected(tmp_path):
    with pytest.raises(InvalidImageError): load_and_preprocess_image(tmp_path / "missing.png")
    corrupt = tmp_path / "corrupt.png"; corrupt.write_bytes(b"not an image")
    with pytest.raises(InvalidImageError): load_and_preprocess_image(corrupt)
    unsupported = tmp_path / "image.bmp"; Image.new("RGB", (20, 20)).save(unsupported)
    with pytest.raises(InvalidImageError): load_and_preprocess_image(unsupported)
    tiny = make_image(tmp_path / "tiny.png", size=(8, 8))
    with pytest.raises(InvalidImageError): load_and_preprocess_image(tiny)


def test_resize_never_overwrites_original(tmp_path):
    path = make_image(tmp_path / "large.png", size=(200, 100)); original = path.read_bytes()
    processed = load_and_preprocess_image(path, maximum_dimension=80)
    assert processed.image.size == (80, 40)
    assert path.read_bytes() == original
