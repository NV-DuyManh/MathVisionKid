"""
CRNN OCR Provider for Vietnamese Handwriting.
Consumes CRNN+CTC model checkpoint and vocabulary.
Memory-safe micro-batching and CPU/CUDA inference.
"""
from typing import List, Union, Optional, Dict, Any
from pathlib import Path
import os
import json
import logging
import threading

import torch
from torchvision import transforms
from PIL import Image

from app.ocr.provider import OcrProvider
from app.ocr.model import CRNN

logger = logging.getLogger(__name__)

IMG_H = 64
IMG_W = 1024
BLANK_IDX = 0

_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_H, IMG_W)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class CrnnOcrProvider(OcrProvider):
    """
    Production-grade adapter for the CRNN Vietnamese handwriting OCR engine.
    """

    def __init__(
        self,
        model_dir: Optional[Union[str, Path]] = None,
        device: Optional[Union[str, torch.device]] = None,
    ):
        if model_dir is None:
            # Default to services/ai-service/models/ocr/crnn_vi_handwriting_v1
            base_dir = Path(__file__).resolve().parent.parent.parent
            model_dir = base_dir / "models" / "ocr" / "crnn_vi_handwriting_v1"

        self.model_dir = Path(model_dir)
        self.weights_path = self.model_dir / "best_cer.pth"
        self.vocab_path = self.model_dir / "vocab.json"
        self.manifest_path = self.model_dir / "model_manifest.json"

        # Determine inference device (default: CPU for predictable memory & background execution)
        if device is not None:
            self.device = torch.device(device)
        else:
            env_dev = os.environ.get("OCR_DEVICE")
            if env_dev:
                self.device = torch.device(env_dev)
            else:
                self.device = torch.device("cpu")

        self._model: Optional[CRNN] = None
        self._vocab: Optional[Dict[str, int]] = None
        self._inv_vocab: Optional[Dict[int, str]] = None
        self._manifest: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()

    def _ensure_loaded(self):
        """Lazy load model weights and vocabulary safely with threading lock."""
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            if not self.weights_path.is_file():
                raise FileNotFoundError(f"OCR checkpoint not found: {self.weights_path}")
            if not self.vocab_path.is_file():
                raise FileNotFoundError(f"OCR vocab file not found: {self.vocab_path}")

            with open(self.vocab_path, "r", encoding="utf-8") as f:
                self._vocab = json.load(f)

            self._inv_vocab = {int(v): k for k, v in self._vocab.items()}

            if self.manifest_path.is_file():
                try:
                    with open(self.manifest_path, "r", encoding="utf-8") as f:
                        self._manifest = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load OCR manifest: {e}")

            model = CRNN(len(self._vocab), dropout=0.2).to(self.device)
            state = torch.load(self.weights_path, map_location=self.device, weights_only=True)
            model.load_state_dict(state)
            model.eval()
            self._model = model
            logger.info(
                f"CrnnOcrProvider loaded successfully on {self.device} "
                f"(vocab: {len(self._vocab)}, params: {sum(p.numel() for p in model.parameters()):,})"
            )

    def is_available(self) -> bool:
        return self.weights_path.is_file() and self.vocab_path.is_file()

    def get_metadata(self) -> Dict[str, Any]:
        if self._manifest is None and self.manifest_path.is_file():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self._manifest = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load OCR manifest: {e}")
        if self._manifest:
            return self._manifest
        return {
            "model_name": "Vietnamese-Handwriting-OCR-Full",
            "model_dir": str(self.model_dir),
            "weights_path": str(self.weights_path),
            "vocab_path": str(self.vocab_path),
            "device": str(self.device),
            "is_available": self.is_available(),
        }

    def _decode_logits(self, logits: torch.Tensor) -> List[str]:
        """Greedy CTC decode [B, T, C]."""
        preds = logits.argmax(2).cpu().numpy()
        texts: List[str] = []
        for b in range(preds.shape[0]):
            out, prev = [], -1
            for idx in preds[b, :]:
                if idx != BLANK_IDX and idx != prev:
                    out.append(self._inv_vocab.get(int(idx), "?"))
                prev = idx
            texts.append("".join(out))
        return texts

    def _prepare_image(self, image: Union[str, Path, Image.Image]) -> Image.Image:
        if isinstance(image, (str, Path)):
            p = Path(image)
            if not p.is_file():
                raise FileNotFoundError(f"Image not found: {p}")
            return Image.open(str(p)).convert("RGB")
        elif isinstance(image, Image.Image):
            return image.convert("RGB")
        else:
            raise TypeError(f"Expected str, Path or PIL.Image.Image, got {type(image)}")

    @torch.no_grad()
    def recognize_line(self, image: Union[str, Path, Image.Image]) -> str:
        """
        Recognize text in a single line image crop.
        """
        self._ensure_loaded()
        pil_img = self._prepare_image(image)
        x = _TRANSFORM(pil_img).unsqueeze(0).to(self.device)
        logits = self._model(x)
        res = self._decode_logits(logits)[0]
        del x, logits
        return res

    @torch.no_grad()
    def recognize_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        batch_size: int = 4,
    ) -> List[str]:
        """
        Recognize text in a batch of line image crops using memory-safe micro-batching.
        """
        self._ensure_loaded()
        if not images:
            return []

        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size}")

        results: List[str] = []
        total = len(images)

        for start_idx in range(0, total, batch_size):
            chunk = images[start_idx : start_idx + batch_size]
            tensors = []
            for item in chunk:
                pil_img = self._prepare_image(item)
                tensors.append(_TRANSFORM(pil_img))

            chunk_x = torch.stack(tensors, dim=0).to(self.device)
            chunk_logits = self._model(chunk_x)
            chunk_texts = self._decode_logits(chunk_logits)
            results.extend(chunk_texts)

            # Release tensor references immediately
            del chunk_x
            del chunk_logits

        return results
