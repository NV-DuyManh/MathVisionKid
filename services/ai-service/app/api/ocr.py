import io
import time
import base64
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from PIL import Image

from app.ocr.factory import get_ocr_provider
from app.ocr.crnn_provider import CrnnOcrProvider
from app.schemas.ocr_pilot import OcrRecognizeLineResponse, OcrRecognizeLineRequest
from app.image.resolver import ImageSourceResolver
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

CHECKPOINT_SHA256 = "a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941"
VOCAB_SHA256 = "6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d"

@router.post("/recognize-line", response_model=OcrRecognizeLineResponse)
async def recognize_line(request: Request):
    """
    Dedicated OCR Pilot endpoint for single text-line Vietnamese handwriting recognition.
    Strictly isolated from YOLO, StructuredParser, and ArithmeticValidator.
    Supports raw image bytes (image/jpeg, image/png) or JSON (image_base64, image_reference).
    """
    content_type = request.headers.get("content-type", "").lower()
    img_bytes: Optional[bytes] = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            req = OcrRecognizeLineRequest(**body)
            if req.image_base64:
                img_bytes = base64.b64decode(req.image_base64)
            elif req.image_reference:
                resolver = ImageSourceResolver(settings.runtime_mode)
                img_bytes = resolver.resolve(req.image_reference)
            else:
                raise HTTPException(status_code=400, detail="Missing image_base64 or image_reference in JSON body")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON request: {e}")
    else:
        img_bytes = await request.body()

    if not img_bytes or len(img_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image payload")

    try:
        pil_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        logger.error(f"[OCR_PILOT] Failed to decode image: {e}")
        raise HTTPException(status_code=400, detail="Invalid image bytes or unreadable image file")

    start_time = time.perf_counter()
    try:
        provider = get_ocr_provider("crnn_vi_handwriting_v1")
        if not isinstance(provider, CrnnOcrProvider):
            raise RuntimeError("CRNN OCR provider is not configured properly")

        recognized_text = provider.recognize_line(pil_image)
        latency_ms = (time.perf_counter() - start_time) * 1000

        meta = provider.get_metadata()
        model_name = meta.get("model_name", "Vietnamese-Handwriting-OCR-Full")
        model_version = meta.get("model_version", "1.0.0")

        return OcrRecognizeLineResponse(
            recognized_text=recognized_text,
            model_name=model_name,
            model_version=model_version,
            checkpoint_sha256=CHECKPOINT_SHA256,
            vocab_sha256=VOCAB_SHA256,
            preprocessing_version="v1_resize_64x1024_imagenet",
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        logger.error(f"[OCR_PILOT] Inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CRNN recognition error: {str(e)}")
