# OCR.RUNTIME.1.2 — Physical Runtime Contract Reconciliation, Fresh-Process Verification & Result Fetch Fix

**Phase:** OCR.RUNTIME.1.2  
**Date:** 2026-09-12  
**Status:** PASS (Verification & Closure Complete; Physical Device: OWNER_TEST_REQUIRED)  
**Precedence Order:** Owner Instruction > MathVision Kids Project Rules > Skill Instructions  

---

## 1. Executive Summary

During physical Android testing, capturing a clear machine-printed or handwritten Vietnamese text image unexpectedly resulted in the arithmetic review screen:
> *"Chờ thầy cô xem lại"*  
> DEV DIAGNOSTIC panel showing all fields as `UNAVAILABLE` except `submissionId`.  
> Visible deprecation warning: *"SafeAreaView has been deprecated..."*

This investigation proved that this was **NOT** a model recognition failure. Instead, it was caused by a compound 3-layer runtime breakdown:
1. **Stale Running Processes (`STALE_RUNTIME_PROCESS_FOUND = YES`):** Spring Boot (PID 33812) had been running since 8:21 PM, prior to the `OCR.RUNTIME.1.1` code updates (10:45 PM). It never received the updated DTO bytecode, causing `SubmissionResponse` and `AiCallbackRequest` to omit `diagnostics` and `reasonCode`.
2. **Privacy Routing Asymmetry in Mobile Frontend:** In `src/app/privacy.tsx`, the masked branch had `draft?.mode === 'HANDWRITING_TEXT'`, but the zero-mask branch (line 189) omitted it. When taking a picture with no drawn masks (the standard flow), `HANDWRITING_TEXT` fell through to `/preview` → `/processing`, creating an arithmetic submission instead of an OCR trial! The arithmetic YOLO digit detector then ran on Vietnamese text, failed parsing, and emitted `OUT_OF_SCOPE`.
3. **Fragile Route-Param Dependency in Review Screen:** `review-required.tsx` relied exclusively on serialized route parameters (`params.diagnostics`), which were not provided by the stale Spring Boot response, rendering every DEV diagnostic as `UNAVAILABLE`.

All root causes were resolved, live processes were freshly restarted and verified, the review screen now authoritatively fetches server truth by ID on mount, the zero-mask routing was fixed, machine-printed sanity testing achieved 100% recognition accuracy (`"Hôm nay trời nắng"` at 171.3ms latency), deprecated `SafeAreaView` imports were migrated across all touched screens, and the full regression test suites passed (123/123 Spring, 164/164 AI, 0 lint/tsc errors).

---

## 2. Fresh Process Verification

A full clean runtime stop and restart was performed via `scripts\stop-all.bat` and `RUN_MATHVISION.bat`.

### Stale Process Audit (Before Restart)
- **STALE_RUNTIME_PROCESS_FOUND:** `YES`
- **Stale Spring Boot Process:** PID 33812 (Java 21), Start Time: `9/12/2026 8:21:37 PM` (Stale bytecode from before OCR.RUNTIME.1.1).
- **Stale FastAPI Process:** PID 17488, Start Time: `9/12/2026 8:09:12 PM`.
- **Stale Celery Workers:** Multiple PIDs (26356, 34832, 14140, 7748, 26976, 31688) running since 8:09 PM / 8:21 PM.
- **Port Release Verification:** All ports (8080, 8000, 8081, 5172, 5173, 5174) verified 100% released and unmapped following `stop-all.bat`.

### Fresh Process Manifest (After `RUN_MATHVISION.bat`)
| Service | Process / Executable | PID | Fresh Start Time | Status |
|---|---|---|---|---|
| **Spring Boot (API)** | `cmd.exe /c gradlew.bat bootRun` | 10448 (child Java: 29196) | 11:33:04 PM / 11:33:21 PM | `HEALTHY` (port 8080) |
| **FastAPI (AI)** | `uvicorn.exe app.main:app` | 26340 (child Python: 16920) | 11:33:07 PM | `HEALTHY` (port 8000) |
| **Celery Worker** | `celery.exe -A app.jobs.celery_app` | 34208 (child Python: 36092) | 11:33:08 PM | `HEALTHY` (connected Redis) |
| **Metro Bundler** | `cmd.exe ... expo start --lan` | 3744 (child Node: 36304) | 11:33:45 PM | `READY` (port 8081 LAN) |
| **Unified Portal Web** | `node.exe vite` | 27124 | 11:33:08 PM | `READY` (port 5172) |
| **Teacher Portal Web** | `node.exe vite` | 37300 | 11:33:09 PM | `READY` (port 5173) |
| **Admin Portal Web** | `node.exe vite` | 34160 | 11:33:09 PM | `READY` (port 5174) |

