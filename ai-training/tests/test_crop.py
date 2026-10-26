"""Unit tests for line segmentation and crop quality gate."""
import numpy as np
import cv2
from pathlib import Path

from scripts.segment_lines import segment_worksheet_lines
from scripts.validate_crops import evaluate_single_crop

_ROOT = Path(__file__).resolve().parent.parent


def cv2_imwrite_unicode(filepath: Path, img: np.ndarray) -> bool:
    try:
        ext = filepath.suffix if filepath.suffix else ".png"
        success, encoded = cv2.imencode(ext, img)
        if success:
            encoded.tofile(str(filepath))
            return True
        return False
    except Exception:
        return False


def test_segment_synthetic_lines():
    # Create white canvas with two realistic text lines
    img = np.full((300, 600, 3), 255, dtype=np.uint8)
    # Line 1: text
    cv2.putText(img, "Thoi gian xe chay la: 1 gio", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    # Line 2: text
    cv2.putText(img, "Dap so: 165 km", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    cfg = {
        "preprocessing": {"deskew_enabled": False},
        "segmentation": {
            "horizontal_merge_distance": 25,
            "vertical_gap_threshold": 10,
            "min_line_width": 50,
            "min_line_height": 14,
            "max_line_height": 150,
            "accent_padding_top": 5,
            "accent_padding_bottom": 5,
            "lateral_padding": 5,
        }
    }

    lines = segment_worksheet_lines(img, cfg)
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
    assert lines[0]["bbox"][1] < lines[1]["bbox"][1], "Lines must be sorted top to bottom"


def test_quality_gate_rejects_pure_white():
    # Pure white image
    blank_img_path = _ROOT / "artifacts" / "crop_debug" / "test_blank.png"
    blank_img_path.parent.mkdir(parents=True, exist_ok=True)
    cv2_imwrite_unicode(blank_img_path, np.full((64, 500, 3), 255, dtype=np.uint8))

    q_cfg = {
        "min_width": 40,
        "min_height": 16,
        "min_ink_pixels": 80,
        "min_ink_ratio": 0.004,
        "blank_line_thresh": 0.995,
    }

    passed, reason, _ = evaluate_single_crop(blank_img_path, q_cfg)
    assert not passed, "Pure white crop must be rejected"
    assert "BLANK" in reason or "INSUFFICIENT_INK" in reason


def test_quality_gate_accepts_valid_crop():
    # Valid line crop with text
    valid_img_path = _ROOT / "artifacts" / "crop_debug" / "test_valid.png"
    valid_img_path.parent.mkdir(parents=True, exist_ok=True)
    img = np.full((64, 400, 3), 255, dtype=np.uint8)
    cv2.putText(img, "55 x 3 = 165", (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2_imwrite_unicode(valid_img_path, img)

    q_cfg = {
        "min_width": 40,
        "min_height": 16,
        "max_height": 250,
        "min_aspect_ratio": 0.8,
        "min_ink_pixels": 50,
        "min_ink_ratio": 0.002,
        "blank_line_thresh": 0.995,
    }

    passed, reason, metrics = evaluate_single_crop(valid_img_path, q_cfg)
    assert passed, f"Valid crop was rejected: {reason}"
    assert reason == "ACCEPTED"
