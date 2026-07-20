from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any, Callable

from .config import VisionConfig
from .exceptions import VisionModelUnavailableError
from .schemas import VisionHealthStatus


class VisionModelManager:
    """Lazy, thread-safe loader for a custom YOLO model or a technical COCO fallback."""

    def __init__(
        self,
        config: VisionConfig,
        *,
        model: Any | None = None,
        loader: Callable[[str], Any] | None = None,
        injected_custom_model: bool = True,
    ) -> None:
        self.config = config
        self._model = model
        self._loader = loader
        self._lock = Lock()
        self._load_error: str | None = None
        self.custom_model_loaded = bool(model is not None and injected_custom_model)
        self.technical_fallback = bool(model is not None and not injected_custom_model)
        self.device = self._select_device()
        model_config = config.values["model"]
        self.model_name = str(model_config["architecture"])
        self.model_version = str(model_config.get("version", "phase8a-v1"))

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self) -> Any:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            model_config = self.config.values["model"]
            custom_path = self.config.path(model_config["weights_path"])
            if custom_path.is_file():
                weights = str(custom_path)
                custom = True
            elif self.config.values["mode"] == "demo" and model_config.get("fallback_weights"):
                weights = str(model_config["fallback_weights"])
                custom = False
            else:
                raise VisionModelUnavailableError(f"Custom vision weights not found: {custom_path}")
            try:
                loader = self._loader or self._ultralytics_loader
                model = loader(weights)
                if custom:
                    self._validate_custom_names(model)
                self._model = model
                self.custom_model_loaded = custom
                self.technical_fallback = not custom
                self._load_error = None
                return model
            except VisionModelUnavailableError:
                raise
            except Exception as exc:
                self._load_error = str(exc)
                raise VisionModelUnavailableError(f"Unable to load vision model '{weights}': {exc}") from exc

    def predict(self, image: Any) -> Any:
        model = self.load()
        values = self.config.values["model"]
        try:
            return model.predict(
                source=image,
                conf=float(values["confidence_threshold"]),
                iou=float(values["iou_threshold"]),
                imgsz=int(values["image_size"]),
                device=self.device,
                verbose=False,
            )
        except Exception as exc:
            raise VisionModelUnavailableError(f"Vision inference failed: {exc}") from exc

    def status(self) -> VisionHealthStatus:
        custom_path = self.config.path(self.config.values["model"]["weights_path"])
        available = self._load_error is None and (self.loaded or custom_path.is_file() or bool(
            self.config.values["mode"] == "demo" and self.config.values["model"].get("fallback_weights")
        ))
        return VisionHealthStatus(
            enabled=bool(self.config.values["enabled"]),
            mode=str(self.config.values["mode"]),
            loaded=self.loaded,
            available=available,
            custom_model_loaded=self.custom_model_loaded,
            technical_fallback=self.technical_fallback,
            model_name=self.model_name,
            model_version=self.model_version,
            device=self.device,
            detail=self._load_error,
        )

    def _validate_custom_names(self, model: Any) -> None:
        names = getattr(model, "names", None)
        if isinstance(names, dict):
            names = [names[index] for index in sorted(names)]
        if list(names or []) != list(self.config.classes):
            raise VisionModelUnavailableError(
                "Custom model classes do not match the configured industrial vocabulary."
            )

    @staticmethod
    def _ultralytics_loader(weights: str) -> Any:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise VisionModelUnavailableError("ultralytics is not installed.") from exc
        return YOLO(weights)

    def _select_device(self) -> str:
        configured = str(self.config.values["model"].get("device", "auto"))
        if configured != "auto":
            return configured
        try:
            import torch

            return "0" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"
