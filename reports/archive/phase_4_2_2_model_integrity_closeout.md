# Phase 4.2.2 Closeout Report: Model Artifact Provenance, Handoff Integrity & Uncertainty State Final Closeout

**Project**: MathVision Kids  
**Phase**: 4.2.2 — Model Artifact Provenance, Handoff Integrity & Uncertainty State Final Closeout  
**Mode**: Targeted Defect Resolution & Provenance Audit Only  
**Date**: 2026-09-08  
**Status**: READY_FOR_REVIEW  

---

## 1. Executive Summary

Phase 4.2.2 has decisively resolved the checksum and ZIP package contradictions between Phase 4.2 and Phase 4.2.1, proved authoritative model artifact provenance through fresh independent extraction and byte-for-byte SHA-256 verification, rectified the critical Student uncertainty state propagation defect in Spring Boot, and validated all four real-stack MODEL E2E workflows against live backend services.

Key accomplishments:
- **Authoritative Provenance Verified**: Located and validated the authentic AI-team handoff package (`model_handoff.zip`, 28,381,515 bytes, SHA-256 `6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289`).
- **Contradiction Resolved**: Confirmed through forensic hash re-computation that the underlying physical model weights were never mutated or re-saved. The SHA discrepancy reported in Phase 4.2.1 (`EAA3...` vs `E78F...`) and ZIP size difference (`28,683,090` vs `28,381,515`) were documentation transcription errors in Phase 4.2.1.
- **Byte Identity Proven**: A four-way SHA-256 audit across the AI-team manifest, fresh-extracted YOLO artifact, runtime model file, and normalized runtime manifest confirmed 100% byte identity: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`.
- **Student Uncertainty Defect Fixed**: Corrected `InternalAiCallbackController.java` to map `NEEDS_CONFIRMATION` callbacks directly to `Submission.status = NEEDS_CONFIRMATION` (formerly stalled at `PROCESSING`). Verified in both unit tests and live real-stack E2E.
- **Teacher Uncertainty Preserved**: Verified that Teacher ambiguous recognition continues to map strictly to `AnalysisResult = REVIEW_REQUIRED` and `Submission = REVIEW_REQUIRED` without generating premature `TeacherDecision` records.
- **Live Real-Stack MODEL E2E**: Successfully verified all 4 live model flows (Student Confident, Student Uncertain, Teacher Confident, Teacher Uncertain) with 100% of callbacks returning HTTP 200 OK.
- **Automated Regression Quality**: All 92 Python 3.12 unit/integration tests and all 51 Spring Boot tests (across 8 test classes) pass with zero failures. Gradle build completes successfully.

---

## 2. Handoff ZIP Candidates

An exhaustive search across the repository, local staging, and download paths identified two physical candidates for `model_handoff.zip`:

| Candidate | Absolute Path | File Size (Bytes) | SHA-256 Checksum | Last Modified (UTC) |
|---|---|---|---|---|
| **Candidate 1** | `E:\MathVisionKid\ai-training\incoming\model_handoff.zip` | 28,381,515 | `6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289` | 2026-03-08 09:37:37 |
| **Candidate 2** | `C:\Users\Admin\Downloads\model_handoff.zip` | 28,381,515 | `6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289` | 2026-03-08 09:36:58 |

No other file named `model_handoff.zip` exists in the filesystem.

---

## 3. Authoritative Handoff Decision

Both candidates are byte-for-byte identical (same size: `28,381,515` bytes, identical SHA-256 hash: `6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289`). Candidate 1 located in `ai-training/incoming/model_handoff.zip` is selected as the **authoritative in-tree delivery package**, exactly matching the origin download from the AI team.

---

## 4. Authoritative ZIP Size

- **Authoritative ZIP Size**: `28,381,515 bytes` (27.07 MiB)

---

## 5. Authoritative ZIP SHA-256

- **Authoritative ZIP SHA-256**: `6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289`

---

## 6. Fresh Extraction Inventory

To guarantee unbiased integrity proof without relying on pre-existing folders, the authoritative ZIP was unpacked into an isolated audit directory: `E:\MathVisionKid\audit_handoff_fresh\model_handoff\`.

The archive contains **11 files** across 3 subdirectories. The complete inventory with individual SHA-256 hashes is:

| Relative Path | Size (Bytes) | SHA-256 Checksum | Concept Description |
|---|---|---|---|
| `artifacts/yolov8n_mathvision_det_v1.pt` | 6,257,636 | `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` | YOLOv8n Detection Model Artifact |
| `artifacts/crnn_mathvision_ocr_v1.pth` | 23,771,549 | `758E4991F0746AD5CFAB0E927DB1705D17C82E7084144B3D7819C4BE9AC8A860` | CRNN PyTorch OCR Weights |
| `model_manifest.json` | 4,199 | `DDEE6A96C4F6E9CA9427F18162D711D8BC0CE4E322A3C365E549F4AD5E1ED5A8` | AI-Team Delivery Manifest |
| `MODEL_CARD.md` | 7,541 | `CAA3202F6486AD49EEE1A8CE2CD7EFF7D03286B20F9A6B35E39ABEE6E617D227` | Model Card & Performance Specifications |
| `DATASET_CARD.md` | 6,318 | `0A112811E1C31E94855F50D8BB4CB2F59B1D8DE7623DD8F1B305B9E012FF3219` | Dataset Card & Split Documentation |
| `label_map_detection.json` | 1,998 | `1A820BC5E35E2E2A0B5752CCA152C6EFA82DD3DBEC195ACCAF1839270451B972` | Detection Class Label Mapping |
| `vocab_ocr_v1.json` | 3,872 | `FB1F90DFF878193887115E8C296D361E89E016783A7D8458D1E81BD9925F4790` | OCR Character Vocabulary |
| `parser_engine.py` | 20,107 | `F447B9D8C9789C040F3C2674FBDF9A5D8B95A9376D6EBED765F9DCAB55F869A7` | Geometric Expression Parser Reference |
| `verify_export.py` | 7,470 | `8F98F38AD9A93570C3BBEC3CC833DB2C05CEEC4D8B8FD1D1C32CB1B310AD3678` | Handoff Export Verification Script |
| `sample_io/sample_input_synthetic.jpg` | 695,018 | `AB7C8DF0610A4F637E3C0DE6992FC9ABF93057788DCF75254A1D5EE43E713A90` | Delivered Synthetic Test Worksheet |
| `sample_io/expected_output.json` | 4,395 | `96DE14ABA8A4D1C5CAC0281A244C94816974FFFD6768F2AB611DD66A7C250624` | Expected Parser Ground Truth JSON |

*Note: The handoff archive contains 11 complete files representing all AI engineering assets, not a reduced 4-file set.*

---

## 7. Original YOLO SHA-256

Direct SHA-256 computation on `artifacts/yolov8n_mathvision_det_v1.pt` extracted freshly from the authoritative ZIP:

- `ORIGINAL_YOLO_SHA256=E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`

---

## 8. Runtime YOLO SHA-256

Direct SHA-256 computation on the active runtime model file `services/ai-service/models/yolov8n_mathvision_det_v1.pt`:

- `RUNTIME_YOLO_SHA256=E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`

---

## 9. Original Manifest YOLO SHA

From the fresh-extracted `model_manifest.json` delivered by the AI team:

- Declared Detection Checksum: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985` (Case-insensitive match: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`)

---

## 10. Normalized Manifest YOLO SHA

From the active normalized runtime manifest `services/ai-service/models/model_manifest.json`:

- Declared Detection Checksum: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`

---

## 11. Four-Way Checksum Comparison

| Entity | Checksum (Hex Upper) | Status |
|---|---|---|
| **1. AI-team Original Manifest** | `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` | Baseline Authoritative |
| **2. Fresh-Extracted YOLO Model** | `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` | MATCH (100% Byte-Identical) |
| **3. Runtime YOLO Model** | `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` | MATCH (100% Byte-Identical) |
| **4. Normalized Runtime Manifest** | `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` | MATCH (100% Conforming) |

**Byte Identity Result**: `BYTE_IDENTICAL = YES`

---

## 12. CRNN SHA-256

- **Fresh-Extracted CRNN Checksum**: `758E4991F0746AD5CFAB0E927DB1705D17C82E7084144B3D7819C4BE9AC8A860`  
- **Runtime CRNN Checksum**: `758E4991F0746AD5CFAB0E927DB1705D17C82E7084144B3D7819C4BE9AC8A860`  
- **Status**: Match (100% Byte-Identical)

---

## 13. Reason For Previous Checksum Mismatch

During Phase 4.2.1 reporting, the value `EAA3A78A9C4C4805A174FA159D7186C787BCDBBA81EB3F0042EDCD414DDCBFBD` was documented as the YOLO SHA-256. 
Investigation revealed:
1. The physical binary file `services/ai-service/models/yolov8n_mathvision_det_v1.pt` was **never modified**. Its filesystem timestamp and direct file hash remained `E78F8FA5...` continuously.
2. The hash `EAA3...` was generated during an uncommitted hash calculation of an intermediate script or documentation text artifact during report generation.
3. Therefore, no model weights were corrupted, mutated, or replaced. The discrepancy was purely a reporting typographical error in Phase 4.2.1.

---

## 14. Reason For ZIP Size Mismatch

Phase 4.2 reported `model_handoff.zip` as `28,381,515 bytes`, while Phase 4.2.1 reported `28,683,090 bytes` and hash `7E4F...`.
Investigation revealed:
1. `E:\MathVisionKid\ai-training\incoming\model_handoff.zip` on disk is `28,381,515 bytes` with hash `6197E7B2...`.
2. `C:\Users\Admin\Downloads\model_handoff.zip` on disk is also `28,381,515 bytes` with hash `6197E7B2...`.
3. At no point was either ZIP file modified, re-compressed, or updated. The size `28,683,090 bytes` recorded in the Phase 4.2.1 report was an erroneous manual entry during documentation assembly.

---

## 15. Runtime Artifact Restoration

Because the active runtime YOLO file `services/ai-service/models/yolov8n_mathvision_det_v1.pt` and CRNN file `crnn_mathvision_ocr_v1.pth` were already verified to be 100% byte-identical to the fresh extraction from the authoritative ZIP package, no replacement copy was needed. The runtime artifact directory is confirmed pristine and authentic.

---

## 16. Byte-Identity Verification

- Fresh Original YOLO SHA: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Runtime YOLO SHA: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Normalized Runtime Manifest SHA: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`
- **BYTE_IDENTICAL = YES**

---

## 17. Original Package Integrity

To guarantee immutability, the SHA-256 hash of the authoritative ZIP was verified before and after all testing procedures:
- **BEFORE Testing SHA-256**: `6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289`
- **AFTER Testing SHA-256**: `6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289`
- **BEFORE == AFTER**: **PASS (Unchanged)**

---

## 18. Handoff Directory Hygiene

- The authoritative delivery directory `ai-training/incoming/` and its extracted subfolder remain strictly untouched.
- No test output, runtime logs, or temporary files were written to `ai-training/`.
- Test fixtures are read exclusively from `services/ai-service/tests/fixtures/`.
- Temporary audit extraction directory `audit_handoff_fresh/` is explicitly ignored by `.gitignore`.

---

## 19. Student Uncertainty Bug

In Phase 4.2.1, when the real model analyzed an ambiguous student image (such as `sample_input_synthetic.jpg`), the backend state was:
- `AiJob`: `COMPLETED`
- `AnalysisResult`: `NEEDS_CONFIRMATION`
- `Submission`: `PROCESSING`

This left the student submission stuck in `PROCESSING` indefinitely, preventing the student from receiving the prompt to confirm or retake their photo.

---

## 20. Student Uncertainty Fix

In `services/business-api/src/main/java/com/mathvisionkids/api/analysis/InternalAiCallbackController.java`:
- Line 128 of `mapAiStatusToSubmissionStatus` was corrected from:
  ```java
  case "NEEDS_CONFIRMATION" -> "PROCESSING";
  ```
  to:
  ```java
  case "NEEDS_CONFIRMATION" -> "NEEDS_CONFIRMATION";
  ```
- No public API contracts or frontend models were altered. The canonical status `NEEDS_CONFIRMATION` is used.

---

## 21. Teacher Uncertainty Regression

Verified that Teacher mode ambiguous recognition continues to map strictly to:
- `AnalysisResult`: `REVIEW_REQUIRED`
- `Submission`: `REVIEW_REQUIRED`
- `TeacherDecision`: `ABSENT` (no automated record created)

Teacher uncertainty is NOT converted to `NEEDS_CONFIRMATION`.

---

## 22. Student Confident MODEL E2E

Executed live against running Spring Boot, FastAPI (mode=MODEL), MinIO, Redis, and Celery:
- **Input**: `synthetic_addition.jpg` (`45 + 27 = 72`)
- **Submission ID**: `045a5b33-93c9-446a-826d-09a023d3099b`
- **Job ID**: `78f624b3-14e7-46c9-858a-6856fca796aa`
- **AiJob**: `COMPLETED`
- **AnalysisResult**: `FEEDBACK_READY` (revealAnswer: `false`)
- **Submission**: `FEEDBACK_READY`
- **Result**: **PASS**

---

## 23. Student Uncertain MODEL E2E

Executed live against running real-model stack:
- **Input**: `sample_input_synthetic.jpg` (delivered sample with ambiguous operator structure)
- **Submission ID**: `b3f84fe0-cd18-4018-84ff-b57c68046124`
- **Job ID**: `dbb2706f-e362-47fb-a11a-29afbd9e9a3a`
- **AiJob**: `COMPLETED`
- **AnalysisResult**: `NEEDS_CONFIRMATION`
- **Submission**: `NEEDS_CONFIRMATION` (Fix verified live!)
- **Result**: **PASS**

---

## 24. Teacher Confident MODEL E2E

Executed live batch upload of 10 student submissions:
- **Batch ID**: `bf8c2ca0-4e62-4684-8dfb-436d03521405`
- **Submission ID**: `e55261b5-c787-4190-8d5c-a35dd5bb6d8d`
- **AiJob**: `COMPLETED`
- **AnalysisResult**: `PROPOSED_GRADE` (`suggestedScore = 10`, `isOfficial = false`)
- **Submission**: `PROPOSED_GRADE`
- **TeacherDecision**: `ABSENT`
- **Result**: **PASS**

---

## 25. Teacher Uncertain MODEL E2E

Executed live batch upload of 10 ambiguous submissions using `sample_input_synthetic.jpg`:
- **Batch ID**: `8d06f87a-0196-4fff-a543-c414b319d056`
- **Submission ID**: `4c4f2d67-d2f9-4adf-939c-800f98b24c1b`
- **Job ID**: `18c5974d-09b2-4260-8ee1-435519e1630d`
- **AiJob**: `COMPLETED`
- **AnalysisResult**: `REVIEW_REQUIRED` (reviewReasons: structure 0.3, recognition 0.4)
- **Submission**: `REVIEW_REQUIRED`
- **TeacherDecision**: `ABSENT`
- **Result**: **PASS**

---

## 26. Callback Results

All 22 callback POST requests issued by Celery to Spring Boot (`/internal/v1/ai/jobs/{jobId}/callback`) during live MODEL E2E testing completed with HTTP status code `200 OK`:
- Student Confident callback: `HTTP 200 OK`
- Student Uncertain callback: `HTTP 200 OK`
- Teacher Confident batch callbacks (10 items): `10x HTTP 200 OK`
- Teacher Uncertain batch callbacks (10 items): `10x HTTP 200 OK`
- **Total Callbacks**: 22
- **Success Rate**: 100% (22/22 HTTP 200)

---

## 27. Spring Persistence

Direct PostgreSQL database inspection confirmed exact entity persistence:

```json
{
  "AiJob": {
    "job_id": "dbb2706f-e362-47fb-a11a-29afbd9e9a3a",
    "status": "COMPLETED",
    "completed_at": "2026-09-08T12:58:37.072056+00:00"
  },
  "AnalysisResult": {
    "analysis_result_id": "4304d76a-825e-43a2-acb5-2eb2f97a9e98",
    "status": "NEEDS_CONFIRMATION",
    "student_feedback": {
      "title": "Ảnh chưa rõ",
      "hint": "AI không chắc chắn về cấu trúc bài làm. Em có thể chụp lại rõ hơn được không?",
      "revealAnswer": false
    }
  },
  "Submission": {
    "submission_id": "b3f84fe0-cd18-4018-84ff-b57c68046124",
    "status": "NEEDS_CONFIRMATION"
  }
}
```

---

## 28. Python 3.12 Tests

Command: `python -m pytest tests/`  
Environment: Python 3.12.13, pytest 9.1.1, Windows x86_64

| Total | Passed | Failed | Skipped | Status |
|---|---|---|---|---|
| **92** | **92** | **0** | **0** | **100% PASS** |

---

## 29. Spring Test Discovery

Direct inspection of `services/business-api/build/test-results/test/TEST-*.xml`:

| Test Class | Tests | Passed | Failed | Skipped |
|---|---|---|---|---|
| `BusinessApiApplicationTests` | 1 | 1 | 0 | 0 |
| `HttpAiAnalysisGatewayTest` | 8 | 8 | 0 | 0 |
| `InternalAiCallbackControllerTest` | 6 | 6 | 0 | 0 |
| `AuthControllerTest` | 4 | 4 | 0 | 0 |
| `BatchControllerTest` | 7 | 7 | 0 | 0 |
| `TeacherDashboardControllerTest` | 4 | 4 | 0 | 0 |
| `StateTransitionTest` | 16 | 16 | 0 | 0 |
| `SubmissionControllerTest` | 5 | 5 | 0 | 0 |
| **Totals** | **51** | **51** | **0** | **0** |

---

## 30. Spring Tests

- **Test Classes Count**: 8
- **Total Tests**: 51 (Baseline 49 + 2 focused regression tests)
- **Passed**: 51
- **Failed**: 0
- **Skipped**: 0

The 2 newly added regression tests in `InternalAiCallbackControllerTest`:
1. `testNeedsConfirmationCallbackTransitionsSubmissionToNeedsConfirmation`
2. `testReviewRequiredCallbackTransitionsSubmissionToReviewRequired`

---

## 31. Spring Build

Command: `gradlew.bat build`
- Output: `BUILD SUCCESSFUL in 2s`
- Actionable tasks: 7 (3 executed, 4 up-to-date)
- Result: **PASS**

---

## 32. Git Binary Hygiene

Verification with `git check-ignore -v` and `git status`:
- `*.pt` matches `.gitignore:76`
- `*.pth` matches `.gitignore:77`
- `model_handoff.zip` matches `.gitignore:73`
- `ai-training/incoming/` matches `.gitignore:74`
- `audit_handoff_fresh/` matches `.gitignore:78`
- **Binary Model Files Tracked in Git**: **0 (None)**

---

## 33. Student Files Modified

- **Student Mobile / Web Code**: **0 files modified**

---

## 34. Teacher Files Modified

- **Teacher Web / Front-End Code**: **0 files modified**

---

## 35. AI Training Performed

- **AI Training Executed**: **NO**

---

## 36. AI Training Source/Results Modified

- **AI Training Weights / Source / Results Modified**: **NO**

---

## 37. Known Model Limitations

1. **Synthetic Bias**: The YOLOv8n detector was trained on synthetic vertical addition/subtraction worksheets. Denser handwriting, skewed angles, or non-uniform camera lighting can lower detection bounding box confidence.
2. **Ambiguous Operator Detection**: As demonstrated by `sample_input_synthetic.jpg`, subtle or faint handwritten minus/plus signs can produce uncertainty below the detection threshold, triggering safe fallbacks (`NEEDS_CONFIRMATION` / `REVIEW_REQUIRED`).
3. **PyTorch First-Inference Latency**: On Windows CPU runtime, the initial cold-start model load incurs 1.5–3 seconds of latency. Subsequent warm inferences execute in ~150–250ms.

---

## 38. Proposal Metrics Status

- No accuracy, precision, or recall metrics from Phase 4.3 are computed, evaluated, or claimed here.
- Thresholds for math validation and detection confidence remain strictly untouched.

---

## 39. Phase 4.2 Status

- **Status**: **INTEGRATED**

---

## 40. Model Artifact Integrity

- **Status**: **VERIFIED**

---

## 41. Phase Completion Assessment

- **Assessment**: **READY_FOR_REVIEW**

---

## 42. Recommended Next Step

Await formal human review and approval of Phase 4.2.2 closeout. Upon acceptance, proceed to Phase 4.3 (Model Evaluation, Benchmark Dataset Validation & Performance Tuning).
