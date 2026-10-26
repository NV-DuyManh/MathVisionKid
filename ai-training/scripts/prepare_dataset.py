"""
Prepare verified line crop records into unified dataset format.

Fields per record:
  - image_path: path to line crop image
  - source_image_id: ID of parent worksheet
  - source_group: grouping key (folder / source document)
  - source_folder: directory category
  - text: verified target text string
  - category: TEXT_ONLY | MATH_ONLY | MIXED
  - status: VERIFIED
  - image_sha256: SHA-256 hash of image file
  - dataset_version: 1.0.0
  - preprocessing_version: 1.0.0

Usage:
    python scripts/prepare_dataset.py --input data/manifests/verified_labels.jsonl --output data/manifests/unified_dataset.jsonl
"""
import sys
import os
import json
import hashlib
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def compute_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def classify_text_category(text: str) -> str:
    """Classify line into TEXT_ONLY, MATH_ONLY, or MIXED."""
    # Math operators (+, =, ×, ÷, *, or division ':' surrounded by spaces/numbers, or minus '-' between digits)
    has_math_ops = bool(
        re.search(
            r"[+=×÷*<>]|(?:\d+\s*[:]\s*\d+)|(?:\s+[:]\s+\d+)|(?:\d+\s*[-]\s*\d+)|(?:\b\d+\s*x\s*\d+\b)|(?:\s+x\s+\d+)|(?:\d+\s+x\s+)",
            text,
        )
    )
    has_digits = bool(re.search(r"\d", text))

    # Strip math operator x (e.g. 55 x 3) so 'x' is not misidentified as a word
    text_without_math_x = re.sub(r"(?:\b\d+\s*x\s*\d+\b)|(?:\s+x\s+\d+)|(?:\d+\s+x\s+)", " ", text)
    has_viet_words = bool(
        re.search(
            r"[a-zA-ZàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]",
            text_without_math_x,
        )
    )

    is_math = has_math_ops or has_digits
    if is_math and has_viet_words:
        return "MIXED"
    elif is_math and not has_viet_words:
        return "MATH_ONLY"
    else:
        return "TEXT_ONLY"


def prepare_dataset(
    input_manifest_path: Path,
    output_unified_path: Path,
    dataset_version: str = "1.0.0",
    preprocessing_version: str = "1.0.0",
) -> List[Dict[str, Any]]:
    print("=" * 70)
    print("            MATHVISION DATASET PREPARATION")
    print("=" * 70)
    print(f"Input manifest  : {input_manifest_path}")
    print(f"Output manifest : {output_unified_path}")

    if not input_manifest_path.is_file():
        raise FileNotFoundError(f"Input manifest not found: {input_manifest_path}")

    raw_records = []
    with open(input_manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                raw_records.append(json.loads(line.strip()))

    print(f"Processing {len(raw_records)} input records...")

    prepared = []
    cat_counts = {"TEXT_ONLY": 0, "MATH_ONLY": 0, "MIXED": 0}

    for rec in raw_records:
        status = rec.get("status", "VERIFIED")
        if status != "VERIFIED":
            # Only VERIFIED records are permitted into training dataset
            continue

        crop_p = Path(rec.get("crop_path", rec.get("image_path", "")))
        text = rec.get("text", rec.get("reviewed_text", "")).strip()

        if not crop_p.is_file() or not text:
            continue

        sha256 = compute_file_sha256(crop_p)
        category = classify_text_category(text)
        cat_counts[category] = cat_counts.get(category, 0) + 1

        # Derive source image ID and group
        src_img_id = rec.get("source_image_id") or crop_p.stem.split("_line_")[0]
        src_folder = rec.get("source_folder") or crop_p.parent.name
        src_group = rec.get("source_group") or src_folder

        unified_rec = {
            "image_path": str(crop_p),
            "source_image_id": src_img_id,
            "source_group": src_group,
            "source_folder": src_folder,
            "text": text,
            "category": category,
            "status": "VERIFIED",
            "image_sha256": sha256,
            "dataset_version": dataset_version,
            "preprocessing_version": preprocessing_version,
        }
        prepared.append(unified_rec)

    output_unified_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_unified_path, "w", encoding="utf-8") as f:
        for r in prepared:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n" + "=" * 70)
    print(f"Total VERIFIED records packaged: {len(prepared)}")
    print(f"  TEXT_ONLY : {cat_counts.get('TEXT_ONLY', 0)}")
    print(f"  MATH_ONLY : {cat_counts.get('MATH_ONLY', 0)}")
    print(f"  MIXED     : {cat_counts.get('MIXED', 0)}")
    print(f"Saved to: {output_unified_path}")
    print("=" * 70)
    return prepared


def main():
    parser = argparse.ArgumentParser(description="Prepare verified OCR records into unified dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/manifests/verified_labels.jsonl",
        help="Path to verified labels manifest",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/manifests/unified_dataset.jsonl",
        help="Path to output unified manifest",
    )

    args = parser.parse_args()
    prepare_dataset(
        input_manifest_path=Path(args.input).resolve(),
        output_unified_path=Path(args.output).resolve(),
    )


if __name__ == "__main__":
    main()
