# MathVision Kids
## Phase 4.2 — Trained Model Handoff Acceptance, YOLO Runtime Integration & Real-Model E2E

**Date:** September 8, 2026  
**Environment:** Windows 11 (Primary Developer Environment)  
**Status:** READY_FOR_REVIEW  
**Runtime Mode:** READY_IN_MODEL_MODE  
**Integration Status:** INTEGRATED  

---

### 1. Executive Summary

Phase 4.2 successfully ingested, validated, normalized, and integrated the trained machine learning model delivered by the AI/ML training team (`model_handoff.zip`). The primary MVP model, **MathVision-Kids-Detection (YOLOv8n)**, was integrated into the production AI runtime (`services/ai-service`) without retraining, without modifying frozen frontends (Student Mobile / Teacher Web), and without altering Spring Boot business logic.

Key achievements:
1. **Immutable Evidence Preservation**: The original `model_handoff.zip` (28,381,515 bytes) was preserved immutably at `ai-training/incoming/model_handoff.zip` and unpacked to `ai-training/incoming/extracted/model_handoff/` without tampering.
2. **Cryptographic Checksum Verification**: Both the YOLOv8n `.pt` artifact and CRNN `.pth` artifact were verified independently via SHA-256 with 100% exact matches against expected values.
3. **Primary Model & CRNN Status**: YOLOv8n was accepted as the primary MVP detection/recognition engine. CRNN was designated as `EXPERIMENTAL_AVAILABLE` due to documented dataset and CTC vocabulary limitations.
4. **Contract Normalization**: Multi-model handoff manifest was normalized to runtime-consumable `services/ai-service/models/model_manifest.json` while maintaining complete provenance tracking.
5. **Explicit Label Adapter & Borrow Handling**: 14-class detection model was mapped to canonical tokens (`0..9` -> digit, `+`/`-` -> operator, `=` -> separator, `c1` -> carry). `EXPLICIT_BORROW_MARK_RECOGNITION` was explicitly declared as `NOT_SUPPORTED_BY_MODEL`, with subtraction borrow handled mathematically by the frozen `VerticalSubtractionValidator`.
6. **Frozen Runtime Authority**: The handoff's `parser_engine.py` was treated strictly as reference/comparison only. The existing frozen `StructuredParser` and deterministic Python validators remain the sole mathematical correctness authority.
7. **End-to-End Real Inference & MinIO Wiring**: Images were loaded via private MinIO (`minio://mathvision/...`) through `ImageSourceResolver`, run through real YOLOv8n inference, mapped to canonical tokens, parsed, validated, and evaluated by Student and Teacher policies.
8. **Regression & Safety**: All 92 Python tests pass (including 10 fixture regression tests and new YOLO/MinIO/E2E tests). All 49 Spring Boot tests pass. Spring Boot build succeeds.

---

### 2. Original Handoff Package

The AI/ML team delivered the model package as a ZIP archive:
- **Original Location**: `C:\Users\Admin\Downloads\model_handoff.zip`
- **Archived In-Repo Location**: `ai-training/incoming/model_handoff.zip`
- **Extracted Location**: `ai-training/incoming/extracted/model_handoff/`
- **Archive Size**: 28,381,515 bytes
- **Delivery Date**: September 8, 2026

The original ZIP file is treated as immutable evidence and has not been modified.

---

### 3. Package Integrity

All 9 expected core files and artifacts were verified present in the package:

| Expected File | Size (Bytes) | Integrity Status |
|---------------|--------------|------------------|
| `artifacts/yolov8n_mathvision_det_v1.pt` | 6,257,636 | PASS (Present) |
| `artifacts/crnn_mathvision_ocr_v1.pth` | 23,771,549 | PASS (Present) |
| `model_manifest.json` | 4,204 | PASS (Present, valid JSON) |
| `MODEL_CARD.md` | 7,541 | PASS (Present, valid Markdown) |
| `DATASET_CARD.md` | 6,318 | PASS (Present, valid Markdown) |
| `label_map_detection.json` | 1,998 | PASS (Present, valid JSON) |
| `vocab_ocr_v1.json` | 3,872 | PASS (Present, valid JSON) |
| `sample_io/sample_input_synthetic.jpg` | 61,544 | PASS (Present, 1200x896 JPEG) |
| `sample_io/expected_output.json` | 4,395 | PASS (Present, valid JSON) |
| `parser_engine.py` | 20,107 | PASS (Present, reference parser) |
| `verify_export.py` | 7,470 | PASS (Present, helper script) |

