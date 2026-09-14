import cv2
import numpy as np
from typing import List, Tuple
from app.schemas.ocr_pilot import LineBox

def score_and_assign_rows(
    primary: List[dict],
    satellite: List[dict], 
    ambiguous: List[dict],
    global_bands: List[Tuple[int, int]],
    median_h: float
) -> Tuple[List[dict], List[dict]]:
    """
    Step 6: Row Assignment
    Assign components to row proposals using a score based on distance, overlap, mass.
    Returns (assigned_rows, unassigned_components).
    An assigned_row is a dict: {"band": (y1, y2), "components": [], "box": (x,y,w,h)}
    """
    assigned_rows = [{"band": b, "components": [], "box": None} for b in global_bands]
    unassigned = []
    
    all_comps = primary + satellite + ambiguous
    
    for comp in all_comps:
        x, y, w, h = comp["x"], comp["y"], comp["w"], comp["h"]
        c_y = y + h / 2.0
        
        best_band_idx = -1
        best_score = -99999.0
        
        for idx, row in enumerate(assigned_rows):
            b_start, b_end = row["band"]
            b_c_y = (b_start + b_end) / 2.0
            b_h = max(1, b_end - b_start)
            
            v_overlap = max(0, min(y + h, b_end) - max(y, b_start))
            overlap_ratio = v_overlap / max(1, h)
            dist = abs(c_y - b_c_y)
            
            # Distance penalty
            score = (overlap_ratio * 100.0) - (dist / b_h * 50.0)
            
            if score > best_score and dist < max(35.0, median_h * 3.5):
                # Additional check: don't assign if it's completely disconnected horizontally?
                # Actually, components are just assigned vertically.
                best_score = score
                best_band_idx = idx
                
        if best_band_idx >= 0 and best_score > -50.0:
            assigned_rows[best_band_idx]["components"].append(comp)
        else:
            unassigned.append(comp)
            
    # Compute bounding boxes for each row based on assigned components
    final_rows = []
    for row in assigned_rows:
        if not row["components"]:
            continue
        min_x = min(c["x"] for c in row["components"])
        min_y = min(c["y"] for c in row["components"])
        max_x = max(c["x"] + c["w"] for c in row["components"])
        max_y = max(c["y"] + c["h"] for c in row["components"])
        row["box"] = (min_x, min_y, max_x - min_x, max_y - min_y)
        
        # Check if the row has any primary evidence
        has_primary = any(c in primary for c in row["components"])
        row["has_primary"] = has_primary
        
        final_rows.append(row)
        
    return final_rows, unassigned

def compute_strong_body_bands(binary_mask: np.ndarray, median_h: float, w: int, h: int, thresh_multiplier: float = 0.015) -> List[Tuple[int, int]]:
    # Exact same logic used in global proposal but specifically for a crop (splitting)
    ink_per_row = np.sum(binary_mask > 0, axis=1)
    smooth_window = max(3, int(median_h * 0.4))
    smoothed_proj = np.convolve(ink_per_row, np.ones(smooth_window) / smooth_window, mode='same')
    
    strong_thresh = max(10.0, w * thresh_multiplier)
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
    if in_band and (h - start_y) >= min_band_h:
        strong_bands.append((start_y, h))
        
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

def recursive_split_merged_rows(box: Tuple[int, int, int, int], binary_mask: np.ndarray, median_h: float) -> List[Tuple[int, int, int, int]]:
    """
    Step 7: Merged-Row Splitting
    """
    x, y, w, h = box
    if h < median_h * 1.5:
        return [box]
        
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(binary_mask.shape[1], x + w), min(binary_mask.shape[0], y + h)
    crop = binary_mask[y1:y2, x1:x2]
    
    best_bands = []
    # Iterative water-level splitting: raise threshold if it's suspiciously tall
    for multiplier in [0.015, 0.03, 0.05, 0.08, 0.12, 0.15]:
        bands = compute_strong_body_bands(crop, median_h, w, h, thresh_multiplier=multiplier)
        if len(bands) >= 2:
            best_bands = bands
            break
            
    if not best_bands:
        return [box]
        
    bands = best_bands
        
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
        
        child_box = (x1 + c_min, c_y_offset + r_min, c_max - c_min + 1, r_max - r_min + 1)
        
        children.extend(recursive_split_merged_rows(child_box, binary_mask, median_h))
        
    return children if children else [box]

