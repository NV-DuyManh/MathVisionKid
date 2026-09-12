# SYSTEM.AUDIT.1.2.1 — Final Two-Gap Closure: Storage-Verified Eligibility + Local AI Port Hardening

**Date:** 2026-09-12  
**Environment:** Local Windows (Development / Docker Engine / Native Spring Boot & FastAPI)  
**Task Type:** Micro-Closure of SYSTEM.AUDIT.1.2  
**Commit Status:** None (Local only)  
**Push Status:** None  
**Training Commands:** 0  
**New Checkpoints:** NONE  

---

## 1. Executive Summary

`SYSTEM.AUDIT.1.2.1` delivers targeted micro-closure for the final two remaining technical gaps identified in `SYSTEM.AUDIT.1.2`:

1. **Storage-Verified Training Eligibility (Elimination of DB False Positives):**
   Previously, OCR feedback samples for both Pilot 1 (`OcrPilotService`) and Pilot 2 (`OcrMultilineService`) evaluated training eligibility based solely on metadata (non-null object key string and 64-character SHA string format). Physical existence in MinIO and byte-level SHA-256 equivalence were deferred to downstream dataset export. This gap created the risk of database-level false positive eligibility.  
   **Resolution:** Implemented `OcrStorageVerifier` and added `loadBytes()` to `ObjectStorageService` (backed by both `MinioObjectStorageService` and `LocalFileObjectStorageService`). Now, both Pilot 1 and Pilot 2 verify that the image or crop actually exists in MinIO, retrieve its bytes, compute its SHA-256 hash, and assert exact equality with the stored DB SHA before granting `training_eligible = true`. In the event of a missing object, unreadable object, or SHA mismatch, the feedback payload (verdict, raw text, timestamp) is preserved intact, `training_eligible` is set to `false`, no HTTP 500 is thrown, and a sanitized warning is logged without leaking PII or raw object bytes.

2. **FastAPI Local Bind Hardening (LAN Exposure Elimination):**
   Previously, FastAPI bound by default to `0.0.0.0:8000` while utilizing the local development fallback internal key (`secret-key-default`). While Spring Boot (8080) requires `0.0.0.0` so mobile devices on the local Wi-Fi LAN can connect to public endpoints, the internal AI service is strictly a backend subsystem called only by Spring Boot (`http://localhost:8000`) and Celery.  
   **Resolution:** Hardened `app/config.py` default host to loopback `127.0.0.1` (configurable via `AI_HOST` / `HOST`), updated `.env` and `scripts/start-all.ps1`, terminated the old `0.0.0.0:8000` listener, and verified that FastAPI listens exclusively on `127.0.0.1:8000`. Direct unauthenticated or bad-key calls return HTTP 401, while Spring Boot continues communicating seamlessly over loopback.

All automated and live integration test suites passed with zero regressions:
- Spring Boot Unit & Integration Tests: **111 / 111 PASSED**
- AI Service Pytest Suite: **154 / 154 PASSED**
- Student Mobile: **`npx tsc --noEmit` (0 errors) & `npm run lint` (0 errors, 0 warnings)**
- Live E2E Verification Suite (`scratch/test_system_audit_1_2_1_closure.py`): **ALL CHECKS PASSED**
- Default TEST Dataset Export: **0 samples exported**

---

## 2. Repository State

| Subsystem | Service / App | Host / Port | Bind Status | Security Status |
|---|---|---|---|---|
| Business API | Spring Boot 3.3.4 | `0.0.0.0:8080` (or `::8080`) | **Preserved for LAN / Phone** | JWT Auth + Fail-Closed Privacy & Domain Gates |
| AI Service | FastAPI 0.115 / Uvicorn | `127.0.0.1:8000` | **Hardened to Loopback Only** | `X-Internal-API-Key` required on internal endpoints (401 on missing/wrong key) |
| Async Worker | Celery 5.4.0 (solo pool) | Native Worker Process | Connected to Redis 6379 | Internal tasks queue + Spring callback |
| Database | PostgreSQL 16 (Docker) | `localhost:5432` | Containerized | Flyway migrations V1-V9 consistent |
| Object Storage | MinIO S3 (Docker) | `localhost:9000` | Containerized | S3 API + byte-retrieval verification |
| Mobile Client | Expo 57 / React Native | Local / Expo Dev Server | Phone connects to Spring 8080 | Verified fail-closed mobile privacy gates |