---

### 4. YOLO Checksum

SHA-256 was calculated independently on `artifacts/yolov8n_mathvision_det_v1.pt`:
- **Expected SHA-256**: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- **Computed SHA-256**: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`
- **Result**: **MATCH (100% Exact Match)**

---

### 5. CRNN Checksum

SHA-256 was calculated independently on `artifacts/crnn_mathvision_ocr_v1.pth`:
- **Expected SHA-256**: `758E4991F0746AD5CFAB0E927DB1705D17C82E7084144B3D7819C4BE9AC8A860`
- **Computed SHA-256**: `758e4991f0746ad5cfab0e927db1705d17c82e7084144b3d7819c4be9ac8a860`
- **Result**: **MATCH (100% Exact Match)**

---

### 6. Primary Model Decision

**Primary Model**: `MathVision-Kids-Detection` (YOLOv8n)  
- **Role**: Object detection of handwritten mathematical tokens (digits 0–9, operators `+` and `-`, separator `=`, carry marker `c1`), bounding-box extraction, and token confidence scoring.  
- **Architecture**: CSPDarknet backbone, YOLOv8 detection head, 14 classes, ~3.2M parameters.  
- **Rationale**: The YOLOv8n model provides simultaneous token classification and 2D spatial bounding box localization necessary for vertical layout reconstruction (`StructuredParser`).

---

### 7. Experimental CRNN Decision

**CRNN Model**: `MathVision-Kids-OCR` (CRNN CNN + BiLSTM + CTC)  
- **Status**: `EXPERIMENTAL_AVAILABLE` (NOT primary MVP path)  
- **Rationale**: The delivered `MODEL_CARD.md` and `DATASET_CARD.md` explicitly disclose:
  - No reproducible final CER/WER evaluation on children's handwriting.
  - Trained on general Vietnamese handwriting (2,000 line-level samples), not vertical child arithmetic worksheets.
  - Timestep and CTC vocabulary limitations for fragmented handwritten digits.  
- **Decision**: CRNN artifact is cataloged and verified in `services/ai-service/models/` but not forced into the primary runtime pipeline.

---

### 8. Original Manifest Audit

The delivered `model_manifest.json` is a multi-model envelope:
```json
{
  "manifestVersion": "1.0.0",
  "generatedAt": "2026-09-08T00:00:00Z",
  "models": [
    { "modelName": "mathvision-yolov8n-det", ... },
    { "modelName": "mathvision-crnn-ocr", ... }
  ],
  "parserEngine": { ... }
}
```
The canonical runtime manifest boundary (`app/schemas/model.py`) requires a single-model manifest format with fields `modelName`, `modelVersion`, `task`, `framework`, `artifactFilename`, `artifactFormat`, `sha256`, etc. Overwriting or mutating the original multi-model manifest was avoided.

---

### 9. Runtime Manifest Normalization

A normalized runtime manifest was created at `services/ai-service/models/model_manifest.json`:
- **Model Name**: `MathVision-Kids-Detection`
- **Model Version**: `1.0.0`
- **Task**: `OBJECT_DETECTION`
- **Framework**: `ULTRALYTICS_YOLO` (Framework Version: `8.4.143`)
- **Architecture**: `YOLOv8n`
- **Artifact Filename**: `yolov8n_mathvision_det_v1.pt`
- **Artifact Format**: `PYTORCH`
- **SHA-256**: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`
- **Input Dimensions**: 640×640×3
- **Preprocessing**: `RESIZE_ONLY`
- **Label Map Version**: `mathvision_det_v1.0` (File: `label_map_detection.json`)
- **Runtime Requirements**: `torch>=2.0.0, ultralytics>=8.0.0`
- **Provenance**: Preserved pointing to `ai-training/incoming/model_handoff.zip` (model index 0).

