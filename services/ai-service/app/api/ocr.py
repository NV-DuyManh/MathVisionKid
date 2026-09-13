import io
import time
import logging
from typing import Optional, List
import cv2
import numpy as np
from fastapi import APIRouter, Request, HTTPException
from PIL import Image, ImageOps

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


import math

def correct_skew(bgr_image: np.ndarray, max_angle: float = 10.0) -> np.ndarray:
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    
    # Fast Otsu for text estimation
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Suppress long continuous lines (notebook ruling) from dominating deskew
    h, w = bgr_image.shape[:2]
    ruling_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, int(w * 0.15)), 1))
    rulings = cv2.morphologyEx(binary, cv2.MORPH_OPEN, ruling_kernel)
    text_only = cv2.subtract(binary, rulings)
    
    # Estimate median component height for safe morphology
    raw_cnts, _ = cv2.findContours(text_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
    median_h = np.median(heights) if heights else 15

    # Dilate text to form cohesive words/lines for angle estimation
    k_w = max(10, int(median_h * 1.5))
    k_h = max(3, int(median_h * 0.3))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_w, k_h))
    dilated = cv2.dilate(text_only, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    angles = []
    for cnt in contours:
        # Ignore tiny noise
        if cv2.contourArea(cnt) < 50:
            continue
        rect = cv2.minAreaRect(cnt)
        # rect[-1] returns angle in [-90, 0) or [0, 90] depending on OpenCV version
        angle = rect[-1]
        
        # Normalize angle to [-45, 45]
        # In newer OpenCV, angle is in [0, 90]. In older, [-90, 0).
        if angle > 45:
            angle = angle - 90
        elif angle < -45:
            angle = angle + 90
            
        # We only care about nearly horizontal text
        if -20 < angle < 20:
            angles.append(angle)
            
    if len(angles) < 2:
        return bgr_image
        
    median_angle = np.median(angles)
    print(f"Deskew median_angle: {median_angle}, OpenCV version: {cv2.__version__}")
    
    if abs(median_angle) > max_angle or abs(median_angle) < 0.5:
        return bgr_image
        
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    
    rotated = cv2.warpAffine(bgr_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def run_classical_line_detection(bgr_image: np.ndarray, max_lines: int = MAX_DETECTED_LINES) -> List[LineBox]:
    """
    Classical deterministic OpenCV text-line candidate segmentation.
    Upgraded for handwriting: includes small-angle deskew, adaptive ellipse morphology,
    and tolerant vertical-center collinear merging to handle sloped lines and diacritics.
    """
    if bgr_image is None or bgr_image.size == 0:
        return []

    # 0. Deskew to normalize sloped handwriting / tilted camera
    bgr_image = correct_skew(bgr_image, max_angle=10.0)

    height, width = bgr_image.shape[:2]
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)

    # 1. Background illumination normalization
    bg = cv2.morphologyEx(gray, cv2.MORPH_DILATE, cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35)))
    norm = cv2.divide(gray, bg, scale=255)

    # 2. Gaussian blur to suppress noise
    blurred = cv2.GaussianBlur(norm, (5, 5), 0)

    # 3. Otsu global thresholding with inversion
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    if cv2.countNonZero(binary) < 50:
        return []

    # 4. Minimal horizontal ruling line suppression
    ruling_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(50, int(width * 0.20)), 1))
    rulings = cv2.morphologyEx(binary, cv2.MORPH_OPEN, ruling_kernel)
    binary = cv2.subtract(binary, rulings)

    # 4.5 Clean up residual ruling fragments (jagged lines from deskew interpolation)
    noise_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, noise_kernel)

    # Estimate median component height for morphology
    raw_cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
    median_h = np.median(heights) if heights else 15

    # 5. Adaptive morphology: Ellipse kernel to capture sloped text and diacritics
    k_width = max(15, int(median_h * 1.5))
    k_height = max(3, int(median_h * 0.3))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_width, k_height))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    # 6. Find external contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = []
    min_w = max(10, int(median_h * 0.5))
    min_h = max(5, int(median_h * 0.2))
    max_h = int(height * 0.5)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w >= min_w and h >= min_h and h <= max_h:
            # Dynamic padding to ensure diacritics and descenders are preserved
            pad_x = max(5, int(w * 0.02))
            pad_y = max(5, int(h * 0.15))
            x_pad = max(0, x - pad_x)
            y_pad = max(0, y - pad_y)
            w_pad = min(width - x_pad, w + 2 * pad_x)
            h_pad = min(height - y_pad, h + 2 * pad_y)
            raw_boxes.append((x_pad, y_pad, w_pad, h_pad))

    raw_boxes.sort(key=lambda b: (b[1], b[0]))

    # 7. Tolerant collinear merge based on vertical centers and overlap
    merged_boxes = []
    for box in raw_boxes:
        if not merged_boxes:
            merged_boxes.append(box)
            continue
            
        prev = merged_boxes[-1]
        prev_y1, prev_y2 = prev[1], prev[1] + prev[3]
        curr_y1, curr_y2 = box[1], box[1] + box[3]
        
        prev_cy = prev[1] + prev[3] / 2
        curr_cy = box[1] + box[3] / 2
        
        overlap_y = max(0, min(prev_y2, curr_y2) - max(prev_y1, curr_y1))
        min_h_overlap = min(prev[3], box[3])
        y_dist = abs(curr_cy - prev_cy)
        avg_h = (prev[3] + box[3]) / 2.0

        # Merge if vertical overlap is significant OR centers are close relative to their actual size
        if (min_h_overlap > 0 and (overlap_y / min_h_overlap) > 0.4) or (y_dist < avg_h * 0.4):
            new_x = min(prev[0], box[0])
            new_y = min(prev[1], box[1])
            new_x2 = max(prev[0] + prev[2], box[0] + box[2])
            new_y2 = max(prev[1] + prev[3], box[1] + box[3])
            merged_boxes[-1] = (new_x, new_y, new_x2 - new_x, new_y2 - new_y)
        else:
            merged_boxes.append(box)

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
        pil_image = Image.open(io.BytesIO(img_bytes))
        pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")
        cv_img = np.array(pil_image)
        # Convert RGB to BGR for OpenCV
        cv_img = cv_img[:, :, ::-1].copy()
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
        pil_image = Image.open(io.BytesIO(img_bytes))
        pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")
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