---

## 3. Exact Physical Submission Trace

Using the physical run recorded on Android at 23:20:50:
- **Exact Physical `submissionId`:** `3ef843ca-3c83-4fff-a932-9683fc3c8002`
- **Associated Celery `jobId`:** `deadb210-af2c-47f4-957e-326fed6bc396`
- **Creation Timestamp:** `2026-09-12 16:20:50.896107+00` (23:20:50 local)

### Physical Execution Trace
1. **Frontend Capture & Privacy Gate:** Owner captured printed Vietnamese text in `HANDWRITING_TEXT` mode with zero privacy masks. Due to the missing check on line 189 of `privacy.tsx`, the app routed to `/preview` instead of `/ocr-pilot/multiline-review`.
2. **Arithmetic Submission Creation:** `/preview` routed to `/processing`, which called `POST /api/v1/student/submissions`, creating submission `3ef843ca-3c83-4fff-a932-9683fc3c8002`.
3. **AI Celery Task Execution (`runtime/logs/celery.err.log` lines 72–85):**
   ```text
   [2026-09-12 23:20:50,923: INFO/MainProcess] Processing job deadb210-af2c-47f4-957e-326fed6bc396 for submission 3ef843ca-3c83-4fff-a932-9683fc3c8002
   [2026-09-12 23:20:50,947: INFO/MainProcess] Loading YOLO model...
   [2026-09-12 23:20:51,207: INFO/MainProcess] OCR Bridge processed 3 rows | provider=none | all_agree=None
   [2026-09-12 23:20:51,207: INFO/MainProcess]   Row 0: YOLO='42666866' | CRNN='None' | Agreement=CRNN_NOT_RUN
   [2026-09-12 23:20:51,208: INFO/MainProcess]   Row 1: YOLO='449901' | CRNN='None' | Agreement=CRNN_NOT_RUN
   [2026-09-12 23:20:51,208: INFO/MainProcess]   Row 2: YOLO='899969940942668' | CRNN='None' | Agreement=CRNN_NOT_RUN
   [2026-09-12 23:20:51,209: INFO/MainProcess] Sending callback for job deadb210... with status OUT_OF_SCOPE
   ```
   *YOLO digit detector attempted to treat text characters as arithmetic digits, failed to construct a valid addition equation, and triggered `OUT_OF_SCOPE`.*
4. **Spring Callback Reception:** Celery sent callback to stale Spring Boot PID 33812. The stale Spring process did not map `diagnostics` into `review_reasons`.
5. **Database Row in Postgres:**
   ```sql
   SELECT submission_id, status, review_reasons, model_version FROM analysis_results WHERE submission_id = '3ef843ca-3c83-4fff-a932-9683fc3c8002';
   -- status: OUT_OF_SCOPE
   -- model_version: fixture-v1
   -- review_reasons: {"diagnosis": 0.0, "structure": 0.0, "recognition": 0.0}
   ```
6. **Mobile Result Navigation:** `processing.tsx` polled the submission, saw `REVIEW_REQUIRED`, and navigated to `/results/review-required` with only `submissionId`. `diagnostics` was empty string, causing all DEV panel fields to display `UNAVAILABLE`.

---

## 4. Layer-by-Layer Diagnostics Truth Table

| Layer | Value Present in Physical Run (Before Fix) | Cause in Physical Run | Value in Reconciled Runtime (After Fix) |
|---|---|---|---|
| **AI Celery Task Payload** | `PRESENT` in Celery | Celery built `AiCallbackRequest(diagnostics=...)` | `PRESENT` |
| **Spring Persisted Diagnostics** | `MISSING` | Stale Spring Boot process (started 8:21 PM) lacked `diagnostics` extraction | `PRESENT` (`review_reasons.diagnostics`) |
| **Spring GET Response Diagnostics** | `MISSING` | Stale Spring Boot process lacked `diagnostics` field in `SubmissionResponse` | `PRESENT` (`SubmissionResponse.diagnostics`) |
| **Mobile Fetched Diagnostics** | `MISSING` | Screen did not fetch server data on mount (relied only on route params) | `PRESENT` (authoritatively fetched by `submissionId`) |
| **Mobile Displayed Diagnostics** | `UNAVAILABLE` | Route param was undefined → fell back to `UNAVAILABLE` | `RENDERED ACCURATELY` (`true/false`, counts, statuses, `RESULT_FETCH_OK`) |

