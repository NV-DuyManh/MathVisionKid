# OCR.RUNTIME.1.1 — Recognition Attempt Proof & Truth Closure

**Date:** 2026-09-12  
**Task:** `OCR.RUNTIME.1.1 — Prove Recognition Was Actually Attempted, Remove Quality-Gate Short Circuit & Close Missing Runtime Evidence`  
**Status:** **PASS** (Physical Android verification marked `OWNER_TEST_REQUIRED`)

---

## 1. Executive Summary

This phase directly resolves the defect identified in independent review following `OCR.RUNTIME.1`:
1. **Removed QualityGate Hard Short-Circuit:** Previously, in `services/ai-service/app/jobs/tasks.py`, `QualityGate` returning any status other than `"PASS"` (e.g. `DARK`, `INCOMPLETE_CROP`, `BLUR`) aborted processing and triggered a callback with `IMAGE_QUALITY_FAILED` **before** the recognition engine/YOLO detector was ever called.
2. **Always-Attempt Recognition:** Quality heuristics (blur, darkness, glare, uneven lighting, incomplete crop) are now strictly **advisory flags** (`qualityFlags`). The recognition engine is **always** invoked for any decodable, non-empty image. Pre-recognition termination is restricted exclusively to unreadable/corrupt payloads (`IMAGE_DECODE_FAILED`) and pixel-proven blank images (`IMAGE_EFFECTIVELY_EMPTY`).
3. **Internal Recognition Stage Diagnostics:** Structured diagnostics (`detectorInvoked`, `detectorTokenCount`, `ocrInvoked`, `ocrTextLength`, `parserInvoked`, `parserStatus`, `validatorInvoked`, `validatorStatus`, `qualityFlags`, `reasonCode`) are now captured by the AI service, propagated through Spring Boot via `reviewReasons.diagnostics` on `SubmissionResponse`, and displayed on the student mobile app in the `{__DEV__ && ...}` diagnostic panel.
4. **Student Copy Neutralized:** Rewrote student-facing Vietnamese copy to eliminate blame on children's handwriting. Replaced misleading messages with neutral explanations indicating MathVision attempted recognition ("MathVision đã thử đọc bài của em nhưng chưa đủ chắc chắn để kết luận", "MathVision đã thử nhận diện nhưng chưa nhận ra đủ chữ số hoặc dấu phép tính trong ảnh.").
5. **OCR Pilot 1 & Pilot 2 Verified:** Verified non-regression of Pilot 1 single-line recognition and Pilot 2 multiline pipeline. Specifically confirmed that when auto line detection returns zero boxes on a blank or faint page, the student can manually add line boxes, adjust geometry, and proceed to per-line CRNN recognition without being blocked by false quality gates.
6. **Full Suite Execution Without Deselection:**
   - **Full AI Suite (`pytest tests/`):** **164 / 164 passed** (0 deselected, 2 warnings).
   - **Full Spring Suite (`gradlew test`):** **123 / 123 passed** (0 failed).
   - **Student Mobile:** `npx tsc --noEmit` and `npm run lint` both passed with 0 errors.

---

## 2. Skill Routing Evidence

In strict accordance with the mandatory canonical skill routing policy:
- **Task Domains:** React Native Mobile UI, TypeScript / Vercel React Best Practices, Accessibility & Form UI.
- **Skills Matched & Loaded:**
  - `vercel-react-best-practices`: Canonical `.agents/skills/react-best-practices/SKILL.md` (read prior to code edits)
  - `fixing-accessibility`: Canonical `.agents/skills/fixing-accessibility/SKILL.md` (read prior to code edits)
- **Canonical Resolution:** No skills were loaded from legacy `.agent/skills/`. All loaded paths originated from `.agents/skills/`.

---

## 3. QualityGate Execution Order Before Fix

Tracing executable branches in `services/ai-service/app/jobs/tasks.py` prior to this fix:
1. `decode_image_bytes(image_bytes)`
2. `quality_status, quality_issue = QualityGate.evaluate(image)`
3. **Execution Branch:**
   ```python
   # OLD CODE in tasks.py (L30-35):
   if quality_status != "PASS":
       callback = AiCallbackRequest(
           status=SubmissionStatus.REVIEW_REQUIRED.value,
           reasonCode="IMAGE_QUALITY_FAILED",
           evidence={"quality_issue": quality_issue}
       )
       _send_callback(callback_url, callback)
       return quality_status  # <-- TERMINATED BEFORE DETECTOR / OCR
   ```