def verify_primary_body_requirement(box: Tuple[int, int, int, int], binary_mask: np.ndarray, median_h: float) -> bool:
    """
    Step 9: Primary-Body Requirement for Standalone Rows
    """
    x, y, w, h = box
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(binary_mask.shape[1], x + w), min(binary_mask.shape[0], y + h)
    crop = binary_mask[y1:y2, x1:x2]
    ink = cv2.countNonZero(crop)
    
    if w >= max(60.0, median_h * 2.8) and ink >= max(90, int(median_h * 4.5)):
        return True
    if ink >= max(160, int(median_h * 8.0)):
        return True
    if h >= max(10.0, median_h * 0.5) and ink >= max(35, int(median_h * 1.8)) and w >= max(15.0, median_h * 0.8):
        return True
    return False

def get_body_center(b: Tuple[int, int, int, int], binary_mask: np.ndarray) -> float:
    x, y, w, h = b
    crop = binary_mask[max(0,y):min(binary_mask.shape[0],y+h), max(0,x):min(binary_mask.shape[1],x+w)]
    row_proj = np.sum(crop > 0, axis=1)
    total_ink = np.sum(row_proj)
    if total_ink == 0:
        return float(y + h / 2.0)
    com = np.sum(np.arange(crop.shape[0]) * row_proj) / total_ink
    return float(y + com)

def consolidate_fragments(boxes: List[Tuple[int, int, int, int]], binary_mask: np.ndarray, median_h: float) -> List[Tuple[int, int, int, int]]:
    """
    Step 8: Same-Row Consolidation (post-split)
    Merge fragmented boxes that clearly belong to the same line.
    """
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    changed = True
    while changed:
        changed = False
        new_boxes = []
        skip = set()
        for i in range(len(boxes)):
            if i in skip: continue
            b1 = boxes[i]
            x1, y1, w1, h1 = b1
            c1_y = get_body_center(b1, binary_mask)
            
            for j in range(i + 1, len(boxes)):
                if j in skip: continue
                b2 = boxes[j]
                x2, y2, w2, h2 = b2
                c2_y = get_body_center(b2, binary_mask)
                
                v_gap = max(0, max(y1, y2) - min(y1+h1, y2+h2))
                h_gap = max(0, max(x1, x2) - min(x1+w1, x2+w2))
                v_overlap = max(0, min(y1+h1, y2+h2) - max(y1, y2))
                h_overlap = max(0, min(x1+w1, x2+w2) - max(x1, x2))
                
                center_dist = abs(c1_y - c2_y)
                
                # MERGE GATE MUST BE STRICTER: Require small body-center distance
                should_merge = False
                if center_dist <= max(15.0, median_h * 1.5):
                    if v_overlap / max(1, min(h1, h2)) >= 0.4 and h_gap <= max(40.0, median_h * 4.0):
                        should_merge = True
                    elif v_gap <= max(15.0, median_h * 1.5) and h_overlap > 0:
                        should_merge = True
                        
                        # Do not merge two independent full-width lines
                        if w1 > median_h * 15 and w2 > median_h * 15 and v_overlap / max(1, min(h1, h2)) < 0.3:
                            should_merge = False

                        
                if should_merge:
                    nx, ny = min(x1, x2), min(y1, y2)
                    nw = max(x1+w1, x2+w2) - nx
                    nh = max(y1+h1, y2+h2) - ny
                    b1 = (nx, ny, nw, nh)
                    x1, y1, w1, h1 = b1
                    c1_y = get_body_center(b1, binary_mask)
                    skip.add(j)
                    changed = True
            new_boxes.append(b1)
        boxes = sorted(new_boxes, key=lambda b: (b[1], b[0]))
    return boxes

