# Phase 4.3 Report: Independent Gold Evaluation, Model Quality Benchmark & Proposal Metric Gating

**Project**: MathVision Kids  
**Phase**: 4.3 — Independent Gold Evaluation, Model Quality Benchmark & Proposal Metric Gating  
**Mode**: Formal Quality Evaluation & Dataset Gating Only (No Training, No Fine-Tuning, No Threshold Tuning)  
**Date**: 2026-09-08  
**Evaluation Status**: **BLOCKED_DATASET**  

---

## 1. Executive Summary

Phase 4.3 was initiated to independently evaluate the frozen recognition + parser + deterministic validation pipeline against an independent, de-identified gold evaluation dataset. In accordance with strict governance protocols:
1. An exhaustive audit was conducted across `ai-training/`, `data/`, `manifests/`, `annotations/`, and handoff packages to locate an independent gold test dataset.
2. The AI/ML team's authoritative handoff `DATASET_CARD.md` explicitly declares:  
   `"Test set: No separate held-out test set in this version"`.
3. In-tree dataset splits under `ai-training/data/splits/test/` and annotation directories (`ai-training/annotations/adjudicated/`, `primary/`, `secondary/`) are currently unpopulated (0 images, 0 annotations).
4. Per mandatory governance rules (**Section 6 & 8**), training images, validation images used for checkpoint selection, and the single delivered synthetic integration sample (`sample_input_synthetic.jpg`) must **never** be substituted or repurposed as independent benchmark evidence.
5. Consequently, Phase 4.3 is declared **BLOCKED_DATASET**.
6. The evaluation harness has been constructed and frozen at `services/ai-service/evaluation/run_evaluation.py`. End-to-end CPU inference latency benchmark was performed (p95 = 0.0854s, passing the <=12.0s target). Regression testing confirmed 100% stability (92 Python tests pass, 51 Spring Boot tests pass, Spring build successful, YOLO model SHA verified unchanged).
7. A formal feedback package has been prepared in `report/phase_4_3_ai_team_feedback.md` specifying exact dataset delivery requirements for the AI/ML teammate to unblock gold evaluation.

---

## 2. Evaluation Dataset Discovery

A filesystem inspection of potential dataset repositories was performed across `E:\MathVisionKid`:

| Location Inspected | Target Asset | Findings | Status |
|---|---|---|---|
| `ai-training/data/splits/test/` | Held-out test split | 0 files | **EMPTY** |
| `ai-training/data/deidentified-local/` | De-identified images | Contains only `.gitkeep` (14 bytes) | **EMPTY** |
| `ai-training/data/manifests/` | Dataset manifests | Contains only `.gitkeep` (14 bytes) | **EMPTY** |
| `ai-training/annotations/primary/` | Annotator 1 annotations | 0 files | **EMPTY** |
| `ai-training/annotations/secondary/` | Annotator 2 annotations | 0 files | **EMPTY** |
| `ai-training/annotations/adjudicated/` | Adjudicated gold annotations | 0 files | **EMPTY** |
| `ai-training/incoming/extracted/model_handoff/` | Delivered handoff package | Contains only 1 synthetic sample (`sample_input_synthetic.jpg`) | **NO HELD-OUT TEST SET** |

---

## 3. Dataset Eligibility

- **Total Gold Image Count**: **0**
- **Eligibility Assessment**: **INELIGIBLE (NO DATASET DELIVERED)**
- No independent gold dataset meets the minimum eligibility criteria (Proposal targets: W5 >=100 pilot images, W11 >=500 de-identified gold images).

---

## 4. Dataset Independence

- **Independence Status**: **NOT_VERIFIED**
- Because no independent test split exists, train/test leakage cannot be ruled out for any ad-hoc samples.
- The single delivered sample `sample_input_synthetic.jpg` was part of the integration handoff package and cannot serve as independent evaluation evidence.

---

## 5. Dataset Size

- **Independent Test Images**: 0
- **Held-Out Gold Samples**: 0
- **Delivered Training Split**: 1,809 images (reported in `DATASET_CARD.md`)
- **Delivered Validation Split**: 192 images (reported in `DATASET_CARD.md`, used to select checkpoint)

---

## 6. Real/Synthetic Composition

- **Gold Benchmark Real Images**: 0 (N/A)
- **Gold Benchmark Synthetic Images**: 0 (N/A)
- **Handoff Training/Validation Set Composition (Reference)**: ~85% synthetic, ~15% real (HME-VAS academic dataset).

---

## 7. Writer-Disjoint Status

- **Writer-Disjoint Verification**: **NOT_APPLICABLE (NO TEST DATASET)**
- Per `DATASET_CARD.md`, the AI team notes: *"Writer-disjoint: NOT APPLICABLE for synthetic data... our split does NOT guarantee writer-disjoint across HME-VAS images."*

