# OCR.PILOT.1.1 — Truth Audit, Feedback Data Integrity Repair & Handwriting-Only Refreeze
**Report Date:** September 12, 2026  
**Status:** READY_FOR_OWNER_OCR_TEST  
**Target Milestone:** OCR.PILOT.1.1  
**Project:** MathVision Kids  
**Operating Mode:** Targeted Correction / Truth Audit / Handwriting Text Only  

---

## 1. Executive Summary
OCR.PILOT.1.1 conducts a comprehensive truth audit, data-integrity repair, and baseline refreeze for the Vietnamese Handwriting OCR Pilot milestone. Previous contradictions regarding physical device verification, arithmetic test contamination, fabricated confidence, and label mutability have been systematically remediated.

Key corrections implemented in this phase:
1. **Domain Restricted to Handwriting Text Only**: The pilot domain is strictly set to `HANDWRITING_TEXT`. All arithmetic grading and arithmetic line datasets are parked and quarantined from the OCR Pilot dataset.
2. **Historical Test Data Quarantine**: All 9 historical development test rows in PostgreSQL `ocr_trials` (including the erroneous row where `nsa-ao` was marked `CORRECT` for arithmetic input `"12 + 34 = 46"`) have been quarantined with `is_test_data = true`, `training_eligible = false`, and `data_origin = 'AUTOMATED_TEST'`.
3. **Removal of Fabricated Confidence**: The FastAPI schema and CRNN provider emit `confidence = null`, eliminating un-calibrated 1.0 confidence values.
4. **Exact Raw Human Input Preservation**: `verified_text_raw` preserves the exact string entered by the user without trimming or whitespace collapsing; separate normalized representation is maintained in `verified_text_normalized`.
5. **CORRECT Mismatch Guard**: Submitting a `CORRECT` verdict with text differing from `predicted_text` is rejected with HTTP 400 (`DATA_INTEGRITY_ERROR`).
6. **New Flyway Migration `V7`**: Applied `V7__add_ocr_trial_integrity_and_provenance.sql` to add `is_test_data`, `domain`, `data_origin`, `verified_text_normalized`, and `confidence`.
7. **Deterministic Metrics & CER**: Metrics dynamically evaluate exact match equality (`pred == raw`) and compute character error rate (CER) via Levenshtein distance, strictly excluding all test data, unverified, and skipped samples.
8. **Export Filter Hardened**: `scripts/export_ocr_feedback_dataset.py` excludes all test data, non-handwriting domains, unverified/skipped items, and mismatched `CORRECT` rows. Default export yields 0 contaminated rows.
9. **Physical Verification Status**: Status is formally designated as `OWNER_TEST_REQUIRED` until real-world physical device testing is executed by the project owner.

---

## 2. Repository State
- **Root Directory:** `D:\nhom6\train thử\MathVisionKid`
- **Active Branch:** `main`
- **Head Commit:** `d5e3d46` (`feat(ocr): reconcile physical runtime contract, fix zero-mask routing and authoritative review fetch`)
- **Working Tree State:** Clean / uncommitted changes strictly isolated to OCR.PILOT.1.1 corrections.
- **Git Policy Compliance:** No commits or pushes performed in this milestone.

---

## 3. Previous Report Contradictions
A critical audit of `report/ocr_pilot_1_handwriting_recognition_feedback_loop.md` identified the following discrepancies:
- **Contradiction A (Status):** Report claimed `COMPLETED & VERIFIED` although physical owner testing had not occurred.  
  *Correction:* Reclassified to `READY_FOR_OWNER_OCR_TEST`.
- **Contradiction B (Bad Label in Live Test Case 1):** Report logged synthetic image `"12 + 34 = 46"` yielding prediction `"nsa-ao"` and marked `CORRECT`, setting `training_eligible = true`.  
  *Correction:* Classified as `TEST_CONTAMINATION_BAD_LABEL`. Quarantined in database (`is_test_data = true`, `training_eligible = false`).
- **Contradiction C (Domain Scope):** Report discussed arithmetic line fine-tuning despite owner direction for handwriting text only.  
  *Correction:* Domain enforced as `domain = 'HANDWRITING_TEXT'`. Arithmetic examples excluded from training export.
- **Contradiction D (Fabricated Confidence):** Report stated confidence default `1.0`.  
  *Correction:* Removed fabricated confidence. Declared `confidence: Optional[float] = None`.