---

## 3. Pilot 1 Storage-Verified Eligibility

In `OcrPilotService.java`, the method `recordFeedback()` was updated to integrate `OcrStorageVerifier`.

### Eligibility Formula
A sample is marked `training_eligible = true` if and only if:
1. `trial.isPrivacyConfirmed() == true`
2. `trial.isTestData() == false`
3. `domain == "HANDWRITING_TEXT"`
4. `verdict` is `CORRECT` or `CORRECTED`
5. `verified_text_raw` is non-null and non-empty after trimming
6. If `CORRECT`: `verified_text_raw` equals `predicted_text` exactly
7. Image object key is non-null and non-empty
8. `line_image_sha256` string length is exactly 64
9. **`ocrStorageVerifier.verifyStorageIntegrity(key, sha256)` returns `true`** (loads raw object bytes from MinIO, computes SHA-256 over retrieved bytes, verifies exact string equality).

### Live Test Proof (Test 2.1)
- Single-line trial uploaded with `privacyConfirmed=true`, `isTestData=false`.
- Verdict submitted: `CORRECT`.
- Result: `res.trainingEligible = true`, DB `ocr_trials.training_eligible = true`.
- Status: **PASS**.

---

## 4. Pilot 2 Storage-Verified Eligibility

In `OcrMultilineService.java`, the method `recordLineFeedback()` was updated to integrate `OcrStorageVerifier`.

### Eligibility Formula
A multi-line candidate line is marked `training_eligible = true` if and only if:
1. Parent trial `privacyConfirmed == true`
2. Parent trial `isTestData == false`
3. Parent trial `domain == "HANDWRITING_TEXT"`
4. Parent trial `status == "COMPLETED"`
5. `verdict` is `CORRECT` or `CORRECTED`
6. `line.verified_text_raw` is non-null and non-empty after trimming
7. If `CORRECT`: `line.verified_text_raw` equals `line.predicted_text` exactly
8. Line crop object key is non-null and non-empty
9. `line_image_sha256` string length is exactly 64
10. **`ocrStorageVerifier.verifyStorageIntegrity(key, sha256)` returns `true`** (loads raw line crop bytes from MinIO, computes SHA-256 over retrieved crop bytes, verifies exact string equality).

### Live Test Proof (Test 3.1)
- Multi-line page detected (3 lines).
- Multi-line trial created with `privacyConfirmed=true`, parent `isTestData=false`.
- Line 1 verdict submitted: `CORRECT` with non-empty predicted text.
- Result: `res.trainingEligible = true`, DB `ocr_multiline_lines.training_eligible = true`.
- Status: **PASS**.

---

## 5. Missing Object Behavior

When an object key does not exist in MinIO (e.g., storage corruption, key misdirection, or deleted object):

### Implementation
- `OcrStorageVerifier` calls `objectStorageService.loadBytes(objectKey)`.
- In `MinioObjectStorageService`: `ErrorResponseException` (such as `NoSuchKey`), `IOException`, or general storage exceptions are caught.
- A sanitized warning is logged:
  ```
  WARN OcrStorageVerifier - Storage verification failed for key '...': Object not found in storage bucket
  ```
- `OcrStorageVerifier.verifyStorageIntegrity()` returns `false`.
- The service sets `trainingEligible = false`.
- The human feedback is saved normally to PostgreSQL: `verdict`, `verifiedTextRaw`, `verifiedTextNormalized`, and `feedbackAt` are fully recorded.
- HTTP 200 OK is returned to the client (no HTTP 500 error).

### Live Test Proof
- **Pilot 1 (Test 2.2):**
  - Trial image object key pointed to `'ocr-trials/nonexistent-missing-object.jpg'`.
  - Feedback submitted: `CORRECT`.
  - HTTP Status: `200 OK`.
  - Response: `trainingEligible: false`.
  - DB record: `verdict = 'CORRECT'`, `training_eligible = false`, `verified_text_raw = 'Đ'`.
  - Status: **PASS**.
- **Pilot 2 (Test 3.2):**
  - Line 2 object key pointed to `'ocr-multiline-trials/missing-crop.jpg'`.
  - Feedback submitted: `CORRECTED` with text `"Dòng chữ kiểm tra sửa lỗi"`.
  - HTTP Status: `200 OK`.
  - Response: `trainingEligible: false`.
  - DB record: `verdict = 'CORRECTED'`, `training_eligible = false`, `verified_text_raw = 'Dòng chữ kiểm tra sửa lỗi'`.
  - Status: **PASS**.

