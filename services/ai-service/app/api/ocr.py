import io
import time
import logging
from typing import Optional, List
import cv2
import numpy as np
from fastapi import APIRouter, Request, HTTPException
from PIL import Image

from app.ocr.factory import get_ocr_provider
from app.ocr.crnn_provider import CrnnOcrProvider
from app.schemas.ocr_pilot import OcrRecognizeLineResponse, OcrDetectLinesResponse, LineBox
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

CHECKPOINT_SHA256 = "a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941"
VOCAB_SHA256 = "6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d"
MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10 MB maximum line crop size
MAX_DETECTED_LINES = 30


def run_classical_line_detection(bgr_image: np.ndarray, max_lines: int = MAX_DETECTED_LINES) -> List[LineBox]:
    """
    Classical deterministic OpenCV text-line candidate segmentation.
    Uses background illumination normalization, Otsu global thresholding,
    minimal horizontal ruling line suppression, and horizontal morphological dilation.
    Strictly isolated from YOLO detection and arithmetic parser.
    """
    if bgr_image is None or bgr_image.size == 0:
        return []

    height, width = bgr_image.shape[:2]
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)

    # 1. Background illumination normalization (reduces shadow and uneven lighting gradients)
    bg = cv2.morphologyEx(gray, cv2.MORPH_DILATE, cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35)))
    norm = cv2.divide(gray, bg, scale=255)

    # 2. Gaussian blur to suppress scanner / sensor high-frequency noise
    blurred = cv2.GaussianBlur(norm, (5, 5), 0)

    # 3. Otsu global thresholding with inversion (dark ink becomes white foreground)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 4. Blank page check: if negligible foreground pixels exist
    if cv2.countNonZero(binary) < 50:
        return []

    # 5. Minimal horizontal ruling line suppression before character dilation
    # Detects continuous thin lines spanning >= 20% width to prevent ruling lines forming false line boxes
    ruling_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(50, int(width * 0.20)), 1))
    rulings = cv2.morphologyEx(binary, cv2.MORPH_OPEN, ruling_kernel)
    binary = cv2.subtract(binary, rulings)

    # 6. Horizontal morphological kernel to connect adjacent characters into full line candidates
    k_width = max(30, int(width * 0.035))
    k_height = 3
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_width, k_height))
    dilated = cv2.dilate(binary, kernel, iterations=2)

    # 7. Find external contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = []
    min_w = max(15, int(width * 0.02))
    min_h = 8
    max_h = int(height * 0.45)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w >= min_w and h >= min_h and h <= max_h:
            pad_x = 8
            pad_y = 6
            x_pad = max(0, x - pad_x)
            y_pad = max(0, y - pad_y)
            w_pad = min(width - x_pad, w + 2 * pad_x)
            h_pad = min(height - y_pad, h + 2 * pad_y)
            raw_boxes.append((x_pad, y_pad, w_pad, h_pad))

    # Sort top to bottom initially
    raw_boxes.sort(key=lambda b: (b[1], b[0]))

    # 8. Merge collinear boxes on near-same vertical level
    merged_boxes = []
    for box in raw_boxes:
        if not merged_boxes:
            merged_boxes.append(box)
            continue
        prev = merged_boxes[-1]
        prev_y1, prev_y2 = prev[1], prev[1] + prev[3]
        curr_y1, curr_y2 = box[1], box[1] + box[3]

        overlap_y = max(0, min(prev_y2, curr_y2) - max(prev_y1, curr_y1))
        min_h_overlap = min(prev[3], box[3])

        # Merge if vertical overlap > 35% or vertical distance <= 8px on adjacent fragments
        if (min_h_overlap > 0 and (overlap_y / min_h_overlap) > 0.35) or (curr_y1 - prev_y2 <= 8 and abs(curr_y1 - prev_y1) < 40):
            new_x = min(prev[0], box[0])
            new_y = min(prev[1], box[1])
            new_x2 = max(prev[0] + prev[2], box[0] + box[2])
            new_y2 = max(prev[1] + prev[3], box[1] + box[3])
            merged_boxes[-1] = (new_x, new_y, new_x2 - new_x, new_y2 - new_y)
        else:
            merged_boxes.append(box)

    # Sort final order top-to-bottom by y, then x
    merged_boxes.sort(key=lambda b: (b[1], b[0]))
    if len(merged_boxes) > max_lines:
        merged_boxes = merged_boxes[:max_lines]

    line_results = []
    for idx, b in enumerate(merged_boxes, 1):
        line_results.append(LineBox(
            line_id=f"line_{idx}",
            x=int(b[0]),
            y=int(b[1]),
            width=int(b[2]),
            height=int(b[3]),
            order=idx
        ))

    return line_results