---

### 10. Label Map Audit

The delivered detection label map (`label_map_detection.json`) specifies 14 classes:
- Digits: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9` (Class IDs 0–9)
- Operators: `+` (ID 10), `-` (ID 11)
- Separator: `=` (ID 12)
- Carry Marker: `c1` (ID 13)

Canonical runtime enum `SUPPORTED_LABEL_MAP_VERSIONS` in `app/recognition/manifest.py` was updated to include `"mathvision_det_v1.0"` to avoid renaming or mutating the AI team's label version.

---

### 11. Label Adapter

Implemented in `app/recognition/yolo_adapter.py`:
- `0..9`: `tokenClass = "digit"`, `value = "0".."9"`
- `+`: `tokenClass = "operator"`, `value = "+"`
- `-`: `tokenClass = "operator"`, `value = "-"`
- `=`: `tokenClass = "separator"`, `value = "="`
- `c1`: `tokenClass = "carry"`, `value = "1"`

---

### 12. Borrow-Mark Limitation

- **Delivered Model Capability**: The model has NO borrow-mark class in its 14 output heads.
- **Formal Status**:
  ```
  EXPLICIT_BORROW_MARK_RECOGNITION: NOT_SUPPORTED_BY_MODEL
  ```
- **Runtime Handling**: No artificial borrow detections are invented. Subtraction borrow mathematics is computed and verified by the deterministic `VerticalSubtractionValidator` using recognized digit operands.

---

### 13. Original Parser Handling

The handoff included `parser_engine.py`. In accordance with Section 15:
- `parser_engine.py` is treated strictly as **REFERENCE_ONLY** / **COMPARISON_ONLY**.
- Existing frozen and tested components (`StructuredParser`, `VerticalAdditionValidator`, `VerticalSubtractionValidator`) were **NOT** replaced.
- Mathematical correctness authority remains 100% with the deterministic runtime validator.

---

### 14. Model Runtime Dependencies

Installed and locked in `services/ai-service/.venv`:
- **Python**: 3.14.6 (win32)
- **PyTorch**: 2.14.0+cpu
- **Ultralytics**: 8.4.143
- **Torchvision**: 0.29.0
- Documented in `services/ai-service/requirements.txt`: `torch>=2.0.0`, `ultralytics>=8.0.0`.

---

### 15. YOLO Adapter

The `YoloDetectionAdapter` in `app/recognition/yolo_adapter.py`:
- Filters raw detections below confidence threshold (default 0.25).
- Performs IoU non-maximum suppression (NMS, threshold 0.50) to eliminate duplicate overlapping bounding boxes.
- Assigns vertical `row` (0=top operand, 1=bottom operand, 2=result) based on adaptive vertical clustering.
- Assigns `column` (0=units, 1=tens, 2=hundreds) by sorting each row's digits descending by horizontal center (`x_center`), perfectly feeding `StructuredParser`'s right-to-left reverse sort.

---

### 16. ImageSourceResolver

All real-model inference paths utilize `ImageSourceResolver`:
- Validates URI format (`minio://<bucket>/<object-key>` or `fixture://<tag>`).
- Rejects path traversal (`../`), external URLs (`http://`, `https://`), and local filesystem paths (`file://`).
- Fetches private bytes directly from MinIO using authenticated internal credentials without public bucket exposure.

---

### 17. Bounding Box Mapping

Implemented in `xyxy_to_normalized_xywh(xyxy, img_w, img_h)`:
- Converts pixel `[x1, y1, x2, y2]` to `[x, y, width, height]`.
- Normalized range: `[0.0, 1.0]`.
- Origin: top-left `(0, 0)`.
- Verified with unit tests covering standard dimensions, edge clipping, and out-of-bounds coordinate clamping.

---

### 18. Confidence Mapping