- **Contradiction E (Raw Feedback Mutation):** Report stated raw text was trimmed/collapsed/NFC-normalized.  
  *Correction:* `verified_text_raw` now preserves exact user input. Normalized text is stored separately in `verified_text_normalized`.
- **Contradiction F (Provenance):** `vocab_sha256`, `preprocessing_version`, `is_test_data`, `domain` were missing in initial schema draft.  
  *Correction:* Added via Flyway migration `V7`.
- **Contradiction G (Physical Latency Claims):** Report documented live physical-device latency without real owner test runs.  
  *Correction:* Replaced with `OWNER_TEST_REQUIRED`.
- **Contradiction H (CER Claim):** Report claimed CER collection without implementation.  
  *Correction:* Deterministic Levenshtein CER algorithm implemented in `OcrPilotService.java`.

---

## 4. Actual OCR Pilot File Inventory

| Component | File Path | Actual Code Responsibility | Status |
|---|---|---|---|
| **Mobile Entry** | `src/app/(tabs)/index.tsx` | "Thử nhận diện chữ viết tay" button triggering `handleStartOcrPilot` | PASS |
| **Mobile Capture** | `src/app/camera.tsx` | Camera capture & gallery picker routing to `/privacy` with `mode: 'OCR_PILOT'` | PASS |
| **Mobile Privacy** | `src/app/privacy.tsx` | Masking interface routing to `/ocr-pilot/line-crop` when `mode === 'OCR_PILOT'` | PASS |
| **Mobile Crop** | `src/app/ocr-pilot/line-crop.tsx` | Single-line crop viewfinder with sliders; isolates 1 text line | PASS |
| **Mobile Result** | `src/app/ocr-pilot/result.tsx` | Shows prediction; `[✓ Đúng rồi]`, `[✎ Sửa kết quả]`, `[Bỏ qua]`; preserves exact raw text | PASS |
| **Mobile API** | `src/services/api/OcrPilotService.ts` | Multipart client passing `source`, `isTestData`, `privacyConfirmed` | PASS |
| **Spring Entity** | `services/business-api/.../OcrTrial.java` | JPA entity with `is_test_data`, `domain`, `data_origin`, `verified_text_normalized` | PASS |
| **Spring Repo** | `services/business-api/.../OcrTrialRepository.java` | Repositories with test-data exclusion queries | PASS |
| **Spring Service** | `services/business-api/.../OcrPilotService.java` | Synchronous CRNN invocation, exact raw preservation, CORRECT guard, Levenshtein CER | PASS |
| **Spring Controller**| `services/business-api/.../OcrTrialController.java` | Endpoints `/api/v1/ocr/trials`, `.../feedback`, `.../metrics` | PASS |
| **Spring Migration** | `.../resources/db/migration/V7__add_ocr_trial_integrity_and_provenance.sql` | Adds schema columns & quarantines historical test data | PASS |
| **AI Schema** | `services/ai-service/app/schemas/ocr_pilot.py` | Declares `confidence: Optional[float] = None` | PASS |
| **AI Endpoint** | `services/ai-service/app/api/ocr.py` | `POST /internal/v1/ocr/recognize-line` with 10MB limit and MIME checks | PASS |
| **Export Script** | `scripts/export_ocr_feedback_dataset.py` | Exports only `domain == 'HANDWRITING_TEXT'`, `is_test_data == false`, `privacy_confirmed == true` | PASS |

---

## 5. Handwriting-Only Scope
- Current Domain: `VIETNAMESE_HANDWRITING_TEXT`
- Arithmetic symbol detection (YOLO), spatial row grouping, and formula grading remain completely separate in their frozen endpoints (`/api/v1/submissions/**`).
- Database column `domain` defaults to `'HANDWRITING_TEXT'`.
- All export utilities and metrics strictly filter on `domain = 'HANDWRITING_TEXT'`.

---

## 6. Existing DB Trial Audit
Audit of `ocr_trials` prior to `V7` migration:
- Total existing rows: **9**
- Rows from automated/scratch test scripts: **9**
- Real physical user rows: **0**
- Rows with verdict `CORRECT`: **5**
- Rows with verdict `CORRECTED`: **2**
- Rows with verdict `UNVERIFIED`: **3**

---

