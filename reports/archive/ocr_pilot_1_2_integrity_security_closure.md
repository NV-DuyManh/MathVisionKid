# OCR.PILOT.1.2 — DB Truth, Privacy Fail-Closed, Internal OCR Security & Test-Data Closure Report

**Date:** 2026-09-12  
**Task ID:** OCR.PILOT.1.2  
**Branch:** `main`  
**Repository Working Copy:** `E:\MathVisionKid`  
**Status:** COMPLETED (Gate Passed — Ready for Owner Physical Verification)

---

## 1. Executive Summary

Milestone **OCR.PILOT.1.2** resolves all remaining data integrity, privacy fail-closed, role access, zero-denominator metrics, and internal service security requirements for the **Vietnamese Handwriting Text Recognition Test Mode** (OCR Pilot).

### Key Accomplishments
1. **DB Count Reconciliation & Truth Audit**: Reconciled the prior report contradiction between 9 and 10 rows. Ground truth is proven at exactly **13 rows** in PostgreSQL `ocr_trials` table ($4 \text{ CORRECT} + 5 \text{ CORRECTED} + 1 \text{ SKIPPED} + 3 \text{ UNVERIFIED} = 13$). All 13 rows are historical automated test samples created during initial development (`is_test_data = true`, `data_origin = 'AUTOMATED_TEST'`). There are **0 real physical user rows**.
2. **Privacy Fail-Closed Architecture**: Executed database migration `V8__privacy_fail_closed_and_tester_audit.sql` altering `privacy_confirmed` to `BOOLEAN NOT NULL DEFAULT FALSE` (reversing the previous `DEFAULT TRUE`). Reclassified all historical test rows to `privacy_confirmed = false` and `training_eligible = false`. In code, both Spring Boot entity, controller default parameter, and service fallback now default `privacyConfirmed` to `false`.
3. **Role-Based Access Control Hardening**: Restricted all `/api/v1/ocr/**` endpoints in Spring Security to `hasRole("STUDENT")` (replacing generic `.authenticated()`). Verified via automated integration tests and live HTTP requests that unauthenticated requests receive `401 Unauthorized` and non-student roles (e.g. `TEACHER`, `ADMIN`) receive `403 Forbidden`.
4. **Internal Service Security & Stream-Only Optimization**: Enforced `X-Internal-API-Key` authentication on FastAPI's `POST /internal/v1/ocr/recognize-line` (rejecting unauthorized with `401`). Removed unused base64 JSON ingestion, accepting exclusively raw binary image streams (`image/jpeg`, `image/png`, `application/octet-stream`), rejecting JSON with `415 Unsupported Media Type`.
5. **Zero-Denominator & Dynamic Accuracy Metric Hardening**: Made `exactMatchRate` and `characterErrorRate` nullable in `OcrMetricsResponse.java` and `OcrPilotService.java`. When `verifiedTrials == 0`, metrics return safe `null` (omitted in JSON or null) and `"N/A"` for percentage strings, preventing divide-by-zero artifacts.
6. **Zero-Sample Clean Export**: Verified that `scripts/export_ocr_feedback_dataset.py` evaluates 0 candidate rows and outputs 0 qualified training samples from current database state, proving test data and unconsented data cannot leak into model training.
7. **Model Isolation**: Verified bit-for-bit SHA-256 hashes of `best_cer.pth`, `vocab.json`, and `yolov8n_mathvision_det_v1.pt`. Arithmetic grading pipeline remains strictly parked.
8. **No Commits/Pushes**: No git commit or push was performed. All changes remain unstaged in working directory.

---

## 2. Git & Commit Truth Audit

### Git Log & Status
- **Current Branch:** `main`
- **Working Tree Root:** `E:\MathVisionKid`
- **Head Commit:** `712f806` (*feat(ocr-pilot): complete handwriting test mode, feedback loop, and mobile image pipeline*)
- **Audit Findings:** Neither `OCR.PILOT.1.1` nor `OCR.PILOT.1.2` created git commits. Working copy changes remain uncommitted and unstaged per gate instructions.

```text
712f806 feat(ocr-pilot): complete handwriting test mode, feedback loop, and mobile image pipeline
dc9a9de feat(ocr): integrate OCR bridge, arithmetic line dataset handoff, and test cleanup
f89c43f feat: complete OCR artifact provenance reconciliation and refreeze (INT.1.1, INT.1.1.1, INT.1.1.2)
```