4. `engine.recognize(image)` (Never reached when QualityGate evaluated `DARK`, `INCOMPLETE_CROP`, or `BLUR`).

### Explicit Answers:
- **QUALITY_GATE_CAN_SHORT_CIRCUIT_BEFORE_DETECTOR:** `YES` (Prior to fix)
- **QUALITY_GATE_CAN_SHORT_CIRCUIT_BEFORE_OCR:** `YES` (Prior to fix)

---

## 4. Root Cause

The root cause of false "blurry handwriting" and early rejections reported by the owner on physical devices was the hard short-circuit in step 3 above. Minor blur, imperfect crop, or low lighting caused `QualityGate.evaluate()` to fail, which immediately triggered an early return with `IMAGE_QUALITY_FAILED` and aborted before YOLO or OCR could even attempt to find tokens or decode characters.

---

## 5. QualityGate Behavior After Fix

1. **Preflight Stage (`QualityGate.check_preflight(image)`):**
   - **Corrupt / Non-decodable:** Returns `(can_continue=False, hard_stop="IMAGE_DECODE_FAILED", quality_flags=[])`.
   - **Effectively Empty:** Robust pixel variance & edge count check (`np.var(gray) < 1.0` and `edge_count < 10`). If proven blank, returns `(can_continue=False, hard_stop="IMAGE_EFFECTIVELY_EMPTY", quality_flags=["IMAGE_BLANK"])`.
   - **Decodable Non-Empty Image:** Evaluates heuristic checks (darkness, blur, glare, uneven lighting, incomplete crop) and accumulates advisory flags (`quality_flags`), but returns `can_continue=True, hard_stop=None`.
2. **Recognition Always Runs:**
   - `engine.recognize(image)` is **always** executed for all decodable, non-empty images.
   - Heuristics never abort execution before YOLO/detector/OCR.
3. **Post-Recognition Substantiation:**
   - Quality heuristics are only consulted **after** recognition has executed. If YOLO returns 0 tokens AND quality heuristics detected severe issues (e.g. `BLUR`), then `IMAGE_QUALITY_FAILED` may be selected with concrete supporting evidence. If no quality issues were detected, it selects `DETECTOR_NO_TOKENS`.

### Explicit Answers After Fix:
- **QUALITY_GATE_CAN_SHORT_CIRCUIT_BEFORE_DETECTOR:** `ABSENT`
- **QUALITY_GATE_CAN_SHORT_CIRCUIT_BEFORE_OCR:** `ABSENT`

---

## 6. Recognition Attempt Diagnostics

The AI service, Spring Boot API, and Student Mobile now track and propagate the following internal stage proof fields:

| Field | Type | Description |
|---|---|---|
| `detectorInvoked` | `boolean` | `true` if YOLO detector was called |
| `detectorTokenCount` | `number` | Total tokens/bounding boxes found by YOLO |
| `ocrInvoked` | `boolean` | `true` if OCR bridge or CRNN was called |
| `ocrTextLength` | `number` | Length of raw text recognized by OCR |
| `parserInvoked` | `boolean` | `true` if arithmetic syntax parser ran |
| `parserStatus` | `string` | Status from parser (`PARSED`, `INVALID_LAYOUT`, etc.) |
| `validatorInvoked` | `boolean` | `true` if column-wise math validator ran |
| `validatorStatus` | `string` | Status from validator (`VALID`, `INVALID`, etc.) |
| `qualityFlags` | `string[]` | Heuristic quality warnings observed |
| `reasonCode` | `string` | Canonical reason code selected |

In `{__DEV__ && ...}` on Student Mobile, these fields are rendered directly in the `dev-diagnostic-panel`. Unavailable or non-applicable values render cleanly as `UNAVAILABLE` or `N/A`. In production (`__DEV__ == false`), the panel is completely stripped from the UI tree.

---

## 7. Reason Code Contract Consistency

