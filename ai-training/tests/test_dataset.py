"""Unit tests for dataset parsing, categorization, and zero-leakage splits."""
import json
from pathlib import Path
import pytest

from scripts.prepare_dataset import classify_text_category
from scripts.split_dataset import split_dataset

_ROOT = Path(__file__).resolve().parent.parent


def test_classify_text_category():
    assert classify_text_category("Bài giải") == "TEXT_ONLY"
    assert classify_text_category("Thời gian xe chạy là:") == "TEXT_ONLY"
    assert classify_text_category("55 x 3 = 165") == "MATH_ONLY"
    assert classify_text_category("12 + 5 = 17") == "MATH_ONLY"
    assert classify_text_category("Thời gian xe chạy là: 45 x 3 = 135 (phút)") == "MIXED"
    assert classify_text_category("55 x 3 = 165 (km)") == "MIXED"
    assert classify_text_category("Đáp số: 165 km") == "MIXED"


def test_split_zero_leakage():
    manifest_p = _ROOT / "data" / "manifests" / "unified_dataset.jsonl"
    if not manifest_p.is_file():
        pytest.skip("unified_dataset.jsonl not yet built")

    report_p = _ROOT / "artifacts" / "reports" / "split_report.json"
    with open(report_p, "r", encoding="utf-8") as f:
        rep = json.load(f)

    audit = rep["leakage_audit"]
    assert audit["zero_leakage_verified"] is True
    assert audit["source_overlap_train_val"] == 0
    assert audit["source_overlap_train_test"] == 0
    assert audit["source_overlap_val_test"] == 0
