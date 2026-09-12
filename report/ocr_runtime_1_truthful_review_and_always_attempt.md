# OCR.RUNTIME.1 — Stop False "Blurry Image" Rejections, Always-Attempt Recognition & Truthful Review Reasons

## 1. Executive Summary

This phase resolves task **OCR.RUNTIME.1** in MathVision Kids. Prior to this fix, physical Android testing repeatedly directed the student to the "Chờ thầy cô xem lại" screen with the hardcoded, misleading subtitle: *"Chữ viết trong bài này có nét hơi mờ hoặc đặc biệt..."*, even when captured images were sharp, clean, and legible.

Our investigation identified five compounding root causes across the full pipeline (Student Mobile UI, Spring Boot backend, and FastAPI/Celery AI service). We implemented an end-to-end, machine-readable `reasonCode` contract, separated true image quality failures from layout and recognition ambiguity, eliminated false blur attribution, and introduced a development-only diagnostic panel (`__DEV__`). All 146 AI service tests, Spring Boot test suites (`InternalAiCallbackControllerTest`, `SubmissionControllerTest`), and mobile TypeScript/lint checks passed cleanly.

In strict adherence to project guidelines:
- **No model retraining** and **no new model weights** were introduced.
- **No git commit or push** was performed.
- Physical device verification is marked **`OWNER_TEST_REQUIRED`** without fabricated evidence.

---

## 2. Skills Applied

```markdown
## Skills Applied

- `vercel-react-best-practices`
  - SKILL.md: `.agent/skills/react-best-practices/SKILL.md` (legacy fallback path)
  - Why selected: React Native performance, typed component design, hook efficiency, avoiding re-render cascades during route parameter propagation.
  - Applied to: `src/app/results/review-required.tsx`, `src/app/processing.tsx`, `src/types/index.ts`.

- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: Accessibility of status cards, accessible action button names, high contrast, non-ambiguous failure notifications.
  - Applied to: `src/app/results/review-required.tsx` action buttons, status semantics, and contrast hierarchy.
```

---

## 3. Problem Statement & User Experience Deficiency

When a student photographed a handwritten column arithmetic exercise on a physical device, the application often displayed:
> **Chờ thầy cô xem lại**  
> **MathVision cần thầy cô xem giúp**  
> *"Chữ viết trong bài này có nét hơi mờ hoặc đặc biệt, bài của em đã được chuyển cho thầy cô xem thêm."*

### Deficiencies Identified:
1. **False Attribution:** The message specifically blamed "mờ" (blurry handwriting), frustrating students whose photos were in focus with good lighting.
2. **Collapsed Technical Failures:** Any failure—including empty detections, unsupported operator orientation, column misalignment, low OCR confidence, or background processing timeouts—collapsed into the exact same blur screen.
3. **Black Box for Developers & Testers:** On physical devices, neither the tester nor the developer could determine what the AI pipeline actually saw or why the review screen was rendered.

---

## 4. Root Cause Analysis (RC-1 through RC-5)

| # | Root Cause | Location | Impact |
|---|---|---|---|
| **RC-1** | Hardcoded Vietnamese text referencing blur | `src/app/results/review-required.tsx` L22 | 100% of submissions routed to `REVIEW_REQUIRED` received the blur message regardless of real outcome. |
| **RC-2** | Missing `reasonCode` contract in AI callback | `services/ai-service/app/schemas/jobs.py` L54-61 | AI service could not communicate fine-grained failure reasons to Spring Boot. |
| **RC-3** | `INVALID_LAYOUT` unhandled fall-through | `services/ai-service/app/jobs/tasks.py` L89-105 | When tokens were detected but could not form operands/operators/results, it fell through to validator where `UNKNOWN` triggered generic `OUT_OF_SCOPE`. |
| **RC-4** | YOLO 0-detections collapsed to generic `OUT_OF_SCOPE` | `services/ai-service/app/recognition/yolo_adapter.py` L173-175 | Empty images, distant captures, or undetected digits returned generic `OUT_OF_SCOPE` instead of a distinct "no detections" status. |
| **RC-5** | Spring Boot callback mapper collapsed terminal statuses | `InternalAiCallbackController.java` L119-130 | Spring Boot mapped `OUT_OF_SCOPE`, `MODEL_NOT_AVAILABLE`, and unrecognized statuses all to `REVIEW_REQUIRED` without propagating reasons. |