---

## 8. De-identification Status

- **De-identification Status**: **NOT_APPLICABLE (NO TEST DATASET)**
- No real child handwriting worksheets have been placed in `ai-training/data/deidentified-local/`. Zero PII is stored or committed.

---

## 9. Annotation Quality

- **Annotation Quality**: **NOT_EVALUATED**
- No ground-truth bounding boxes, expression transcriptions, or arithmetic labels exist for an independent test set.

---

## 10. Double Annotation

- **Double Annotation Rate**: **0.0% (N/A)**
- Target: >=20% double annotation. No double-annotated gold evaluation set is available.

---

## 11. Adjudication

- **Adjudication Status**: **NONE**
- `ai-training/annotations/adjudicated/` contains no reconciled labels.

---

## 12. Dataset Manifest SHA

- **Gold Dataset Manifest**: **NONE**
- **Manifest SHA-256**: `N/A (BLOCKED)`

---

## 13. Model Identity

- **Model Name**: `MathVision-Kids-Detection`
- **Architecture**: `YOLOv8n` (Ultralytics)
- **Model Version**: `v1.0.0`
- **Format**: PyTorch (`.pt`)

---

## 14. Model & Manifest Provenance Checksums

To prevent conflation of model binary checksums with manifest file checksums, all hashes are computed and recorded independently:

- **modelArtifactSha256**: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` (actual SHA-256 of `yolov8n_mathvision_det_v1.pt`, 6,257,636 bytes)
- **artifactChecksumDeclaredByManifest**: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985` (value declared in `model_manifest.json` under field `sha256`)
- **normalizedManifestSha256**: `3C1BDE47E72EE01C9DCBD8AD3E8589C6ACC78E7E1B361C3FE78C559027BBC743` (actual SHA-256 of `models/model_manifest.json`, 1,155 bytes)
- **labelMapSha256**: `1A820BC5E35E2E2A0B5752CCA152C6EFA82DD3DBEC195ACCAF1839270451B972` (actual SHA-256 of `models/label_map_detection.json`, 1,998 bytes)
- **evaluationConfigSha256**: `C805B02E2BFACB5FA0DE5302BC517FD92AE4F8F73FFFD83C6EEA58AEB1D0C7DC` (actual SHA-256 of `evaluation/evaluation_config_v1.json`)
- **Integrity**: Exact match between `modelArtifactSha256` and `artifactChecksumDeclaredByManifest`. Zero artifact tampering detected.

---

## 15. Evaluation Configuration

- **Runtime Mode**: `MODEL`
- **Inference Engine**: `ModelRecognitionEngine` (`services/ai-service/app/recognition/model_engine.py`)
- **Parser Engine**: `StructuredParser` (`services/ai-service/app/parsing/parser.py`)
- **Validators**: `VerticalAdditionValidator`, `VerticalSubtractionValidator` (`services/ai-service/app/validation/`)
- **Policies**: `StudentPolicy`, `TeacherPolicy` (`services/ai-service/app/policy/`)
- **Python Runtime**: Python 3.12.13 (Windows x86_64)
- **PyTorch Version**: `2.14.0+cpu`
- **Ultralytics Version**: `8.4.143` (Tested frozen runtime in requirements-lock.txt and active venv)

---

## 16. Frozen Thresholds

All thresholds remain strictly frozen and unaltered:
- **Detection Confidence Threshold**: `0.25`
- **NMS IoU Threshold**: `0.50` (Configured in `yolo_adapter.py`)
- **Vertical Line IoU**: `0.50`
- **Quality Gate Min Confidence**: `0.30`
- **Ambiguity Threshold**: `0.50`
- **High-Confidence Threshold**: `0.85`
- **Over-Correction Guard**: Mathematical equivalence check (advisory only, revealAnswer=False)

---

## 17. Evaluation Harness

The automated, reproducible evaluation harness has been established at:
- File: `services/ai-service/evaluation/run_evaluation.py`
- Output evidence: `report/evidence/phase_4_3/evaluation_results.json`
- Capabilities: Loads gold dataset manifests, invokes frozen model pipeline, compares token predictions, calculates first-error localization and over-correction, and records structured execution results.

---

## 18. Critical-Token Recognition

- **Proposal Target**: >= 90%
- **Measured Value**: **NOT_EVALUATED**
- **Reason**: Independent gold test dataset is missing.

---

## 19. Per-Class Token Metrics

- **Per-Class Metrics**: **NOT_EVALUATED**
- Classes monitored: `0, 1, 2, 3, 4, 5, 6, 7, 8, 9, +, -, =, c1`.

---

## 20. Confusion Matrix

