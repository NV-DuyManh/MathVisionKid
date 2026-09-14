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

def compute_strong_body_bands(binary_mask: np.ndarray, median_h: float, width: int, height: int) -> List[Tuple[int, int]]:
    """
    Computes strong primary text bands based on horizontal projection profile.
    Distinguishes primary text rows from weak satellite evidence (accents, punctuation).
    """
    if binary_mask is None or binary_mask.size == 0:
        return []
    ink_per_row = np.sum(binary_mask > 0, axis=1)
    smooth_window = max(3, int(median_h * 0.4))
    smoothed_proj = np.convolve(ink_per_row, np.ones(smooth_window) / smooth_window, mode='same')
    
    strong_thresh = max(15.0, width * 0.02)
    is_strong = smoothed_proj >= strong_thresh
    
    strong_bands = []
    in_band = False
    start_y = 0
    min_band_h = max(6, int(median_h * 0.5))
    for y, s in enumerate(is_strong):
        if s and not in_band:
            in_band = True
            start_y = y
        elif not s and in_band:
            in_band = False
            if (y - start_y) >= min_band_h:
                strong_bands.append((start_y, y))
    if in_band and (height - start_y) >= min_band_h:
        strong_bands.append((start_y, height))
        
    merged = []
    for b in strong_bands:
        if not merged:
            merged.append(b)
        else:
            if b[0] - merged[-1][1] <= max(8, int(median_h * 0.8)):
                merged[-1] = (merged[-1][0], b[1])
            else:
                merged.append(b)
    return merged


def has_primary_body_evidence(w: float, h: float, ink: int, median_h: float) -> bool:
    """
    Two-level model: Determines if a box has primary body evidence to anchor a text line.
    Primary line criteria:
    - Meaningful horizontal ink span OR
    - Meaningful ink mass (dense text / cursive strokes) OR
    - Normal character body height with sufficient ink mass (short legitimate rows like 'Bài giải', 'Đáp số')
    Satellites (accents, diacritics, dots over i, isolated noise) return False.
    """
    if w >= max(60.0, median_h * 2.8) and ink >= max(90, int(median_h * 4.5)):
        return True
    if ink >= max(160, int(median_h * 8.0)):
        return True
    if h >= max(13.0, median_h * 0.65) and ink >= max(45, int(median_h * 2.2)) and w >= max(20.0, median_h * 0.9):
        return True
    return False


def is_component_satellite(w: float, h: float, ink: int, median_h: float) -> bool:
    """
    Two-level model helper:
    Identifies if a box is a satellite (diacritic, accent, tone mark, dot over i/j, or fragment).
    A full word or text row is never classified as a satellite.
    """
    return not has_primary_body_evidence(w, h, ink, median_h)


def recursive_split_giant_box(box: Tuple[int, int, int, int], binary_mask: np.ndarray, median_h: float) -> List[Tuple[int, int, int, int]]:
    """
    Recursively splits giant boxes that contain multiple strong handwriting body bands.
    """
    x, y, w, h = box
    if h < median_h * 1.5:
        return [box]
        
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(binary_mask.shape[1], x + w), min(binary_mask.shape[0], y + h)
    crop = binary_mask[y1:y2, x1:x2]
    
    bands = compute_strong_body_bands(crop, median_h, w, h)
    
    if len(bands) <= 1:
        return [box]
        
    # We have >= 2 strong bands, need to split.
    best_valley_y = -1
    max_gap = 0
    
    for i in range(len(bands) - 1):
        b1_end = bands[i][1]
        b2_start = bands[i+1][0]
        gap = b2_start - b1_end
        if gap > max_gap:
            max_gap = gap
            best_valley_y = b1_end + gap // 2
            
    if best_valley_y <= 0:
        return [box]
        
    # Split horizontally at best_valley_y
    split_y_global = y1 + best_valley_y
    
    top_crop = binary_mask[y1:split_y_global, x1:x2]
    bot_crop = binary_mask[split_y_global:y2, x1:x2]
    
    children = []
    
    for c_crop, c_y_offset in [(top_crop, y1), (bot_crop, split_y_global)]:
        if cv2.countNonZero(c_crop) == 0:
            continue
            
        row_proj = np.any(c_crop > 0, axis=1)
        col_proj = np.any(c_crop > 0, axis=0)
        
        if not np.any(row_proj) or not np.any(col_proj):
            continue
            
        r_min, r_max = int(np.argmax(row_proj)), int(len(row_proj) - np.argmax(row_proj[::-1]))
        c_min, c_max = int(np.argmax(col_proj)), int(len(col_proj) - np.argmax(col_proj[::-1]))
        
        child_box = (x1 + c_min, c_y_offset + r_min, c_max - c_min, r_max - r_min)
        
        # recursively split
        children.extend(recursive_split_giant_box(child_box, binary_mask, median_h))
        
    return children if children else [box]