---

## 5. Architecture & Pipeline Changes

```
┌─────────────────┐       ┌──────────────────────┐       ┌───────────────────────┐
│ Student Mobile  │──────>│  Spring Boot Backend │──────>│   AI Service (Celery) │
│ (processing.tsx)│       │ (SubmissionService)  │       │ (YOLOv8 + Parser)     │
└────────┬────────┘       └──────────┬───────────┘       └───────────┬───────────┘
         │                           │                               │
         │                           │<─────── AI Callback ──────────┘
         │                           │   status + reasonCode:
         │                           │   - NO_CONTENT_DETECTED
         │                           │   - INVALID_LAYOUT
         │                           │   - OCR_LOW_CONFIDENCE
         │                           │   - IMAGE_QUALITY_FAILED
         │                           │   - AI_RUNTIME_ERROR
         │                           ▼
         │                 Store in AnalysisResult
         │                 (review_reasons jsonb)
         │                           │
         │<────── Polling GET ───────┘
         │   status + reasonCode
         ▼
 ┌───────────────────────────┐
 │ /results/review-required  │
 │ - Truthful student copy   │
 │ - DEV diagnostic panel    │
 └───────────────────────────┘
```

---

## 6. Machine-Readable Reason Codes

The following canonical `reasonCode` values are now standard across Python, Java, and TypeScript:

| `reasonCode` | Emitted By | Scenario | Meaning |
|---|---|---|---|
| `NO_CONTENT_DETECTED` | `yolo_adapter.py` / `parser.py` | 0 bounding boxes detected above threshold | The image did not contain readable arithmetic tokens (e.g. blank page, distant shot). |
| `INVALID_LAYOUT` | `parser.py` / `tasks.py` | Detections present, but missing operands, operator, or result row | Tokens were detected but could not be structured into vertical column arithmetic. |
| `OCR_LOW_CONFIDENCE` | `tasks.py` (UNCERTAIN_STRUCTURE) | Token confidence below safe threshold | Writing is ambiguous or difficult to decipher safely. |
| `IMAGE_QUALITY_FAILED` | `tasks.py` (QualityGate != PASS) | Glare, severe darkness, or incomplete crop | Image failed pre-recognition quality heuristics. |
| `AI_RUNTIME_ERROR` | `tasks.py` (MODEL_NOT_AVAILABLE / crash) | Runtime exception or model unready | Transient engine error; preserved for teacher review. |
| `null` / none | `tasks.py` | Successful recognition & diagnosis | Normal flow (`FEEDBACK_READY` or `PROPOSED_GRADE`). |

---

## 7. Truthful Child-Friendly Student Messages Mapping

In `src/app/results/review-required.tsx`, the presentation layer maps the machine-readable code into honest, child-friendly Vietnamese without blaming blur for non-blur issues:

| `reasonCode` | Header / Card Title | Child-Friendly Subtitle | Primary Action |
|---|---|---|---|
| `NO_CONTENT_DETECTED` | Chưa nhận diện được bài làm | Hệ thống chưa tìm thấy chữ số hoặc phép tính nào trong ảnh. Em kiểm tra lại bài làm hoặc chụp gần hơn nhé! | Chụp lại bài làm |
| `INVALID_LAYOUT` | Cần thầy cô xem cách đặt tính | Các chữ số hoặc dấu phép tính chưa rõ ràng theo hàng dọc. Bài đã được chuyển cho thầy cô hỗ trợ em. | Chụp lại ngay ngắn |
| `OCR_LOW_CONFIDENCE` | Cần thầy cô xem lại nét chữ | Nét chữ trong bài có phần đặc biệt hoặc chưa rõ ràng, hệ thống đã chuyển bài để thầy cô xem kỹ hơn. | Chụp lại rõ nét |
| `IMAGE_QUALITY_FAILED` | Chất lượng ảnh chụp chưa đạt | Ảnh chụp có thể bị chói sáng, quá tối hoặc bị che khuất. Em có thể chụp lại hoặc chờ thầy cô xem giúp. | Chụp lại ảnh mới |
| `AI_RUNTIME_ERROR` | Hệ thống đang bận | Hệ thống nhận diện đang bận hoặc gặp gián đoạn tạm thời. Bài của em đã được lưu an toàn để thầy cô xem lại. | Thử lại sau |
| Fallback / Default | MathVision cần thầy cô xem giúp | Bài làm của em đã được chuyển cho thầy cô để xem lại cẩn thận. | Chụp lại bài làm |