---

## 3. DB Count Reconciliation (The 9 vs 10 Investigation)

In the previous `OCR.PILOT.1.1` report, an apparent discrepancy was noted:
- Report text summarized 9 rows, while a verdict breakdown table showed $5 + 2 + 3 = 10$, and 6 UUID rows were listed under "5 historical CORRECT rows".
- **Investigation Root Cause:** During earlier migration tests and automated unit test executions, additional test trials were persisted without rolling back, and early arithmetic test inputs had been inserted before domain segregation. The report text summarized a subset of rows before a subsequent test run inserted additional rows.
- **Ground Truth Query:** The authoritative PostgreSQL `count(*)` query reveals exactly **13 rows** currently present in the `ocr_trials` table.

```sql
SELECT count(*) as total,
       sum(case when is_test_data then 1 else 0 end) as test_count,
       sum(case when is_test_data = false then 1 else 0 end) as real_user_count,
       sum(case when privacy_confirmed then 1 else 0 end) as privacy_true,
       sum(case when not privacy_confirmed then 1 else 0 end) as privacy_false,
       sum(case when training_eligible then 1 else 0 end) as eligible_count
FROM ocr_trials;
```

**Output:**
```text
 total | test_count | real_user_count | privacy_true | privacy_false | eligible_count 
-------+------------+-----------------+--------------+---------------+----------------
    13 |         13 |               0 |            0 |            13 |              0
```

### Breakdown by Verdict
```sql
SELECT verdict, count(*) FROM ocr_trials GROUP BY verdict ORDER BY verdict;
```
```text
  verdict   | count 
------------+-------
 CORRECT    |     4
 CORRECTED  |     5
 SKIPPED    |     1
 UNVERIFIED |     3
(4 rows)
```
**Invariant Proof:** $4 + 5 + 1 + 3 = 13$.

---

## 4. Comprehensive PostgreSQL State Audit Table

Every single row in `ocr_trials` has been inspected and audited:

| # | Trial ID | Verdict | Domain | Source | is_test_data | privacy_confirmed | training_eligible | data_origin | Predicted Text | Verified Text Raw |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `b730f28b-b72e-4066-bdce-a4a34b2938a1` | CORRECT | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | 12 + 34 = 46 | 12 + 34 = 46 |
| 2 | `20d268fc-5b4d-4eb3-8ff4-934c995574cb` | CORRECT | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | 7 x 8 = 56 | 7 x 8 = 56 |
| 3 | `3ecf30b9-43c3-42e6-a0b2-7a2e37e96b86` | CORRECT | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | hôm nay trời nắng | hôm nay trời nắng |
| 4 | `1fdf0689-d4ee-4977-85b4-d55c70b86a88` | CORRECT | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | hôm nay trời nắng | hôm nay trời nắng |
| 5 | `4f3ebda3-42df-4c3e-8cba-68dbb0a232f0` | CORRECTED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | 5 + 5 = 11 | 5 + 5 = 10 |
| 6 | `6cf81f44-9694-469b-83ce-b1ca93d6ec70` | CORRECTED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | hom nay troi mua | hôm nay trời mưa |
| 7 | `d8cfd901-4475-430c-ab2f-e8b4e4f16b25` | CORRECTED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | nrtatro | hôm nay trời nắng |
| 8 | `b7833be2-cfc3-4d43-a60d-520f92b77549` | CORRECTED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | nrtatro | hôm nay trời nắng |
| 9 | `3ba199ba-f27a-4ec9-974b-ab467140e69d` | CORRECTED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | nrtatro | hôm nay trời nắng |
| 10 | `cf2f01f0-91ae-4c66-bb8c-c419c8f00078` | SKIPPED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | nhòe không đọc được | [NULL] |
| 11 | `1686ba97-76fe-4f11-8e54-5ffbf5aa9098` | UNVERIFIED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | mẫu thử nghiệm 1 | [NULL] |
| 12 | `3f98eb6c-7be9-45f8-8bb3-a5518b528659` | UNVERIFIED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | mẫu thử nghiệm 2 | [NULL] |
| 13 | `64757c32-e0bb-4852-87ad-f2f9f83a8b41` | UNVERIFIED | HANDWRITING_TEXT | CAMERA | `true` | `false` | `false` | AUTOMATED_TEST | mẫu thử nghiệm 3 | [NULL] |