@router.post("/detect-lines", response_model=OcrDetectLinesResponse)
async def detect_lines_endpoint(request: Request):
    """
    Dedicated OCR Pilot endpoint for candidate text-line segmentation.
    Uses classical OpenCV morphology and contour grouping.
    Requires internal service authentication via X-Internal-API-Key header.
    Accepts raw binary image stream only (image/jpeg, image/png, application/octet-stream).
    Does NOT invoke CRNN or YOLO arithmetic models.
    """
    # 1. Enforce Internal Authentication
    api_key = request.headers.get("X-Internal-API-Key")
    if not api_key or api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized internal API request")

    # 2. Reject JSON payloads — Raw binary stream only
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        raise HTTPException(
            status_code=415,
            detail="JSON payload not supported. Send raw image binary stream (e.g. image/jpeg, image/png, application/octet-stream)"
        )

    # 3. Read raw image stream
    img_bytes = await request.body()
    if not img_bytes or len(img_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image payload")

    if len(img_bytes) > MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Payload exceeds maximum allowed size of {MAX_PAYLOAD_BYTES} bytes"
        )

    try:
        nparr = np.frombuffer(img_bytes, np.uint8)
        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if cv_img is None:
            raise ValueError("Decoded image is None")
    except Exception as e:
        logger.error(f"[OCR_PILOT] Failed to decode image for line detection: {e}")
        raise HTTPException(status_code=400, detail="Invalid image bytes or unreadable image file")

    height, width = cv_img.shape[:2]
    try:
        lines = run_classical_line_detection(cv_img, max_lines=MAX_DETECTED_LINES)
        return OcrDetectLinesResponse(
            width=width,
            height=height,
            lines=lines
        )
    except Exception as e:
        logger.error(f"[OCR_PILOT] Line detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Line detection error: {str(e)}")


@router.post("/recognize-line", response_model=OcrRecognizeLineResponse)
async def recognize_line(request: Request):
    """
    Dedicated OCR Pilot endpoint for single text-line Vietnamese handwriting recognition.
    Strictly isolated from YOLO, StructuredParser, and ArithmeticValidator.
    Requires internal service authentication via X-Internal-API-Key header.
    Accepts raw binary image stream only (Content-Type: image/jpeg, image/png, application/octet-stream).
    Enforces payload size limit, valid image decoding, and truth-first null confidence.
    """
    # 1. Enforce Internal Authentication
    api_key = request.headers.get("X-Internal-API-Key")
    if not api_key or api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized internal API request")

    # 2. Reject JSON payloads — Raw binary stream only
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        raise HTTPException(
            status_code=415, 
            detail="JSON payload not supported. Send raw image binary stream (e.g. image/jpeg, image/png, application/octet-stream)"
        )

    # 3. Read raw image stream
    img_bytes = await request.body()
    if not img_bytes or len(img_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image payload")

    if len(img_bytes) > MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=413, 
            detail=f"Payload exceeds maximum allowed size of {MAX_PAYLOAD_BYTES} bytes"
        )

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

        # Confidence must be null/omitted (no fabricated confidence score)
        return OcrRecognizeLineResponse(
            recognized_text=recognized_text,
            model_name=model_name,
            model_version=model_version,
            checkpoint_sha256=CHECKPOINT_SHA256,
            vocab_sha256=VOCAB_SHA256,
            preprocessing_version="v1_resize_64x1024_imagenet",
            confidence=None,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        logger.error(f"[OCR_PILOT] Inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CRNN recognition error: {str(e)}")