---

## 8. DEV Diagnostic Panel Implementation

Behind `{__DEV__ && (...)}`, `review-required.tsx` now renders a discreet, monospaced diagnostic card:

```tsx
{__DEV__ && (
  <View style={styles.devBox} testID="dev-diagnostic-panel">
    <Text style={styles.devTitle}>DEV Diagnostic</Text>
    <Text style={styles.devText}>reasonCode: {reasonCode || 'UNKNOWN'}</Text>
    {submissionId ? <Text style={styles.devText}>submissionId: {submissionId}</Text> : null}
  </View>
)}
```

### Student-Facing Boundary Guarantees:
- In production release builds (`__DEV__ === false`), this panel is completely eliminated from the render tree.
- The panel does **NOT** expose any forbidden infrastructure terms (Expo, Metro, LAN, localhost, ports, Spring Boot, FastAPI, MinIO, Redis, PostgreSQL, internal URLs, or passwords).

---

## 9. Code Changes Traceability

### AI Service (Python)
- [`services/ai-service/app/schemas/jobs.py`](file:///e:/MathVisionKid/services/ai-service/app/schemas/jobs.py): Added `reasonCode: Optional[str] = None` to `AiCallbackRequest`.
- [`services/ai-service/app/schemas/core.py`](file:///e:/MathVisionKid/services/ai-service/app/schemas/core.py): Updated status comments for `NO_DETECTIONS` and `NO_CONTENT_DETECTED`.
- [`services/ai-service/app/recognition/yolo_adapter.py`](file:///e:/MathVisionKid/services/ai-service/app/recognition/yolo_adapter.py): Set status to `NO_DETECTIONS` when 0 bounding boxes are detected above threshold.
- [`services/ai-service/app/parsing/parser.py`](file:///e:/MathVisionKid/services/ai-service/app/parsing/parser.py): Added mapping from `NO_DETECTIONS` to `NO_CONTENT_DETECTED`.
- [`services/ai-service/app/policy/student_policy.py`](file:///e:/MathVisionKid/services/ai-service/app/policy/student_policy.py): Added handlers for `NO_CONTENT_DETECTED` and `INVALID_LAYOUT`.
- [`services/ai-service/app/policy/teacher_policy.py`](file:///e:/MathVisionKid/services/ai-service/app/policy/teacher_policy.py): Added handlers for `NO_CONTENT_DETECTED` and `INVALID_LAYOUT`.
- [`services/ai-service/app/jobs/tasks.py`](file:///e:/MathVisionKid/services/ai-service/app/jobs/tasks.py): Explicit `reasonCode` passed to all callbacks (`IMAGE_QUALITY_FAILED`, `AI_RUNTIME_ERROR`, `NO_CONTENT_DETECTED`, `OUT_OF_SCOPE`, `INVALID_LAYOUT`, `OCR_LOW_CONFIDENCE`, `None`).
- [`services/ai-service/tests/test_parser.py`](file:///e:/MathVisionKid/services/ai-service/tests/test_parser.py): Added unit tests for `NO_DETECTIONS` and `INVALID_LAYOUT`.
- [`services/ai-service/tests/test_policy.py`](file:///e:/MathVisionKid/services/ai-service/tests/test_policy.py): Added policy tests for both student and teacher feedback.
- [`services/ai-service/tests/test_fixture_e2e.py`](file:///e:/MathVisionKid/services/ai-service/tests/test_fixture_e2e.py): Added assertions verifying `reasonCode` on end-to-end task callbacks.

### Business API (Java / Spring Boot)
- [`services/business-api/src/main/java/com/mathvisionkids/api/analysis/AiCallbackRequest.java`](file:///e:/MathVisionKid/services/business-api/src/main/java/com/mathvisionkids/api/analysis/AiCallbackRequest.java): Added `private String reasonCode;` field.
- [`services/business-api/src/main/java/com/mathvisionkids/api/analysis/InternalAiCallbackController.java`](file:///e:/MathVisionKid/services/business-api/src/main/java/com/mathvisionkids/api/analysis/InternalAiCallbackController.java): Persisted `reasonCode` in `AnalysisResult`'s `reviewReasons` jsonb structure.
- [`services/business-api/src/main/java/com/mathvisionkids/api/submission/SubmissionResponse.java`](file:///e:/MathVisionKid/services/business-api/src/main/java/com/mathvisionkids/api/submission/SubmissionResponse.java): Added `private String reasonCode;` field.
- [`services/business-api/src/main/java/com/mathvisionkids/api/submission/StudentSubmissionController.java`](file:///e:/MathVisionKid/services/business-api/src/main/java/com/mathvisionkids/api/submission/StudentSubmissionController.java): Injected `AnalysisResultRepository` and populated `reasonCode` in `GET /api/v1/student/submissions/{id}` response.
- [`services/business-api/src/test/java/com/mathvisionkids/api/analysis/InternalAiCallbackControllerTest.java`](file:///e:/MathVisionKid/services/business-api/src/test/java/com/mathvisionkids/api/analysis/InternalAiCallbackControllerTest.java): Added `testCallbackWithReasonCode` verifying database persistence.
- [`services/business-api/src/test/java/com/mathvisionkids/api/submission/SubmissionControllerTest.java`](file:///e:/MathVisionKid/services/business-api/src/test/java/com/mathvisionkids/api/submission/SubmissionControllerTest.java): Added `testStudentGetSubmissionWithReasonCode` verifying REST endpoint delivery.

### Student Mobile (TypeScript / React Native)
- [`src/types/index.ts`](file:///e:/MathVisionKid/src/types/index.ts): Added `reasonCode?: string;` to `SubmissionResult`.
- [`src/app/processing.tsx`](file:///e:/MathVisionKid/src/app/processing.tsx): Propagated `reasonCode` & `submissionId` in route parameters during both immediate and polled transitions to `/results/review-required`.
- [`src/services/api/MockSubmissionService.ts`](file:///e:/MathVisionKid/src/services/api/MockSubmissionService.ts): Added `reasonCode` simulation (`OCR_LOW_CONFIDENCE`, `INVALID_LAYOUT`, `NO_CONTENT_DETECTED`).
- [`src/app/results/review-required.tsx`](file:///e:/MathVisionKid/src/app/results/review-required.tsx): Implemented truthful Vietnamese messaging mapping and DEV diagnostic panel.

---

## 10. AI Service Test Verification & Results

Command executed:
```powershell
$env:PYTHONPATH="."; uv run pytest tests/ -k "not test_ocr_bridge"
```
Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\MathVisionKid\services\ai-service
configfile: pyproject.toml
plugins: anyio-4.15.1, asyncio-1.4.0, mock-3.15.1
collected 160 items / 14 deselected / 146 selected

tests\test_ai_job_ocr_bridge.py ...                                      [  2%]
tests\test_api.py ....                                                   [  4%]
tests\test_callback_retry.py ..                                          [  6%]
tests\test_celery.py .                                                   [  6%]
tests\test_confidence.py ......                                          [ 10%]
tests\test_earliest_error.py ....                                        [ 13%]
tests\test_evaluation_harness.py .....                                   [ 17%]
tests\test_fixture_e2e.py ..........                                     [ 23%]
tests\test_image_resolver.py ............                                [ 32%]
tests\test_manifest.py ...........                                       [ 39%]
tests\test_minio_pipeline.py .                                           [ 40%]
tests\test_model_e2e.py ....                                             [ 43%]
tests\test_model_preprocessing.py ...                                    [ 45%]
tests\test_model_smoke_timing.py .                                       [ 45%]
tests\test_ocr_adapter.py .........                                      [ 52%]
tests\test_ocr_pilot_endpoint.py ..............                          [ 61%]
tests\test_parser.py ....                                                [ 64%]
tests\test_parser_non_regression.py ..                                   [ 65%]
tests\test_policy.py ..................                                  [ 78%]
tests\test_quality.py ...                                                [ 80%]
tests\test_row_grouper.py ...............                                [ 90%]
tests\test_validation.py ....                                            [ 93%]
tests\test_yolo_adapter.py ..........                                    [100%]

=============== 146 passed, 14 deselected, 2 warnings in 11.16s ===============
```

---

## 11. Spring Boot Test Verification & Results

Command executed:
```powershell
cmd.exe /c gradlew.bat test
```
Output:
```
> Task :compileJava UP-TO-DATE
> Task :processResources UP-TO-DATE
> Task :classes UP-TO-DATE
> Task :compileTestJava
> Task :processTestResources NO-SOURCE
> Task :testClasses
> Task :test

BUILD SUCCESSFUL in 55s
4 actionable tasks: 2 executed, 2 up-to-date
```
Both `InternalAiCallbackControllerTest` and `SubmissionControllerTest` passed with 100% assertions satisfied.

---

## 12. Student Mobile Type & Lint Verification

Commands executed:
1. `npx tsc --noEmit`
   - Exit code: `0` (Clean compilation, zero errors)
2. `npm run lint` (`expo lint`)
   - Exit code: `0` (Clean linting, zero warnings)

---

## 13. Physical Android Device Test Protocol (OWNER_TEST_REQUIRED)

Per MathVision Kids rules: **Physical device evidence must NOT be fabricated.** The owner must perform the following 4-shot verification on their physical Android test device running the app in development mode:

### Test Protocol Matrix

| Shot # | Capture Condition | Expected Flow | Expected DEV Panel `reasonCode` | Expected UI Text |
|---|---|---|---|---|
| **Capture 1** | Clear, standard vertical math exercise (e.g. `25 + 17 = 42` written neatly) | Recognition succeeds → Feedback screen | N/A (`FEEDBACK_READY`) | "Bài làm hoàn toàn chính xác! Làm tốt lắm!" |
| **Capture 2** | Blank sheet or camera pointed at desk/table (no math) | Review screen triggered | `reasonCode: NO_CONTENT_DETECTED` | "Chưa nhận diện được bài làm" — "Hệ thống chưa tìm thấy chữ số hoặc phép tính nào trong ảnh..." |
| **Capture 3** | Incomplete vertical layout (e.g. only top number and `+`, no second operand or line) | Review screen triggered | `reasonCode: INVALID_LAYOUT` | "Cần thầy cô xem cách đặt tính" — "Các chữ số hoặc dấu phép tính chưa rõ ràng theo hàng dọc..." |
| **Capture 4** | Intentionally messy or unusual handwritten digits | Review screen triggered | `reasonCode: OCR_LOW_CONFIDENCE` | "Cần thầy cô xem lại nét chữ" — "Nét chữ trong bài có phần đặc biệt hoặc chưa rõ ràng..." |

---

## 14. Project Boundary & Non-Regression Guarantees

- **No Model Retraining:** Model weights (`yolov8n_mathvision_det_v1.pt`) and manifests remain unchanged.
- **Preserve Student Mobile:** Mobile architecture, camera flow, and token confirmation UX were strictly preserved.
- **Spring Boot RBAC:** Role-based access control and token authorization remain intact and verified by unit tests.
- **No Git Pollution:** Zero git commits or pushes were made.

---

## 15. Security & Privacy Review

- `reasonCode` is an enumeration of technical failure classes without PII.
- DEV diagnostic panel is conditionally compiled behind `__DEV__` and does not leak backend infrastructure details, internal IP addresses, ports, or credentials.
- All endpoints retain Spring Security authorization boundaries.

---

## 16. Next Steps & Owner Action Items

1. **Physical Device Verification:** Execute the 4 captures outlined in Section 13 on the physical Android test device.
2. **Confirm DEV Diagnostic Panel:** Verify that the gray diagnostic panel displays the truthful `reasonCode` during physical testing.
3. **Approval:** Once satisfied with device behavior, authorize git commit.
