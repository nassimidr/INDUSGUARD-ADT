class VisionError(RuntimeError):
    """Base error for the vision subsystem."""


class InvalidImageError(VisionError):
    """The input is absent, unsupported, corrupt, or has invalid dimensions."""


class VisionModelUnavailableError(VisionError):
    """No usable vision model can be loaded."""


class VisionDatasetError(VisionError):
    """The dataset structure or annotations are invalid."""
