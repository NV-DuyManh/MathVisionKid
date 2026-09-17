import cv2
import numpy as np
from typing import List, Tuple

def extract_ink_mask(bgr_image: np.ndarray, height: int, width: int, profile: str = "PROFILE_A") -> np.ndarray:
    """
    Step 3/4: Adaptive ensemble ink mask extraction.
    Combines chromatic ink extraction when a dominant pen-color cluster is reliable,
    with grayscale/adaptive-threshold fallback. Includes grid suppression.
    Supports Profiles: PROFILE_A (Default), PROFILE_B (Strong Grid Suppression), PROFILE_C (Weak Grid Suppression)
    """
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    h_chan, s_chan, v_chan = cv2.split(hsv)
    
    # 1. Chromatic ink extraction
    sat_mask = (s_chan > 25) & (v_chan < 235)
    candidate_hue = h_chan[sat_mask]
    
    chromatic_mask = np.zeros((height, width), dtype=np.uint8)
    if len(candidate_hue) > 50:
        hist = cv2.calcHist([candidate_hue], [0], None, [180], [0, 180])
        dominant_hue = int(np.argmax(hist))
        if hist.flatten()[dominant_hue] > 10:
            lower_hue = (dominant_hue - 25) % 180
            upper_hue = (dominant_hue + 25) % 180
            if lower_hue < upper_hue:
                hue_mask = (h_chan >= lower_hue) & (h_chan <= upper_hue)
            else:
                hue_mask = (h_chan >= lower_hue) | (h_chan <= upper_hue)
            ink_mask = hue_mask & sat_mask
            chromatic_mask = (ink_mask * 255).astype(np.uint8)

    # 2. Grayscale/Adaptive fallback
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    
    # Illumination normalization
    bg = cv2.morphologyEx(gray, cv2.MORPH_DILATE, cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35)))
    norm = cv2.divide(gray, bg, scale=255)
    
    blurred = cv2.GaussianBlur(norm, (5, 5), 0)
    # Otsu
    _, binary_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Adaptive
    binary_adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 41, 10)
    
    # Combine masks. We want a robust mask. 
    # Adaptive tends to pick up grid lines strongly. We must suppress them.
    binary_base = cv2.bitwise_or(binary_otsu, binary_adapt)
    
    # If chromatic mask is strong and clean, we combine it with base.
    final_mask = cv2.bitwise_or(binary_base, chromatic_mask)
    
    # Paper Background / Grid suppression MUST apply to the combined mask
    # because chromatic mask might capture blue/purple graph lines!
    v_thresh = max(30, int(height * 0.25))
    h_thresh = max(30, int(width * 0.25))
    
    if profile == "PROFILE_B":
        v_thresh = max(15, int(height * 0.10))
        h_thresh = max(15, int(width * 0.10))
    elif profile == "PROFILE_C":
        v_thresh = max(50, int(height * 0.40))
        h_thresh = max(50, int(width * 0.40))

    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_thresh))
    vert_lines = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, vert_kernel)
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_thresh, 1))
    horiz_lines = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, horiz_kernel)
    grid = cv2.bitwise_or(vert_lines, horiz_lines)
    final_mask = cv2.subtract(final_mask, grid)
    
    # Clean up residual grid noise
    noise_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, noise_kernel)
    
    return final_mask, chromatic_mask

def compute_global_row_proposals(binary_mask: np.ndarray, median_h: float) -> List[Tuple[int, int]]:
    """
    Step 4: Global Row Proposal Pass
    Compute GLOBAL horizontal text-density profile over the entire crop.
    Returns list of candidate PRIMARY BODY BANDS (start_y, end_y).
    """
    height, width = binary_mask.shape
    ink_per_row = np.sum(binary_mask > 0, axis=1)
    
    smooth_window = max(3, int(median_h * 0.4))
    smoothed_proj = np.convolve(ink_per_row, np.ones(smooth_window) / smooth_window, mode='same')
    
    # Adaptive threshold based on robust statistics (median absolute deviation)
    nonzero_proj = smoothed_proj[smoothed_proj > 0]
    if len(nonzero_proj) == 0:
        return []
        
    med = np.median(nonzero_proj)
    mad = np.median(np.abs(nonzero_proj - med))
    
    # The threshold must be image-relative and robust to preserve short rows (e.g. 'Bài 1:') alongside long rows.
    # Sustained activation bands.
    strong_thresh = max(8.0, min(max(10.0, width * 0.015), 25.0), min(med * 0.35, 25.0))
    
    is_strong = smoothed_proj >= strong_thresh
    
    strong_bands = []
    in_band = False
    start_y = 0
    min_band_h = max(5, int(median_h * 0.4))
    
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
        
    # Merge bands that are extremely close
    merged = []
    for b in strong_bands:
        if not merged:
            merged.append(b)
        else:
            # Tolerate intra-line gaps (e.g., descenders, dots, tone marks)
            if b[0] - merged[-1][1] <= max(12, int(median_h * 1.2)):
                merged[-1] = (merged[-1][0], b[1])
            else:
                merged.append(b)
                
    return merged

def classify_components(binary_mask: np.ndarray, global_bands: List[Tuple[int, int]], median_h: float) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
    """
    Step 5: Local Component Analysis
    Categories: PRIMARY_BODY, SATELLITE, NOISE, AMBIGUOUS
    """
    k_width = max(10, int(median_h * 1.0))
    k_height = max(3, int(median_h * 0.2))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_width, k_height))
    dilated = cv2.dilate(binary_mask, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    primary = []
    satellite = []
    noise = []
    ambiguous = []
    
    img_h, img_w = binary_mask.shape
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        crop = binary_mask[y:y+h, x:x+w]
        ink = cv2.countNonZero(crop)
        
        comp = {"x": x, "y": y, "w": w, "h": h, "ink": ink, "cnt": cnt}
        
        # Calculate overlap with global bands
        overlap_scores = []
        for b_start, b_end in global_bands:
            v_overlap = max(0, min(y + h, b_end) - max(y, b_start))
            overlap_scores.append(v_overlap / max(1, h))
        max_overlap = max(overlap_scores) if overlap_scores else 0
        
        if w < max(4, int(median_h * 0.2)) and h < max(4, int(median_h * 0.2)) and ink < 15:
            noise.append(comp)
            continue
            
        # Primary body check using robust rules
        is_primary = False
        if w >= max(40.0, median_h * 2.5) and ink >= max(50, int(median_h * 3.0)):
            is_primary = True
        elif ink >= max(120, int(median_h * 6.0)):
            is_primary = True
        elif h >= max(10.0, median_h * 0.5) and ink >= max(30, int(median_h * 1.5)) and max_overlap >= 0.5:
            is_primary = True
            
        if is_primary:
            primary.append(comp)
        elif h <= median_h * 1.5 and w <= median_h * 3.0:
            satellite.append(comp)
        else:
            ambiguous.append(comp)
            
    return primary, satellite, noise, ambiguous