- YOLO box confidence maps directly to `Token.confidence` (token recognition confidence).
- Bounding box confidence does NOT determine arithmetic diagnosis confidence, student score, or official grade.
- Tokens with `confidence < 0.50` are marked with `ambiguity = True`.

---

### 19. Actual Sample Inference

Executed delivered YOLO model against `sample_io/sample_input_synthetic.jpg`:
- Detections observed at `imgsz=640`:
  - `8` (ID 8): conf = 0.9742, bbox = [0.518, 0.224, 0.102, 0.184]
  - `8` (ID 8): conf = 0.9395, bbox = [0.405, 0.596, 0.102, 0.184]
  - `5` (ID 5): conf = 0.8848, bbox = [0.522, 0.596, 0.108, 0.179]
  - `3` (ID 3): conf = 0.8791, bbox = [0.405, 0.232, 0.106, 0.175]
  - `+` (ID 10): conf = 0.3057, bbox = [0.312, 0.325, 0.095, 0.140]
  - `4` (ID 4): conf = 0.2740, bbox = [0.414, 0.418, 0.093, 0.155]
  - `=` (ID 12): conf = 0.2496, bbox = [0.383, 0.559, 0.243, 0.060]
- Saved actual integration evidence at `services/ai-service/tests/fixtures/runtime_sample_output_actual.json` and `ai-training/incoming/extracted/model_handoff/sample_io/runtime_sample_output_actual.json` with metadata label `GENERATED_BY_RUNTIME_INTEGRATION`.

---

### 20. Expected-vs-Actual Sample Semantics

- **Expected Semantics in sample_io/expected_output.json**: `38 + 47 = 85`
- **Actual Model Behavior**:
  - Model detected `3` (0.879) and `8` (0.974) in Row 0 -> operand `38`.
  - Model detected `8` (0.940) and `5` (0.885) in Row 2 -> result `85`.
  - Operator `+` had confidence `0.3057` (< 0.50 ambiguity threshold).
  - Digit `4` had confidence `0.2740` (< 0.50 ambiguity threshold).
  - Digit `7` was low confidence on this synthetic sample (conf = 0.065 at 640px, conf = 0.35 at 896px).
- **Discrepancy Report**: The actual model detections for this synthetic sample trigger `status = "UNCERTAIN_RECOGNITION"` due to low confidence on operator and digit `4`. This discrepancy is reported truthfully without faking detections.

---

### 21. Addition Real Inference

Executed against synthetic worksheet addition image (`synthetic_addition.jpg`):
- **Detections**:
  - `4`: conf = 0.9824, Row 0, Col 1
  - `5`: conf = 0.5044, Row 0, Col 0
  - `+`: conf = 0.7685, Row 1, Col 99
  - `2`: conf = 0.6650, Row 1, Col 1
  - `7`: conf = 0.9666, Row 1, Col 0
  - `7`: conf = 0.9045, Row 2, Col 1
  - `2`: conf = 0.6550, Row 2, Col 0
- **Parsed Operands**: `45 + 27`
- **Parsed Result**: `72`
- **Validator Decision**: `is_valid = True` (PASS)

---

### 22. Subtraction Real Inference

Executed against synthetic worksheet subtraction image (`synthetic_subtraction.jpg`):
- **Detections**:
  - `5`: conf = 0.5711, Row 0, Col 1
  - `2`: conf = 0.7856, Row 0, Col 0
  - `-`: conf = 0.6866, Row 1, Col 99
  - `1`: conf = 0.9246, Row 1, Col 1
  - `8`: conf = 0.9851, Row 1, Col 0
  - `3`: conf = 0.6850, Row 2, Col 1
  - `4`: conf = 0.9588, Row 2, Col 0
- **Parsed Operands**: `52 - 18`
- **Parsed Result**: `34`
- **Validator Decision**: `is_valid = True` (PASS)

---

### 23. Carry Case

Tested addition with carry (`45 + 27 = 72` and `synthetic_addition_carry.jpg`):
- **Model Detection**: Model explicitly detected `c1` with conf = 0.2828.
- **Mathematical Validation**: `VerticalAdditionValidator` mathematically infers incoming carry `1` at column 1 (`5 + 7 = 12 -> carry 1`).
- **Conclusion**: Arithmetic correctness does NOT require `c1` detection; the deterministic validator reliably verifies carry mathematics from digits.