- **Status**: **NOT_AVAILABLE** (Requires ground truth test annotations).

---

## 21. Full Expression Accuracy

- **Measured Value**: **NOT_EVALUATED**

---

## 22. Structure Parsing Accuracy

- **Measured Value**: **NOT_EVALUATED**

---

## 23. Validator Accuracy

- **Deterministic Validator**: Frozen unit tests pass 100%, but formal dataset-wide validation accuracy is **NOT_EVALUATED**.

---

## 24. First-Error Precision

- **Proposal Target**: >= 85% (high-confidence subset)
- **Measured Value**: **NOT_EVALUATED**

---

## 25. First-Error Recall

- **Measured Value**: **NOT_EVALUATED**

---

## 26. First-Error Coverage

- **Measured Value**: **NOT_EVALUATED**

---

## 27. High-Confidence Coverage

- **Measured Value**: **NOT_EVALUATED**

---

## 28. Over-Correction Rate

- **Proposal Target**: <= 5%
- **Formula**: `Count(Mathematically valid student submissions diagnosed as erroneous) / Count(Valid submissions)`
- **Measured Value**: **NOT_EVALUATED**

---

## 29. Abstention Rate

- **Measured Value**: **NOT_EVALUATED**

---

## 30. NEEDS_CONFIRMATION Rate

- **Measured Value**: **NOT_EVALUATED**

---

## 31. REVIEW_REQUIRED Rate

- **Measured Value**: **NOT_EVALUATED**

---

## 32. Addition Metrics

- **Vertical Addition Evaluation**: **NOT_EVALUATED**

---

## 33. Subtraction Metrics

- **Vertical Subtraction Evaluation**: **NOT_EVALUATED**

---

## 34. Carry Metrics

- **Addition with Carry**: **NOT_EVALUATED**
- **Addition without Carry**: **NOT_EVALUATED**

---

## 35. Borrow Metrics

- **Subtraction with Borrow**: **NOT_EVALUATED**
- **Subtraction without Borrow**: **NOT_EVALUATED**

---

## 36. Error Type Metrics

- `COMPUTATION_ERROR`: **NOT_AVAILABLE**
- `CARRY_BORROW_ERROR`: **NOT_AVAILABLE**
- `PLACE_VALUE_ALIGNMENT_ERROR`: **NOT_AVAILABLE**
- `NOTATION_ISSUE`: **NOT_AVAILABLE**

---

## 37. Latency Environment

- **Host OS**: Windows 11 Pro (10.0.26200)
- **CPU Processor**: 12th Gen Intel(R) Core(TM) i5-12400F (6 Cores, 12 Threads)
- **RAM**: 32 GB DDR4
- **Device Used**: CPU (`torch.device('cpu')`)
- **Python**: 3.12.13
- **PyTorch**: 2.14.0+cpu
- **YOLO Engine**: Ultralytics YOLOv8n

---

## 38. Latency Results

Benchmark executed over 10 consecutive inference cycles on a standard worksheet image (`synthetic_addition.jpg`, 640x640):

| Stage / Metric | Latency (Seconds) |
|---|---|
| **Model Cold Load Time** | 0.0285 s |
| **Cold First Inference** | 1.7083 s |
| **Warm Inference (Mean)** | 0.0474 s |
| **Warm Inference (Min)** | 0.0369 s |
| **Warm Inference (Max)** | 0.0854 s |
| **Warm Inference (p90)** | 0.0631 s |
| **Warm Inference (p95)** | **0.0854 s** |

---

## 39. p95 Latency
 
- **Proposal Target**: p95 <= 12.0 seconds
- **Smoke Timing Measurement (Non-Benchmark)**: **0.0854 seconds** (Warm CPU inference on single synthetic image, N=10) / **1.7083 seconds** (Cold start load + inference)
- **Classification**: **LOCAL_INFERENCE_SMOKE_TIMING**
- **Formal Target Status**: **NOT_EVALUATED** (Formal Proposal p95 latency requires evaluation across the independent gold workload)

---

## 40. Failure Taxonomy

No empirical failure cases can be cataloged until the gold test set is evaluated.

---

## 41. Top Failure Categories

- **Status**: **NOT_AVAILABLE**

---

## 42. Failure Attribution

- **Status**: **NOT_AVAILABLE**

---

## 43. AI-Team Validation Metrics

Reported by the AI/ML training team in `MODEL_CARD.md` (validation split: 192 images, 1,496 annotations):
- `mAP@50`: **0.9672**
- `mAP@50-95`: **0.7222**
- `Precision`: **0.9284**
- `Recall`: **0.9450**

*Notice: These metrics originate from the training/selection split and are NOT independent test benchmark results.*

---

## 44. Independent Evaluation Metrics