| Internal Code (AI Engine) | Public Reason Code (Spring Boot / API) | UI Title | UI Subtitle |
|---|---|---|---|
| `IMAGE_DECODE_FAILED` | `IMAGE_DECODE_FAILED` | Lỗi đọc tệp ảnh | Tệp ảnh tải lên không đọc được. Em vui lòng chụp lại nhé! |
| `IMAGE_EFFECTIVELY_EMPTY` | `IMAGE_EFFECTIVELY_EMPTY` | Ảnh chụp chưa có bài làm | Ảnh chụp có vẻ còn trống hoặc chưa có nội dung bài tập. Em hãy đặt bài làm vào khung hình và chụp lại nhé. |
| `DETECTOR_NO_TOKENS` | `DETECTOR_NO_TOKENS` | MathVision chưa nhận diện được bài làm | MathVision đã thử nhận diện nhưng chưa nhận ra đủ chữ số hoặc dấu phép tính trong ảnh. |
| `INVALID_LAYOUT` | `INVALID_LAYOUT` | Cần thầy cô xem cách đặt tính | Các chữ số hoặc dấu phép tính chưa rõ ràng theo hàng dọc. Bài đã được chuyển cho thầy cô hỗ trợ em. |
| `OCR_LOW_CONFIDENCE` | `OCR_LOW_CONFIDENCE` | MathVision chưa chắc chắn kết quả | MathVision đã thử đọc bài của em nhưng chưa đủ chắc chắn để kết luận. Bài làm đã được giữ lại để xem thêm. |
| `IMAGE_QUALITY_FAILED` | `IMAGE_QUALITY_FAILED` | Chất lượng ảnh chụp chưa đạt | Ảnh chụp có thể bị chói sáng, quá tối hoặc bị che khuất. Em có thể chụp lại hoặc chờ thầy cô xem giúp. |
| `AI_RUNTIME_ERROR` | `AI_RUNTIME_ERROR` | Hệ thống đang bận | Hệ thống nhận diện đang bận hoặc gặp gián đoạn tạm thời. Bài của em đã được lưu an toàn để thầy cô xem lại. |

---

## 8. Student Copy Changes

| Reason Code | Previous Copy | Updated Neutral Copy |
|---|---|---|
| `OCR_LOW_CONFIDENCE` | *"Nét chữ trong bài có phần đặc biệt hoặc chưa rõ ràng, hệ thống đã chuyển bài để thầy cô xem kỹ hơn."* (Action: "Chụp lại rõ nét") | **"MathVision đã thử đọc bài của em nhưng chưa đủ chắc chắn để kết luận. Bài làm đã được giữ lại để xem thêm."** (Action: "Thử lại") |
| `DETECTOR_NO_TOKENS` / `NO_CONTENT_DETECTED` | *"Hệ thống chưa tìm thấy chữ số hoặc phép tính nào trong ảnh. Em kiểm tra lại bài làm hoặc chụp gần hơn nhé!"* | **"MathVision đã thử nhận diện nhưng chưa nhận ra đủ chữ số hoặc dấu phép tính trong ảnh."** (Action: "Thử lại") |
| `INVALID_LAYOUT` | Action: "Chụp lại ngay ngắn" | Action: "Thử lại" |

The child's handwriting is no longer blamed. The system truthfully communicates that it attempted recognition.

---

## 9. Arithmetic Runtime Tests

Controlled fixture tests added and verified in `services/ai-service/tests/test_fixture_e2e.py`:
- **Clear Supported Image (`test_e2e_clear_image_attempts_recognition`):** `detectorInvoked = True`, tokens found, successful grade proposal.
- **Slight Blur Image (`test_e2e_quality_severe_blur_attempts_recognition_and_abstains`):** `detectorInvoked = True`, `qualityFlags = ["SLIGHT_BLUR"]`. Image is not short-circuited before detector.
- **Dark Image (`test_e2e_quality_dark_image_still_attempts_recognition`):** `detectorInvoked = True`, `qualityFlags = ["DARK"]`. Recognition is attempted.
- **Incomplete Crop Image (`test_e2e_quality_crop_still_attempts_recognition`):** `detectorInvoked = True`, `qualityFlags = ["INCOMPLETE_CROP"]`. Recognition is attempted.
- **Uneven Lighting Image (`test_e2e_uneven_lighting_attempts_recognition`):** `detectorInvoked = True`. Recognition is attempted.
- **Blank Image (`test_e2e_empty_image_stops_as_effectively_empty`):** Preflight pixel variance check flags `IMAGE_EFFECTIVELY_EMPTY`.
- **Corrupt Image (`test_e2e_corrupt_payload_rejects`):** Preflight check fails with `IMAGE_DECODE_FAILED`.

---

## 10. Pilot 1 Regression