---

### 24. Borrow Case

Tested subtraction with borrow (`52 - 18 = 34`):
- **Borrow Mark Detection**:
  ```
  BORROW_MARK_DETECTION: NOT_SUPPORTED
  ```
- **Mathematical Validation**:
  ```
  BORROW_MATHEMATICAL_VALIDATION: PASS
  ```
  Units column: `2 < 8` requires borrow from tens column (`12 - 8 = 4`, borrow = 1). Tens column: `(5 - 1) - 1 = 3`.

---

### 25. Uncertainty Handling

- If any critical digit or operator has confidence below ambiguity threshold (0.50):
  - Token is marked `ambiguity = True`.
  - `ImageRecognitionResult.status = "UNCERTAIN_RECOGNITION"`.
  - `StructuredParser` outputs `UNCERTAIN_STRUCTURE`.
  - Student Policy outputs `NEEDS_CONFIRMATION`.
  - Teacher Policy outputs `REVIEW_REQUIRED`.
- Low confidence triggers uncertainty/human review, never false mathematical invalidity.

---

### 26. Student Model E2E

Verified in `test_model_e2e.py::test_model_e2e_student_addition`:
- Flow: `Spring Boot -> MinIO -> FastAPI MODEL mode -> Celery -> YOLOv8n -> StructuredParser -> VerticalAdditionValidator -> Student Policy -> Callback`.
- Result: Task returns `COMPLETED`, callback sends HTTP 200 payload with `status: "FEEDBACK_READY"` and `studentFeedback: {title: "Bài làm chính xác!"}`.

---

### 27. Teacher Model E2E

Verified in `test_model_e2e.py::test_model_e2e_teacher_addition`:
- Flow: `Teacher batch path -> Celery -> YOLOv8n -> StructuredParser -> Validator -> Teacher Policy -> Callback`.
- Result:
  - `policyMode = "TEACHER"`
  - `status = "PROPOSED_GRADE"`
  - `gradeProposal.isOfficial = false`
  - `gradeProposal.suggestedScore = 10`

---

### 28. Callback

- Callbacks serialize `AiCallbackRequest` with status, student feedback, grade proposal, and confidence bundle.
- In MODEL mode, average token recognition confidence is populated in `confidenceBundle.recognition`.

---

### 29. Teacher Authority

- `gradeProposal.isOfficial` is guaranteed `False` in all model responses.
- The AI model cannot generate `TeacherDecision` or official grades. Final grading authority remains strictly human.

---

### 30. MODEL Readiness

In `app/main.py`, `GET /ready` checks:
1. Redis broker connectivity.
2. If `RUNTIME_MODE == "MODEL"`, checks `ModelRecognitionEngine.is_ready` (manifest present, artifact checksum verified, model loaded).
3. Returns `{"status": "ready"}` if all pass, or `{"status": "NOT_READY"}` if model fails.

---

### 31. FIXTURE Regression

Full regression testing performed:
- All 10 tests in `test_fixture_e2e.py` PASS.
- All fixture engine tests PASS.
- Zero fixture regression observed.

---

### 32. Performance Smoke

Measured integration smoke timings on representative 640×640 image (`synthetic_addition.jpg`):

| Pipeline Stage | Timing (ms) |
|----------------|-------------|
| MinIO / Image Load | 0.14 ms |
| Preprocessing & Decode | 10.27 ms |
| YOLOv8n Inference (CPU) | 1,222.69 ms (warm) |
| Token Mapping & NMS | 0.80 ms |
| StructuredParser | 0.03 ms |
| Validator | 0.01 ms |
| **Total Worker Processing** | **1,233.93 ms** |

*Note: Labeled INTEGRATION SMOKE TIMINGS on CPU environment; not formal Phase 4.3 GPU benchmarks.*

---

### 33. Python Tests