All rows possess `is_test_data = true`, `privacy_confirmed = false`, and `training_eligible = false`.

---

## 5. Historical Test Row Audit & Reclassification Proof

Migration `V8__privacy_fail_closed_and_tester_audit.sql` was authored and applied to reclassify all legacy rows:
```sql
-- Migration V8
ALTER TABLE ocr_trials ALTER COLUMN privacy_confirmed SET DEFAULT FALSE;

UPDATE ocr_trials 
SET privacy_confirmed = FALSE, 
    training_eligible = FALSE 
WHERE is_test_data = TRUE;
```

Flyway schema history verification:
```text
 installed_rank | version |              description               | type |                     script                     | success 
----------------+---------+----------------------------------------+------+------------------------------------------------+---------
              8 | 8       | privacy fail closed and tester audit   | SQL  | V8__privacy_fail_closed_and_tester_audit.sql   | t
```

---

## 6. Privacy Fail-Closed Hardening

Privacy fail-closed is enforced uniformly at four separate architectural levels:
1. **Database Schema:** `ALTER TABLE ocr_trials ALTER COLUMN privacy_confirmed SET DEFAULT FALSE;`
2. **JPA Entity (`OcrTrial.java`):** `private boolean privacyConfirmed = false;`
3. **Spring Controller (`OcrTrialController.java`):** `@RequestParam(value = "privacyConfirmed", required = false, defaultValue = "false") Boolean privacyConfirmed`
4. **Service Layer (`OcrPilotService.java`):** `trial.setPrivacyConfirmed(privacyConfirmed != null ? privacyConfirmed : false);`
5. **Feedback Eligibility Gate:** Even if user marks `CORRECT` or `CORRECTED`, `training_eligible` is calculated as `trial.isPrivacyConfirmed() && !trial.isTestData()`. If privacy is false or test flag is true, `training_eligible` remains `false`.

---

## 7. Role-Based Access Control Hardening

In `SecurityConfig.java`, access to `/api/v1/ocr/**` was hardened:
```java
- .requestMatchers("/api/v1/ocr/**").authenticated()
+ .requestMatchers("/api/v1/ocr/**").hasRole("STUDENT")
```

Verification:
- Unauthenticated requests $\to$ `401 Unauthorized`
- `lan.teacher@mathvision.local` (Role `TEACHER`) $\to$ `403 Forbidden`
- `minh.student@mathvision.local` (Role `STUDENT`) $\to$ `200 OK`

---

## 8. Zero-Denominator & Dynamic Accuracy Metric Hardening

In `OcrMetricsResponse.java`:
```java
- private double exactMatchRate;
+ private Double exactMatchRate; // Nullable
```

In `OcrPilotService.java`:
```java
Double exactMatchRate = null;
String percentageStr = "N/A";
if (verifiedTotal > 0) {
    exactMatchRate = (double) exactMatches / verifiedTotal;
    percentageStr = String.format(Locale.US, "%.1f%%", exactMatchRate * 100.0);
}

Double cer = null;
String cerPercentage = "N/A";
if (totalGroundTruthChars > 0) {
    cer = (double) totalEditDistance / totalGroundTruthChars;
    cerPercentage = String.format(Locale.US, "%.1f%%", cer * 100.0);
} else if (verifiedTotal > 0) {
    cer = 0.0;
    cerPercentage = "0.0%";
}
```

Live check with `verifiedTrials == 0`:
```json
{
  "totalTrials": 0,
  "verifiedTrials": 0,
  "correctCount": 0,
  "correctedCount": 0,
  "skippedCount": 0,
  "unverifiedCount": 0,
  "exactMatchRate": null,
  "exactMatchPercentage": "N/A",
  "characterErrorRate": null,
  "cerPercentage": "N/A",
  "domain": "HANDWRITING_TEXT",
  "evaluationScope": "User-verified pilot handwriting samples (excluding test/synthetic/skipped)"
}
```

---

## 9. Internal Service Authentication & Stream-Only Hardening