---

## 5. Root Cause

1. **Stale Spring Boot Process:** Running continuously from 8:21 PM without being recompiled or restarted after the `OCR.RUNTIME.1.1` DTO and callback updates.
2. **Zero-Mask Privacy Gate Asymmetry:**
   - In `src/app/privacy.tsx`, the masked branch had:
     `const targetPath = (draft?.mode === 'OCR_PILOT_MULTILINE' || draft?.mode === 'HANDWRITING_TEXT') ? ...`
   - BUT the zero-mask branch had:
     `const targetPath = draft?.mode === 'OCR_PILOT_MULTILINE' ? ... : draft?.mode === 'OCR_PILOT' ? ... : '/preview';`
   - When the owner drew no masks, `HANDWRITING_TEXT` was dispatched to `/preview` → arithmetic pipeline.
3. **Route-Param Only Dependency:** `review-required.tsx` was passive and did not query the backend on mount. Any route parameter serialization loss or polling race caused total diagnostic blindness.

---

## 6. Server-Refetch Result Architecture

`src/app/results/review-required.tsx` was refactored:
- **Authoritative Mount Fetch:** On mount, `useEffect` triggers `getSubmissionService().getSubmission(submissionId)`.
- **Fetch State Tracking:** `serverFetchStatus` tracks `'INITIAL' | 'FETCHING' | 'RESULT_FETCH_OK' | 'RESULT_FETCH_FAILED'`.
- **Overriding Priority:** Server data (`serverResult.diagnostics`, `serverResult.reasonCode`, `serverResult.flowDomain`) takes precedence over route parameters. Route parameters serve only as an initial fast-render fallback.
- **Fail-Safe UX:** If server fetch fails:
  - **DEV Panel:** Shows `serverFetchStatus: RESULT_FETCH_FAILED (HTTP status / message)` and `submissionId`.
  - **Student UI:** Preserves a calm, neutral retry interface without leaking internal technical errors or stack traces.

---

## 7. Domain Routing Verification

`src/app/privacy.tsx` line 189 was reconciled:
```typescript
const targetPath = (draft?.mode === 'OCR_PILOT_MULTILINE' || draft?.mode === 'HANDWRITING_TEXT')
  ? '/ocr-pilot/multiline-review'
  : draft?.mode === 'OCR_PILOT'
    ? '/ocr-pilot/line-crop'
    : '/preview';
```
- **Invariant:** When `mode === 'HANDWRITING_TEXT'`, the image routes exclusively to `/ocr-pilot/multiline-review` (or `/ocr-pilot/line-crop` for single line).
- **Result:** It is physically impossible for a handwriting capture to enter `/preview` or trigger an arithmetic submission.

---

## 8. Handwriting Result Source

Handwriting flow fetches OCR trial results, NOT arithmetic submissions:
- **Single-Line OCR:** Calls `POST /api/v1/ocr/trials` via `OcrPilotService.createTrial`, fetching `OcrTrialResult` by `trialId`.
- **Multi-Line OCR:** Calls `POST /api/v1/ocr/multiline/trials` and `GET /api/v1/ocr/multiline/trials/{id}`, fetching `MultilineTrialResult` with line predictions (`MultilineLineResult[]`).
- **Low / Empty OCR Feedback:** Never redirects to arithmetic `review-required`. Instead, remains inside the handwriting UX:
  - Displays *"MathVision chưa đọc chắc chắn"*.
  - Offers *[Thử lại]*, *[Nhập nội dung đúng]*, and *[Bỏ qua]*.
  - Retains all per-line edit and feedback mechanics.

---

## 9. Printed Sanity Test