def run_generalized_line_detection(bgr_image: np.ndarray, max_lines: int = 30) -> Tuple[List[LineBox], dict]:
    """
    The General Handwriting Line Segmentation Pipeline.
    """
    from app.api.ocr import correct_skew
    bgr_image = correct_skew(bgr_image, max_angle=10.0)
    height, width = bgr_image.shape[:2]
    
    from app.api.generalized import extract_ink_mask, compute_global_row_proposals, classify_components
    final_mask, chromatic_mask = extract_ink_mask(bgr_image, height, width)
    
    if cv2.countNonZero(final_mask) < 20:
        return [], {
            "detector_version": "generalized-20260914",
            "path_a_count": 0,
            "path_a_suspicious": True,
            "suspicious_reason": "EMPTY_IMAGE",
            "path_b_invoked": False,
            "dominant_hue": None,
            "projection_band_count": 0,
            "final_box_count": 0,
            "needs_review": False
        }
        
    raw_cnts, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
    median_h = float(np.median(heights)) if heights else 15.0
    
    global_bands = compute_global_row_proposals(final_mask, median_h)
    primary, satellite, noise, ambiguous = classify_components(final_mask, global_bands, median_h)
    
    assigned_rows, unassigned = score_and_assign_rows(primary, satellite, ambiguous, global_bands, median_h)
    
    # Generate initial candidate boxes from assigned rows
    candidate_boxes = [r["box"] for r in assigned_rows if r["box"] is not None]
        
    # Same row consolidation with Strict Body Centers
    consolidated = consolidate_fragments(candidate_boxes, final_mask, median_h)
    
    # Satellite Attachment
    for comp in unassigned:
        sx, sy, sw, sh = comp["x"], comp["y"], comp["w"], comp["h"]
        best_p_idx = -1
        best_dist = 999999.0
        
        for p_idx, b in enumerate(consolidated):
            px, py, pw, ph = b
            v_gap = max(0, max(py, sy) - min(py + ph, sy + sh))
            h_overlap = max(0, min(px + pw, sx + sw) - max(px, sx))
            h_gap = max(0, max(px, sx) - min(px + pw, sx + sw))
            
            if v_gap <= max(40.0, median_h * 4.0) and (h_overlap > 0 or h_gap <= max(25.0, median_h * 2.0)):
                dist = v_gap + h_gap * 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_p_idx = p_idx
                    
        if best_p_idx >= 0:
            p = consolidated[best_p_idx]
            nx, ny = min(p[0], sx), min(p[1], sy)
            nw = max(p[0] + p[2], sx + sw) - nx
            nh = max(p[1] + p[3], sy + sh) - ny
            consolidated[best_p_idx] = (nx, ny, nw, nh)

    # POST-MERGE PURITY AUDIT
    final_split_boxes = []
    for b in consolidated:
        final_split_boxes.extend(recursive_split_merged_rows(b, final_mask, median_h))
        
    consolidated = final_split_boxes
    
    # Filter by primary body requirement
    final_boxes = []
    for b in consolidated:
        if verify_primary_body_requirement(b, final_mask, median_h):
            final_boxes.append(b)
            
    # Check Coverage / Missing Rows
    unassigned_ink = sum(c["ink"] for c in unassigned)
    total_ink = cv2.countNonZero(final_mask)
    ink_coverage = (total_ink - unassigned_ink) / max(1, total_ink)
    
    sorted_final = sorted(final_boxes, key=lambda b: (b[1], b[0]))
    if len(sorted_final) > max_lines:
        sorted_final = sorted_final[:max_lines]
    line_results = [
        LineBox(line_id=f"line_{idx}", x=int(b[0]), y=int(b[1]), width=int(b[2]), height=int(b[3]), order=idx)
        for idx, b in enumerate(sorted_final, 1)
    ]
    
    needs_review = False
    if ink_coverage < 0.20 or (len(global_bands) > 0 and len(line_results) > len(global_bands) * 2):
        needs_review = True
    if any(b.height > max(60, int(median_h * 3.5)) for b in line_results):
        needs_review = True
    if ink_coverage < 0.5:
        needs_review = True
        
    if len(ambiguous) + len(noise) > max(20, len(primary) * 3):
        needs_review = True
        
    # Padding
    padded_boxes = []
    for b in final_boxes:
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
        
    diagnostics = {
        "detector_version": "generalized-20260914",
        "bands_detected": len(global_bands),
        "final_box_count": len(line_results),
        "ink_coverage_ratio": float(ink_coverage),
        "needs_review": needs_review,
        # Legacy compatibility keys for contract tests
        "path_a_suspicious": False,
        "path_b_invoked": False,
        "path_a_count": len(line_results)
    }
    
    return line_results, diagnostics