Executed: `pytest tests/` in `services/ai-service`
- **Total Tests**: **92**
- **Passed**: **92 (100%)**
- **Failed**: **0**
- **Skipped**: **0**

---

### 34. Spring Tests

Executed: `gradlew.bat clean test` in `services/business-api`
- **Total Tests**: **49**
- **Passed**: **49 (100%)**
- **Failed**: **0**
- **Build Outcome**: `BUILD SUCCESSFUL in 34s`

---

### 35. Spring Build

Executed: `gradlew.bat build -x test` in `services/business-api`
- **Build Outcome**: `BUILD SUCCESSFUL in 3s`

---

### 36. Local Launcher

- `scripts/start-all.bat` and `scripts/stop-all.bat` continue to default to `FIXTURE` mode for immediate zero-dependency developer onboarding.
- `MODEL` mode is configured via `.env` (`RUNTIME_MODE=MODEL`) and validated.

---

### 37. Diagnostics

`tools/diagnostics/check_runtime.py` updated and verified:
- Truthfully reads FastAPI `/ready` status and models directory.
- Displays:
  ```
  AI Mode ............... MODEL (or FIXTURE)
  Primary Model ......... MathVision-Kids-Detection
  Model Version ......... 1.0.0
  Model Artifact ........ LOADED
  ```

---

### 38. Student Files Modified

**NONE** (0 student mobile files modified).

---

### 39. Teacher Files Modified

**NONE** (0 teacher web files modified).

---

### 40. Spring Files Modified

**NONE** (0 business code files modified).

---

### 41. AI Training Files Modified

**NONE** (0 training scripts, datasets, or teammate results modified).

---

### 42. Original Handoff Files Modified

**NONE** (Original ZIP and extracted files preserved immutably).

---

### 43. Known Model Limitations

Disclosed from `MODEL_CARD.md`:
1. `=` sign has lowest mAP@50 (0.748), can be confused with ruled lines.
2. `-` sign has mAP@50 = 0.845, can be confused with horizontal artifacts.
3. Fine-tuned for only 3 epochs from COCO pretrained weights.
4. Heavily synthetic dataset (~85% synthetic, 15% real HME-VAS).
5. Only vertical addition and subtraction supported (no horizontal, multiplication, or division).
6. Multi-problem pages may produce layout confusion.

---

### 44. Dataset Limitations

Disclosed from `DATASET_CARD.md`:
1. Total images: 2,001 (1,809 train, 192 val, no held-out test split).
2. Class imbalance: digit `1` (1,508) vs `=` (468) is 3.2:1.
3. Writer-disjoint split not guaranteed for HME-VAS subset.
4. 196 bounding box annotations had slight clipping out of [0, 1] bounds.
5. Inconsistent semantics for `c1` in source data.
6. Real collected images (33 samples) were excluded from training.

---

### 45. AI-Team Reported Metrics

Reported by AI team on 192 validation images:
- **mAP@50**: `0.9672`
- **mAP@50-95**: `0.7222`
- **Precision**: `0.9284`
- **Recall**: `0.9450`
- **Latency (Validation Mean)**: `28.4 ms` (GPU)

---

### 46. Proposal Metrics Status

- Proposal targets (critical-token recognition >= 90%, first-error precision >= 85%, over-correction <= 5%, p95 latency <= 12s) are **NOT YET DECLARED ACHIEVED**.
- In accordance with Section 34 and 35, achieving proposal targets requires formal Phase 4.3 evaluation on an independent gold evaluation dataset.

---

### 47. Integration Status

```
INTEGRATED
```

---

### 48. Runtime MODEL Status

```
READY_IN_MODEL_MODE
```

---

### 49. Phase Completion Assessment

```
READY_FOR_REVIEW
```

All 20 Phase 4.2 ready conditions have been met in full.

---

### 50. Recommended Next Step

Wait for human user approval. Upon review gate signoff, proceed to **Phase 4.3 (Model Evaluation & Golden Benchmark Testing)** using an independent, held-out evaluation dataset.

---
*End of Report — Antigravity Integration Agent*