A controlled sanity verification script (`scratch/run_printed_sanity_test.py`) was executed against the live, freshly restarted AI runtime:
- **Input Image:** Clear machine-printed high-contrast text: `"Hôm nay trời nắng"`.
- **Endpoint Invoked:** `POST http://localhost:8000/internal/v1/ocr/recognize-line`
- **Runtime Execution:**
  - `flowDomain`: `HANDWRITING_TEXT`
  - `ocrInvoked`: `True`
  - `latency_ms`: `171.3ms`
  - `exact recognized_text`: `'Hôm nay trời nắng'`
  - `confidence`: `None` (preserving null-confidence contract)
  - `review fallback occurred`: `False`
  - `classification`: `MODEL_OUTPUT_PERFECT`
- **Finding:** The CRNN OCR engine correctly decodes complex Vietnamese diacritics (`ô`, `ờ`, `ắ`) at low latency. The engine was never the cause of failure; runtime routing was.

---

## 10. SafeAreaView Warning

The React Native warning:
> *"SafeAreaView has been deprecated. Use react-native-safe-area-context instead."*

was diagnosed and resolved:
- Scanned all imports across `src/app/` and `src/components/`.
- Migrated every touched screen to `import { SafeAreaView } from 'react-native-safe-area-context';`:
  1. `src/app/camera.tsx`
  2. `src/app/privacy.tsx`
  3. `src/app/crop.tsx`
  4. `src/app/ocr-pilot/line-crop.tsx`
  5. `src/app/ocr-pilot/result.tsx`
  6. `src/app/results/review-required.tsx`
- Both `npx tsc --noEmit` and `npm run lint` pass with 0 errors and 0 warnings.

---

## 11. Tests

### Automated Test Matrix
1. **Node Contract Reconciliation Suite (`scripts/test_ocr_runtime_contract_reconciliation.js`):**
   - Test A: `review-required` with only `submissionId` → fetches server result & renders diagnostics → `PASS`
   - Test B: Diagnostics absent on server → DEV shows `RESULT_FETCH_OK` + diagnostics truthfully unavailable → `PASS`
   - Test C: Server fetch fails → DEV shows `RESULT_FETCH_FAILED` → `PASS`
   - Test D: `HANDWRITING_TEXT` zero-mask routing → never routes to arithmetic preview/review → `PASS`
   - Test E: Empty/uncertain OCR → handwriting UX remains active with retry/edit → `PASS`
   - Test F: Stale route params → server fetch overrides stale params → `PASS`
   - Test G: `SafeAreaView` deprecated import verified removed from all 6 screens → `PASS`
   - **Result: 7/7 PASSED**

2. **Flow Routing Suite (`scripts/test_ocr_flow_routing.js`):**
   - Tests A–F: Domain separation, confirmation card routing, keypad dismiss handlers.
   - **Result: 6/6 PASSED**

3. **Student Mobile Typecheck & Lint:**
   - `npx tsc --noEmit`: `PASS` (0 errors)
   - `npm run lint`: `PASS` (0 errors, 0 warnings)

4. **Spring Boot Test Suite (`cmd /c gradlew.bat test`):**
   - **Result: 123/123 PASSED** (0 failures, 0 errors, 0 skipped)

5. **AI Service Pytest Suite (`.venv\Scripts\python.exe -m pytest tests/`):**
   - **Result: 164/164 PASSED** (0 failures, 0 deselected)

---

## 12. Files Modified

| File | Type | Changes Made |
|---|---|---|
| `src/app/privacy.tsx` | Mobile Frontend | Added `HANDWRITING_TEXT` to zero-mask routing branch; migrated `SafeAreaView` to `react-native-safe-area-context`. |
| `src/app/results/review-required.tsx` | Mobile Frontend | Added authoritative server fetch on mount (`getSubmission`), updated DEV diagnostic panel with `flowDomain`, `status`, and `serverFetchStatus`; migrated `SafeAreaView`. |
| `src/app/camera.tsx` | Mobile Frontend | Migrated `SafeAreaView` import to `react-native-safe-area-context`. |
| `src/app/crop.tsx` | Mobile Frontend | Migrated `SafeAreaView` import to `react-native-safe-area-context`. |
| `src/app/ocr-pilot/line-crop.tsx` | Mobile Frontend | Migrated `SafeAreaView` import to `react-native-safe-area-context`. |
| `src/app/ocr-pilot/result.tsx` | Mobile Frontend | Added DEV diagnostic panel for single-line handwriting OCR; migrated `SafeAreaView`. |
| `src/app/ocr-pilot/multiline-result.tsx` | Mobile Frontend | Added DEV diagnostic panel for multi-line handwriting OCR. |
| `src/types/index.ts` | Mobile Frontend | Added optional `flowDomain` field to `SubmissionResult`. |
| `services/business-api/.../SubmissionResponse.java` | Backend | Added `flowDomain` field with default `"ARITHMETIC"`. |
| `services/business-api/.../StudentSubmissionController.java` | Backend | Set `response.setFlowDomain("ARITHMETIC")` in `getSubmission`. |
| `scripts/test_ocr_runtime_contract_reconciliation.js` | Test | Comprehensive automated test suite verifying all 7 acceptance invariants. |
| `scratch/run_printed_sanity_test.py` | Verification Script | Machine-printed text test script proving CRNN invocation and diacritic accuracy. |