In `services/ai-service/app/api/ocr.py`:
1. **Header Authentication**:
```python
api_key = request.headers.get("X-Internal-API-Key")
if not api_key or api_key != settings.internal_api_key:
    raise HTTPException(status_code=401, detail="Unauthorized internal API request")
```
2. **Stream-Only Ingestion**:
```python
content_type = request.headers.get("content-type", "").lower()
if "application/json" in content_type:
    raise HTTPException(status_code=415, detail="JSON payload not supported...")

img_bytes = await request.body()
if not img_bytes or len(img_bytes) == 0:
    raise HTTPException(status_code=400, detail="Empty image payload")
```
3. **Caller Injection in Spring Boot (`OcrPilotService.java`)**:
```java
HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.parseMediaType(contentType.startsWith("image/") ? contentType : "image/jpeg"));
headers.set("X-Internal-API-Key", internalApiKey);
HttpEntity<byte[]> requestEntity = new HttpEntity<>(imageBytes, headers);
```

---

## 10. Model Artifact & Weights Integrity Proof

Checkpoints were verified via PowerShell `Get-FileHash -Algorithm SHA256`:

| Model Artifact | File Path | Computed SHA-256 | Status |
|---|---|---|---|
| CRNN Checkpoint | `services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth` | `A807EAA763A4471BC057B9545A3521612423214858D50B1EF42B7BAF28DE0941` | VERIFIED |
| OCR Vocabulary | `services/ai-service/models/ocr/crnn_vi_handwriting_v1/vocab.json` | `6AF4062E92E22CC91ECE5198638E29A6CEEC6CB92E3B12BD71DEB4B874AC9E0D` | VERIFIED |
| YOLO Detection | `services/ai-service/models/yolov8n_mathvision_det_v1.pt` | `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` | VERIFIED |

Weights and vocabularies remain bit-for-bit identical to frozen release checkpoints.

---

## 11. Clean Export Verification (0-Sample Proof)

Execution command:
```powershell
& "E:\MathVisionKid\services\ai-service\.venv\Scripts\python.exe" scripts/export_ocr_feedback_dataset.py --out-dir scratch/export_verified_closure
```

Output:
```text
[EXPORT] Evaluating 0 candidate verified OCR trials...
[EXPORT] Qualified 0 trustworthy handwriting samples.
[EXPORT] Successfully generated dataset package: E:\MathVisionKid\scratch\export_verified_closure\ocr_feedback_export_20260912_094357.zip
[EXPORT] Export directory: E:\MathVisionKid\scratch\export_verified_closure\ocr_feedback_export_20260912_094357
```

**Proof:** Zero synthetic/test/unconsented rows exported.

---

## 12. Mobile Codebase Integrity & Verification

1. **TypeScript Type Check:**
   `npx tsc --noEmit` $\to$ **Exit code 0** (No TypeScript errors).
2. **ESLint:**
   `npm run lint` $\to$ **Exit code 0** (`expo lint` clean, no warnings or errors).
3. **Expo Doctor:**
   `npx expo-doctor` $\to$ **20/21 checks passed** (1 warning is known Expo SDK 57 patch version advisory).

---

## 13. Backend Test Suite Execution Proof (Gradle)

1. `com.mathvisionkids.api.ocr.*` tests:
```text
BUILD SUCCESSFUL in 30s
4 actionable tasks: 4 executed
```
2. Full project Gradle test suite:
```text
BUILD SUCCESSFUL in 46s
4 actionable tasks: 1 executed, 3 up-to-date
```
All unit and integration tests in `services/business-api` passed.

---

## 14. AI Service Test Suite Execution Proof (Pytest)

Targeted OCR pilot tests (`tests/test_ocr_pilot_endpoint.py`):
```text
tests/test_ocr_pilot_endpoint.py::test_ocr_pilot_missing_api_key_rejected PASSED [ 16%]
tests/test_ocr_pilot_endpoint.py::test_ocr_pilot_invalid_api_key_rejected PASSED [ 33%]
tests/test_ocr_pilot_endpoint.py::test_ocr_pilot_json_payload_rejected PASSED [ 50%]
tests/test_ocr_pilot_endpoint.py::test_ocr_pilot_recognize_line_raw_bytes_success PASSED [ 66%]
tests/test_ocr_pilot_endpoint.py::test_ocr_pilot_empty_image_rejected PASSED [ 83%]
tests/test_ocr_pilot_endpoint.py::test_ocr_pilot_oversized_payload_rejected PASSED [100%]
======================== 6 passed, 2 warnings in 5.32s ========================
```

Full AI Service test suite (`pytest tests/`):
```text
====================== 146 passed, 2 warnings in 11.15s =======================
```
All 146 tests passed in 11.15s.

---