---

## 6. SHA Mismatch Behavior

When an object exists in MinIO but its byte-level SHA-256 does not match the database `line_image_sha256` (e.g., bit rot, tampering, or incorrect hash record):

### Implementation
- `OcrStorageVerifier` retrieves actual bytes from MinIO and calculates `MessageDigest.getInstance("SHA-256")`.
- Compares computed hex string to `expectedSha256` using case-insensitive exact match.
- If hashes do not match:
  - Logs sanitized warning:
    ```
    WARN OcrStorageVerifier - Storage verification SHA-256 mismatch for key '...': expected [expectedSha256], computed [actualSha256]
    ```
  - Returns `false`.
- Service persists human feedback normally, sets `trainingEligible = false`, and returns HTTP 200 OK.

### Live Test Proof
- **Pilot 1 (Test 2.3):**
  - Trial image SHA set to 64 `'a'` characters (`"a"*64`). Real MinIO object exists.
  - Feedback submitted: `CORRECT`.
  - HTTP Status: `200 OK`.
  - Response: `trainingEligible: false`.
  - DB record: `verdict = 'CORRECT'`, `training_eligible = false`.
  - Status: **PASS**.
- **Pilot 2 (Test 3.3):**
  - Line 3 crop SHA set to 64 `'a'` characters. Real MinIO crop exists.
  - Feedback submitted: `CORRECT`.
  - HTTP Status: `200 OK`.
  - Response: `trainingEligible: false`.
  - DB record: `verdict = 'CORRECT'`, `training_eligible = false`.
  - Status: **PASS**.

---

## 7. Exact Raw Equality

Both Pilot 1 and Pilot 2 guard against contradiction between `CORRECT` verdicts and predicted text.

### Implementation
- In both `OcrPilotService.java` and `OcrMultilineService.java`:
  ```java
  if ("CORRECT".equals(verdictUpper)) {
      if (request.getVerifiedText() != null && !request.getVerifiedText().isEmpty()) {
          if (!request.getVerifiedText().equals(trial.getPredictedText())) {
              throw new ApiException(
                      "DATA_INTEGRITY_ERROR",
                      "CORRECT verdict cannot contradict predicted text. If text differs, use CORRECTED verdict.",
                      HttpStatus.BAD_REQUEST
              );
          }
      }
      trial.setVerifiedTextRaw(trial.getPredictedText());
  ...
  ```
- If a client submits `verdict: "CORRECT"` with a `verifiedText` string that differs from `predictedText` by whitespace (e.g. trailing space), the server rejects the request with HTTP 400 `DATA_INTEGRITY_ERROR`.

### Live Test Proof
- **Pilot 1 (Test 2.7):**
  - Submitted `verdict: "CORRECT"`, `verifiedText: predictedText + "   "`.
  - Response: HTTP 400 Bad Request, Error Code `DATA_INTEGRITY_ERROR`.
  - Status: **PASS**.
- **Pilot 2 (Test 3.7):**
  - Submitted `verdict: "CORRECT"`, `verifiedText: predictedText + "   "`.
  - Response: HTTP 400 Bad Request, Error Code `DATA_INTEGRITY_ERROR`.
  - Status: **PASS**.

---

## 8. FastAPI Bind Before/After

### Before
- Bind Address: `0.0.0.0:8000` (listening across all network interfaces, exposing AI internal endpoints to local Wi-Fi LAN).
- Configuration: Default `host = "0.0.0.0"` in `app/config.py`.

### After
- Bind Address: `127.0.0.1:8000` (listening strictly on loopback interface).
- Configuration:
  - `services/ai-service/app/config.py`:
    ```python
    host: str = Field(default="127.0.0.1", validation_alias=AliasChoices("AI_HOST", "HOST", "host"))
    ```
  - `services/ai-service/.env`: `HOST=127.0.0.1`
  - `.env`: `HOST=127.0.0.1`
  - `scripts/start-all.ps1`: `--host 127.0.0.1 --port 8000`
