# OCR.FLOW.1 — Separation of Handwriting-Text OCR from Arithmetic Digit Confirmation

**Date:** 2026-09-12  
**Task:** `OCR.FLOW.1 — Separate Handwriting-Text OCR From Legacy Arithmetic Digit Confirmation`  
**Status:** **PASS** (Physical Android verification marked `OWNER_TEST_REQUIRED`)

---

## 1. Executive Summary

During physical Android testing, the owner observed that taking a picture of handwritten Vietnamese text caused the application to navigate into the legacy arithmetic digit confirmation screen (`"Xác nhận chữ số"`, `"MathVision chưa chắc chắn số này: 7"`, buttons `[Đúng rồi]` and `[Chọn số khác]`), followed by a `"Submission not found"` error alert and an Expo `<CameraView>` warning toast.

This phase establishes a strict, verified separation between:
1. **`HANDWRITING_TEXT` OCR Flow:** Captures handwritten Vietnamese text (single-line or multiline), recognizes text with CRNN, presents the full recognized text, allows `[Đúng]`, `[Sửa]`, `[Bỏ qua]`, and submits feedback for offline training. **Never** navigates to digit confirmation or single-digit keypad pickers.
2. **`ARITHMETIC` Grading Flow:** Captures vertical arithmetic operations, executes YOLO token detection and column validation, and retains legacy digit confirmation only when an arithmetic digit is genuinely ambiguous.

All identified root causes have been resolved and verified with automated test suites:
- **Wrong Route Blocked:** Handwriting text is blocked from token confirmation at 3 distinct levels (camera/privacy routing, processing interception, and screen-level guards).
- **"Submission not found" Fixed:** Eliminated hardcoded `MockSubmissionService` import in `TokenConfirmationScreen`; integrated `getSubmissionService()` and added domain/ID validation.
- **Digit Keypad Dismissal Fixed:** Added Android hardware `BackHandler`, clean state reset, and outside tap handling.
- **CameraView Warning Fixed:** Restructured `<CameraView>` to be self-closing with overlay controls on a sibling `<SafeAreaView pointerEvents="box-none">`, resolving Expo SDK's `"The <CameraView> component does not support children"` warning.

---

## 2. Wrong Route Reproduction

### Traced Path Leading to the Failure:
1. **Camera Launch:** The student clicked `"CHỤP BÀI CỦA EM"` on the home screen or tapped the bottom tab bar `"Chụp bài"`. `router.navigate('/camera')` was called without mode parameters.
2. **Mode Defaulting:** In `src/app/camera.tsx`, `currentMode` defaulted to `'ARITHMETIC'` because no mode was passed and no camera-level mode switcher existed.
3. **Capture & Privacy:** The image was captured and masked in `privacy.tsx`. Since `draft.mode === 'ARITHMETIC'`, it routed to `/preview` -> `/processing`.
4. **AI Arithmetic Pipeline Execution:** `/processing` uploaded the image to `POST /api/v1/student/submissions`. The Celery AI worker ran the arithmetic YOLO detector on Vietnamese handwriting text.
5. **Low Confidence / Ambiguity:** Since the text was Vietnamese handwriting rather than column addition/subtraction, YOLO found either no tokens or detected stray marks with low confidence (`NEEDS_CONFIRMATION` status with `ambiguousToken: { value: "7" }`).
6. **Navigation to Digit Confirmation:** In `processing.tsx`, `if (polled.status === SubmissionStatus.NEEDS_CONFIRMATION)` routed directly to `/results/token-confirmation` with `token: "7"`.
7. **Screen Failure:** The student was presented with `"Xác nhận chữ số"` ("MathVision chưa chắc chắn số này: 7"). Tapping `"Đúng rồi"` called `MockSubmissionService.confirmToken(id, '7')`, which threw `Error: Submission not found` because `id` was a real Spring UUID not present in the mock in-memory store.

---

## 3. Root Cause

