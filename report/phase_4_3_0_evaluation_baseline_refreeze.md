# Phase 4.3.0 Closeout Report: Evaluation Baseline Refreeze & Gold Dataset Request Correction

**Project**: MathVision Kids  
**Phase**: 4.3.0 — Evaluation Baseline Refreeze & Gold Dataset Request Correction  
**Mode**: Documentation & Configuration Audit Only (No Training, No Fine-Tuning, No Threshold Tuning)  
**Date**: 2026-09-08  
**Status**: READY_FOR_REVIEW  

---

## 1. Runtime Version Audit

An audit was performed across all three dependency definitions in `services/ai-service`:

| Component | Target Artifact | Version Found | Status |
|---|---|---|---|
| `requirements.txt` | `services/ai-service/requirements.txt` | `ultralytics==8.4.143` | Pinned Frozen |
| `requirements-lock.txt` | `services/ai-service/requirements-lock.txt` | `ultralytics==8.4.143` | Locked |
| Active `.venv` | Python 3.12.13 runtime environment | `8.4.143` | Verified Installed |

---

## 2. Ultralytics Resolution

- **Discrepancy Cause**: The Phase 4.3 evaluation report had erroneously stated `ultralytics==8.3.28` (a typographical error carried over from legacy AI team training notes).
- **Physical Environment State**: The active Python virtual environment never drifted; it has consistently been `8.4.143` as established in Phase 4.2.1.
- **Resolution**: Corrected the documentation in `report/phase_4_3_gold_model_evaluation.md` to accurately cite `ultralytics==8.4.143`. No virtual environment re-installation or package modification was required.

---

## 3. Threshold Audit

An audit was conducted on the inference detection and NMS thresholds across source code, runtime manifest, and documentation:

| Parameter | Source Code (`yolo_adapter.py`) | Phase 4.2 Integration Baseline | Phase 4.3 Initial Report |
|---|---|---|---|
| **Confidence Threshold** | `0.25` | `0.25` | `0.25` |
| **NMS IoU Threshold** | `0.50` | `0.50` | `0.45` |
| **Ambiguity Threshold** | `0.50` | `0.50` | `0.50` |
| **Row Tolerance Factor** | `0.55` | `0.55` | `0.55` |

---

## 4. NMS Resolution

- `SOURCE_VALUE`: `0.50`
- `PHASE_4_2_BASELINE`: `0.50`
- `PHASE_4_3_REPORTED_VALUE`: `0.45`
- **Resolution**: The source code in `services/ai-service/app/recognition/yolo_adapter.py` remained unchanged at `0.50`. The initial Phase 4.3 report contained an errant manual entry of `0.45`. The report has been corrected to `0.50` to match the frozen source code. Zero threshold tuning was performed.

---

## 5. Frozen Evaluation Config

A machine-readable canonical configuration has been established at:
`services/ai-service/evaluation/evaluation_config_v1.json`