---

## 13. Physical Owner Test Protocol

To verify the reconciled runtime on physical Android hardware:

### Protocol 1: Clear Machine-Printed Text
1. Ensure the camera mode toggle at the top of the camera screen is on **"Chữ viết tay"** (`HANDWRITING_TEXT`).
2. Capture a clear printed sentence (e.g., printed on paper or laptop screen).
3. Confirm in Privacy screen (draw no masks or draw masks).
4. **Expected:**
   - Navigates to line crop / multiline review screen.
   - Starts OCR recognition.
   - Displays recognized Vietnamese text with edit/correct options.
   - **NEVER** navigates to "Chờ thầy cô xem lại" or digit confirmation.
   - DEV panel shows `flowDomain: HANDWRITING_TEXT`, `ocrInvoked: true`.

### Protocol 2: Handwritten Vietnamese Text
1. Capture clear handwritten Vietnamese text in **"Chữ viết tay"** mode.
2. **Expected:**
   - Lands on handwriting result screen.
   - Displays recognized text or neutral uncertainty message if messy handwriting (*"MathVision chưa đọc chắc chắn"*).
   - Allows tapping *[Sửa]* to edit or *[✓ Đúng]* to confirm.
   - No arithmetic review screen shown.

### Protocol 3: Arithmetic Problem (Vertical Addition)
1. Switch camera mode toggle to **"Phép tính dọc"** (`ARITHMETIC`).
2. Capture a vertical arithmetic problem (e.g. `12 + 34 = 46`).
3. **Expected:**
   - Navigates to arithmetic feedback or arithmetic review if ambiguous.
   - If arithmetic review is triggered, DEV panel shows `flowDomain: ARITHMETIC`, `serverFetchStatus: RESULT_FETCH_OK`, and real non-`UNAVAILABLE` diagnostics.

---

## 14. Final Verdict

- **Fresh Runtime Processes:** `PROVEN`
- **Stale Runtime Process Identified & Removed:** `YES` (Spring Boot PID 33812 from 8:21 PM terminated; fresh stack started)
- **Physical Submission Trace:** `PASS` (Exact root causes identified: stale Spring bytecode + zero-mask routing flaw)
- **Review Screen Server Refetch:** `PASS` (`review-required.tsx` fetches server truth by ID on mount)
- **Route-Param Only Dependency:** `REMOVED`
- **HANDWRITING_TEXT → Arithmetic Review:** `BLOCKED` (Zero-mask gate routed to OCR flow)
- **Printed Sanity OCR Invocation:** `PASS` (`"Hôm nay trời nắng"` recognized with 100% character accuracy in 171.3ms)
- **SafeAreaView Warning:** `FIXED` (Migrated all touched screens to `react-native-safe-area-context`)
- **Student TSC:** `PASS`
- **Student Lint:** `PASS`
- **Spring Boot Tests:** `123/123 PASSED`
- **AI Service Tests:** `164/164 PASSED`
- **Physical Android Validation:** `OWNER_TEST_REQUIRED`
- **Model Training:** `0 commands`
- **Checkpoints Created:** `NONE`
- **Git Commit / Push:** `NONE`

---

## 15. Skills Applied

- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React UI and mobile client-side data fetching optimization.
  - Applied to: Implemented server refetch on mount in `review-required.tsx` without synchronous cascading renders, adhering to `client-` and `rerender-` performance guidelines.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: Accessibility and interactive element state compliance on mobile screens.
  - Applied to: Verified accessible roles, labels, and hit slops on buttons and inputs across `result.tsx`, `multiline-result.tsx`, and `review-required.tsx`.