- **Endpoint:** `POST /internal/v1/ocr/recognize-line`
- **Verification:** Tested in `test_ocr_pilot_endpoint.py` (lines 36-111).
- **Behavior:**
  - Valid line crop invokes CRNN recognizer.
  - Returns `recognized_text`, checkpoint SHA-256 (`a807...`), vocab SHA-256 (`6af4...`), and execution latency.
  - Requires `X-Internal-API-Key`; rejects invalid or missing auth with 401.
  - Rejects oversized payloads (>10MB) with 413.
- **Verdict:** **PASS** (Non-regressed).

---

## 11. Pilot 2 Manual Fallback Regression

- **Endpoint:** `POST /internal/v1/ocr/detect-lines`
- **Verification:** Tested in `test_ocr_pilot_endpoint.py` (lines 115-227) and inspected in `src/app/ocr-pilot/multiline-review.tsx`.
- **Behavior:**
  - When auto line detection runs on a blank or faint page, it returns HTTP 200 with `len(data["lines"]) == 0`.
  - In `multiline-review.tsx`:
    - Zero-line state is safely handled (`boxes = []`, `selectedId = null`).
    - The student/teacher can tap "Thêm dòng" (`handleAddLine`), which inserts a default manual line box.
    - Drag/resize controls (`handleMove`, `handleResize`) allow positioning the box over handwriting.
    - Submitting ("Nhận diện") sends the user-defined boxes to `POST /api/v1/ocr/multiline/trials` without being blocked by an automated blur or review gate.
- **Verdict:** **PASS** (Non-regressed).

---

## 12. Full AI Test Suite

Executed via `uv run pytest tests/` with `PYTHONPATH=.` from `services/ai-service`:

```
collected 164 items

tests\test_ai_job_ocr_bridge.py ...                                      [  1%]
tests\test_api.py ....                                                   [  4%]
tests\test_callback_retry.py ..                                          [  5%]
tests\test_celery.py .                                                   [  6%]
tests\test_confidence.py ......                                          [  9%]
tests\test_earliest_error.py ....                                        [ 12%]
tests\test_evaluation_harness.py .....                                   [ 15%]
tests\test_fixture_e2e.py ..............                                 [ 23%]
tests\test_image_resolver.py ............                                [ 31%]
tests\test_manifest.py ...........                                       [ 37%]
tests\test_minio_pipeline.py .                                           [ 38%]
tests\test_model_e2e.py ....                                             [ 40%]
tests\test_model_preprocessing.py ...                                    [ 42%]
tests\test_model_smoke_timing.py .                                       [ 43%]
tests\test_ocr_adapter.py .........                                      [ 48%]
tests\test_ocr_bridge.py ..............                                  [ 57%]
tests\test_ocr_pilot_endpoint.py ..............                          [ 65%]
tests\test_parser.py ....                                                [ 68%]
tests\test_parser_non_regression.py ..                                   [ 69%]
tests\test_policy.py ..................                                  [ 80%]
tests\test_quality.py ...                                                [ 82%]
tests\test_row_grouper.py ...............                                [ 91%]
tests\test_validation.py ....                                            [ 93%]
tests\test_yolo_adapter.py ..........                                    [100%]

====================== 164 passed, 2 warnings in 16.92s =======================
```

- **Total:** 164
- **Passed:** 164
- **Failed:** 0
- **Skipped:** 0
- **XFailed:** 0
- **Warnings:** 2 (Starlette deprecation notices)
- **Manually Deselected:** **0**

---

## 13. Full Spring Test Suite

Executed via `gradlew.bat test` from `services/business-api`:

- **Gradle Build Result:** `BUILD SUCCESSFUL in 50s`
- **Total Tests Run:** 123
- **Passed:** 123
- **Failures:** 0
- **Errors:** 0
- **Skipped:** 0

Verified with XML report aggregation:
`Total: 123, Passed: 123, Failures: 0, Errors: 0, Skipped: 0`

---

## 14. Mobile Type & Lint Verification

Executed from workspace root:
- `npx tsc --noEmit`: **0 errors (Exit code 0)**
- `npm run lint`: **0 errors (Exit code 0)**
- Production UI inspection: `{__DEV__ && ...}` ensures that in production builds (`__DEV__ == false`), the DEV diagnostic panel is completely omitted from the rendered UI tree.

---

## 15. Physical Test Protocol

The matrix no longer predicts hypothetical model output. Outcomes must be recorded live on an Android physical device:

