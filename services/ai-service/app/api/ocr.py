import io
import os
import json
import hashlib
import time
import logging
from typing import Optional, List, Tuple
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

HW_LINE_DETECTOR_VERSION = "runtime6-hue-projection-20260914"

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


def run_grid_handwriting_detection(bgr_image: np.ndarray, max_lines: int = MAX_DETECTED_LINES) -> Tuple[List[LineBox], dict]:
    """
    Detector B: Specialized fallback for handwriting on graph/squared paper.
    Uses adaptive chromatic ink extraction or adaptive thresholding, followed
    by conservative long-line suppression.
    """
    if bgr_image is None or bgr_image.size == 0:
        return [], {}

    bgr_image = correct_skew(bgr_image, max_angle=10.0)
    height, width = bgr_image.shape[:2]
    
    diagnostics = {}

    # A. Adaptive Chromatic-Ink Extraction
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    h_chan, s_chan, v_chan = cv2.split(hsv)
    
    # Identify candidate colored-ink pixels: strong saturation, not pure white/bright
    sat_mask = (s_chan > 30) & (v_chan < 230)
    candidate_hue = h_chan[sat_mask]
    
    chromatic_cluster_found = False
    dominant_hue = -1
    binary = None
    
    if len(candidate_hue) > 50:
        hist = cv2.calcHist([candidate_hue], [0], None, [180], [0, 180])
        dominant_hue = int(np.argmax(hist))
        
        # We need a meaningful peak
        if hist.flatten()[dominant_hue] > 10:
            chromatic_cluster_found = True
            
            # Create circular mask around dominant hue
            lower_hue = (dominant_hue - 15) % 180
            upper_hue = (dominant_hue + 15) % 180
            
            if lower_hue < upper_hue:
                hue_mask = (h_chan >= lower_hue) & (h_chan <= upper_hue)
            else:
                hue_mask = (h_chan >= lower_hue) | (h_chan <= upper_hue)
                
            ink_mask = hue_mask & sat_mask
            binary = (ink_mask * 255).astype(np.uint8)

    # B. Fallback to Grayscale & Conditional Grid Subtraction
    if not chromatic_cluster_found or cv2.countNonZero(binary) < 50:
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 41, 10
        )
        
        # Only aggressively subtract grid if we are in the grayscale fallback!
        # Chromatic mask naturally separates pen from gray grid.
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, int(height * 0.30))))
        vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel)
        
        horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, int(width * 0.30)), 1))
        horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel)
        
        grid = cv2.bitwise_or(vert_lines, horiz_lines)
        binary = cv2.subtract(binary, grid)

    # Clean up isolated noise
    noise_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, noise_kernel)

    # Estimate component height
    raw_cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
    median_h = np.median(heights) if heights else 15

    # Adaptive morphology for handwriting connectivity
    k_width = max(10, int(median_h * 1.2))
    k_height = max(3, int(median_h * 0.2))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_width, k_height))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    # NEW: Projection Row Segmentation
    # Calculate row-wise foreground density on a vertically closed mask to bridge diacritics
    v_close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(15, int(height * 0.05))))
    v_close = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, v_close_kernel)
    ink_per_row = np.sum(v_close > 0, axis=1) # 1D array of length `height`
    
    # Smooth the projection conservatively
    smooth_window = max(3, int(median_h * 0.3))
    smoothed_proj = np.convolve(ink_per_row, np.ones(smooth_window)/smooth_window, mode='same')
    
    # Identify bands of meaningful ink
    ink_threshold = max(5, width * 0.005) # 0.5% of width or minimum 5 pixels
    is_ink = smoothed_proj > ink_threshold
    
    bands = [] # list of (y_start, y_end)
    in_band = False
    start_y = 0
    min_band_h = max(15, height * 0.05) # At least 5% of image height
    for y, has_ink in enumerate(is_ink):
        if has_ink and not in_band:
            in_band = True
            start_y = y
        elif not has_ink and in_band:
            in_band = False
            if (y - start_y) >= min_band_h:
                bands.append((start_y, y))
    if in_band:
        if (height - start_y) >= min_band_h:
            bands.append((start_y, height))
            
    if not bands:
        bands = [(0, height)]

    # 3.5 Merge very close bands (valleys < 3% of height are likely intra-line gaps, e.g. accents)
    merged_bands = []
    max_gap = max(10, height * 0.03)
    for b in bands:
        if not merged_bands:
            merged_bands.append(b)
        else:
            prev = merged_bands[-1]
            if (b[0] - prev[1]) < max_gap:
                merged_bands[-1] = (prev[0], b[1])
            else:
                merged_bands.append(b)
    bands = merged_bands

    # 4. Giant-Box Split Logic (recursive split based on local valleys)
    def recursive_split_band(start_y, end_y):
        band_h = end_y - start_y
        if band_h <= median_h * 2.5:
            return [(start_y, end_y)]
            
        sub_proj = smoothed_proj[start_y:end_y]
        mid_start = int(band_h * 0.2)
        mid_end = int(band_h * 0.8)
        if mid_end <= mid_start:
            return [(start_y, end_y)]
            
        split_idx = mid_start + np.argmin(sub_proj[mid_start:mid_end])
        split_y = start_y + split_idx
        
        # Split if the valley is lower than 85% of the local peak
        if smoothed_proj[split_y] < np.max(sub_proj) * 0.85:
            return recursive_split_band(start_y, split_y) + recursive_split_band(split_y, end_y)
        else:
            return [(start_y, end_y)]

    final_bands = []
    for b in bands:
        final_bands.extend(recursive_split_band(b[0], b[1]))
    bands = final_bands

    # B. Component Y-Clustering
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    raw_boxes = []
    min_area = 5
    max_h = int(height * 0.5)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Preserve small components (diacritics/punctuation) by checking area instead of strict height/width
        if cv2.contourArea(cnt) >= min_area and h <= max_h:
            # Assign component to band based on maximum overlap
            best_band = 0
            best_overlap = -1
            cy = y + h / 2.0
            
            for i, b in enumerate(bands):
                overlap = max(0, min(y+h, b[1]) - max(y, b[0]))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_band = i
            
            # If no vertical overlap, assign to nearest center
            if best_overlap == 0:
                best_band = min(range(len(bands)), key=lambda i: abs(cy - ((bands[i][0]+bands[i][1])/2.0)))
                
            raw_boxes.append({
                'box': [x, y, w, h],
                'band_idx': best_band
            })

    # Group components by band to form final line boxes
    merged_boxes = []
    for i, band in enumerate(bands):
        band_boxes = [b['box'] for b in raw_boxes if b['band_idx'] == i]
        if not band_boxes:
            continue
            
        x_min = min([b[0] for b in band_boxes])
        y_min = min([b[1] for b in band_boxes])
        x_max = max([b[0]+b[2] for b in band_boxes])
        y_max = max([b[1]+b[3] for b in band_boxes])
        
        # Chain-merge prevention: clamp y_min/y_max roughly to the band's limits 
        # allowing for natural ascenders/descenders, but preventing adjacent lines from colliding
        margin = int(median_h * 0.4)
        y_min = max(y_min, band[0] - margin)
        y_max = min(y_max, band[1] + margin)
        
        w_line = x_max - x_min
        h_line = y_max - y_min
        
        # Apply padding
        pad_x = max(5, int(w_line * 0.02))
        pad_y = max(5, int(h_line * 0.15))
        
        x_pad = max(0, x_min - pad_x)
        y_pad = max(0, y_min - pad_y)
        w_pad = min(width - x_pad, w_line + 2 * pad_x)
        h_pad = min(height - y_pad, h_line + 2 * pad_y)
        
        merged_boxes.append((x_pad, y_pad, w_pad, h_pad))

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

    diagnostics["chromatic_cluster_found"] = chromatic_cluster_found
    diagnostics["dominant_hue"] = dominant_hue
    diagnostics["bands_detected"] = len(bands)
    diagnostics["final_boxes"] = len(line_results)

    return line_results, diagnostics