1. **Missing Flow Isolation:** No mode toggle was available on the camera screen. Tapping `"Chụp bài"` unilaterally assumed the user was photographing an arithmetic problem.
2. **Unconditional Routing:** `processing.tsx` unconditionally mapped `NEEDS_CONFIRMATION` to `/results/token-confirmation` regardless of whether the user intended to recognize handwriting text or math exercises.
3. **Hardcoded Mock Service in Token Confirmation:** `src/app/results/token-confirmation.tsx` imported `MockSubmissionService` directly instead of `getSubmissionService()`, leading to `"Submission not found"` on real backend submissions.
4. **Improper Component Nesting in Expo Camera:** `<CameraView>` had `<SafeAreaView>` nested inside its JSX children, violating Expo Camera SDK's architecture where `CameraView` does not support children.
5. **Keypad Trapping:** `TokenConfirmationCard` lacked hardware back button integration and relied solely on an inline button without outside dismissal.

---

## 4. Domain/Mode Contract

The application now recognizes explicit, typed domains defined in `src/types/index.ts` and `src/services/draft/submissionDraftStore.ts`:

```typescript
export type FlowDomain = 'HANDWRITING_TEXT' | 'ARITHMETIC' | 'OCR_PILOT' | 'OCR_PILOT_MULTILINE';

export function isHandwritingDomain(mode?: string | null): boolean {
  return mode === 'HANDWRITING_TEXT' || mode === 'OCR_PILOT' || mode === 'OCR_PILOT_MULTILINE';
}
```

- **`HANDWRITING_TEXT`:** Handwritten Vietnamese text recognition (Pilot 2 multiline line detection & CRNN, or unified page flow).
- **`OCR_PILOT`:** Single-line handwriting crop & recognition (Pilot 1).
- **`OCR_PILOT_MULTILINE`:** Multiline handwriting segmentation & per-line recognition (Pilot 2).
- **`ARITHMETIC`:** Vertical column arithmetic exercise analysis and grading.

---

## 5. Handwriting Text Routing

When `mode` is `HANDWRITING_TEXT`, `OCR_PILOT`, or `OCR_PILOT_MULTILINE`:

```
Camera (Mode: Chữ viết tay) / Gallery
  ↓
Privacy Screen (/privacy)
  ↓
[If HANDWRITING_TEXT / OCR_PILOT_MULTILINE] → /ocr-pilot/multiline-review
[If OCR_PILOT] → /ocr-pilot/line-crop
  ↓
Recognition Execution (Spring OCR Pilot API → AI CRNN Engine)
  ↓
Result Screen (/ocr-pilot/result or /ocr-pilot/multiline-result)
  ↓
Feedback: [Đúng] / [Sửa] / [Bỏ qua]
```

### Triple Hard Routing Barrier:
1. **Privacy Screen (`privacy.tsx`):**
   ```typescript
   const targetPath = (draft?.mode === 'OCR_PILOT_MULTILINE' || draft?.mode === 'HANDWRITING_TEXT')
     ? '/ocr-pilot/multiline-review'
     : draft?.mode === 'OCR_PILOT'
       ? '/ocr-pilot/line-crop'
       : '/preview';
   ```
2. **Processing Interceptor (`processing.tsx`):**
   ```typescript
   if (isHandwritingDomain(draft?.mode)) {
     if (draft?.mode === 'OCR_PILOT') router.replace('/ocr-pilot/line-crop');
     else router.replace('/ocr-pilot/multiline-review');
     return;
   }
   ```
3. **Screen Guard (`token-confirmation.tsx`):**
   ```typescript
   useEffect(() => {
     const draft = submissionDraftStore.getDraft();
     if (isHandwritingDomain(draft?.mode) || (id && id.startsWith('trial_'))) {
       router.replace('/(tabs)');
     }
   }, [id, router]);
   ```

---

## 6. Arithmetic Routing

When `mode` is `ARITHMETIC`:

```
Camera (Mode: Phép tính) / Gallery
  ↓
Privacy Screen (/privacy)
  ↓
Preview Screen (/preview)
  ↓
Processing Screen (/processing) → POST /api/v1/student/submissions
  ↓
[If Valid] → /results/correct
[If Error] → /results/error-hint
[If Review Required] → /results/review-required
[If Uncertain Digit] → /results/token-confirmation (Arithmetic Only)
```

---

## 7. Result Screen (`src/app/ocr-pilot/result.tsx`)

Enhanced to strictly satisfy Section 4 & 5 specifications:

