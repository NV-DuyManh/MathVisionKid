"""
MathVision Kids — Arithmetic OCR Line Dataset Builder
Task: OCR.DATA.1 — Arithmetic Line Dataset Builder & Fine-Tuning Handoff Preparation
Mode: DATA ENGINEERING / NO MODEL TRAINING / LOCAL-FIRST
"""
import os
import sys
import json
import hashlib
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont

# Workspace roots
WORKSPACE_ROOT = Path(r"E:\MathVisionKid")
CROPS_DIR = WORKSPACE_ROOT / "ai-training" / "datasets" / "arithmetic_ocr_line_v1" / "crops"
HANDOFF_DIR = WORKSPACE_ROOT / "ai-training" / "handoff" / "outgoing" / "arithmetic_ocr_line_v1"
EVIDENCE_DIR = WORKSPACE_ROOT / "report" / "evidence" / "ocr_data_1"

CROPS_DIR.mkdir(parents=True, exist_ok=True)
HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
(HANDOFF_DIR / "splits").mkdir(parents=True, exist_ok=True)
(HANDOFF_DIR / "config").mkdir(parents=True, exist_ok=True)
(HANDOFF_DIR / "reports").mkdir(parents=True, exist_ok=True)
(HANDOFF_DIR / "samples").mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().lower()


# ─── Raw Source Definitions ──────────────────────────────────────────────────
# All bounding boxes are defined in pixel coordinates [x1, y1, x2, y2]
# derived strictly from verified ground-truth annotations and programmatic layouts.
# NO model predictions are used.

