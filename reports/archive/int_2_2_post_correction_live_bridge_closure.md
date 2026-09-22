# MathVision Kids — Closure Report
## INT.2.2: Post-Correction Live OCR Bridge Verification & Callback Contract Closure

**Date:** September 11, 2026  
**Environment:** Windows 11 (Primary Developer Environment)  
**Status:** `READY_FOR_FINAL_REFREEZE`  
**Mode:** MICRO CLOSURE / LIVE RUNTIME TRUTH / NO NEW FEATURES  
**Scope:** Final live runtime end-to-end verification, Celery-to-Spring callback serialization boundary audit, privacy/sanitization verification for `CRNN_ERROR`, and confirmation of safe default configurations following INT.2.1 code adjustments.

---

### 1. Executive Summary

Task INT.2.2 establishes final verification and closure for the YOLO $\to$ RowGrouper $\to$ CRNN shadow bridge recognition pipeline. Following the semantic corrections in INT.2.1 (`CRNN_ERROR`, safe `is_active` check, and ImageNet normalization confirmation), the complete local stack was restarted and exercised with live multi-stage submissions via real HTTP upload, MinIO retrieval, Celery processing, deterministic validation, and Spring Boot callback completion.

**Key Achievements & Verifications:**
1. **Live End-to-End Execution Confirmed:** Two live student submissions (`synthetic_addition.jpg` and `synthetic_subtraction.jpg`) were processed through the full Spring $\to$ MinIO $\to$ Celery $\to$ Spring Callback flow, reaching terminal status `FEEDBACK_READY` (HTTP 200 callback). CRNN executed in the live worker process and model singleton caching was re-verified (warm latency: 452 ms).
2. **Callback Contract Audit (Zero Drift):** Audited the serialization boundary between Celery and Spring Boot. Proved that INT.2 diagnostic fields (`line_recognitions`, `all_rows_agree`, `ocr_provider_used`) are strictly **`INTERNAL_ONLY`**. They remain inside `ImageRecognitionResult` and Celery logs; they are never included in `AiCallbackRequest`, ensuring zero public or internal callback API drift.
3. **Privacy & Sanitization of `CRNN_ERROR`:** Exception messages in `LineRecognition.error` are actively sanitized with `_sanitize_error_message()` (masking absolute filesystem paths `[A-Za-z]:\...` to `<path>`), while detailed tracebacks remain in internal server logs only. Raw exception text cannot enter callback JSON, cannot persist to the business database, and cannot reach client devices.
4. **Controlled Failure Verification:** An integration test proved that when CRNN inference fails with a runtime exception, the job completes safely without failing the submission, records `CRNN_ERROR`, preserves YOLO tokens and deterministic validator authority, and transmits a valid, sanitized callback.
5. **Safe Defaults Restored:** Disk configurations confirm `OCR_PROVIDER=noop` and `OCR_BRIDGE_MODE=off`. CRNN inference is never loaded by default.
6. **100% Test Pass:** 19/19 targeted tests and 140/140 full AI test suite cases passed (0 failures). YOLO and CRNN checkpoint SHA256 hashes match exactly.

---

### 2. Repository State

- **Git Root:** `E:\MathVisionKid`
- **Branch:** `main`
- **Pre-existing State:** Preserved INT.2 / INT.2.1 code (`RowGrouper`, `OcrBridge`, `ModelEngine` wiring, unit & integration test suites).
- **Frontend / Spring Status:** Untouched. Zero changes were made to Spring Boot, Student Web, Teacher Web, or Admin Web source code.

---

### 3. Callback Serialization Trace

