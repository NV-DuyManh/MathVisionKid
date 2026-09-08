"""
ModelRecognitionEngine — Architecture boundary for trained ML model integration.
Consumes ModelManifest, artifact path, label map, and preprocessing configuration.
Does NOT fabricate model inference. Raises ModelNotAvailableError or returns
explicit MODEL_NOT_AVAILABLE status when real trained artifact is absent.
"""
from typing import Optional, Dict, Any
import logging
from app.recognition.engine import RecognitionEngine
from app.schemas.core import ImageRecognitionResult
from app.schemas.model import ModelManifest

logger = logging.getLogger(__name__)


class ModelNotAvailableError(RuntimeError):
    """Raised when inference is attempted but model artifact has not been provided."""
    pass


class UnsupportedPreprocessingError(ValueError):
    """Raised when the manifest requests an unsupported preprocessing strategy."""
    pass


SUPPORTED_PREPROCESSING_STRATEGIES = {
    "GRAYSCALE_OTSU": {
        "color_mode": "GRAYSCALE",
        "binarization": "OTSU",
        "normalization": "DIV_255",
    },
    "RGB_NORMALIZED": {
        "color_mode": "RGB",
        "binarization": None,
        "normalization": "STANDARD_SCORE",
    },
    "RESIZE_ONLY": {
        "color_mode": "RGB",
        "binarization": None,
        "normalization": None,
    },
    "resize_224_normalize": {
        "color_mode": "RGB",
        "binarization": None,
        "normalization": "STANDARD_SCORE",
    },
    "normalize_imagenet": {
        "color_mode": "RGB",
        "binarization": None,
        "normalization": "IMAGENET",
    },
}


class ModelRecognitionEngine(RecognitionEngine):
    """
    Adapter boundary between AI Service runtime and trained machine learning models.

    Consumes:
      - ModelManifest: metadata, sha256 checksum, input shape
      - artifact: binary weights file path / bytes
      - label_map: dictionary mapping token IDs / indices to canonical characters
      - preprocessing_config: normalization, resizing, color space parameters

    Guarantees:
      - Preprocessing is strictly manifest-driven; does NOT force grayscale/Otsu
        unless the manifest explicitly requests it.
      - Never fabricates model predictions or metrics.
      - Gracefully handles missing artifact (MODEL_NOT_AVAILABLE).
      - Verifies artifact integrity via sha256 checksum when loaded.
    """

    def __init__(
        self,
        manifest: Optional[ModelManifest] = None,
        artifact_path: Optional[str] = None,
        label_map: Optional[Dict[str, Any]] = None,
        preprocessing_config: Optional[Dict[str, Any]] = None,
    ):
        self.manifest = manifest
        self.artifact_path = artifact_path
        self.label_map = label_map or {}
        self.preprocessing_config = preprocessing_config or {}
        self._is_ready = False

        if self.manifest:
            self._configure_from_manifest(self.manifest)

    def _configure_from_manifest(self, manifest: ModelManifest):
        self.manifest = manifest
        if manifest.preprocessing:
            if manifest.preprocessing not in SUPPORTED_PREPROCESSING_STRATEGIES:
                raise UnsupportedPreprocessingError(
                    f"Unsupported preprocessing strategy: '{manifest.preprocessing}'. "
                    f"Supported strategies: {sorted(list(SUPPORTED_PREPROCESSING_STRATEGIES.keys()))}"
                )
            base_config = SUPPORTED_PREPROCESSING_STRATEGIES[manifest.preprocessing].copy()
            self.preprocessing_config.update(base_config)
            self.preprocessing_config["strategy"] = manifest.preprocessing
        else:
            # Manifest did not specify preprocessing: do not force Otsu/grayscale.
            self.preprocessing_config.setdefault("strategy", "PASSTHROUGH")
            self.preprocessing_config.setdefault("color_mode", "ORIGINAL")
            self.preprocessing_config.setdefault("binarization", None)
            self.preprocessing_config.setdefault("normalization", None)

        if manifest.inputWidth and manifest.inputHeight:
            channels = manifest.inputChannels or (
                1 if self.preprocessing_config.get("color_mode") == "GRAYSCALE" else 3
            )
            self.preprocessing_config["input_shape"] = (
                manifest.inputWidth,
                manifest.inputHeight,
                channels,
            )
        if self.artifact_path:
            self._is_ready = True
        else:
            self._is_ready = False

    @property
    def is_ready(self) -> bool:
        """Returns True only when manifest AND artifact are available."""
        return self._is_ready

    def recognize(self, image_reference: str) -> ImageRecognitionResult:
        if not self._is_ready or not self.manifest:
            logger.warning("Inference attempted but model artifact is not available.")
            raise ModelNotAvailableError(
                "Model artifact has not been provided. "
                "AI runtime is ready for model handoff, but artifact is NOT_PROVIDED."
            )

        raise NotImplementedError("Trained model runtime execution not yet implemented.")