| Capture Case | Description | recognitionAttempted | detectorInvoked | detectorTokenCount | Actual reasonCode | Actual Result |
|---|---|---|---|---|---|---|
| **Capture A** | Clear neat handwriting | `[ ] YES / [ ] NO` | `[ ] true / [ ] false` | `___` | `__________________` | `__________________` |
| **Capture B** | Clear but messy handwriting | `[ ] YES / [ ] NO` | `[ ] true / [ ] false` | `___` | `__________________` | `__________________` |
| **Capture C** | Slightly blurred handwriting | `[ ] YES / [ ] NO` | `[ ] true / [ ] false` | `___` | `__________________` | `__________________` |
| **Capture D** | Blank / irrelevant page | `[ ] YES / [ ] NO` | `[ ] true / [ ] false` | `___` | `__________________` | `__________________` |

- **PASS Criterion:** Captures A, B, and C **must have recognition attempted** (`detectorInvoked = true` or `recognitionAttempted = true`). They must not be rejected by a pre-recognition quality gate.
- **Physical Test Status:** `OWNER_TEST_REQUIRED`

---

## 16. Files Modified

1. `services/ai-service/app/recognition/quality.py`: Added `check_preflight()` for non-short-circuit advisory quality flags.
2. `services/ai-service/app/jobs/tasks.py`: Removed early quality gate abort; added recognition stage diagnostics capture; updated reason code selection.
3. `services/ai-service/app/schemas/jobs.py`: Added `diagnostics: Optional[Dict[str, Any]]` to `AiCallbackRequest`.
4. `services/ai-service/app/policy/student_policy.py`: Neutralized Vietnamese student messages.
5. `services/ai-service/tests/test_fixture_e2e.py`: Converted tests from early-rejection assertions to always-attempt assertions.
6. `services/ai-service/tests/test_policy.py`: Updated title assertions for neutral copy.
7. `services/business-api/src/main/java/com/mathvisionkids/api/analysis/AiCallbackRequest.java`: Added `private Map<String, Object> diagnostics`.
8. `services/business-api/src/main/java/com/mathvisionkids/api/analysis/InternalAiCallbackController.java`: Stored `diagnostics` in `reviewReasons`.
9. `services/business-api/src/main/java/com/mathvisionkids/api/submission/SubmissionResponse.java`: Added `private Map<String, Object> diagnostics`.
10. `services/business-api/src/main/java/com/mathvisionkids/api/submission/StudentSubmissionController.java`: Exposed `diagnostics` in submission response.
11. `services/business-api/src/test/java/com/mathvisionkids/api/analysis/InternalAiCallbackControllerTest.java`: Added diagnostics persistence test.
12. `services/business-api/src/test/java/com/mathvisionkids/api/submission/SubmissionControllerTest.java`: Added diagnostics exposure test.
13. `src/types/index.ts`: Added `RecognitionAttemptDiagnostics` interface and `diagnostics` field to `SubmissionResult`.
14. `src/services/api/MockSubmissionService.ts`: Added diagnostics to mock review results.
15. `src/app/processing.tsx`: Forwarded `diagnostics` in router parameters to `/results/review-required`.
16. `src/app/results/review-required.tsx`: Neutralized copy; expanded DEV diagnostic panel with stage fields.

---

## 17. Remaining Model-Accuracy Limitations

1. **OCR / YOLO Accuracy on Extreme Distortions:** The AI pipeline now guarantees that an attempt is always made on decodable images. However, when handwriting is severely degraded, YOLO may detect 0 tokens (`DETECTOR_NO_TOKENS`) or CRNN confidence may fall below certainty thresholds (`OCR_LOW_CONFIDENCE`). This is expected model behavior and is safely routed to teacher review.
2. **Physical Device Verification Required:** Live camera sensor noise and varied lighting must be verified on the physical device via the protocol in Section 15.

---

## 18. Final Verdict

- **OCR.RUNTIME.1.1:** **PASS**
- **QualityGate Short-Circuit Before Detector:** **ABSENT**
- **Recognition Attempted for Clear & Degraded Images:** **PASS**
- **Full AI Suite (0 Deselected):** **164 / 164 PASSED**
- **Full Spring Suite:** **123 / 123 PASSED**
- **Mobile TSC & Lint:** **PASS**
- **Physical Android:** **OWNER_TEST_REQUIRED**
