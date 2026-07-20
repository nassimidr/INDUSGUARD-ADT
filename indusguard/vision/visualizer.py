from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .detector import RawVisionDetection


COLORS = {
    "belt_misalignment": (255, 181, 71),
    "obstacle": (255, 85, 105),
    "material_accumulation": (87, 211, 198),
    "unknown_defect": (190, 190, 190),
}


def save_annotated_image(
    image: Image.Image,
    detections: list[RawVisionDetection],
    destination: str | Path,
) -> Path:
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for detection in detections:
        color = COLORS.get(detection.defect_type, COLORS["unknown_defect"])
        draw.rectangle(detection.box, outline=color, width=5)
        label = f"{detection.defect_type} {detection.confidence:.2f}"
        x, y = detection.box[0], max(0, detection.box[1] - 18)
        draw.rectangle((x, y, x + max(120, len(label) * 7), y + 18), fill=color)
        draw.text((x + 3, y + 2), label, fill=(5, 14, 22))
    annotated.save(output)
    return output.resolve()