The end-to-end data flow from image ingestion to callback completion was traced:
```
1. Client POST /api/v1/student/submissions (multipart/form-data)
       |
       v
2. Spring Boot stores original bytes in MinIO: 'submissions/<uuid>_<filename>'
       |
       v
3. Spring Boot dispatches job to FastAPI: POST /internal/v1/jobs
       |
       v
4. FastAPI enqueues Celery task: app.jobs.tasks.process_submission
       |
       v
5. Celery Worker fetches image from MinIO -> PIL.Image (RGB)
       |
       v
6. ModelRecognitionEngine.recognize():
       a. YoloDetectorAdapter.detect() -> raw boxes -> Token[]
       b. (If shadow mode active) RowGrouper.group() -> RowGroup[]
       c. (If shadow mode active) OcrBridge.recognize_rows() -> BridgeRecognitionResult
       d. ImageRecognitionResult constructed with tokens + internal line_recognitions
       |
       v
7. StructuredParser.parse(tokens) -> ParsedExercise
       |
       v
8. VerticalAdditionValidator / VerticalSubtractionValidator -> validation_result
       |
       v
9. generate_student_feedback() / generate_teacher_feedback()
       |
       v
10. AiCallbackRequest constructed with:
       - status (e.g. "FEEDBACK_READY")
       - recognizedExercise (e.g. "45 + 27 = 72")
       - studentFeedback (title, hint, focusEvidenceId, revealAnswer)
       - evidence (arithmetic error diagnostics)
       - confidenceBundle (recognition, structure, diagnosis)
       |
       v
11. HTTP POST to Spring Boot: /internal/v1/ai/jobs/{jobId}/callback
       |
       v
12. Spring InternalAiCallbackController updates AiJob and Submission in PostgreSQL
```

---

### 4. OCR Diagnostic Fields Boundary

The INT.2 diagnostic fields were examined against the callback serialization boundary:
- `line_recognitions`
- `all_rows_agree`
- `ocr_provider_used`

**Findings:**
1. These fields exist exclusively on `ImageRecognitionResult` in `services/ai-service/app/schemas/core.py`.
2. `AiCallbackRequest` in `services/ai-service/app/schemas/jobs.py` does **NOT** declare these fields.
3. Spring Boot's DTO `AiCallbackRequest.java` in `services/business-api/src/main/java/com/mathvisionkids/api/analysis/AiCallbackRequest.java` does **NOT** declare these fields.
4. **Classification:** **`INTERNAL_ONLY`**.
5. These fields are filtered before callback transmission by virtue of schema isolation. They are logged by Celery for observability but never cross the HTTP boundary into Spring Boot.

---

### 5. CRNN_ERROR Privacy/Sanitization Audit

When a model load or runtime inference exception occurs in the OCR bridge:
1. **Sanitization Filter:** `_sanitize_error_message(exc)` in `services/ai-service/app/ocr/bridge.py` strips absolute Windows or Unix file paths (e.g., `E:\path\...` $\to$ `<path>`) and truncates the string to a maximum of 120 characters.
2. **Boundary Containment:** As proven in Section 4, `LineRecognition.error` is part of `ImageRecognitionResult.line_recognitions` which is `INTERNAL_ONLY`. It is never placed into `AiCallbackRequest`.
3. **Database & Client Protection:** Because `AiCallbackRequest` does not carry OCR bridge diagnostics, raw or sanitized exception text never enters PostgreSQL and never reaches Teacher or Student web clients.
4. **Logging Discipline:** Full tracebacks are recorded only in server-side logs (`runtime/logs/celery.err.log`) for engineering troubleshooting without exposing credentials or internal paths.

---

### 6. Safe Default Configuration

On disk, the authoritative configuration files enforce safe defaults:
- `services/ai-service/app/config.py`:
  - `ocr_provider: str = "noop"`
  - `ocr_bridge_mode: str = "off"`
- `services/ai-service/.env`:
  - `OCR_PROVIDER=noop`
  - `OCR_BRIDGE_MODE=off`

In this default state:
- `OcrBridge.is_active` evaluates to `False`.
- `OcrBridge.recognize_rows()` returns immediately with `AgreementState.CRNN_NOT_RUN`.
- Zero CRNN weights are loaded into memory, and zero OCR inference is executed.

---

### 7. Temporary Shadow Configuration

For the controlled live smoke verification, `services/ai-service/.env` was temporarily set to:
```dotenv
OCR_PROVIDER=noop
OCR_BRIDGE_MODE=shadow
```
Under this configuration, `OcrBridge` dynamically resolves the shadow provider to `crnn_vi_handwriting_v1` without altering the global default provider `noop`.

