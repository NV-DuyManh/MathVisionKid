# Arithmetic OCR Line Full Handoff Package (v1)

**Task**: OCR.DATA.EXPORT.1  
**Dataset Name**: `arithmetic_ocr_line_full_v1`  
**Classification**: **`BLOCKED_SOURCE_DATA`** (External 2,001-image dataset `combined_dataset_fixed_v1.0` at `D:\nhom6\...` not present on this host; local 9-sample synthetic export packaged)  
**Evaluation Readiness**: **`DATASET_TOO_SMALL`**  

---

## 1. Directory Structure

```
arithmetic_ocr_line_full_v1/
├── README.md                                 # Package overview
├── DATASET_CARD.md                           # Formal dataset documentation
├── dataset_manifest.jsonl                    # Authoritative manifest (relative paths)
├── dataset_manifest.csv                      # CSV export of manifest
├── checksums.sha256                          # Cryptographic checksums of all members
├── crops/                                    # Natural unscaled PNG line crops
│   ├── sample_input_synthetic_row_00_38_c5b62178.png
│   ├── sample_input_synthetic_row_01_plus47_803b0402.png
│   ├── sample_input_synthetic_row_03_85_302aaaf1.png
│   ├── synthetic_addition_row_00_45_1c104bab.png
│   ├── synthetic_addition_row_01_plus27_92fe5a05.png
│   ├── synthetic_addition_row_03_72_2f241f26.png
│   ├── synthetic_subtraction_row_00_52_503481c7.png
│   ├── synthetic_subtraction_row_01_minus18_b92a5657.png
│   └── synthetic_subtraction_row_03_34_aa54bab9.png
├── splits/
│   ├── train.txt                             # 6 samples
│   ├── val.txt                               # 3 samples
│   └── test.txt                              # 0 samples
├── config/
│   └── recommended_finetune_config.yaml      # CRNN fine-tuning configuration (NO padding)
├── reports/
│   ├── coverage_summary.json                 # Statistical distributions
│   ├── exclusions.json                       # Excluded rows & reasons
│   ├── duplicate_groups.json                 # Deduplication groups
│   ├── privacy_review.json                   # PII safety audit
│   └── source_inventory.json                 # Source image metadata
└── samples/
    └── review_grid_arithmetic_lines.png      # 9-sample contact sheet
```

## 2. Baseline Preprocessing Contract

```
PIL Image -> RGB -> Resize((64, 1024)) -> ToTensor() -> ImageNet Normalization
(NO pad-to-width in baseline)
```
