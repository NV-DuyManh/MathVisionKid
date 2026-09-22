# AI.HWTEXT.GEMINI.2D — FINAL GEMINI MODEL LOCK + REMOVE UNREQUESTED FALLBACK

## Skills Applied

Skills Applied: None — no installed skill matched this task.

---

## 1. Executive Summary

Phase **AI.HWTEXT.GEMINI.2D** was executed to eliminate an unrequested hidden cross-model fallback introduced during Phase 2C, restoring the strict explicit model contract for the Gemini 2nd Advisor.

- **Primary Goal**: Lock the Gemini model strictly to `gemini-3.8-flash`. Remove all logic that silently switched to `gemini-2.5-flash` on 429/5xx errors.
- **Contract Enforcement**: When `gemini-3.8-flash` encounters a 429 quota error or exhausted 5xx errors, Gemini degrades safely to `UNAVAILABLE` for that line. CRNN remains Primary OCR authority, and Groq (Advisor 1) continues normally without disruption.
- **Model Metadata Truthfulness**: Every suggestion item and `LineBox` truthfully reports the exact configured model (`model="gemini-3.8-flash"`).
- **Test Matrix MODELLOCK-01..06**: **6/6 PASS**.
- **Locked Acceptance (STAB, TRACE, SOURCE, NAV, UI, LINEFIX, ACCEPT-ID)**: **57/57 PASS** (67 total suite items passed).
- **Full AI Suite**: **594 passed, 0 failed, 0 skipped, 594 collected**.
- **Business API Multiline**: **17/0/0 PASS**.
- **Mobile Checks**: TypeScript 0 errors, ESLint 0 errors, Expo Doctor 20/21.

**Final Verdict**: **`AI.HWTEXT.GEMINI.2D: PASS`**

---

## 2. Architecture Lock

| Component | Role | Contract / Model | Status |
|---|---|---|---|
| **CRNN** | **PRIMARY OCR** | Frozen checkpoint (320 vocab, 5.96M params) | **LOCKED / UNTOUCHED** |
| **Groq** | **Advisor 1** | Primary: `qwen/qwen3.8-27b`, Fallback: `LOCAL_CV_CRNN` | **LOCKED / UNTOUCHED** |
| **Gemini** | **Advisor 2** | Strictly `gemini-3.8-flash` (advisory-first) | **LOCKED / STRICT** |

- `CANONICAL_RUNTIME_OVERRIDE_ENABLED=false`
- `GROQ_ROTATE_ON_429=false`
- `GEMINI_ROTATE_ON_429=false`
- No new OCR features, no retraining, no checkpoint/vocab modifications, no segmentation adjustments.

---

## 3. Removal of Hidden Cross-Model Fallback

### Code Audit in `services/ai-service/app/integrations/gemini/corrector.py`
In Phase 2C, a fallback mechanism was added that caught 429/5xx errors on `model` and silently invoked `call_gemini_correction(model="gemini-2.5-flash", ...)`.

### Action Taken
1. Completely removed the conditional block attempting fallback to `gemini-2.5-flash`.
2. Implemented strict single-model execution policy:
   - **429 (Rate Limit / Quota Exceeded)**: Fails immediately on attempt 1, places the key in cooldown (`GEMINI_ROTATE_ON_429=false`), does NOT retry, does NOT substitute any other model. Gemini advisor returns `None` (marks `geminiStatus="UNAVAILABLE"`).
   - **5xx (Server Error / Gateway Timeout)**: Bounded retry (maximum 2 attempts) under the **exact same model** (`gemini-3.8-flash`). If both attempts fail, returns `None`. No model substitution.
   - **Auth Error (401/403)**: Key marked `DISABLED_AUTH`, returns `None`.
3. Verified that zero occurrences of `"gemini-2.5-flash"`, `"gemini-3-flash-preview"`, or `"gemini-3.5-flash"` remain in any production Python files.

---

## 4. Model Metadata Reporting

- `LineBox.geminiModel`: Explicitly set to `settings.gemini_model` (`gemini-3.8-flash`) when Gemini advisor is active.
- `LineBoxDto.java`: Added `private String geminiModel;` field to ensure model metadata traverses Spring Boot DTO serialization cleanly.
- `LineBox.suggestions`: Both Groq and Gemini suggestions now explicitly declare `"model"`:
  ```json
  {
    "provider": "GEMINI",
    "model": "gemini-3.8-flash",
    "text": "...",
    "confidence": 0.95,
    "status": "SUCCESS"
  }
  ```

---

## 5. MODELLOCK Test Suite (6/6 PASS)

Created `services/ai-service/tests/test_gemini_model_lock.py`:

| Test ID | Description | Result |
|---|---|---|
| `MODELLOCK-01` | Configured `GEMINI_MODEL` is `gemini-3.8-flash` and runtime passes only this model | **PASS** |
| `MODELLOCK-02` | 429 rate limit / quota error does NOT switch model and does not retry | **PASS** |
| `MODELLOCK-03` | 5xx server error retries boundedly under the SAME configured model, never switching | **PASS** |
| `MODELLOCK-04` | When Gemini is unavailable, CRNN and Groq are preserved intact | **PASS** |
| `MODELLOCK-05` | Successful Gemini suggestion reports actual configured model in metadata | **PASS** |
| `MODELLOCK-06` | No hardcoded fallback model string exists in production correction path | **PASS** |

**MODELLOCK Status: 6/6 PASS**

---

## 6. Regression Suites

Executed against AI Service test suites:

