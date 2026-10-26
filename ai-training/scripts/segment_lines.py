"""
Line segmentation pipeline for MathVision Kids handwriting worksheets.

Pipeline:
  1. Grayscale conversion & optional deskew.
  2. Otsu/adaptive thresholding for ink foreground extraction.
  3. Connected components & horizontal projection profile.
  4. Primary row detection & satellite diacritic absorption (accent preservation).
  5. Pure grid line rejection.
  6. Tight crop extraction with configurable safety padding.
  7. Saves line crops and debug bounding-box visualizations.

Usage:
    python scripts/segment_lines.py --input path/to/worksheet.jpg
    python scripts/segment_lines.py --input_dir path/to/worksheets/ --config configs/crop.yaml
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import cv2
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def cv2_imread_unicode(filepath: Path) -> Optional[np.ndarray]:
    """Unicode-safe image reader for Windows filesystem paths."""
    try:
        data = np.fromfile(str(filepath), dtype=np.uint8)
        if data is None or len(data) == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def cv2_imwrite_unicode(filepath: Path, img: np.ndarray) -> bool:
    """Unicode-safe image writer for Windows filesystem paths."""
    try:
        ext = filepath.suffix if filepath.suffix else ".png"
        success, encoded = cv2.imencode(ext, img)
        if success:
            encoded.tofile(str(filepath))
            return True
        return False
    except Exception:
        return False


def deskew_image(gray: np.ndarray, max_angle: float = 15.0) -> Tuple[np.ndarray, float]:
    """Estimate skew angle via Hough lines or minAreaRect and rotate image."""
    h, w = gray.shape[:2]
    # Simple Otsu invert: ink is white, background is black
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) < 100:
        return gray, 0.0

    angle = 0.0
    try:
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) > max_angle:
            angle = 0.0
    except Exception:
        angle = 0.0

    if abs(angle) > 0.5:
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated, angle
    return gray, 0.0


def segment_worksheet_lines(
    image: np.ndarray,
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Segment handwritten text lines from worksheet image."""
    h_orig, w_orig = image.shape[:2]

    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Deskew if enabled
    skew_angle = 0.0
    if config.get("preprocessing", {}).get("deskew_enabled", True):
        max_ang = config.get("preprocessing", {}).get("deskew_max_angle", 15.0)
        gray, skew_angle = deskew_image(gray, max_angle=max_ang)

    # Invert binary: ink is foreground (255), paper is background (0)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Remove thin graph paper lines (horizontal and vertical line filter)
    # Long thin horizontal lines (> 80px wide, <= 2px high)
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    detected_h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
    detected_v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)
    grid_mask = cv2.bitwise_or(detected_h_lines, detected_v_lines)

    # Ink without grid lines (for line detection)
    ink_clean = cv2.subtract(binary, grid_mask)

    # Morphological dilation horizontally to connect words in the same line
    h_dist = config.get("segmentation", {}).get("horizontal_merge_distance", 25)
    merge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_dist, 3))
    dilated = cv2.dilate(ink_clean, merge_kernel, iterations=1)

    # Connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)

    min_line_w = config.get("segmentation", {}).get("min_line_width", 50)
    min_line_h = config.get("segmentation", {}).get("min_line_height", 14)
    max_line_h = config.get("segmentation", {}).get("max_line_height", 220)

    candidate_boxes = []
    for i in range(1, num_labels):
        bx = stats[i, cv2.CC_STAT_LEFT]
        by = stats[i, cv2.CC_STAT_TOP]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        if bw >= min_line_w and min_line_h <= bh <= max_line_h and area > 100:
            candidate_boxes.append((bx, by, bw, bh))

    # Sort boxes top to bottom
    candidate_boxes.sort(key=lambda b: b[1])

    # Merge overlapping or close rows on similar baseline (y overlap)
    v_gap_thresh = config.get("segmentation", {}).get("vertical_gap_threshold", 12)
    merged_rows = []
    for box in candidate_boxes:
        bx, by, bw, bh = box
        merged = False
        for j, (mx, my, mw, mh) in enumerate(merged_rows):
            # Check vertical overlap or close proximity
            y_overlap = max(0, min(by + bh, my + mh) - max(by, my))
            v_gap = max(0, max(by, my) - min(by + bh, my + mh))
            h_overlap = max(0, min(bx + bw, mx + mw) - max(bx, mx))

            # Merge if on same horizontal baseline (v_gap == 0 or significant y overlap)
            if y_overlap > 0.4 * min(bh, mh) or (v_gap <= v_gap_thresh and h_overlap > 0):
                nx1 = min(bx, mx)
                ny1 = min(by, my)
                nx2 = max(bx + bw, mx + mw)
                ny2 = max(by + bh, my + mh)
                merged_rows[j] = (nx1, ny1, nx2 - nx1, ny2 - ny1)
                merged = True
                break
        if not merged:
            merged_rows.append((bx, by, bw, bh))

    # Add accent safety padding to protect Vietnamese diacritics
    pad_top = config.get("segmentation", {}).get("accent_padding_top", 8)
    pad_bottom = config.get("segmentation", {}).get("accent_padding_bottom", 8)
    pad_lat = config.get("segmentation", {}).get("lateral_padding", 12)

    line_crops_info = []
    for idx, (bx, by, bw, bh) in enumerate(sorted(merged_rows, key=lambda b: b[1])):
        crop_y1 = max(0, by - pad_top)
        crop_y2 = min(h_orig, by + bh + pad_bottom)
        crop_x1 = max(0, bx - pad_lat)
        crop_x2 = min(w_orig, bx + bw + pad_lat)

        crop_w = crop_x2 - crop_x1
        crop_h = crop_y2 - crop_y1

        if crop_w < 30 or crop_h < 12:
            continue

        # Extract crop from original image
        crop_img = image[crop_y1:crop_y2, crop_x1:crop_x2]

        line_crops_info.append({
            "line_index": idx + 1,
            "bbox": [crop_x1, crop_y1, crop_w, crop_h],
            "crop_image": crop_img,
            "original_size": [w_orig, h_orig],
            "skew_angle": skew_angle,
        })

    return line_crops_info