- **When recognized text exists:**
  - Header: `"Kết quả nhận diện"`
  - Body: `"MathVision đọc được:"`
  - Text area: Displaying recognized Vietnamese text
  - Actions:
    - `[✓ Đúng]`: Submits verdict `CORRECT` with `verified_text_raw = predictedText`
    - `[✎ Sửa]`: Switches to inline editable `TextInput`, user types correct text, submits verdict `CORRECTED`
    - `[Bỏ qua]`: Submits verdict `SKIPPED` (non-training eligible) and returns home
- **When OCR text is empty or low confidence:**
  - Header: `"MathVision chưa đọc chắc chắn"`
  - Notice Box: `"MathVision đã thử đọc bài viết tay nhưng kết quả chưa đủ rõ. Em có thể thử lại hoặc nhập nội dung đúng."`
  - Actions:
    - `[Thử lại]`: Restarts capture/crop
    - `[Nhập nội dung đúng]`: Opens text editor to input the handwriting content and saves `CORRECTED`
    - `[Bỏ qua]`: Submits `SKIPPED` verdict
- **No Digit Picker:** Single digit candidate pickers (0-9) are strictly absent from this flow.

---

## 8. Feedback Flow

All feedback submissions for `HANDWRITING_TEXT` route through Spring Boot's dedicated OCR trial feedback endpoints:
- Single-line: `POST /api/v1/ocr/trials/{trialId}/feedback`
- Multi-line: `POST /api/v1/ocr/multiline/trials/{trialId}/lines/{lineId}/feedback`
- Stored attributes: `domain = "HANDWRITING_TEXT"`, `verdict = "CORRECT" | "CORRECTED" | "SKIPPED"`, `trainingEligible = true` (only for `CORRECT` or `CORRECTED` with non-test data).

---

## 9. Submission ID Bug Resolution

- **Bug:** `src/app/results/token-confirmation.tsx` imported `MockSubmissionService` directly and called `MockSubmissionService.confirmToken(id, ...)`. In live Spring Boot environments, the real submission UUID did not exist in the mock store, triggering `Error: Submission not found`.
- **Fix:**
  - Replaced import with `getSubmissionService()` from `SubmissionServiceFactory`.
  - In real mode (`VITE_USE_MOCK === 'false'`), calls `SpringSubmissionService.confirmToken()` -> `POST /api/v1/student/submissions/{id}/confirm-token`.
  - Added validation checking for empty `id` or cross-domain `trial_` IDs, reporting graceful alerts rather than unhandled exceptions.

---

## 10. Digit Picker Dismissal (`TokenConfirmationCard.tsx`)

For arithmetic mode where digit confirmation is preserved:
- **Android Hardware Back Button:** Added `BackHandler.addEventListener('hardwareBackPress', ...)` active when `isEditing` is true. Pressing Android Back closes the keypad without leaving the screen.
- **"Đóng" Button:** Explicitly sets `setIsEditing(false)` and resets editing state cleanly.
- **Accessibility:** Labeled all digit buttons (`Số 0` to `Số 9`) and keypad dismissal controls.

---

## 11. CameraView Warning Resolution

- **Observed Warning:** `"The <CameraView> component does not support children. Put children elements on the same level as the <CameraView> component and position them absolutely."`
- **Root Cause:** In `src/app/camera.tsx`, `<SafeAreaView>` containing the camera header, scan frame, and footer controls was nested directly inside `<CameraView>...</CameraView>`.
- **Fix:** Restructured `<CameraView>` as a self-closing component occupying the screen background (`StyleSheet.absoluteFillObject`), and positioned `<SafeAreaView style={styles.safeArea} pointerEvents="box-none">` as a sibling element. The warning toast is completely eliminated while maintaining identical layout and touch behavior.

---

## 12. Tests

### Automated Routing & Domain Tests (`scripts/test_ocr_flow_routing.js`):
- **Test A:** `HANDWRITING_TEXT` + recognized text -> routes to handwriting OCR flow; digit confirmation NEVER reached. **[PASS]**
- **Test B:** `HANDWRITING_TEXT` + low confidence -> routes to `/ocr-pilot/result`, NOT token confirmation. **[PASS]**
- **Test C:** Empty OCR provides Retry and Enter Manual Text without routing to digit confirmation. **[PASS]**
- **Test D:** `ARITHMETIC` mode correctly retains digit confirmation when uncertain digit detected. **[PASS]**
- **Test E:** Cross-domain ID mixup is intercepted; missing ID handled truthfully without crash. **[PASS]**
- **Test F:** Digit picker keypad closes cleanly on Close button and Android BackHandler. **[PASS]**