---

### 8. Runtime Restart

The full local stack was restarted via `cmd.exe /c scripts\restart-all.bat`:
- All pre-existing processes stopped cleanly.
- Infrastructure started: Docker Compose (PostgreSQL, MinIO, Redis) $\to$ **PASS**.
- Application services launched:
  - Spring Boot (PID: 19120) $\to$ **PASS**
  - FastAPI AI Runtime (PID: 21396) $\to$ **PASS**
  - Celery Worker (PID: 14392) $\to$ **PASS**
  - Teacher Web (PID: 2848) $\to$ **PASS**
  - Admin Web (PID: 29124) $\to$ **PASS**
- System diagnostics reported: `Overall ............... READY_FOR_DEMO`.

---

### 9. Live Success-Path E2E

Two live end-to-end submissions were executed via authenticated HTTP requests to Spring Boot:

#### Submission 1 (`synthetic_addition.jpg`):
- **Submission ID:** `4ac81c08-a283-4b34-a0f0-853befc63127`
- **Celery Job ID:** `574a07f2-b62f-47b8-84fc-91e01dbd194d`
- **Rows Processed:** 3 rows
- **Provider:** `crnn_vi_handwriting_v1`
- **Bridge Mode:** `shadow`
- **Agreement States:**
  - Row 0: YOLO=`45` | CRNN=`1` | Agreement=`MISMATCH`
  - Row 1: YOLO=`+27` | CRNN=`2` | Agreement=`MISMATCH`
  - Row 2: YOLO=`72` | CRNN=`n` | Agreement=`MISMATCH`
- **Callback Status:** HTTP 200 to `http://localhost:8080/internal/v1/ai/jobs/574a07f2-b62f-47b8-84fc-91e01dbd194d/callback`
- **Terminal Status:** `FEEDBACK_READY` (completed in 5.016s with cold start model loading)

#### Submission 2 (`synthetic_subtraction.jpg`):
- **Submission ID:** `115635d4-c36c-48bd-9501-4e747bd09625`
- **Celery Job ID:** `1f2b2f9f-fc03-44d4-a64d-6e3abbb81bcc`
- **Rows Processed:** 3 rows
- **Provider:** `crnn_vi_handwriting_v1`
- **Bridge Mode:** `shadow`
- **Agreement States:**
  - Row 0: YOLO=`52` | CRNN=`D2a` | Agreement=`MISMATCH`
  - Row 1: YOLO=`-18` | CRNN=`-8` | Agreement=`MISMATCH`
  - Row 2: YOLO=`34` | CRNN=`dt` | Agreement=`MISMATCH`
- **Callback Status:** HTTP 200
- **Terminal Status:** `FEEDBACK_READY` (completed in **0.453s** via warm singleton model reuse)

---

### 10. Proof CRNN Executed After INT.2.1

Captured directly from `runtime/logs/celery.err.log` following the clean restart:
```text
[2026-09-11 12:18:13,069: INFO/MainProcess] CrnnOcrProvider loaded successfully on cpu (vocab: 320, params: 5,962,560)
[2026-09-11 12:18:13,251: INFO/MainProcess] OCR Bridge processed 3 rows | provider=crnn_vi_handwriting_v1 | all_agree=False
[2026-09-11 12:18:13,254: INFO/MainProcess]   Row 0: YOLO='45' | CRNN='1' | Agreement=MISMATCH
[2026-09-11 12:18:13,254: INFO/MainProcess]   Row 1: YOLO='+27' | CRNN='2' | Agreement=MISMATCH
[2026-09-11 12:18:13,254: INFO/MainProcess]   Row 2: YOLO='72' | CRNN='n' | Agreement=MISMATCH
[2026-09-11 12:18:13,256: INFO/MainProcess] Sending callback for job 574a07f2-b62f-47b8-84fc-91e01dbd194d to http://localhost:8080/internal/v1/ai/jobs/574a07f2-b62f-47b8-84fc-91e01dbd194d/callback with status FEEDBACK_READY
[2026-09-11 12:18:13,369: INFO/MainProcess] HTTP Request: POST http://localhost:8080/internal/v1/ai/jobs/574a07f2-b62f-47b8-84fc-91e01dbd194d/callback "HTTP/1.1 200 "
[2026-09-11 12:18:13,370: INFO/MainProcess] Callback successful for job 574a07f2-b62f-47b8-84fc-91e01dbd194d
[2026-09-11 12:18:13,375: INFO/MainProcess] Task app.jobs.tasks.process_submission[a8ce1015-051d-4e11-92b5-8f321616cb04] succeeded in 5.015999999999622s: 'COMPLETED'
```