Key frozen parameters recorded:
- **Python**: `3.12.13`
- **PyTorch**: `2.14.0+cpu`
- **Ultralytics**: `8.4.143`
- **Model Name**: `MathVision-Kids-Detection` (YOLOv8n v1.0.0)
- **Model Checksum**: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- **Manifest Checksum**: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`
- **Input Resolution**: 640x640, 3 channels, `RESIZE_ONLY`
- **Detection Confidence**: `0.25`
- **NMS IoU**: `0.50`
- **Ambiguity**: `0.50`
- **High-Confidence**: `0.85`
- **Parser**: `StructuredParser v1.0.0`
- **Validators**: `VerticalAdditionValidator v1.0.0`, `VerticalSubtractionValidator v1.0.0`

---

## 6. Latency Wording Correction

- The previous measurement of `0.0854s` warm inference on local CPU was derived from 10 sample passes on a single synthetic image.
- Per governance guidelines, this has been re-classified as:
  `LOCAL_INFERENCE_SMOKE_TIMING`
- In `report/phase_4_3_gold_model_evaluation.md`, the formal Proposal p95 latency target (<= 12.0s) has been updated from `PASS` to **`NOT_EVALUATED`**.
- Formal p95 latency will only be evaluated when a full, credible gold evaluation workload is executed.

---

## 7. Proposal Gold Target Correction

`report/phase_4_3_ai_team_feedback.md` and evaluation requirements have been aligned to Proposal specifications:
- **W5 Milestone Target**: `>= 100 verified pilot images`
- **W11 Milestone Target**: `>= 500 de-identified gold images` (Project Target: `700 images`, `>= 20% double-annotated`)

---

## 8. 1–6 Digit Scope Correction

- The evaluation scope is **not** restricted to 2-digit calculations.
- Canonical MVP scope covers:
  - Natural numbers vertical arithmetic.
  - Operations: `VERTICAL_ADDITION` and `VERTICAL_SUBTRACTION`.
  - Two operands, one exercise per image.
  - **1 to 6 digits per operand/result**.
  - Features: with carry, without carry, with borrow, without borrow.
- The AI team is requested to disclose digit-length distribution (counts for 1-digit, 2-digit, 3-digit, 4-digit, 5-digit, 6-digit subsets) in the manifest to demonstrate domain coverage.

---

## 9. Gold Annotation Contract

For each image in the independent gold evaluation set, the manifest must specify:
1. `image_id`: Unique de-identified string.
2. `filepath`: Relative path to image.
3. `operation`: `VERTICAL_ADDITION` or `VERTICAL_SUBTRACTION`.
4. `is_supported`: Boolean (true for 1–6 digit vertical arithmetic).
5. `ground_truth_expression`: `operand1`, `operand2`, `operator`, `student_result`.
6. `is_mathematically_correct`: Boolean.
7. `earliest_error`: `has_error`, `column_index` (0-indexed from right), `error_type` (`COMPUTATION_ERROR`, `CARRY_BORROW_ERROR`, `PLACE_VALUE_ALIGNMENT_ERROR`).
8. `tokens`: Bounding boxes `[x_center, y_center, width, height]` (normalized) with class ID (0-13) where available.
9. `annotation_provenance`: Origin collection metadata.
10. `double_annotated`: Boolean.
11. **Adjudication Metadata** (only for double-annotated / disputed samples):
    - `primary_annotation`
    - `secondary_annotation`
    - `adjudicated_result`
    - `adjudicator_id`
    *(No fabricated adjudication records for undisputed samples).*

---

## 10. Evaluation Harness Gate

The harness `services/ai-service/evaluation/run_evaluation.py` has been updated with pre-execution validation gates:
- Rejects missing manifests (`MANIFEST_NOT_SPECIFIED` / `MANIFEST_NOT_FOUND`).
- Rejects empty datasets (`EMPTY_DATASET`).
- Rejects invalid schema formats (`INVALID_SCHEMA_ENTRY`).
- Rejects training / validation leakage (`DATA_LEAKAGE_DETECTED` for `sample_input_synthetic.jpg` or known training samples).
- When run without a valid gold test manifest, it exits cleanly with status **`BLOCKED_DATASET`** and persists structured gate reasons in `report/evidence/phase_4_3/evaluation_results.json`.

---

## 11. Python Regression

Command: `python -m pytest tests/`
- Runtime: Python 3.12.13, pytest 9.1.1, Windows x86_64
- **Total Tests**: 92
- **Passed**: 92
- **Failed**: 0
- **Skipped**: 0
- **Result**: **100% PASS**

---

## 12. Files Modified

1. `services/ai-service/evaluation/evaluation_config_v1.json` [NEW] — Machine-readable frozen evaluation config.
2. `services/ai-service/evaluation/run_evaluation.py` [MODIFY] — Added gate validation, leakage guard, and formal latency status.
3. `report/phase_4_3_gold_model_evaluation.md` [MODIFY] — Corrected ultralytics version (8.4.143), NMS threshold (0.50), latency classification, and quality gate table.
4. `report/phase_4_3_ai_team_feedback.md` [MODIFY] — Corrected W5/W11 targets, 1–6 digit domain scope, and adjudication contract.
5. `report/phase_4_3_0_evaluation_baseline_refreeze.md` [NEW] — Phase 4.3.0 closeout report.

---

## 13. Student Modified

- **Student Mobile / Web Code**: **0 files modified (NO)**

---

## 14. Teacher Modified

- **Teacher Web Code**: **0 files modified (NO)**

---

## 15. AI Training Performed

- **AI Training Executed**: **NO**

---

## 16. Phase 4.3 Status

- **Status**: **BLOCKED_DATASET**
- Integration is verified and stable, but formal Proposal metric gating remains blocked until the independent gold test dataset is delivered.

---

## 17. Recommended Next Step

Await delivery of the independent gold test dataset package (`>= 500 images`, target 700, `>= 20% double-annotated`, 1–6 digit vertical arithmetic) from the AI/ML team into `ai-training/`.