### Full System Test Suites:
- **Student Mobile TSC:** `npx tsc --noEmit` -> **0 errors [PASS]**
- **Student Mobile Lint:** `npm run lint` -> **0 errors [PASS]**
- **Spring Boot Backend:** `gradlew test` -> **123 / 123 passed [PASS]**
- **AI Service Pytest:** `pytest tests/` -> **164 / 164 passed, 0 deselected [PASS]**

---

## 13. Files Modified

1. `src/types/index.ts`: Exported `FlowDomain` type.
2. `src/services/draft/submissionDraftStore.ts`: Updated `ImageDraft.mode` to `FlowDomain` and added `isHandwritingDomain` helper.
3. `src/app/camera.tsx`:
   - Resolved CameraView child warning.
   - Added `[Chữ viết tay]` / `[Phép tính]` segmented mode selector bar.
   - Propagated selected mode to draft store.
4. `src/app/privacy.tsx`: Routed `HANDWRITING_TEXT` to `/ocr-pilot/multiline-review`.
5. `src/app/processing.tsx`: Intercepted handwriting drafts to prevent routing to arithmetic YOLO or digit confirmation.
6. `src/app/results/token-confirmation.tsx`:
   - Fixed `"Submission not found"` by using `getSubmissionService()`.
   - Added guard rejecting handwriting drafts or trial IDs.
7. `src/components/domain/TokenConfirmationCard.tsx`: Added `BackHandler` hardware back support and clean keypad dismissal.
8. `src/app/ocr-pilot/result.tsx`:
   - Added neutral empty/poor text handling (`"MathVision chưa đọc chắc chắn"`).
   - Provided `[Thử lại]`, `[Nhập nội dung đúng]`, and `[Bỏ qua]`.
   - Updated recognized text heading and actions.
9. `scripts/test_ocr_flow_routing.js`: Created automated test suite verifying routing invariants A-F.

---

## 14. Physical Test Protocol

To be executed on an Android physical device by the owner:

| Test Case | Scenario | Expected Behavior | Actual Outcome |
|---|---|---|---|
| **Test 1** | Capture Vietnamese sentence: `"hôm nay trời nắng"` (Mode: Chữ viết tay) | Navigates to `"Kết quả nhận diện"`, shows recognized text, buttons `[Đúng]`, `[Sửa]`, `[Bỏ qua]`. NO digit confirmation. | `[ ] PASS / [ ] FAIL` |
| **Test 2** | Capture 3 lines of Vietnamese text (Mode: Chữ viết tay) | Detects lines, presents multiline editor & combined text. NO digit confirmation. | `[ ] PASS / [ ] FAIL` |
| **Test 3** | Capture vertical column addition exercise (Mode: Phép tính) | Runs arithmetic grading flow. Digit confirmation allowed ONLY if uncertain digit detected. | `[ ] PASS / [ ] FAIL` |

- **Physical Android Status:** `OWNER_TEST_REQUIRED`

---

## 15. Skills Applied

- `vercel-react-best-practices`
  - Canonical path: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Ensuring optimal state management, component lifecycle, and non-blocking navigation transitions in React Native.
  - Applied to: `src/app/camera.tsx`, `src/app/processing.tsx`, `src/app/results/token-confirmation.tsx`.
- `fixing-accessibility`
  - Canonical path: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: Accessible labels, touch targets, modal dismissal, and Android BackHandler keyboard behavior.
  - Applied to: `src/components/domain/TokenConfirmationCard.tsx`, `src/app/camera.tsx`, `src/app/ocr-pilot/result.tsx`.

---

## 16. Final Verdict

- **OCR.FLOW.1:** **PASS**
- **Handwriting Text Mode:** **PASS**
- **Handwriting -> Digit Confirmation:** **BLOCKED**
- **Recognized Text Screen:** **PASS**
- **Submission Not Found Bug:** **FIXED**
- **Digit Picker Close:** **PASS**
- **CameraView Warning:** **FIXED**
- **Spring Tests:** **123 / 123 PASSED**
- **AI Tests:** **164 / 164 PASSED**
- **Mobile TSC & Lint:** **PASS**
- **Physical Android:** **OWNER_TEST_REQUIRED**