def detect_text_lines(cv_img: np.ndarray, max_lines: int = MAX_DETECTED_LINES) -> Tuple[List[LineBox], dict]:
    """
    Production text-line segmentation pipeline.
    Runs Path A (classical morphology/connected components).
    If Path A is suspicious, runs Path B (hue-clustering + projection bands for grid handwriting).
    Returns (final_lines, diagnostics).
    """
    if cv_img is None or cv_img.size == 0:
        return [], {
            "detector_version": HW_LINE_DETECTOR_VERSION,
            "path_a_count": 0,
            "path_a_suspicious": True,
            "suspicious_reason": "EMPTY_IMAGE",
            "path_b_invoked": False,
            "dominant_hue": None,
            "projection_band_count": 0,
            "final_box_count": 0
        }

    height, width = cv_img.shape[:2]
    lines = run_classical_line_detection(cv_img, max_lines=max_lines)

    path_a_count = len(lines)
    is_suspicious = False
    suspicious_reason = "NONE"

    if path_a_count == 0:
        is_suspicious = True
        suspicious_reason = "ZERO_LINES"
    elif path_a_count == 1:
        if lines[0].height > height * 0.4:
            is_suspicious = True
            suspicious_reason = "SINGLE_GIANT_BOX"
    elif path_a_count >= 2:
        max_h = max(l.height for l in lines)
        min_h = min(l.height for l in lines)
        if min_h > 0 and (max_h / min_h) > 3.0:
            is_suspicious = True
            suspicious_reason = f"EXTREME_HEIGHT_VARIANCE_{round(max_h / min_h, 2)}"

    diagnostics = {
        "detector_version": HW_LINE_DETECTOR_VERSION,
        "path_a_count": path_a_count,
        "path_a_suspicious": is_suspicious,
        "suspicious_reason": suspicious_reason,
        "path_b_invoked": False,
        "dominant_hue": None,
        "projection_band_count": 0,
        "final_box_count": path_a_count
    }

    if is_suspicious:
        logger.info(f"[OCR_PILOT] [{HW_LINE_DETECTOR_VERSION}] Path A suspicious ({suspicious_reason}, lines={path_a_count}). Triggering Path B.")
        fallback_lines, b_diag = run_grid_handwriting_detection(cv_img, max_lines=max_lines)
        diagnostics["path_b_invoked"] = True
        diagnostics["dominant_hue"] = b_diag.get("dominant_hue")
        diagnostics["projection_band_count"] = b_diag.get("bands_detected", 0)
        logger.info(f"[OCR_PILOT] [{HW_LINE_DETECTOR_VERSION}] Path B result: {len(fallback_lines)} lines, diag={b_diag}")

        if len(fallback_lines) > 0:
            lines = fallback_lines
            diagnostics["final_box_count"] = len(lines)

    return lines, diagnostics