def consolidate_line_boxes(boxes: List[Tuple[int, int, int, int]], binary_mask: np.ndarray, median_h: float, img_w: int, img_h: int) -> List[Tuple[int, int, int, int]]:
    """
    Hysteresis Line-Level Consolidation:
    1. Contained Fragment Suppression: absorbs small specks and fragments inside a row's span.
    2. Collinear Word Merge: merges words/tokens on the same horizontal baseline.
    3. Touching Vertical Splits: unifies characters horizontally sliced by graph ruling lines.
    4. Satellite Attachment: attaches Vietnamese accents, tone marks, and descenders to the nearest row.
    5. Minimum Standalone Evidence: unattached satellites and stray noise specks are discarded as non-text noise.
    """
    if not boxes:
        return []

    def get_ink(b):
        x, y, w, h = b
        x1_c, y1_c = max(0, min(img_w - 1, x)), max(0, min(img_h - 1, y))
        x2_c, y2_c = max(x1_c + 1, min(img_w, x + w)), max(y1_c + 1, min(img_h, y + h))
        crop = binary_mask[y1_c:y2_c, x1_c:x2_c]
        return int(cv2.countNonZero(crop)) if crop.size > 0 else 0

    # Step 1: Contained fragment absorption (largest parent first)
    sorted_boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
    parents = []
    for b in sorted_boxes:
        absorbed = False
        for p_idx, p in enumerate(parents):
            h_overlap = max(0, min(b[0] + b[2], p[0] + p[2]) - max(b[0], p[0]))
            min_w = min(b[2], p[2])
            v_overlap = max(0, min(b[1] + b[3], p[1] + p[3]) - max(b[1], p[1]))
            v_gap = max(0, max(b[1], p[1]) - min(b[1] + b[3], p[1] + p[3]))

            # If b is smaller, horizontally contained, and directly touching or inside p vertically
            if (b[2] * b[3] < p[2] * p[3] * 0.45) and (h_overlap / max(1, min_w) >= 0.70) and (v_overlap > 0 or v_gap <= 4):
                nx = min(p[0], b[0])
                ny = min(p[1], b[1])
                nw = max(p[0] + p[2], b[0] + b[2]) - nx
                nh = max(p[1] + p[3], b[1] + b[3]) - ny
                parents[p_idx] = (nx, ny, nw, nh)
                absorbed = True
                break
        if not absorbed:
            parents.append(b)

    # Step 2: Multi-pass row consolidation
    boxes_work = [list(p) for p in parents]
    boxes_work.sort(key=lambda b: (b[1], b[0]))
    max_line_h = min(img_h * 0.35, max(75.0, median_h * 7.5))

    changed = True
    iteration = 0
    while changed and iteration < 12:
        changed = False
        iteration += 1
        new_boxes = []
        skip = set()
        for i in range(len(boxes_work)):
            if i in skip:
                continue
            b1 = boxes_work[i]
            x1, y1, w1, h1 = b1
            c1_y = y1 + h1 / 2.0
            ink1 = get_ink(b1)

            for j in range(i + 1, len(boxes_work)):
                if j in skip:
                    continue
                b2 = boxes_work[j]
                x2, y2, w2, h2 = b2
                c2_y = y2 + h2 / 2.0
                ink2 = get_ink(b2)

                cand_min_y = min(y1, y2)
                cand_max_y = max(y1 + h1, y2 + h2)
                cand_h = cand_max_y - cand_min_y
                if cand_h > max_line_h:
                    continue

                v_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                min_h = min(h1, h2)
                v_overlap_ratio = v_overlap / max(1, min_h)
                h_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                min_w = min(w1, w2)
                h_overlap_ratio = h_overlap / max(1, min_w)
                v_gap = max(0, max(y1, y2) - min(y1 + h1, y2 + h2))
                h_gap = max(0, max(x1, x2) - min(x1 + w1, x2 + w2))

                is_b1_sat = is_component_satellite(w1, h1, ink1, median_h)
                is_b2_sat = is_component_satellite(w2, h2, ink2, median_h)
                is_both_primary = (not is_b1_sat) and (not is_b2_sat)

                should_merge = False

                # Case 1: Collinear words / tokens on same horizontal baseline
                if (v_overlap_ratio >= 0.40 and abs(c1_y - c2_y) <= max(6.0, min_h * 0.50)) or (abs(c1_y - c2_y) <= max(4.0, min_h * 0.35)):
                    should_merge = True
                elif (v_overlap_ratio >= 0.25) and (h_gap < max(70.0, median_h * 7.0) or h_overlap > 0):
                    should_merge = True

                # Case 2: Touching vertical splits (cut by horizontal ruling lines)
                if not should_merge and v_gap <= max(5.0, median_h * 0.6) and h_overlap_ratio >= 0.35:
                    should_merge = True

                # Case 3: Satellite attachment (Vietnamese accents, dots over i, circumflex, descenders)
                if not should_merge and (is_b1_sat or is_b2_sat) and not is_both_primary:
                    if v_gap <= max(25.0, median_h * 2.5):
                        if h_overlap_ratio >= 0.25 or (h_overlap > 0) or (h_gap < max(18.0, median_h * 1.8)):
                            should_merge = True

                # Case 4: Contained fragment / accent band absorption (Rule 6)
                if not should_merge and h_overlap_ratio >= 0.65 and v_gap <= max(25.0, median_h * 2.5):
                    if (h1 <= h2 * 0.55 or h2 <= h1 * 0.55) or (is_b1_sat or is_b2_sat):
                        should_merge = True

                if should_merge:
                    nx = min(x1, x2)
                    ny = min(y1, y2)
                    nw = max(x1 + w1, x2 + w2) - nx
                    nh = max(y1 + h1, y2 + h2) - ny
                    b1 = [nx, ny, nw, nh]
                    x1, y1, w1, h1 = b1
                    c1_y = y1 + h1 / 2.0
                    skip.add(j)
                    changed = True
            new_boxes.append(b1)
        boxes_work = sorted(new_boxes, key=lambda b: (b[1], b[0]))

    # Step 3: Satellite Attachment & Isolated Noise Suppression
    primary_boxes = []
    satellite_boxes = []
    for b in boxes_work:
        ink = get_ink(b)
        if has_primary_body_evidence(b[2], b[3], ink, median_h):
            primary_boxes.append(list(b))
        else:
            satellite_boxes.append(list(b))

    # Attach remaining satellites to nearest primary row if plausible
    for sat in satellite_boxes:
        sx, sy, sw, sh = sat
        best_p_idx = -1
        best_dist = 999999.0
        for p_idx, p in enumerate(primary_boxes):
            px, py, pw, ph = p
            cand_h = max(py + ph, sy + sh) - min(py, sy)
            if cand_h > max_line_h:
                continue
            v_gap = max(0, max(py, sy) - min(py + ph, sy + sh))
            h_overlap = max(0, min(px + pw, sx + sw) - max(px, sx))
            h_gap = max(0, max(px, sx) - min(px + pw, sx + sw))

            if v_gap <= max(35.0, median_h * 3.5) and (h_overlap > 0 or h_gap <= max(25.0, median_h * 2.0)):
                dist = v_gap + h_gap * 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_p_idx = p_idx

        if best_p_idx >= 0:
            # Attach to primary row, expanding bounds to preserve accent/diacritic pixels
            p = primary_boxes[best_p_idx]
            nx = min(p[0], sx)
            ny = min(p[1], sy)
            nw = max(p[0] + p[2], sx + sw) - nx
            nh = max(p[1] + p[3], sy + sh) - ny
            primary_boxes[best_p_idx] = [nx, ny, nw, nh]
        # Otherwise: Satellite component could not attach to any primary row -> DISCARDED AS NON-TEXT NOISE!

    # Final result: only primary rows with primary body evidence
    final_result = [(int(b[0]), int(b[1]), int(b[2]), int(b[3])) for b in primary_boxes]
    final_result.sort(key=lambda b: (b[1], b[0]))
    return final_result