def process_images(
    input_paths: List[Path],
    output_crops_dir: Path,
    output_debug_dir: Path,
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    output_crops_dir.mkdir(parents=True, exist_ok=True)
    output_debug_dir.mkdir(parents=True, exist_ok=True)

    all_crops_metadata = []

    for img_path in input_paths:
        print(f"Segmenting: {img_path.name}...")
        img = cv2_imread_unicode(img_path)
        if img is None:
            print(f"  [WARN] Failed to read image: {img_path}")
            continue

        lines = segment_worksheet_lines(img, config)
        print(f"  -> Extracted {len(lines)} lines.")

        debug_canvas = img.copy()
        for item in lines:
            line_idx = item["line_index"]
            bx, by, bw, bh = item["bbox"]
            crop_img = item["crop_image"]

            crop_filename = f"{img_path.stem}_line_{line_idx:02d}.png"
            crop_save_path = output_crops_dir / crop_filename
            cv2_imwrite_unicode(crop_save_path, crop_img)

            # Draw on debug canvas
            cv2.rectangle(debug_canvas, (bx, by), (bx + bw, by + bh), (0, 200, 0), 2)
            cv2.putText(
                debug_canvas,
                f"L{line_idx}",
                (bx + 2, by + 16),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
            )

            all_crops_metadata.append({
                "crop_id": crop_save_path.stem,
                "crop_file": str(crop_save_path),
                "source_image": str(img_path),
                "source_image_id": img_path.stem,
                "line_index": line_idx,
                "bbox": [bx, by, bw, bh],
                "width": bw,
                "height": bh,
            })

        # Save debug image
        debug_save_path = output_debug_dir / f"{img_path.stem}_boxes.png"
        cv2_imwrite_unicode(debug_save_path, debug_canvas)

    return all_crops_metadata


def main():
    parser = argparse.ArgumentParser(description="Segment handwritten text lines from worksheet images.")
    parser.add_argument("--input", type=str, default="", help="Path to single image")
    parser.add_argument("--input_dir", type=str, default="", help="Path to directory of images")
    parser.add_argument("--config", type=str, default="configs/crop.yaml", help="Path to crop.yaml config")
    parser.add_argument("--output_crops", type=str, default="data/crops", help="Dir to save crops")
    parser.add_argument("--output_debug", type=str, default="artifacts/crop_debug", help="Dir to save debug images")

    args = parser.parse_args()

    config = {}
    if os.path.exists(args.config):
        import yaml
        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    input_paths = []
    if args.input:
        input_paths.append(Path(args.input).resolve())
    elif args.input_dir:
        dir_p = Path(args.input_dir).resolve()
        for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            input_paths.extend(list(dir_p.glob(f"*{ext}")))
    else:
        # Default fixture sample images if no args provided
        sample_dir = Path("artifacts/samples").resolve()
        if sample_dir.exists():
            for ext in [".jpg", ".jpeg", ".png"]:
                input_paths.extend(list(sample_dir.glob(f"*{ext}")))
        if not input_paths:
            # Check ocr_engine samples
            stg_sample = Path("handoff/staging/ocr_engine_handoff_final/ocr_engine/samples").resolve()
            if stg_sample.exists():
                for ext in [".jpg", ".jpeg", ".png"]:
                    input_paths.extend(list(stg_sample.glob(f"*{ext}")))

    print(f"Total worksheet images to process: {len(input_paths)}")
    process_images(
        input_paths=input_paths,
        output_crops_dir=Path(args.output_crops).resolve(),
        output_debug_dir=Path(args.output_debug).resolve(),
        config=config,
    )


if __name__ == "__main__":
    main()