@router.post("/detect-lines", response_model=OcrDetectLinesResponse)
async def detect_lines_endpoint(request: Request):
    """
    Dedicated OCR Pilot endpoint for candidate text-line segmentation.
    Uses classical OpenCV morphology and contour grouping with adaptive chromatic fallback.
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

    upload_sha256 = hashlib.sha256(img_bytes).hexdigest()
    logger.info(f"[OCR_PILOT] [{HW_LINE_DETECTOR_VERSION}] /detect-lines received {len(img_bytes)} bytes, SHA256={upload_sha256}")

    try:
        raw_pil = Image.open(io.BytesIO(img_bytes))
        exif = raw_pil.getexif()
        exif_orientation = exif.get(0x0112, None) if exif else None
        pil_image = ImageOps.exif_transpose(raw_pil).convert("RGB")
        cv_img = np.array(pil_image)
        # Convert RGB to BGR for OpenCV
        cv_img = cv_img[:, :, ::-1].copy()
        if cv_img is None:
            raise ValueError("Decoded image is None")
    except Exception as e:
        logger.error(f"[OCR_PILOT] Failed to decode image for line detection: {e}")
        raise HTTPException(status_code=400, detail="Invalid image bytes or unreadable image file")

    height, width = cv_img.shape[:2]

    # Save live input for runtime forensics under scratch/runtime6_live_input/
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../scratch/runtime6_live_input"))
    try:
        os.makedirs(save_dir, exist_ok=True)
        with open(os.path.join(save_dir, "raw_upload_bytes.bin"), "wb") as f:
            f.write(img_bytes)
        ok, enc = cv2.imencode(".png", cv_img)
        if ok:
            with open(os.path.join(save_dir, "decoded_input.png"), "wb") as f:
                f.write(enc)
    except Exception as se:
        logger.warning(f"[OCR_PILOT] Failed to persist live input capture: {se}")

    try:
        lines, diagnostics = detect_text_lines(cv_img, max_lines=MAX_DETECTED_LINES)

        # Persist metadata.json under scratch/runtime6_live_input/
        try:
            metadata = {
                "timestamp": time.time(),
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "width": width,
                "height": height,
                "channels": cv_img.shape[2] if len(cv_img.shape) > 2 else 1,
                "mode": str(getattr(pil_image, "mode", "RGB")),
                "sha256_upload_bytes": upload_sha256,
                "exif_orientation": exif_orientation,
                "detector_version": HW_LINE_DETECTOR_VERSION,
                "path_a_count": diagnostics.get("path_a_count", 0),
                "suspicious_reason": diagnostics.get("suspicious_reason", "NONE"),
                "path_b_invoked": diagnostics.get("path_b_invoked", False),
                "dominant_hue": diagnostics.get("dominant_hue"),
                "projection_band_count": diagnostics.get("projection_band_count", 0),
                "final_box_count": len(lines)
            }
            with open(os.path.join(save_dir, "metadata.json"), "w", encoding="utf-8") as mf:
                json.dump(metadata, mf, indent=2, default=str)
        except Exception as me:
            logger.warning(f"[OCR_PILOT] Failed to write metadata.json: {me}")

        logger.info(f"[OCR_PILOT] [{HW_LINE_DETECTOR_VERSION}] Response: {len(lines)} lines (diag: {diagnostics})")

        return OcrDetectLinesResponse(
            width=width,
            height=height,
            lines=lines,
            detector_version=HW_LINE_DETECTOR_VERSION,
            diagnostics=diagnostics
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