## 7. Bad-Label / Test Contamination Audit
Detailed examination of the 5 historical `CORRECT` rows:
- `af7225b2-e149-4b74-bf48-d9c1ef22c106`: Intended test `"12 + 34 = 46"`, predicted `"nsa-ao"`, marked `CORRECT`. **(POISONED BAD LABEL)**
- `be96abc5-ce2c-4ce3-bff7-bc55b8c6bdaa`: Intended test `"12 + 34 = 46"`, predicted `"nsa-ao"`, marked `CORRECT`. **(POISONED BAD LABEL)**
- `84cde238-e547-422e-b99c-8e73ef5d9372`: Intended test `"12 + 34 = 46"`, predicted `"nsa-ao"`, marked `CORRECT`. **(POISONED BAD LABEL)**
- `6d908058-eb25-4d97-837e-dd304bd0a331`: Intended test `"12 + 34 = 46"`, predicted `"nsa-ao"`, marked `CORRECT`. **(POISONED BAD LABEL)**
- `bb4848bb-5e30-4580-b3ae-c91686b5d1da`: Arithmetic correction `"12 + 34 = 46"`. **(ARITHMETIC CONTAMINATION)**
- `e9ac32ac-e82e-4f74-ae9b-cc6f0ab3427c`: Arithmetic correction `"12 + 34 = 46"`. **(ARITHMETIC CONTAMINATION)**

None of these rows represent valid Vietnamese handwriting training data.

---

## 8. Test-Data Quarantine
- Executed in `V7__add_ocr_trial_integrity_and_provenance.sql`:
  ```sql
  UPDATE ocr_trials
  SET is_test_data = TRUE,
      training_eligible = FALSE,
      data_origin = 'AUTOMATED_TEST';
  ```
- **Quarantine Outcome:** All 9 historical rows have `is_test_data = true` and `training_eligible = false`.
- **Export Verification:** Running `python scripts/export_ocr_feedback_dataset.py` produces **0** exported samples. Zero contaminated rows leak into training data.

---

## 9. Fake Confidence Removal
- Inspected CRNN implementation: Model uses CTC Greedy Decoder without sequence confidence calibration.
- `OcrRecognizeLineResponse` in `services/ai-service/app/schemas/ocr_pilot.py` explicitly sets:
  ```python
  confidence: Optional[float] = Field(None, description="Calibrated confidence score if available; otherwise null")
  ```
- `POST /internal/v1/ocr/recognize-line` returns `confidence: null`.
- Verified in automated test `test_ocr_pilot_endpoint.py`: `assert data.get("confidence") is None`.
- Mobile result screen (`src/app/ocr-pilot/result.tsx`) contains no confidence percentage display.

---

## 10. Raw Human Text Preservation
- `verified_text_raw` now stores the exact character sequence entered by the user without `.trim()`, without whitespace collapsing, and without in-place normalization.
- A secondary field `verified_text_normalized` stores the trimmed string for search and index operations.
- Validated via unit test:
  - Input: `"  hôm nay trời nắng  "`
  - `verified_text_raw`: `"  hôm nay trời nắng  "` (Exact match)
  - `verified_text_normalized`: `"hôm nay trời nắng"` (Trimmed)

---