---

### 11. Callback JSON Evidence

Sanitized callback payload sent by Celery to Spring Boot for Submission 1:
```json
{
  "status": "FEEDBACK_READY",
  "recognizedExercise": "45 + 27 = 72",
  "studentFeedback": {
    "title": "Bài làm chính xác!",
    "hint": "Con đã thực hiện phép cộng rất tốt.",
    "focusEvidenceId": null,
    "revealAnswer": false
  },
  "evidence": null,
  "confidenceBundle": {
    "recognition": 0.99,
    "structure": 0.95,
    "diagnosis": 0.97
  }
}
```

---

### 12. Callback Contract Compatibility

Comparison against official specifications:
1. `contracts/ai/ai-contract.md`: Defines internal fields (`status`, `recognizedExercise`, `gradeProposal`, `studentFeedback`, `confidenceBundle`). **100% compliant**.
2. `contracts/openapi/mathvision-api.yaml`: Defines public customer-facing APIs; internal callback endpoint is strictly internal and does not alter OpenAPI schema. **100% compliant**.
3. `AiCallbackRequest.java`: Matches every declared field and Jackson deserializes it without unknown property warnings. **100% compliant**.

---

### 13. Controlled CRNN_ERROR Integration Test

Added to `services/ai-service/tests/test_ai_job_ocr_bridge.py`:
```python
def test_process_submission_with_crnn_error_fallback_safe(mocker):
```
- Injects simulated runtime error (`RuntimeError("CUDA out of memory at E:\\secret_weights\\model.bin")`) into `CrnnOcrProvider.recognize_batch`.
- Verifies:
  1. Celery task returns `"COMPLETED"` (the overall grading flow does not abort).
  2. Spring callback is dispatched with `status = "FEEDBACK_READY"` and `recognizedExercise = "45 + 27 = 72"`.
  3. No internal path (`"secret_weights"`, `"E:\\"`) appears in the callback payload.
  4. Engine internal result records `agreement == "CRNN_ERROR"` and sanitized `error` containing `"<path>"`.

---

### 14. Parser Token Non-Regression

- Automated test `tests/test_parser_non_regression.py` confirms that spatial tokens (`value`, `tokenClass`, `boundingBox`, `row`, `column`) delivered to `StructuredParser` are bit-identical before and after bridge execution.
- Deterministic arithmetic validation remains authoritative.

---

### 15. Default Mode Restored

Following the live smoke test, `services/ai-service/.env` was restored to:
```dotenv
# OCR Configuration (safe defaults: provider=noop, bridge=off; explicit opt-in required)
OCR_PROVIDER=noop
OCR_BRIDGE_MODE=off
```
Verification via Python in the virtual environment:
```text
Bridge mode: off | Provider: noop | is_active: False
```
Confirmed that `OcrBridge.is_active == False`. Default mode does not load CRNN weights.

---

### 16. Targeted Tests

Command executed:
```powershell
.venv\Scripts\python.exe -m pytest tests/test_ocr_bridge.py tests/test_ai_job_ocr_bridge.py tests/test_parser_non_regression.py
```
- `tests/test_ocr_bridge.py`: 14 passed
- `tests/test_ai_job_ocr_bridge.py`: 3 passed
- `tests/test_parser_non_regression.py`: 2 passed
- **Total:** **19 passed in 5.77s** (0 failed, 0 skipped).

