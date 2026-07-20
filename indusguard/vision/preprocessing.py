from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from .constants import SUPPORTED_EXTENSIONS
from .exceptions import InvalidImageError


@dataclass(frozen=True)
class ProcessedImage:
    path: Path
    image: Image.Image
    width: int
    height: int


def load_and_preprocess_image(
    path: str | Path,
    *,
    maximum_dimension: int | None = None,
    minimum_dimension: int = 16,
) -> ProcessedImage:
    source = Path(path).resolve()
    if not source.is_file():
        raise InvalidImageError(f"Image file does not exist: {source}")
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise InvalidImageError(f"Unsupported image extension: {source.suffix}")
    try:
        with Image.open(source) as opened:
            opened.verify()
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError(f"Corrupt or unreadable image: {source}") from exc
    width, height = image.size
    if width < minimum_dimension or height < minimum_dimension:
        raise InvalidImageError(
            f"Image dimensions must be at least {minimum_dimension}x{minimum_dimension}; got {width}x{height}."
        )
    if maximum_dimension and max(width, height) > maximum_dimension:
        image.thumbnail((maximum_dimension, maximum_dimension), Image.Resampling.LANCZOS)
        width, height = image.size
    return ProcessedImage(source, image.copy(), width, height)