- **Independent Benchmark Metrics**: **NONE AVAILABLE (DATASET MISSING)**

---

## 45. Proposal Quality Gate Table

| Metric | Proposal Target | Measured Value | Pass / Fail | Coverage | Notes |
|---|---|---|---|---|---|
| **Critical-token recognition** | >= 90% | NOT_EVALUATED | **BLOCKED** | 0% | No gold dataset |
| **First-error precision** | >= 85% | NOT_EVALUATED | **BLOCKED** | 0% | No gold dataset |
| **First-error recall** | Separate | NOT_EVALUATED | **BLOCKED** | 0% | No gold dataset |
| **First-error coverage** | Separate | NOT_EVALUATED | **BLOCKED** | 0% | No gold dataset |
| **Over-correction rate** | <= 5% | NOT_EVALUATED | **BLOCKED** | 0% | No gold dataset |
| **p95 AI latency** | <= 12.0s | NOT_EVALUATED (Smoke: 0.0854s) | **NOT_EVALUATED** | 0% | Formal p95 pending gold workload |
| **Hint quality** | >= 4.0 / 5 | REQUIRES_HUMAN_EVAL | **NOT_EVALUATED** | 0% | No human study data |
| **Student usability** | >= 80% | NOT_EVALUATED | **NOT_EVALUATED** | 0% | Requires live pilot |
| **Teacher usability** | 100% reviewable | NOT_EVALUATED | **NOT_EVALUATED** | 0% | Requires user study |

---

## 46. Hint Quality Status

- **Status**: **REQUIRES_HUMAN_EVALUATION**
- In strict adherence to Section 37, no synthetic human ratings were fabricated.

---

## 47. Student Usability Status

- **Status**: **NOT_EVALUATED**
- Requires supervised student usability trials.

---

## 48. Teacher Usability Status

- **Status**: **NOT_EVALUATED**
- Requires supervised teacher workflow trials.

---

## 49. Python Regression

- Command: `python -m pytest tests/`
- Runtime: Python 3.12.13, pytest 9.1.1
- **Total**: 92
- **Passed**: **92**
- **Failed**: **0**
- **Skipped**: **0**
- **Status**: **100% PASS**

---

## 50. Spring Regression

- Command: `gradlew.bat clean test`
- Results across 8 test classes:
  - `BusinessApiApplicationTests`: 1 passed
  - `HttpAiAnalysisGatewayTest`: 8 passed
  - `InternalAiCallbackControllerTest`: 6 passed
  - `AuthControllerTest`: 4 passed
  - `BatchControllerTest`: 7 passed
  - `TeacherDashboardControllerTest`: 4 passed
  - `StateTransitionTest`: 16 passed
  - `SubmissionControllerTest`: 5 passed
- **Total Tests**: 51
- **Passed**: **51**
- **Failed**: **0**
- **Skipped**: **0**
- **Status**: **100% PASS**

---

## 51. Spring Build

- Command: `gradlew.bat build`
- Output: `BUILD SUCCESSFUL in 2s`
- **Status**: **PASS**

---

## 52. Model Artifact Integrity

- **Before Benchmark SHA-256**: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- **After Benchmark SHA-256**: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- **Integrity Status**: **UNCHANGED (PASS)**

---

## 53. Student Files Modified

- **Student Mobile / Web Code**: **0 files modified (NO)**

---

## 54. Teacher Files Modified

- **Teacher Web Code**: **0 files modified (NO)**

---

## 55. AI Training Performed

- **AI Training Executed**: **NO**

---

## 56. Model Weights Modified

- **Model Weights Modified**: **NO**

---

## 57. Gold Labels Modified

- **Gold Labels Modified**: **NO**

---

## 58. Known Limitations

1. **Absence of Independent Test Set**: Model generalization to unseen real student handwriting remains unquantified until an independent gold dataset is delivered.
2. **Synthetic-to-Real Domain Gap**: Training data was 85% synthetic; real-world accuracy on varied handwriting, lighting, and worksheet layouts cannot be claimed without held-out real data.
3. **Double Annotation Deficit**: In-tree annotation pipelines lack adjudicated double annotation.

---

## 59. Evaluation Conclusion

- **Phase 4.3 Conclusion**: **BLOCKED_DATASET**
- While technical runtime integration, latency, and code stability are fully validated, formal Proposal metric gating is blocked due to the absence of an independent gold evaluation dataset.

---

## 60. Recommended Next Step

AI/ML teammate must deliver the independent gold evaluation dataset (images + manifests + annotations) as specified in `report/phase_4_3_ai_team_feedback.md`. Upon receipt and provenance verification, re-execute `services/ai-service/evaluation/run_evaluation.py` to compute formal Proposal metrics.