SOURCES = [
    {
        "source_image_id": "sample_input_synthetic",
        "image_path": WORKSPACE_ROOT / "services" / "ai-service" / "tests" / "fixtures" / "sample_input_synthetic.jpg",
        "operation": "VERTICAL_ADDITION",
        "is_synthetic": True,
        "pii_status": "DEIDENTIFIED_SYNTHETIC",
        "annotation_source": "expected_output.json + verified ink geometry",
        "writer_id": "ANONYMOUS_SYNTHETIC_01",
        "seen_by_yolo": "YES",
        "target_split": "train",
        "rows": [
            {
                "row_index": 0,
                "raw_label": "38",
                "row_type": "OPERAND",
                "bbox": (506, 220, 722, 340),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 1,
                "raw_label": "+47",
                "row_type": "OPERATOR_OPERAND",
                "bbox": (330, 335, 730, 505),
                "digit_count": 2,
                "contains_operator": True,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 2,
                "raw_label": "=",
                "row_type": "SEPARATOR",
                "bbox": (436, 522, 769, 535),
                "digit_count": 0,
                "contains_operator": False,
                "contains_carry_context": False,
                "contains_borrow_context": False,
                "is_ocr_eligible": False,
                "exclusion_reason": "SEPARATOR_HORIZONTAL_RULE_NON_TEXTUAL",
            },
            {
                "row_index": 3,
                "raw_label": "85",
                "row_type": "RESULT",
                "bbox": (517, 550, 730, 676),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
        ],
    },
    {
        "source_image_id": "synthetic_addition",
        "image_path": WORKSPACE_ROOT / "services" / "ai-service" / "tests" / "fixtures" / "synthetic_addition.jpg",
        "operation": "VERTICAL_ADDITION",
        "is_synthetic": True,
        "pii_status": "DEIDENTIFIED_SYNTHETIC",
        "annotation_source": "programmatic vertical addition fixture (45 + 27 = 72)",
        "writer_id": "ANONYMOUS_SYNTHETIC_02",
        "seen_by_yolo": "YES",
        "target_split": "train",
        "rows": [
            {
                "row_index": 0,
                "raw_label": "45",
                "row_type": "OPERAND",
                "bbox": (261, 154, 376, 207),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 1,
                "raw_label": "+27",
                "row_type": "OPERATOR_OPERAND",
                "bbox": (184, 254, 376, 306),
                "digit_count": 2,
                "contains_operator": True,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 2,
                "raw_label": "=",
                "row_type": "SEPARATOR",
                "bbox": (170, 339, 420, 343),
                "digit_count": 0,
                "contains_operator": False,
                "contains_carry_context": False,
                "contains_borrow_context": False,
                "is_ocr_eligible": False,
                "exclusion_reason": "SEPARATOR_HORIZONTAL_RULE_NON_TEXTUAL",
            },
            {
                "row_index": 3,
                "raw_label": "72",
                "row_type": "RESULT",
                "bbox": (263, 384, 376, 436),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
        ],
    },
    {
        "source_image_id": "synthetic_addition_carry",
        "image_path": WORKSPACE_ROOT / "services" / "ai-service" / "tests" / "fixtures" / "synthetic_addition_carry.jpg",
        "operation": "VERTICAL_ADDITION",
        "is_synthetic": True,
        "pii_status": "DEIDENTIFIED_SYNTHETIC",
        "annotation_source": "programmatic vertical addition with carry marker (1 above 45 + 27 = 72)",
        "writer_id": "ANONYMOUS_SYNTHETIC_02",
        "seen_by_yolo": "YES",
        "target_split": "train",
        "rows": [
            {
                "row_index": 0,
                "raw_label": "1",
                "row_type": "CARRY_ONLY",
                "bbox": (274, 90, 283, 96),
                "digit_count": 1,
                "contains_operator": False,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": False,
                "exclusion_reason": "CARRY_ONLY_AUXILIARY_MARKER_EXCLUDED_PER_SECTION_7",
            },
            {
                "row_index": 1,
                "raw_label": "45",
                "row_type": "OPERAND",
                "bbox": (261, 154, 376, 207),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 2,
                "raw_label": "+27",
                "row_type": "OPERATOR_OPERAND",
                "bbox": (184, 254, 376, 306),
                "digit_count": 2,
                "contains_operator": True,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 3,
                "raw_label": "=",
                "row_type": "SEPARATOR",
                "bbox": (170, 339, 420, 343),
                "digit_count": 0,
                "contains_operator": False,
                "contains_carry_context": False,
                "contains_borrow_context": False,
                "is_ocr_eligible": False,
                "exclusion_reason": "SEPARATOR_HORIZONTAL_RULE_NON_TEXTUAL",
            },
            {
                "row_index": 4,
                "raw_label": "72",
                "row_type": "RESULT",
                "bbox": (263, 384, 376, 436),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": True,
                "contains_borrow_context": False,
                "is_ocr_eligible": True,
            },
        ],
    },
    {
        "source_image_id": "synthetic_subtraction",
        "image_path": WORKSPACE_ROOT / "services" / "ai-service" / "tests" / "fixtures" / "synthetic_subtraction.jpg",
        "operation": "VERTICAL_SUBTRACTION",
        "is_synthetic": True,
        "pii_status": "DEIDENTIFIED_SYNTHETIC",
        "annotation_source": "programmatic vertical subtraction fixture (52 - 18 = 34)",
        "writer_id": "ANONYMOUS_SYNTHETIC_03",
        "seen_by_yolo": "YES",
        "target_split": "val",
        "rows": [
            {
                "row_index": 0,
                "raw_label": "52",
                "row_type": "OPERAND",
                "bbox": (263, 154, 376, 207),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": False,
                "contains_borrow_context": True,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 1,
                "raw_label": "-18",
                "row_type": "OPERATOR_OPERAND",
                "bbox": (182, 254, 376, 307),
                "digit_count": 2,
                "contains_operator": True,
                "contains_carry_context": False,
                "contains_borrow_context": True,
                "is_ocr_eligible": True,
            },
            {
                "row_index": 2,
                "raw_label": "=",
                "row_type": "SEPARATOR",
                "bbox": (170, 339, 420, 343),
                "digit_count": 0,
                "contains_operator": False,
                "contains_carry_context": False,
                "contains_borrow_context": False,
                "is_ocr_eligible": False,
                "exclusion_reason": "SEPARATOR_HORIZONTAL_RULE_NON_TEXTUAL",
            },
            {
                "row_index": 3,
                "raw_label": "34",
                "row_type": "RESULT",
                "bbox": (263, 384, 376, 437),
                "digit_count": 2,
                "contains_operator": False,
                "contains_carry_context": False,
                "contains_borrow_context": True,
                "is_ocr_eligible": True,
            },
        ],
    },
]


def build_dataset():
    print("=" * 70)
    print("BUILDING ARITHMETIC OCR LINE DATASET (OCR.DATA.1)")
    print("=" * 70)

    manifest_records = []
    exclusions_records = []
    seen_crop_hashes = {}  # hash -> sample_id

    total_derived_rows = 0
    total_valid_samples = 0
    duplicates_excluded = 0
    ineligible_excluded = 0

    # 1. Process all source images
    for src in SOURCES:
        src_id = src["source_image_id"]
        img_p = src["image_path"]
        assert img_p.exists(), f"Source image missing: {img_p}"
        src_sha = sha256_file(img_p)

        im = Image.open(img_p)
        W, H = im.size

        for r in src["rows"]:
            total_derived_rows += 1
            r_idx = r["row_index"]
            raw_label = r["raw_label"]
            r_type = r["row_type"]
            is_eligible = r["is_ocr_eligible"]
            x1, y1, x2, y2 = r["bbox"]

            # Proportional padding calculation
            bh = y2 - y1
            pad_y = int(round(bh * 0.15))
            pad_x = int(round(bh * 0.20))
            cx1 = max(0, x1 - pad_x)
            cy1 = max(0, y1 - pad_y)
            cx2 = min(W, x2 + pad_x)
            cy2 = min(H, y2 + pad_y)

            # Crop image (natural unscaled resolution)
            crop_im = im.crop((cx1, cy1, cx2, cy2))
            crop_w, crop_h = crop_im.size

            # Encode bytes to memory to compute exact content hash
            import io
            buf = io.BytesIO()
            crop_im.save(buf, format="PNG")
            crop_bytes = buf.getvalue()
            crop_hash = sha256_bytes(crop_bytes)

            # Determine sample_id
            hash_fragment = crop_hash[:8]
            sample_id = f"{src_id}_row_{r_idx:02d}_{raw_label.replace('+', 'plus').replace('-', 'minus').replace('=', 'eq')}_{hash_fragment}"

            # Check eligibility
            if not is_eligible:
                ineligible_excluded += 1
                exclusions_records.append({
                    "sample_id": sample_id,
                    "source_image_id": src_id,
                    "row_index": r_idx,
                    "raw_label": raw_label,
                    "row_type": r_type,
                    "reason": r.get("exclusion_reason", "INELIGIBLE_ROW_TYPE"),
                    "crop_bbox": [cx1, cy1, cx2, cy2],
                    "crop_dimensions": [crop_w, crop_h],
                })
                print(f"  [EXCLUDED - {r_type}] {sample_id} ({raw_label}) - {r.get('exclusion_reason')}")
                continue

            # Check deduplication
            if crop_hash in seen_crop_hashes:
                duplicates_excluded += 1
                orig_sample_id = seen_crop_hashes[crop_hash]
                exclusions_records.append({
                    "sample_id": sample_id,
                    "source_image_id": src_id,
                    "row_index": r_idx,
                    "raw_label": raw_label,
                    "row_type": r_type,
                    "reason": f"DUPLICATE_CROP_EXACT_BYTES (identical to {orig_sample_id})",
                    "duplicate_of": orig_sample_id,
                    "crop_hash": crop_hash,
                    "crop_bbox": [cx1, cy1, cx2, cy2],
                })
                print(f"  [EXCLUDED - DUPLICATE] {sample_id} ({raw_label}) duplicate of {orig_sample_id}")
                continue

            # Valid unique sample
            seen_crop_hashes[crop_hash] = sample_id
            total_valid_samples += 1

            # Save crop to dataset directory
            crop_filename = f"{sample_id}.png"
            crop_file_path = CROPS_DIR / crop_filename
            with open(crop_file_path, "wb") as f:
                f.write(crop_bytes)

            record = {
                "sample_id": sample_id,
                "crop_path": str(crop_file_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                "crop_filename": crop_filename,
                "raw_label": raw_label,
                "normalized_label": raw_label,
                "source_image_id": src_id,
                "source_image_hash": src_sha,
                "crop_hash": crop_hash,
                "row_index": r_idx,
                "row_type": r_type,
                "operation": src["operation"],
                "digit_count": r["digit_count"],
                "contains_operator": r["contains_operator"],
                "contains_carry_context": r["contains_carry_context"],
                "contains_borrow_context": r["contains_borrow_context"],
                "crop_dimensions": {"width": crop_w, "height": crop_h},
                "split": src["target_split"],
                "annotation_source": src["annotation_source"],
                "is_synthetic": src["is_synthetic"],
                "writer_id": src["writer_id"],
                "pii_status": src["pii_status"],
                "seen_by_yolo": src["seen_by_yolo"],
            }
            manifest_records.append(record)
            print(f"  [SAVED - {record['split'].upper()}] {sample_id} -> '{raw_label}' ({crop_w}x{crop_h})")

    # 2. Write manifest files (JSONL and CSV)
    manifest_jsonl_path = HANDOFF_DIR / "dataset_manifest.jsonl"
    with open(manifest_jsonl_path, "w", encoding="utf-8") as f:
        for rec in manifest_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    manifest_csv_path = HANDOFF_DIR / "dataset_manifest.csv"
    if manifest_records:
        keys = list(manifest_records[0].keys())
        with open(manifest_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(keys)
            for rec in manifest_records:
                row = []
                for k in keys:
                    v = rec[k]
                    if isinstance(v, (dict, list)):
                        row.append(json.dumps(v))
                    else:
                        row.append(v)
                writer.writerow(row)

    # 3. Write split files
    splits_summary = {}
    for split_name in ["train", "val", "test"]:
        split_records = [r for r in manifest_records if r["split"] == split_name]
        split_file = HANDOFF_DIR / "splits" / f"{split_name}.txt"
        with open(split_file, "w", encoding="utf-8") as f:
            for r in split_records:
                f.write(f"{r['crop_path']}\t{r['raw_label']}\n")
        splits_summary[split_name] = len(split_records)

    # 4. Generate Exclusions Report
    exclusions_path = HANDOFF_DIR / "reports" / "exclusions.json"
    with open(exclusions_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_derived_rows": total_derived_rows,
            "total_valid_line_samples": total_valid_samples,
            "duplicates_excluded_count": duplicates_excluded,
            "ineligible_rows_excluded_count": ineligible_excluded,
            "exclusions": exclusions_records,
        }, f, indent=2)

    # 5. Coverage Analysis
    digits_counter = {str(d): 0 for d in range(10)}
    operators_counter = {"+": 0, "-": 0, "=": 0}
    lengths_counter = {f"{i}_digits": 0 for i in range(1, 7)}
    row_types_counter = {}
    ops_counter = {}
    carry_count = 0
    borrow_count = 0

    for r in manifest_records:
        lbl = r["raw_label"]
        rt = r["row_type"]
        row_types_counter[rt] = row_types_counter.get(rt, 0) + 1
        op = r["operation"]
        ops_counter[op] = ops_counter.get(op, 0) + 1

        if r["contains_carry_context"]:
            carry_count += 1
        if r["contains_borrow_context"]:
            borrow_count += 1

        d_cnt = r["digit_count"]
        if 1 <= d_cnt <= 6:
            lengths_counter[f"{d_cnt}_digits"] += 1

        for ch in lbl:
            if ch in digits_counter:
                digits_counter[ch] += 1
            elif ch in operators_counter:
                operators_counter[ch] += 1

    coverage_summary = {
        "dataset_name": "arithmetic_ocr_line_v1",
        "total_valid_samples": total_valid_samples,
        "splits": splits_summary,
        "classification": "PARTIAL_DATASET",
        "dataset_size_assessment": "DATASET_TOO_SMALL",
        "writer_disjoint": "UNKNOWN",
        "seen_by_yolo_evaluation_contamination": "ALL_SAMPLES_SEEN_BY_YOLO",
        "digits_distribution": digits_counter,
        "operators_distribution": operators_counter,
        "operand_lengths_distribution": lengths_counter,
        "operations_distribution": ops_counter,
        "row_types_distribution": row_types_counter,
        "carry_context_samples": carry_count,
        "borrow_context_samples": borrow_count,
        "resolution_info": {
            "source_resolutions": ["1200x896", "640x640"],
            "crop_min_dim": min([r["crop_dimensions"]["height"] for r in manifest_records]) if manifest_records else 0,
            "crop_max_dim": max([r["crop_dimensions"]["width"] for r in manifest_records]) if manifest_records else 0,
        },
    }

    coverage_path = HANDOFF_DIR / "reports" / "coverage_summary.json"
    with open(coverage_path, "w", encoding="utf-8") as f:
        json.dump(coverage_summary, f, indent=2)

    # 6. Generate Visual Review Grid
    generate_review_grid(manifest_records)

    # 7. Generate Recommended Fine-Tuning Config
    generate_training_config()

    # 8. Generate Handoff README
    generate_handoff_readme(coverage_summary, splits_summary)

    print("\n" + "=" * 70)
    print("DATASET BUILD COMPLETED SUCCESSFULLY")
    print(f"Total derived rows: {total_derived_rows}")
    print(f"Valid line OCR samples: {total_valid_samples}")
    print(f"Duplicates excluded: {duplicates_excluded}")
    print(f"Ineligible excluded: {ineligible_excluded}")
    print(f"Splits: Train={splits_summary['train']}, Val={splits_summary['val']}, Test={splits_summary['test']}")
    print(f"Classification: PARTIAL_DATASET (DATASET_TOO_SMALL)")
    print("=" * 70)


def generate_review_grid(records: List[Dict[str, Any]]):
    """Generates a visual contact sheet with sample_id and raw_label overlaid."""
    if not records:
        return

    n_samples = len(records)
    cols = 3
    rows = (n_samples + cols - 1) // cols

    cell_w = 400
    cell_h = 160
    grid_w = cols * cell_w + 40
    grid_h = rows * cell_h + 100

    grid_img = Image.new("RGB", (grid_w, grid_h), color=(245, 247, 250))
    draw = ImageDraw.Draw(grid_img)

    # Header
    draw.text((20, 20), "MathVision Kids - Arithmetic OCR Line Dataset v1 (Contact Sheet)", fill=(20, 30, 50))
    draw.text((20, 45), f"Total Verified Line Crops: {n_samples} | Natural Aspect Ratio | No Artificial Resize", fill=(100, 110, 120))

    for idx, r in enumerate(records):
        col_idx = idx % cols
        row_idx = idx // cols

        x_offset = 20 + col_idx * cell_w
        y_offset = 80 + row_idx * cell_h

        card_rect = [x_offset, y_offset, x_offset + cell_w - 15, y_offset + cell_h - 15]
        draw.rectangle(card_rect, fill=(255, 255, 255), outline=(210, 220, 230), width=1)

        crop_p = WORKSPACE_ROOT / r["crop_path"]
        if crop_p.exists():
            c_im = Image.open(crop_p).convert("RGB")
            max_cw = cell_w - 35
            max_ch = cell_h - 55
            c_im.thumbnail((max_cw, max_ch), Image.Resampling.LANCZOS)
            paste_x = x_offset + 10 + (max_cw - c_im.width) // 2
            paste_y = y_offset + 40 + (max_ch - c_im.height) // 2
            grid_img.paste(c_im, (paste_x, paste_y))

        lbl_text = f"Label: \"{r['raw_label']}\" | Type: {r['row_type']} | Split: {r['split'].upper()}"
        draw.text((x_offset + 10, y_offset + 8), lbl_text, fill=(30, 40, 60))
        sub_text = f"ID: {r['sample_id'][:28]}..."
        draw.text((x_offset + 10, y_offset + 24), sub_text, fill=(120, 130, 140))

    out_evidence = EVIDENCE_DIR / "review_grid_arithmetic_lines.png"
    out_handoff = HANDOFF_DIR / "samples" / "review_grid_arithmetic_lines.png"
    grid_img.save(out_evidence)
    grid_img.save(out_handoff)
    print(f"Review grid saved to:\n  {out_evidence}\n  {out_handoff}")


def generate_training_config():
    """Generates recommended training config yaml for AI teammate."""
    cfg = """# MathVision Kids — Recommended CRNN Fine-Tuning Configuration
# Task: Arithmetic OCR Line Fine-Tuning v1
# Status: PREPARATION ONLY — NO TRAINING PERFORMED IN DATA ENGINEERING TASK

model:
  architecture: "CRNN"
  backbone: "CNN (VGG-style / ResNet feature extractor)"
  recurrent: "Bidirectional LSTM (2 layers, hidden_size=256)"
  head: "CTC Loss Linear Projection"
  initialization: "services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth"
  checkpoint_sha256: "a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941"
  vocab_path: "services/ai-service/models/ocr/crnn_vi_handwriting_v1/vocab.json"
  vocab_size: 320

preprocessing:
  channels: 3  # RGB
  target_height: 64
  target_width: 1024
  interpolation: "BILINEAR"
  normalization:
    mean: [0.485, 0.456, 0.406]
    std: [0.229, 0.224, 0.225]
  pad_to_width: true
  preserve_aspect_ratio: true

dataset:
  manifest_path: "ai-training/handoff/outgoing/arithmetic_ocr_line_v1/dataset_manifest.jsonl"
  crops_dir: "ai-training/datasets/arithmetic_ocr_line_v1/crops/"
  splits_dir: "ai-training/handoff/outgoing/arithmetic_ocr_line_v1/splits/"
  train_split: "train.txt"
  val_split: "val.txt"
  test_split: "test.txt"

training_hyperparameters:
  optimizer: "AdamW"
  learning_rate: 0.00005  # Conservative fine-tuning rate
  weight_decay: 0.0001
  batch_size: 8
  epochs: 50
  early_stopping:
    patience: 10
    metric: "val_exact_match"
    mode: "max"
  lr_scheduler:
    type: "CosineAnnealingLR"
    T_max: 50
    eta_min: 0.000001

domain_experiments:
  experiment_a:
    name: "Full CRNN Fine-Tuning"
    description: "Train all layers on arithmetic line dataset."
  experiment_b:
    name: "Frozen Backbone Transfer"
    description: "Freeze CNN feature extractor for first 15 epochs; tune BiLSTM and linear CTC head only."
  experiment_c:
    name: "Rehearsal Mixed Fine-Tuning"
    description: "Mix 80% arithmetic lines + 20% general Vietnamese handwriting lines to prevent catastrophic forgetting."

evaluation_metrics_required:
  - "Character Error Rate (CER)"
  - "Exact Match Rate (Sequence Accuracy)"
  - "Digit Accuracy (0-9)"
  - "Operator Accuracy (+, -)"
  - "Sequence Length Stratified Accuracy (1-digit to 6-digit)"
"""
    cfg_path = HANDOFF_DIR / "config" / "recommended_training_config.yaml"
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(cfg)
    print(f"Recommended training config saved to {cfg_path}")


def generate_handoff_readme(coverage: Dict[str, Any], splits: Dict[str, int]):
    """Generates outgoing handoff README.md."""
    content = f"""# MathVision Kids — Arithmetic Line OCR Dataset & Training Handoff (v1)

**Date**: 2026-09-11  
**Dataset Name**: `arithmetic_ocr_line_v1`  
**Classification**: **`{coverage['classification']}`**  
**Evaluation Readiness**: **`{coverage['dataset_size_assessment']}`**  
**Training Status**: **NO TRAINING PERFORMED** (Handoff package prepared for AI teammate)

---

## 1. Directory Structure

```
ai-training/handoff/outgoing/arithmetic_ocr_line_v1/
├── README.md                                 # This handoff documentation
├── dataset_manifest.jsonl                    # Authoritative metadata manifest (JSON Lines)
├── dataset_manifest.csv                      # Tabular CSV export of manifest
├── config/
│   └── recommended_training_config.yaml      # Recommended hyperparameter & architecture configuration
├── splits/
│   ├── train.txt                             # Training samples ({splits['train']} samples)
│   ├── val.txt                               # Validation samples ({splits['val']} samples)
│   └── test.txt                              # Test samples ({splits['test']} samples)
├── reports/
│   ├── coverage_summary.json                 # Class, length, and operation distributions
│   └── exclusions.json                       # Full audit trail of excluded/deduplicated rows
└── samples/
    └── review_grid_arithmetic_lines.png      # Contact sheet of derived line crops
```

## 2. Dataset Overview

- **Total Valid Line OCR Samples**: {coverage['total_valid_samples']}
- **Splits**:
  - Train: {splits['train']} samples
  - Validation: {splits['val']} samples
  - Test: {splits['test']} samples
- **Source Images**: 4 local synthetic arithmetic worksheets (`sample_input_synthetic.jpg`, `synthetic_addition.jpg`, `synthetic_addition_carry.jpg`, `synthetic_subtraction.jpg`).
- **Real Student Data**: 0 images locally available in this repository.
- **YOLO Training Overlap**: `seen_by_yolo = YES` for all samples. None of these samples may serve as held-out full-pipeline benchmark evaluation.
- **Writer Disjoint Status**: `UNKNOWN` (synthetic programmatic generation).

## 3. Important Policies

1. **Carry-Only Rows**: Excluded from line-CRNN text fine-tuning per Section 7 (logged in `reports/exclusions.json`).
2. **Separator Rows**: Layout separator bars (`=`) are excluded from text training per Section 8.
3. **No Resizing**: Stored crops in `ai-training/datasets/arithmetic_ocr_line_v1/crops/` are natural aspect ratio PNGs with proportional padding. Preprocessing (Resize 64x1024, RGB, ImageNet normalization) must be performed by the training dataloader.

## 4. Recommended Experiments for AI Teammate

- **Experiment A**: Full CRNN fine-tuning on arithmetic line crops with lower learning rate (`5e-5`).
- **Experiment B**: Freeze CNN backbone initially, train BiLSTM and CTC linear head.
- **Experiment C**: Rehearsal fine-tuning mixing arithmetic crops with general Vietnamese handwriting lines to prevent catastrophic forgetting.
"""
    readme_path = HANDOFF_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Handoff README saved to {readme_path}")


if __name__ == "__main__":
    build_dataset()