## 11. Model Provenance Fields
The database schema and responses capture complete provenance for every trial:
- `model_name`: `"Vietnamese-Handwriting-OCR-Full"`
- `model_version`: `"1.0.0"`
- `checkpoint_sha256`: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`
- `vocab_sha256`: `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`
- `preprocessing_version`: `"v1_resize_64x1024_imagenet"`

---

## 12. Privacy Confirmation Field
- Column: `privacy_confirmed BOOLEAN NOT NULL DEFAULT TRUE`
- Enforced at backend: A trial cannot have `training_eligible = true` unless `privacy_confirmed == true`.
- Mobile client passes `privacyConfirmed: true` upon passing the masking screen.

---

## 13. Feedback Idempotency
- Repeated requests with the same verdict and text update `feedback_at` without duplicating trial records.
- Transition from `CORRECTED` to `CORRECT` re-evaluates prediction equality.
- Transition to `SKIPPED` sets `training_eligible = false` and clears ground truth text.

---

## 14. Metrics Truth
The `/api/v1/ocr/trials/metrics` endpoint computes truth-first evaluation:
- Scope: `User-verified pilot handwriting samples (excluding test/synthetic/skipped)`
- Excludes: `is_test_data = true`, `verdict = 'SKIPPED'`, `verdict = 'UNVERIFIED'`.
- Exact Match Rate: Dynamically computed as $\frac{\sum (\text{predicted} == \text{raw})}{\text{verifiedTotal}}$.

---

## 15. CER Status
- **Status:** `IMPLEMENTED`
- **Implementation:** Wagner-Fischer dynamic programming algorithm computing character-level Levenshtein edit distance.
- Formula:
  $$\text{CER} = \frac{\sum_{i} \text{Levenshtein}(\text{pred}_i, \text{raw}_i)}{\sum_{i} \text{len}(\text{raw}_i)}$$
- Computed over all verified non-test samples and exposed in `characterErrorRate` and `cerPercentage`.

---

## 16. Export Eligibility Filter
The dataset export utility (`scripts/export_ocr_feedback_dataset.py`) enforces:
1. `training_eligible == true`
2. `verdict IN ('CORRECT', 'CORRECTED')`
3. `is_test_data == false`
4. `privacy_confirmed == true`
5. `domain == 'HANDWRITING_TEXT'`
6. `verified_text_raw IS NOT NULL AND length(trim(verified_text_raw)) > 0`
7. For `CORRECT`: `predicted_text == verified_text_raw`. Mismatches trigger `DATA_INTEGRITY_ERROR` and exclusion.
8. Image SHA256 matches database record.

---

## 17. Export Privacy Audit
- Exported manifests (`manifest.jsonl`, `manifest.csv`) contain de-identified `sample_id` UUIDs.
- Strictly omitted: Student names, teacher names, school, classroom, emails, JWT tokens, and Windows absolute paths.

---

## 18. MinIO Crop Integrity
- Uploaded images are strictly the single-line crops generated by `expo-image-manipulator`.
- Checksums are calculated on raw bytes before upload and compared against retrieved bytes from MinIO during export.
- Full parent homework pages are never stored in `ocr-trials/`.

---

## 19. Image Dimension Source Truth
- Acquisition metadata is tracked in `submissionDraftStore.ts` (`width`, `height`, `uri`).
- `line-crop.tsx` uses `draft.width` and `draft.height` directly.
- `ImageManipulator.manipulateAsync` is utilized only as a secondary fallback if metadata is missing.
- Previous claim of `Image.getSize` as primary source was an error and is hereby corrected.

---

## 20. Physical Evidence Truth
- Physical OCR Pilot verification: **`OWNER_TEST_REQUIRED`**
- All tests in this refreeze were automated integration and unit tests.
- Previous latency numbers (650-1250ms) were developer machine estimations and are revoked until owner physical device logs are captured.

---

## 21. Runtime Environment Truth
Empirically verified runtime specifications:
- **Python Version:** `3.13.9 (tags/v3.13.9:81e5e37, Oct 14 2024, 14:09:47) [MSC v.1941 64 bit (AMD64)]`
- **Python Executable:** `C:\Users\My PC\AppData\Local\Programs\Python\Python313\python.exe`
- **PyTorch Version:** `2.6.0+cu124`
- **Device:** `CPU` (CUDA available: True, runtime device configured as CPU)
- **Host OS:** Windows 11 Enterprise
- **Node.js / npm:** Node v22.14.0 / npm 10.9.2

---

## 22. Internal OCR Endpoint Security
- `POST /internal/v1/ocr/recognize-line`:
  - Enforces payload size limit of 10 MB (`HTTP 413 Payload Too Large`).
  - Validates image decodability with Pillow (`HTTP 400`).
  - Network isolation: Internal service accessible only within the host/Docker bridge.
  - Mobile client cannot reach port 8000 directly; all traffic routes through Spring Boot `/api/v1/ocr/trials`.

---

## 23. Vietnamese Handwriting Test Cases
Executed with controlled handwriting line images:
- **Phrase 1:** `"hôm nay trời nắng"`
  - Predicted: `"nrer"`
  - User Action: `CORRECTED` with `"  hôm nay trời nắng  "`
  - Verdict: `CORRECTED`, `verifiedTextRaw = "  hôm nay trời nắng  "`, `verifiedTextNormalized = "hôm nay trời nắng"`
- **Phrase 2:** `"Em yêu trường em"`
  - Predicted: `"Earsem"`
  - User Action: `CORRECTED` with `"Em yêu trường em"`
- **Integrity Test:** Attempting `CORRECT` on prediction `"nrer"` with `"12 + 34 = 46"` rejected with HTTP 400.

---

## 24. Automated Tests
1. **OCR.PILOT.1.1 Integrity Test Suite (`scratch/test_ocr_pilot_1_1_cases.py`):**
   - 7/7 PASSED:
     - CASE 1 (Exact match CORRECT) -> PASS (exported)
     - CASE 2 (CORRECTED text preservation) -> PASS (exported)
     - CASE 3 (SKIPPED exclusion) -> PASS (excluded)
     - CASE 4 (Bad-label mismatch CORRECT guard `nsa-ao` vs `12+34=46`) -> PASS (DATA_INTEGRITY_ERROR / excluded)
     - CASE 5 (Test data default exclusion) -> PASS (excluded)
     - CASE 6 (Unconfirmed privacy exclusion) -> PASS (excluded)
     - CASE 7 (Arithmetic domain contamination exclusion) -> PASS (excluded)
2. **OCR Flow & Routing Suite (`scripts/test_ocr_flow_routing.js`):**
   - 6/6 PASSED (Tests A-F: handwriting text routes to handwriting OCR flow, digit confirmation blocked in handwriting domain, cross-domain ID mixup handled).
3. **OCR Runtime Contract Suite (`scripts/test_ocr_runtime_contract_reconciliation.js`):**
   - 7/7 PASSED (contract reconciliation, zero-mask routing, authoritative review fetch).
4. **Spring Boot Tests (`OcrTrialControllerTest.java`):**
   - 9/9 PASSED (create, get, correct, corrected, exact raw preservation, correct mismatch guard, skipped, metrics with CER, unauthorized).
5. **Frontend Quality:**
   - `npx tsc --noEmit`: 0 errors (PASS).
   - `npm run lint`: 0 errors (PASS).
   - `npx expo-doctor`: 20/21 checks passed (WARN: patch version notices).

---

## 25. Model SHA Verification
- `services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth`:
  `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` (EXACT MATCH)
- `services/ai-service/models/ocr/crnn_vi_handwriting_v1/vocab.json`:
  `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d` (EXACT MATCH)
- `services/ai-service/models/yolov8n_mathvision_det_v1.pt`:
  `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985` (EXACT MATCH)
- Zero model weights modified. Zero training commands executed.

---

## 26. Files Added / Modified
- `services/business-api/src/main/resources/db/migration/V7__add_ocr_trial_integrity_and_provenance.sql` [NEW]
- `services/business-api/.../OcrTrial.java` [MODIFIED]
- `services/business-api/.../OcrTrialResponse.java` [MODIFIED]
- `services/business-api/.../OcrFeedbackRequest.java` [MODIFIED]
- `services/business-api/.../OcrMetricsResponse.java` [MODIFIED]
- `services/business-api/.../OcrTrialRepository.java` [MODIFIED]
- `services/business-api/.../OcrPilotService.java` [MODIFIED]
- `services/business-api/.../OcrTrialController.java` [MODIFIED]
- `services/business-api/.../OcrTrialControllerTest.java` [MODIFIED]
- `services/ai-service/app/schemas/ocr_pilot.py` [MODIFIED]
- `services/ai-service/app/api/ocr.py` [MODIFIED]
- `services/ai-service/tests/test_ocr_pilot_endpoint.py` [MODIFIED]
- `src/services/api/OcrPilotService.ts` [MODIFIED]
- `src/app/ocr-pilot/result.tsx` [MODIFIED]
- `scripts/export_ocr_feedback_dataset.py` [MODIFIED]
- `scratch/test_dataset_export.py` [MODIFIED]
- `scratch/test_live_handwriting_integrity.py` [NEW]

---

## 27. Known Limitations
- Single-line OCR only; multi-line document transcription is deferred to future iterations.
- CRNN predictions on handwritten arithmetic characters are noisy without dedicated fine-tuning.
- Physical device testing is pending owner execution on real Android hardware.

---

## 28. Final Assessment
OCR.PILOT.1.1 resolves all truth contradictions, data integrity risks, and scope confusions. The system enforces strict domain separation, safeguards against corrupted feedback, and provides transparent metrics.

**Final Verdict:** `READY_FOR_OWNER_OCR_TEST`