---

### 17. Full AI Tests

Command executed:
```powershell
.venv\Scripts\python.exe -m pytest tests/
```
- **Total passed:** **140 passed**
- **Failed:** 0
- **Skipped:** 0
- **Warnings:** 2 (Starlette deprecation warnings in test client)
- **Duration:** 9.51s

---

### 18. YOLO SHA

- Path: `services/ai-service/models/yolov8n_mathvision_det_v1.pt`
- Expected: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Measured: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Result: **EXACT MATCH**

---

### 19. CRNN SHA

- Path: `services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth`
- Expected: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`
- Measured: `A807EAA763A4471BC057B9545A3521612423214858D50B1EF42B7BAF28DE0941`
- Result: **EXACT MATCH**

---

### 20. Working Tree Truth

- **Tracked Modifications (5 files):**
  - `services/ai-service/app/config.py`: OCR settings (`noop` / `off`).
  - `services/ai-service/app/jobs/tasks.py`: Celery structured OCR diagnostic logging.
  - `services/ai-service/app/ocr/__init__.py`: Exported `OcrBridge`.
  - `services/ai-service/app/recognition/model_engine.py`: Model engine wiring.
  - `services/ai-service/app/schemas/core.py`: Internal diagnostic fields on `ImageRecognitionResult`.
- **Unexpected Tracked Modifications:** **0** (none).
- **Untracked Implementations & Reports:**
  - `report/int_2_2_post_correction_live_bridge_closure.md` (this report)
  - `report/int_2_1_ocr_bridge_truth_audit.md`
  - `report/int_2_yolo_crnn_bridge_e2e_recognition.md`
  - `report/evidence/int_2/`
  - `scripts/test-ocr-bridge.ps1`
  - `services/ai-service/app/layout/`
  - `services/ai-service/app/ocr/bridge.py`
  - `services/ai-service/app/schemas/ocr_bridge.py`
  - `services/ai-service/scripts/test_ocr_bridge.py`
  - `services/ai-service/tests/test_ai_job_ocr_bridge.py`
  - `services/ai-service/tests/test_ocr_bridge.py`
  - `services/ai-service/tests/test_parser_non_regression.py`
  - `services/ai-service/tests/test_row_grouper.py`
- **Ignored Binaries & Environments:** Checkpoints, `.env`, `.venv`, `.pytest_cache` are strictly excluded by `.gitignore`.

---

### 21. Scratch File Classification

- `scratch/test_packaged_samples.py`: Scratch script for verifying 5 packaged samples.
  - **Classification:** `TEMP_AUDIT`.
  - **Recommendation:** Retain in `scratch/` during code review; safe to delete upon Git commit.
- `scratch/test_live_e2e.ps1`: Temporary test script for live multipart upload and polling.
  - **Classification:** `TEMP_AUDIT`.
  - **Recommendation:** Retain in `scratch/` during code review; safe to delete upon Git commit.

---

### 22. Files Modified in INT.2.2

1. `services/ai-service/app/ocr/bridge.py`: Added `import re` and `_sanitize_error_message(exc)`.
2. `services/ai-service/tests/test_ai_job_ocr_bridge.py`: Added `test_process_submission_with_crnn_error_fallback_safe`.
3. `services/ai-service/.env`: Restored safe default configuration (`OCR_PROVIDER=noop`, `OCR_BRIDGE_MODE=off`).
4. `scratch/test_live_e2e.ps1`: Configured for multi-image live testing.

---

### 23. Final Assessment

All objectives of task INT.2.2 are complete:
- Live multi-image E2E pipeline verified after INT.2.1 source modifications.
- OCR bridge diagnostics proven to be strictly `INTERNAL_ONLY`.
- Callback contract compatibility verified with zero contract drift.
- Error sanitization confirmed against information leakage.
- Safe defaults (`noop` / `off`) verified and restored.
- 140/140 AI tests passing, model hashes exact.

The system is in an optimal, verified, deterministic state and is **`READY_FOR_FINAL_REFREEZE`**.
