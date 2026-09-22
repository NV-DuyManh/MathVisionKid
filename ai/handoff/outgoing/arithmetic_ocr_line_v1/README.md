# MathVision Kids — Arithmetic Line OCR Dataset & Training Handoff (v1)

**Date**: 2026-09-11  
**Dataset Name**: `arithmetic_ocr_line_v1`  
**Classification**: **`PARTIAL_DATASET`**  
**Evaluation Readiness**: **`DATASET_TOO_SMALL`**  
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
│   ├── train.txt                             # Training samples (6 samples)
│   ├── val.txt                               # Validation samples (3 samples)
│   └── test.txt                              # Test samples (0 samples)
├── reports/
│   ├── coverage_summary.json                 # Class, length, and operation distributions
│   └── exclusions.json                       # Full audit trail of excluded/deduplicated rows
└── samples/
    └── review_grid_arithmetic_lines.png      # Contact sheet of derived line crops
```

## 2. Dataset Overview

- **Total Valid Line OCR Samples**: 9
- **Splits**:
  - Train: 6 samples
  - Validation: 3 samples
  - Test: 0 samples
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
