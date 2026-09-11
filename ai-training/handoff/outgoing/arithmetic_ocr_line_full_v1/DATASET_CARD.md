# DATASET CARD: Arithmetic Line OCR Dataset (v1.0.0)

**Version**: 1.0.0  
**Date**: 2026-09-11  
**Task**: OCR.DATA.EXPORT.1 — External Arithmetic OCR Line Dataset Export for CRNN Fine-Tuning  
**Provenance**: MathVision Kids Engineering Pipeline  

---

## 1. Dataset Summary

`arithmetic_ocr_line_full_v1` is an arithmetic-specific line OCR dataset designed for fine-tuning the verified Vietnamese handwriting CRNN (`best_cer.pth`). It contains isolated arithmetic expression row crops directly excised from vertical addition and subtraction problems.

## 2. Dataset Structure

- **Total Exported Samples**: 9 valid line crops
- **Splits**:
  - Train: 6 samples (`sample_input_synthetic`, `synthetic_addition`)
  - Validation: 3 samples (`synthetic_subtraction`)
  - Test: 0 samples (`DATASET_TOO_SMALL` for held-out partition)
- **Image Format**: Lossless PNG (RGB), natural unscaled dimensions (no 64x1024 resizing applied during export).
- **Label Format**: Exact textual transcriptions without spaces (e.g. `38`, `+47`, `85`, `45`, `+27`, `72`, `52`, `-18`, `34`).

## 3. Data Splits & Leakage Prevention

- **Image Disjoint**: 100% of samples from the same source image reside within a single partition.
- **Cross-Split Leakage**: 0% (asserted by automated integrity test).
- **Writer Disjoint Status**: `UNKNOWN` (synthetic programmatic generation).
- **YOLO Training Overlap**: `seen_by_yolo_training = YES` (100% of samples were seen during YOLO development/integration). These samples may be used for CRNN fine-tuning but CANNOT serve as an independent held-out full-pipeline benchmark evaluation.

## 4. Class & Operation Distribution

- **Digits (18 total)**: `1` (1), `2` (3), `3` (2), `4` (3), `5` (3), `7` (3), `8` (3). Digits `0`, `6`, `9` are unrepresented.
- **Operators**: `+` (2), `-` (1). Separator bars (`=`) are excluded from text training.
- **Operations**: Vertical Addition (6 rows), Vertical Subtraction (3 rows).
- **Context**: Carry Context (6 rows), Borrow Context (3 rows).

## 5. Exclusions Policy

- **Separator Rows**: 4 horizontal rule rows excluded (non-textual layout dividers).
- **Carry-Only Rows**: 1 carry marker row excluded per Section 7 (auxiliary annotation, not a line transcript).
- **Duplicates**: 3 exact byte-duplicate crops excluded (detailed in `reports/duplicate_groups.json`).

## 6. Privacy & De-Identification

- Contains ONLY de-identified programmatic synthetic crops.
- Zero student names, school names, student codes, or facial images exist.
