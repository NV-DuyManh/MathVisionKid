"""
Validate line crop quality gate for MathVision Kids line-level OCR.

Checks:
  - File readable & dimensions valid
  - Minimum/maximum width and height
  - Foreground ink pixel area and ratio
  - Connected components count
  - Aspect ratio (width / height)
  - Blank-line probability (reject white/empty lines)
  - Grid line artifact filter (reject horizontal line-only crops)

Usage:
    python scripts/validate_crops.py --crops_dir data/crops --config configs/crop.yaml
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

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


def evaluate_single_crop(
    image_path: Path,
    q_cfg: Dict[str, Any],
) -> Tuple[bool, str, Dict[str, Any]]:
    """Evaluate quality of single crop image against quality gate thresholds."""
    img = cv2_imread_unicode(image_path)
    if img is None:
        return False, "CORRUPT_OR_UNREADABLE", {}

    h, w = img.shape[:2]
    aspect_ratio = w / max(1, h)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # Ink threshold: foreground = dark pixels (255 in binary_inv)
    _, binary_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    total_pixels = h * w
    ink_pixels = int(np.count_nonzero(binary_inv))
    ink_ratio = ink_pixels / max(1, total_pixels)
    white_ratio = 1.0 - ink_ratio

    # Connected components
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary_inv, connectivity=8)
    cc_count = max(0, num_labels - 1)  # exclude background

    metrics = {
        "width": w,
        "height": h,
        "aspect_ratio": round(aspect_ratio, 3),
        "ink_pixels": ink_pixels,
        "ink_ratio": round(ink_ratio, 5),
        "white_ratio": round(white_ratio, 5),
        "connected_components": cc_count,
    }

    # Thresholds from YAML
    min_w = q_cfg.get("min_width", 40)
    min_h = q_cfg.get("min_height", 16)
    max_h = q_cfg.get("max_height", 250)
    min_aspect = q_cfg.get("min_aspect_ratio", 0.8)
    min_ink = q_cfg.get("min_ink_pixels", 80)
    min_ink_r = q_cfg.get("min_ink_ratio", 0.004)
    max_ink_r = q_cfg.get("max_ink_ratio", 0.70)
    blank_thresh = q_cfg.get("blank_line_thresh", 0.995)

    # 1. Dimension checks
    if w < min_w or h < min_h:
        return False, f"TOO_SMALL (w={w}<{min_w} or h={h}<{min_h})", metrics
    if h > max_h:
        return False, f"TOO_TALL (h={h}>{max_h}, likely multi-line)", metrics
    if aspect_ratio < min_aspect:
        return False, f"ABNORMAL_ASPECT_RATIO (ar={aspect_ratio:.2f}<{min_aspect})", metrics

    # 2. Blank checks
    if white_ratio >= blank_thresh or ink_ratio < min_ink_r:
        return False, f"BLANK_OR_EMPTY (ink_ratio={ink_ratio:.4f}<{min_ink_r})", metrics
    if ink_pixels < min_ink:
        return False, f"INSUFFICIENT_INK (ink_pixels={ink_pixels}<{min_ink})", metrics

    # 3. Dense shadow / black blob check
    if ink_ratio > max_ink_r:
        return False, f"SOLID_BLOB_OR_SHADOW (ink_ratio={ink_ratio:.4f}>{max_ink_r})", metrics

    # 4. Pure grid line check (horizontal line only)
    if q_cfg.get("reject_isolated_grid_lines", True):
        h_kern = cv2.getStructuringElement(cv2.MORPH_RECT, (int(w * 0.7), 1))
        h_lines = cv2.morphologyEx(binary_inv, cv2.MORPH_OPEN, h_kern)
        h_line_pixels = int(np.count_nonzero(h_lines))
        if h_line_pixels > 0.85 * ink_pixels and cc_count <= 2:
            return False, "ISOLATED_GRID_LINE (only long horizontal rule)", metrics

    return True, "ACCEPTED", metrics


def validate_crops_directory(
    crops_dir: Path,
    config_path: Path,
    output_report_path: Path,
) -> Dict[str, Any]:
    print("=" * 70)
    print("           MATHVISION LINE CROP QUALITY GATE")
    print("=" * 70)
    print(f"Crops directory: {crops_dir}")

    q_cfg = {}
    if config_path.is_file():
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            q_cfg = cfg.get("quality_gate", {})

    crop_files = []
    for ext in [".png", ".jpg", ".jpeg", ".bmp"]:
        crop_files.extend(list(crops_dir.glob(f"*{ext}")))
    crop_files = sorted(crop_files)

    print(f"Found {len(crop_files)} crops to validate.")

    accepted_list = []
    rejected_list = []

    for p in crop_files:
        passed, reason, metrics = evaluate_single_crop(p, q_cfg)
        record = {
            "crop_path": str(p),
            "filename": p.name,
            "status": "ACCEPTED" if passed else "REJECTED",
            "reason": reason,
            "metrics": metrics,
        }
        if passed:
            accepted_list.append(record)
        else:
            rejected_list.append(record)

    total = len(crop_files)
    acc_count = len(accepted_list)
    rej_count = len(rejected_list)
    pass_rate = (acc_count / max(1, total)) * 100.0

    print("\n" + "=" * 70)
    print(f"  Total crops evaluated : {total}")
    print(f"  Accepted              : {acc_count} ({pass_rate:.1f}%)")
    print(f"  Rejected              : {rej_count}")
    if rejected_list:
        print("  Rejection reasons breakdown:")
        reason_counts = {}
        for r in rejected_list:
            reason = r["reason"].split()[0]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        for reason, cnt in sorted(reason_counts.items(), key=lambda x: -x[1]):
            print(f"    - {reason:<25} : {cnt}")
    print("=" * 70)

    report = {
        "status": "PASS",
        "total_crops": total,
        "accepted_count": acc_count,
        "rejected_count": rej_count,
        "pass_rate_percent": round(pass_rate, 2),
        "accepted_samples": accepted_list[:10],
        "rejected_samples": rejected_list[:10],
    }

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Crop validation report saved to: {output_report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Validate line crops using quality gate.")
    parser.add_argument("--crops_dir", type=str, default="data/crops", help="Path to crops directory")
    parser.add_argument("--config", type=str, default="configs/crop.yaml", help="Path to crop config")
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/reports/crop_report.json",
        help="Path to output JSON report",
    )

    args = parser.parse_args()
    validate_crops_directory(
        crops_dir=Path(args.crops_dir).resolve(),
        config_path=Path(args.config).resolve(),
        output_report_path=Path(args.output).resolve(),
    )


if __name__ == "__main__":
    main()