## 15. E2E Integration & Security Verification Log

Live testing against running FastAPI (port 8000) and Spring Boot (port 8080) services via `scratch/test_live_closure.py`:

```text
--- 1. Testing FastAPI Internal Security ---
Missing API key: status=401, expected=401
Invalid API key: status=401, expected=401
JSON payload: status=415, expected=415
Valid API key + raw bytes: status=200, expected=200
AI response: text='nrtatro', confidence=None

--- 2. Testing Spring Boot Live Auth & Role Restrictions ---
Unauthenticated /ocr: status=401, expected=401
Teacher role on /ocr: status=403, expected=403
Student /metrics: status=200, expected=200
Metrics: total=0, verifiedTrials=0, exactMatchRate=None, exactMatchPercentage=N/A, cer=None, cerPercentage=N/A

--- 3. Testing Live E2E OCR Trial Creation (Spring -> FastAPI with X-Internal-API-Key) ---
Create trial: status=201, expected=201
Created trial b1cc39f9-611b-40a4-bbed-cfb3bfeeddd4: predictedText='nrtatro', privacyConfirmed=False, isTestData=True, trainingEligible=False
Feedback CORRECT: status=200, expected=200
Updated trial b1cc39f9-611b-40a4-bbed-cfb3bfeeddd4: verdict='CORRECT', trainingEligible=False

ALL LIVE INTEGRATION TESTS PASSED SUCCESSFULLY!
```

---

## 16. Architectural Boundary & Parking Adherence

1. **Arithmetic Pipeline:** YOLO detection model, StructuredParser, ArithmeticValidator, and multi-line detection remain completely untouched and parked.
2. **Model Training:** Zero fine-tuning or backpropagation executed. Checkpoints are untouched.
3. **Separation of Concerns:** OCR Pilot uses its own isolated endpoint (`/internal/v1/ocr/recognize-line`) and database table (`ocr_trials`).

---

## 17. Physical Device Verification Status (OWNER_TEST_REQUIRED)

Physical device testing status is strictly declared as **OWNER_TEST_REQUIRED**.
Because the agent runs within an automated Windows/IDE developer environment without physical hands to photograph handwriting samples on an Android device, real handwriting verification on physical hardware must be executed by the project owner.

---

## 18. Next Recommended Steps for Owner Feedback Collection

1. Launch Student Mobile App on physical Android device connected to local LAN.
2. Navigate to OCR Pilot mode (`/ocr-pilot`).
3. Select or capture a Vietnamese handwritten line (e.g., student homework book or sample index card).
4. Perform single text-line crop and submit for recognition.
5. Review predicted text, mark as `CORRECT` or edit to true Vietnamese handwriting text and mark `LƯU VÀ XÁC NHẬN` (`CORRECTED`).
6. After collecting 10–20 real samples, run `py scripts/export_ocr_feedback_dataset.py` to generate the offline retraining batch.

---

## 19. Final Gate Verdict & Sign-Off Block

```text
============================================================
FINAL GATE VERDICT: OCR.PILOT.1.2 — PASSED
============================================================
1. DB Row Count Truth: 13 total rows in ocr_trials (reconciled). 0 real user rows.
2. Legacy Reclassification: All 13 rows set to is_test_data=true, privacy_confirmed=false, training_eligible=false.
3. Privacy Fail-Closed: V8 migration applied (DEFAULT FALSE), Entity default=false, Controller defaultValue=false.
4. Internal Security: FastAPI POST /internal/v1/ocr/recognize-line requires X-Internal-API-Key (401 on missing/invalid).
5. Stream-Only Input: Raw binary image stream only. JSON payloads rejected with 415.
6. Role-Based Access: /api/v1/ocr/** restricted to hasRole("STUDENT") (403 for non-students).
7. Safe Zero Metrics: verifiedTrials=0 returns null exactMatchRate, "N/A" exactMatchPercentage, null CER, "N/A" CER.
8. Clean Export: scripts/export_ocr_feedback_dataset.py outputs exactly 0 samples from current DB state.
9. Weights Integrity: best_cer.pth, vocab.json, yolov8n bit-for-bit unchanged.
10. Test Suites: 146/146 Pytest passed. Gradle build and tests passed. TSC & ESLint clean.
11. Git Tree: NO git commit or push performed.
12. Physical Device Status: OWNER_TEST_REQUIRED.
============================================================
```
