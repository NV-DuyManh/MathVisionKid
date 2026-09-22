"""
Standalone OCR inference for the Vietnamese handwriting CRNN+CTC model.

Intended Input Contract:
  - Input unit: LINE-LEVEL cropped text/formula image (NOT an entire worksheet page).
  - Shape: Model expects RGB image with 3 channels, resized to fixed (H=64, W=1024).
  - Preprocessing:
      * Opened/converted as RGB (3 channels)
      * Resized to (Height=64, Width=1024) via bilinear interpolation
      * Converted to Tensor [0.0, 1.0]
      * Normalized with ImageNet mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
  - CTC greedy decoding: argmax per timestep -> collapse consecutive duplicates -> remove blank token (ID 0).

Usage:
    from ocr_engine import predict_text, predict_batch
    # Or directly if inside the directory:
    # from predict import predict_text, predict_batch

    text = predict_text("path/to/line_crop.jpg")
    batch_texts = predict_batch(["line1.jpg", "line2.jpg"], batch_size=4)
"""
from typing import List, Union, Optional
from pathlib import Path
import os
import json

import torch
from torchvision import transforms
from PIL import Image

try:
    from .model import CRNN
except ImportError:
    from model import CRNN

_HERE = Path(__file__).resolve().parent

IMG_H = 64
IMG_W = 1024
BLANK = 0

_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_H, IMG_W)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

_model = None
_vocab = None
_inv_vocab = None
_device = None


def get_default_device() -> torch.device:
    """Determine the default inference device based on environment or hardware."""
    env_dev = os.environ.get("OCR_DEVICE")
    if env_dev:
        return torch.device(env_dev)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load(device: Optional[Union[str, torch.device]] = None):
    """
    Load vocabulary and model weights into memory.
    Safe offline execution using torch.load(weights_only=True).
    """
    global _model, _vocab, _inv_vocab, _device

    target_device = torch.device(device) if device is not None else get_default_device()

    if _model is not None and _device == target_device:
        return

    vocab_file = _HERE / "vocab.json"
    if not vocab_file.exists():
        raise FileNotFoundError(f"Vocabulary file not found at: {vocab_file}")

    with open(vocab_file, encoding="utf-8") as f:
        _vocab = json.load(f)

    _inv_vocab = {int(v): k for k, v in _vocab.items()}
    _device = target_device

    weights_file = _HERE / "best_cer.pth"
    if not weights_file.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {weights_file}")

    model = CRNN(len(_vocab), dropout=0.2).to(_device)
    state = torch.load(weights_file, map_location=_device, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    _model = model


def _greedy_decode(logits: torch.Tensor) -> List[str]:
    """Greedy CTC decoder for raw model logits [B, T, C]."""
    preds = logits.argmax(2).cpu().numpy()
    texts = []
    for b in range(preds.shape[0]):
        out, prev = [], -1
        for idx in preds[b, :]:
            if idx != BLANK and idx != prev:
                out.append(_inv_vocab.get(int(idx), "?"))
            prev = idx
        texts.append("".join(out))
    return texts


def _prepare_image(image: Union[str, Path, Image.Image]) -> Image.Image:
    """Validate and convert input to RGB PIL Image."""
    if isinstance(image, (str, Path)):
        return Image.open(str(image)).convert("RGB")
    elif isinstance(image, Image.Image):
        return image.convert("RGB")
    else:
        raise TypeError(f"Expected str, Path or PIL.Image.Image, got {type(image)}")


@torch.no_grad()
def predict_text(
    image: Union[str, Path, Image.Image],
    device: Optional[Union[str, torch.device]] = None
) -> str:
    """
    Run line-level OCR on a single image.
    :param image: Path to image file (str/Path) or PIL Image instance.
    :param device: Optional explicit device ('cpu', 'cuda', etc.).
    :return: Recognized text string.
    """
    _load(device=device)
    img = _prepare_image(image)
    x = _TRANSFORM(img).unsqueeze(0).to(_device)
    logits = _model(x)
    return _greedy_decode(logits)[0]


@torch.no_grad()
def predict_batch(
    images: List[Union[str, Path, Image.Image]],
    batch_size: int = 4,
    device: Optional[Union[str, torch.device]] = None
) -> List[str]:
    """
    Run OCR on a list of line images using memory-safe micro-batching.

    Processes images in chunks of `batch_size` to prevent out-of-memory errors
    when processing 10-30+ worksheet crops in practical teacher workflows.

    :param images: List of image paths or PIL Image instances.
    :param batch_size: Micro-batch chunk size (default: 4, conservative and memory-safe).
    :param device: Optional explicit device ('cpu', 'cuda', etc.).
    :return: List of recognized text strings in matching order.
    """
    _load(device=device)
    if not images:
        return []

    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size}")

    results: List[str] = []
    total = len(images)

    for start_idx in range(0, total, batch_size):
        chunk_inputs = images[start_idx : start_idx + batch_size]
        tensors = []
        for im in chunk_inputs:
            pil_img = _prepare_image(im)
            tensors.append(_TRANSFORM(pil_img))

        chunk_x = torch.stack(tensors, dim=0).to(_device)
        chunk_logits = _model(chunk_x)
        chunk_texts = _greedy_decode(chunk_logits)
        results.extend(chunk_texts)

        # Explicitly release chunk tensors between iterations
        del chunk_x
        del chunk_logits

    return results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print("Usage: python predict.py <image_path_1> [image_path_2 ...]")
        print("   or: python -m ocr_engine.predict <image_path>")
        raise SystemExit(1)
    for p in sys.argv[1:]:
        res = predict_text(p)
        print(f"{p} -> {res}")