- Active TCP Socket Proof:
  ```powershell
  Get-NetTCPConnection -LocalPort 8080,8000 | Select-Object LocalAddress,LocalPort,OwningProcess,State
  ```
  Output:
  ```
  LocalAddress LocalPort OwningProcess  State
  ------------ --------- -------------  -----
  ::                8080         34260 Listen
  127.0.0.1         8000         35328 Listen
  ```
  - Port 8080 (Spring Boot) remains open on `0.0.0.0` / `::` for student phone connectivity.
  - Port 8000 (FastAPI) is strictly bound to `127.0.0.1`.

---

## 9. Internal Key Classification

- **Key Value:** `secret-key-default`
- **Classification:** `DEV_DEFAULT_LOCAL_RISK`
- **Operational Status:**
  - Valid only for local single-node development and automated integration testing.
  - Because FastAPI is now bound strictly to `127.0.0.1`, `secret-key-default` cannot be reached or abused by any external client or mobile device on the LAN.
  - Production deployments require overriding `INTERNAL_API_KEY` via environment variable to a cryptographically secure token.

---

## 10. Live Network Regression

Direct live network regression tests verified all authentication boundaries and communication paths:

| Test Target | Request / Client | Expected Status | Actual Status | Result |
|---|---|---|---|---|
| `GET /health` | Public HTTP request | 200 OK | 200 OK | **PASS** |
| `POST /internal/v1/ocr/detect-lines` | No `X-Internal-API-Key` | 401 Unauthorized | 401 Unauthorized | **PASS** |
| `POST /internal/v1/ocr/detect-lines` | `X-Internal-API-Key: wrong-key` | 401 Unauthorized | 401 Unauthorized | **PASS** |
| `POST /internal/v1/ocr/detect-lines` | `X-Internal-API-Key: secret-key-default` | 200 OK | 200 OK | **PASS** |
| Spring Boot Auth | Student login (`/api/v1/auth/login`) | 200 OK | 200 OK | **PASS** |
| Spring -> FastAPI (OCR Recognize) | `POST /api/v1/ocr/trials` (Pilot 1) | 201 Created | 201 Created | **PASS** |
| Spring -> FastAPI (OCR Detect) | `POST /api/v1/ocr/multiline/detect` (Pilot 2) | 200 OK | 200 OK | **PASS** |
| Spring -> FastAPI (Job Enqueue) | `POST /api/v1/student/submissions` | 202 Accepted | 202 Accepted | **PASS** |
| FastAPI -> Celery -> Spring Callback | Cross-process arithmetic pipeline | `REVIEW_REQUIRED` / `FEEDBACK_READY` in DB | `REVIEW_REQUIRED` in DB | **PASS** |

---

## 11. Full Regression Tests

### 11.1 Spring Boot (Business API)
- Command: `./gradlew.bat test --rerun-tasks`
- Scope: ContextLoads, Controller tests, RBAC tests, OcrStorageVerifier unit tests (7 tests), GlobalExceptionHandler tests, BatchService tests.
- Results: **111 tests completed, 0 failures, 0 skipped** (`BUILD SUCCESSFUL in 32s`).

### 11.2 AI Service Pytest
- Command: `& "E:\MathVisionKid\services\ai-service\.venv\Scripts\python.exe" -m pytest tests/`
- Scope: OCR endpoints, CRNN adapters, YOLO adapters, parser, evaluation harness, Celery tasks, callback retries.
- Results: **154 passed in 8.33s** (100% success).

### 11.3 Student Mobile (React Native / Expo)
- Command: `npx tsc --noEmit; npm run lint`
- Scope: TypeScript type checking and ESLint rules.
- Results: **0 errors, 0 warnings** (100% success).

### 11.4 Live Verification Suite
- Script: `scratch/test_system_audit_1_2_1_closure.py`
- Executed:
  - 4 Network & Bind Hardening checks
  - 7 Pilot 1 Eligibility & Storage Integrity checks
  - 7 Pilot 2 Eligibility & Storage Integrity checks
  - 1 Cross-Process Arithmetic E2E check
  - 1 Default Dataset Export verification
- Results: **ALL 20 LIVE CHECKS PASSED**.

### 11.5 Dataset Export Safe Mode Verification
- Command: `python scripts/export_ocr_feedback_dataset.py --out-dir scratch/export_verified_closure`
- Results:
  ```
  [EXPORT] Evaluating 0 candidate verified OCR trials...
  [EXPORT] Qualified 0 trustworthy handwriting samples.
  [EXPORT] Successfully generated dataset package: ...\ocr_feedback_export_20260912_120813.zip
  ```