def run_classical_line_detection(bgr_image: np.ndarray, max_lines: int = MAX_DETECTED_LINES) -> List[LineBox]:
    """
    Classical deterministic OpenCV text-line candidate segmentation.
    Upgraded for handwriting: includes small-angle deskew, adaptive ellipse morphology,
    and two-level satellite consolidation to prevent diacritic over-segmentation.
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

    # 4.5 Clean up residual ruling fragments
    noise_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, noise_kernel)

    # Estimate median component height for morphology
    raw_cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
    median_h = float(np.median(heights)) if heights else 15.0

    # 5. Adaptive morphology: Ellipse kernel to capture sloped text and diacritics
    k_width = max(15, int(median_h * 1.5))
    k_height = max(3, int(median_h * 0.3))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_width, k_height))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    # 6. Find external contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = [
        cv2.boundingRect(cnt) for cnt in contours
        if cv2.boundingRect(cnt)[2] >= max(8, int(median_h * 0.4))
        and cv2.boundingRect(cnt)[3] >= max(4, int(median_h * 0.2))
        and cv2.boundingRect(cnt)[3] <= int(height * 0.5)
    ]

    # 7. Robust Two-Level Consolidation
    consolidated = consolidate_line_boxes(raw_boxes, binary, median_h, width, height)

    padded_boxes = []
    for b in consolidated:
        pad_x = max(5, int(b[2] * 0.02))
        pad_y = max(4, int(b[3] * 0.10))
        xp = max(0, b[0] - pad_x)
        yp = max(0, b[1] - pad_y)
        wp = min(width - xp, b[2] + 2 * pad_x)
        hp = min(height - yp, b[3] + 2 * pad_y)
        padded_boxes.append((xp, yp, wp, hp))

    padded_boxes.sort(key=lambda b: (b[1], b[0]))
    if len(padded_boxes) > max_lines:
        padded_boxes = padded_boxes[:max_lines]

    line_results = []
    for idx, b in enumerate(padded_boxes, 1):
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
    by robust two-level satellite consolidation.
    """
    if bgr_image is None or bgr_image.size == 0:
        return [], {}

    bgr_image = correct_skew(bgr_image, max_angle=10.0)
    height, width = bgr_image.shape[:2]
    diagnostics = {}

    # A. Adaptive Chromatic-Ink Extraction
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    h_chan, s_chan, v_chan = cv2.split(hsv)
    sat_mask = (s_chan > 25) & (v_chan < 235)
    candidate_hue = h_chan[sat_mask]

    chromatic_cluster_found = False
    dominant_hue = -1
    binary = None

    if len(candidate_hue) > 50:
        hist = cv2.calcHist([candidate_hue], [0], None, [180], [0, 180])
        dominant_hue = int(np.argmax(hist))
        if hist.flatten()[dominant_hue] > 10:
            chromatic_cluster_found = True
            lower_hue = (dominant_hue - 25) % 180
            upper_hue = (dominant_hue + 25) % 180
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
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, int(height * 0.30))))
        vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel)
        horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, int(width * 0.30)), 1))
        horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel)
        grid = cv2.bitwise_or(vert_lines, horiz_lines)
        binary = cv2.subtract(binary, grid)

        # Only clean residual grid noise in the grayscale fallback
        noise_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, noise_kernel)

    raw_cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
    median_h = float(np.median(heights)) if heights else 15.0

    k_width = max(15, int(median_h * 1.5))
    k_height = max(3, int(median_h * 0.3))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_width, k_height))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    strong_bands = compute_strong_body_bands(binary, median_h, width, height)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    raw_boxes = [
        cv2.boundingRect(cnt) for cnt in contours
        if cv2.boundingRect(cnt)[2] >= max(8, int(median_h * 0.4))
        and cv2.boundingRect(cnt)[3] >= max(4, int(median_h * 0.2))
        and cv2.boundingRect(cnt)[3] <= int(height * 0.5)
    ]

    consolidated = consolidate_line_boxes(raw_boxes, binary, median_h, width, height)

    padded_boxes = []
    for b in consolidated:
        pad_x = max(5, int(b[2] * 0.02))
        pad_y = max(4, int(b[3] * 0.10))
        xp = max(0, b[0] - pad_x)
        yp = max(0, b[1] - pad_y)
        wp = min(width - xp, b[2] + 2 * pad_x)
        hp = min(height - yp, b[3] + 2 * pad_y)
        padded_boxes.append((xp, yp, wp, hp))

    padded_boxes.sort(key=lambda b: (b[1], b[0]))
    if len(padded_boxes) > max_lines:
        padded_boxes = padded_boxes[:max_lines]

    line_results = []
    for idx, b in enumerate(padded_boxes, 1):
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
    diagnostics["bands_detected"] = len(strong_bands)
    diagnostics["final_boxes"] = len(line_results)

    return line_results, diagnostics


def detect_text_lines(cv_img: np.ndarray, max_lines: int = MAX_DETECTED_LINES) -> Tuple[List[LineBox], dict]:
    """
    Production text-line segmentation pipeline.
    Replaced with the GENERALIZED LINE SEGMENTATION pipeline.
    Legacy paths (Path A and Path B) are retained in the file for fallback/cleanup phase.
    """
    from app.api.generalized_pipeline import run_generalized_line_detection
    return run_generalized_line_detection(cv_img, max_lines)


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