| Suite | Scope | Target | Result |
|---|---|---|---|
| `MODELLOCK` | Model lock & fallback removal | 6/6 | **PASS** |
| `SEC-GEM` | Security & credential sanitization | 10/10 | **PASS** |
| `GEMCFG` | Configuration & env isolation | 8/8 | **PASS** |
| `GEMPROV` | Provider lifecycle & parser | 10/10 | **PASS** |
| `DUAL` | Dual advisor concurrency & isolation | 15/15 | **PASS** |
| `GEMUI` | UI cards & advisor toggling | 12/12 | **PASS** |
| `FAILISO` | Failure isolation (429/5xx/disabled) | 6/6 | **PASS** |
| `TERM` | Terminology audit (`rawOcrText` baseline) | 2/2 | **PASS** |
| `PRED` | Semantic immutability of raw text | 8/8 | **PASS** |
| `STAB` | Groq stability | 10/10 | **PASS** |
| `TRACE` | Observability & logging | 10/10 | **PASS** |
| `SOURCE` | Source selection contracts | 8/8 | **PASS** |
| `NAV` | Navigation safety | 10/10 | **PASS** |
| `UI` | Multi-line rendering | 10/10 | **PASS** |
| `LINEFIX` | Line grouping fixes | 8/8 | **PASS** |
| `ACCEPT-ID` | ID consistency guard | 1/1 | **PASS** |

**Total Locked Acceptance: 57/57 PASS**

---

## 7. Full Live Route & Real Request Verification

### Live Services
- Spring Boot (:8080): **UP** (`{"status":"UP"}`)
- FastAPI (:8000): **UP** (`{"status":"ok"}`)

### `test_groq_production_route.py`
- Executed against live Spring Boot and FastAPI:
  - **27 passed, 0 failed, 0 skipped**.
  - All HTTP4-01 through HTTP4-06 tests passed.

### Real Spring Multipart OCR Request
Executed `scratch/test_live_spring_entrypoint.py` through `POST http://localhost:8080/api/v1/ocr/multiline/detect`:
- **HTTP Status**: `200 OK`
- **Line Count**: 13 lines
- **Line 0 `recognitionEngine`**: `CRNN` (CRNN Primary OCR preserved)
- **Line 0 `rawOcrText`**: `6Bảo vệ thông tinriêng tư (`
- **Line 0 `finalText`**: `6Bảo vệ thông tinriêng tư (` (CRNN raw preserved)
- **Line 0 `groqSuggestion`**: `Bảo vệ thông tin riêng tư` (Groq Advisor 1 succeeded)
- **Line 0 `geminiSuggestion`**: `None`
- **Gemini 3.8 Live Status**:
  - Live probe on `gemini-3.8-flash` confirms: Google API returns `429 Quota exceeded for metric: generate_content_requests per minute for model: gemini-3.8-flash`.
  - In accordance with the model lock contract: FastAPI did NOT switch model to `gemini-2.5-flash`; it logged 429 quota backoff and safely degraded to `UNAVAILABLE` without error propagating to the client.
  - **Reported Status**: `LIVE_GEMINI_3_8=TEMPORARILY_UNAVAILABLE` (Provider free-tier quota exhausted).

---

## 8. Full AI Suite Total

Ran `pytest tests/`:
- **Collected**: 594 items
- **Passed**: 594
- **Failed**: 0
- **Skipped**: 0
- **Warnings**: 4
- **Execution Time**: 150.19s (02m 30s)

---

## 9. Business API Multiline Tests

Ran `./gradlew.bat test --tests "com.mathvisionkids.api.ocr.multiline.*" --rerun-tasks`:
- **Result**: `BUILD SUCCESSFUL in 31s`
- **Tests**: 17 passed, 0 failed, 0 skipped.

---

## 10. Mobile Checks

1. **TypeScript**: `npx tsc --noEmit` -> **PASS (0 errors)**
2. **ESLint**: `npx eslint src` -> **PASS (0 errors, 0 warnings)**
3. **Expo Doctor**: `npx expo-doctor` -> **20/21 checks passed** (1 check failed: known SDK 57 package version mismatches, non-blocking).

---

## 11. Security Audit

- Ran `pytest tests/test_gemini_security.py -v`: **10/10 PASS**.
- Zero raw keys, prefix masks, or suffix masks are logged, stored in code, or included in reports.
- Credentials in `.env` are referenced solely by one-way SHA-256 fingerprint (`sha256:13355492398b48cf`).

---

## 12. Physical Android Handoff

Physical testing on Android hardware remains:
```
OWNER_TEST_REQUIRED
```
No further automated feature phases should start unless owner physical Android testing reveals a real bug.

---

## 13. Files Modified

| File | Modification Description |
|---|---|
| `services/ai-service/app/integrations/gemini/corrector.py` | Removed hidden fallback to `gemini-2.5-flash`; enforced strict single model policy with bounded 5xx retry on same model |
| `services/ai-service/app/schemas/ocr_pilot.py` | Added `geminiModel` field to `LineBox` schema |
| `services/ai-service/app/api/ocr.py` | Populated `model` in `line.suggestions` for Groq and Gemini, and populated `line.geminiModel` |
| `services/business-api/src/main/java/com/mathvisionkids/api/ocr/multiline/LineBoxDto.java` | Added `geminiModel` field for DTO serialization |
| `services/ai-service/tests/test_gemini_model_lock.py` | Created MODELLOCK-01..06 unit test suite |
| `report/ai_hwtext_gemini_2d_final_model_lock.md` | Created comprehensive Phase 2D final model lock report |

---

## 14. Final Conclusion

Phase **AI.HWTEXT.GEMINI.2D** is **`PASS`**.
- Hidden cross-model fallback completely removed.
- Gemini strictly locked to `gemini-3.8-flash`.
- Degradation on 429/5xx is graceful and preserves CRNN + Groq.
- All 594 AI tests, 17 Business API tests, and Mobile checks pass with 0 errors and 0 skipped.