- Samples exported: **0 rows** (Guaranteed zero test/polluted samples).

---

## 12. Files Modified

| File | Subsystem | Nature of Change |
|---|---|---|
| `services/business-api/.../ObjectStorageService.java` | Storage Interface | Added `byte[] loadBytes(String filePath) throws IOException;` |
| `services/business-api/.../MinioObjectStorageService.java` | Storage Implementation | Implemented `loadBytes()` via MinIO `getObject().readAllBytes()` |
| `services/business-api/.../LocalFileObjectStorageService.java` | Storage Implementation | Implemented `loadBytes()` via `Files.readAllBytes(targetPath)` |
| `services/business-api/.../ocr/OcrStorageVerifier.java` | OCR Storage Component | **[NEW]** Storage integrity helper verifying object existence, bytes retrieval, SHA-256 calculation & matching |
| `services/business-api/.../ocr/OcrPilotService.java` | OCR Pilot 1 Service | Injected `OcrStorageVerifier`; added storage integrity check to eligibility formula |
| `services/business-api/.../ocr/multiline/OcrMultilineService.java` | OCR Pilot 2 Service | Injected `OcrStorageVerifier`; added storage integrity check to line eligibility formula |
| `services/business-api/.../ocr/OcrStorageVerifierTest.java` | Unit Test | **[NEW]** 7 comprehensive unit tests for storage verifier |
| `services/business-api/.../ocr/OcrTrialControllerTest.java` | Integration Test | Added `@MockBean OcrStorageVerifier` and storage failure test case |
| `services/business-api/.../ocr/multiline/OcrMultilineControllerTest.java` | Integration Test | Added `@MockBean OcrStorageVerifier` and line storage failure test case |
| `services/ai-service/app/config.py` | AI Config | Hardened default host from `0.0.0.0` to `127.0.0.1` |
| `services/ai-service/.env` | AI Environment | Set `HOST=127.0.0.1` |
| `.env` | Root Environment | Set `HOST=127.0.0.1` |
| `scripts/start-all.ps1` | Startup Script | Updated uvicorn startup command to `--host 127.0.0.1` |
| `scratch/test_system_audit_1_2_1_closure.py` | Test Tooling | **[NEW]** End-to-end verification script for all two-gap closure items |

---

## 13. Remaining Known Limitations

1. **Physical Android Device Verification (`OWNER_TEST_REQUIRED`):**
   Automated integration and mock mobile checks pass completely. However, real-world camera performance on physical Android hardware (real camera auto-focus, diverse ambient lighting, handwriting angles) requires manual testing by the project owner. A step-by-step guide is available in `report/evidence/mobile_physical_1/PHONE_TEST_QUICK_GUIDE_VI.md`.
2. **Local Development Key (`DEV_DEFAULT_LOCAL_RISK`):**
   `INTERNAL_API_KEY` defaults to `secret-key-default` for out-of-the-box local developer convenience. This is safe for local environments because port 8000 is now bound strictly to `127.0.0.1`, but must be overridden in staging and production.
3. **Owner Feedback Collection Mode (`DEV_TEST` vs `REAL_FEEDBACK`):**
   The server-controlled default mode remains `DEV_TEST` (or `TEST`), preventing accidental dataset contamination. Before collecting authentic handwriting samples from children, the owner must explicitly enable `OCR_PILOT_COLLECTION_MODE=REAL_FEEDBACK`.

---

## 14. Final Verdict

`SYSTEM.AUDIT.1.2.1` has closed both remaining gaps completely and cleanly:
- Database false positives for training eligibility are eradicated: MinIO object existence and byte-level SHA-256 equivalence are actively verified in both Pilot 1 and Pilot 2 prior to setting `training_eligible = true`.
- Human corrections are preserved even during storage degradation without generating 500 errors.
- Internal AI port 8000 LAN exposure is eliminated through loopback binding (`127.0.0.1`), while preserving phone access to Spring Boot (`0.0.0.0:8080`).
- All 111 Spring Boot tests, 154 AI Service tests, mobile checks, and live integration tests pass without regression.

**Engineering Readiness:** **GREEN**  
**Final Status:** **PASS**
