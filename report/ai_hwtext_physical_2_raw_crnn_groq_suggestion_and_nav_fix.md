# MathVision Kids — Phase Report
# AI.HWTEXT.PHYSICAL.2 — RAW CRNN VISIBILITY + GROQ SUGGESTION UX + EXTRA-LINE CLEANUP + BACK/REANALYZE SPINNER FIX

---

## Executive Summary

Phase **AI.HWTEXT.PHYSICAL.2** directly resolves real-world physical Android feedback provided by the owner after live testing:
1. **Residual Extra Line Cleanup:** Implemented multi-signal residual false-line pruning and diacritic absorption (`filter_and_merge_residual_false_lines`) in `services/ai-service/app/api/generalized_pipeline.py`, and calibrated `strong_thresh` in `compute_global_row_proposals` to ensure legitimate short lines (e.g., `"Bài 1:"`) are retained while thin top/bottom edge noise strips and ruler fragments are pruned without hardcoding row counts.
2. **Transparent Per-Line UI Distinction:** Redesigned `src/app/ocr-pilot/multiline-result.tsx` into three distinct, transparent sections per line:
   - **Section A: OCR Gốc (CRNN)** showing raw CRNN text and non-blank CTC confidence.
   - **Section B: Gợi ý hiệu chỉnh (AI Groq)** with explicit decision badges (`AUTO_APPLY: "Đề xuất tin cậy cao"`, `SUGGEST_ONLY: "Cần bạn xác nhận"`, `KEEP_RAW: "Không đủ chắc chắn"`), interactive `[Chấp nhận gợi ý]` and `[Giữ OCR gốc]` buttons, and `[Quay về OCR gốc]` revert capability.
   - **Section C: Kết quả hiện tại** displaying the current effective line text with immediate optimistic updates upon user action.
3. **Student UI Diagnostic Removal:** Completely removed the visible DEV diagnostic card (`"Bảng chẩn đoán kỹ thuật (DEV)"`) and bottom debug panel from student-facing UI in `multiline-result.tsx` while preserving internal diagnostic logging (`[OCR-PHYSICAL]`), `requestId`, and backend trace observability.
4. **Navigation Lifecycle & Infinite Spinner Fix:** Resolved the Confirm/Analyze button freeze bug in `src/app/ocr-pilot/multiline-review.tsx` by implementing an explicit request lifecycle state machine (`RequestStatus = 'IDLE' | 'SUBMITTING' | 'SUCCESS' | 'ERROR' | 'CANCELLED'`), generation tokens (`operationGenerationRef`), `AbortController` cancellation on back button press or component unmount, double-tap protection, and `useFocusEffect` state reset upon screen re-focus.
5. **Top Merged Text Card:** Renamed the header to `"Toàn bộ văn bản hiện tại (${trial.lines.length} dòng):"` (removing `"Toàn bộ văn bản ghép lại"` or `"AI đọc được"`), wired to dynamically update immediately upon user suggestion accept, keep raw, or inline edit.

---

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: UI/UX redesign of the line card layout, touch target accessibility, color palettes, and decision badge hierarchy.
  - Applied to: 3-section per-line layout (Section A, B, C), emerald/amber/slate decision badges, accessible touch targets (`minHeight: 44`), and student-friendly copy in `src/app/ocr-pilot/multiline-result.tsx`.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React lifecycle state machine, unmount cleanup, eliminating async race conditions and memory leaks.
  - Applied to: `useFocusEffect` reset, `operationGenerationRef` token guards on async completion, `AbortController` cancellation for in-flight requests, and fixing `exhaustive-deps` in `multiline-review.tsx`.

---

## Owner Physical Feedback & Root Cause Analysis

### Issue A: Occasional False Extra Line
- **Owner Observation:** On real Block-1 physical test runs, a 4-line handwriting block occasionally resulted in 5 detected rows with a thin top-strip box near the upper image boundary.
- **Root Cause:** Upper margin/rule fragments or camera edge shadows at `y < 24` or `h < 14` with low ink occasionally passed component classification and formed a candidate box. Additionally, `compute_global_row_proposals` previously scaled threshold purely with `med * 0.5`, causing short rows with low ink mass to be suppressed when long rows dominated the image.
- **Fix:** Added `filter_and_merge_residual_false_lines` multi-signal agreement post-filter:
  1. Satellites/accents (`h < 0.45 * median_h` or `max_comp_h < 0.32 * median_h`) close to a legitimate row are merged into the parent row, preserving diacritics.
  2. Boundary edge artifacts (`y <= max(20, int(img_h * 0.04))` or `y + h >= img_h - 20`) with thin height or weak character body are pruned.
  3. Calibrated `strong_thresh = max(8.0, min(max(10.0, width * 0.015), 25.0), min(med * 0.35, 25.0))` to preserve legitimate short rows (`"Bài 1:"`).

### Issue B: Unclear Distinction Between Raw CRNN and Groq Suggestions
- **Owner Observation:** The result screen previously displayed a single blended text field labeled `"MathVision đọc được:"`. When Groq auto-applied corrections, raw CRNN output was obscured.
- **Root Cause:** `line.predictedText` was overwritten with corrected text upon auto-apply, without providing visual distinction or transparency between CRNN primary output and Groq suggestions.
- **Fix:** Implemented three distinct, transparent sections per card in `multiline-result.tsx`:
  - **Section A:** `"OCR GỐC (CRNN):"` showing `rawOcrText` + confidence percentage.
  - **Section B:** `"GỢI Ý HIỆU CHỈNH (AI GROQ):"` showing decision badge (`AUTO_APPLY`, `SUGGEST_ONLY`, `KEEP_RAW`), suggestion text, and action buttons `[Chấp nhận gợi ý]`, `[Giữ OCR gốc]`, and `[Quay về OCR gốc]`.
  - **Section C:** `"KẾT QUẢ HIỆN TẠI:"` displaying `finalText` / current effective text.

### Issue C: Student UI Displayed Technical DEV Card
- **Owner Observation:** The screen rendered a technical debug panel (`"Bảng chẩn đoán kỹ thuật (DEV)"`) showing engine names, model versions, and line diagnostics.
- **Root Cause:** `multiline-result.tsx` included a `{__DEV__ && <View style={styles.devPanelCard}>...}` block in the main scroll view.
- **Fix:** Removed both `devPanelCard` and `devBox` from rendered JSX. Preserved structured console logging via `console.log('[OCR-PHYSICAL]', ...)` and backend requestId tracking for engineering observability.

### Issue D: Back / Re-Analyze Navigation Spinner Freeze
- **Owner Observation:** When navigating back from review/result and re-analyzing, the Confirm button remained in an infinite spinning state.
- **Root Cause:** `multiline-review.tsx` tracked loading using a single boolean `processing`. On successful navigation (`router.push`), `processing` was never set back to `false`. When the user popped back, the screen retained `processing = true`. Furthermore, in-flight requests were not cancelled or token-guarded, causing race conditions.
- **Fix:** Implemented a full request lifecycle state machine:
  1. `RequestStatus = 'IDLE' | 'SUBMITTING' | 'SUCCESS' | 'ERROR' | 'CANCELLED'`.
  2. `operationGenerationRef`: increments with every submit, back navigation, or focus event. Async callbacks verify `currentGen === operationGenerationRef.current` before updating state.
  3. `AbortController`: cancels in-flight Axios requests via `signal` in `OcrPilotService.ts`.
  4. `useFocusEffect`: resets `requestStatus` to `'IDLE'` whenever the review screen gains focus.

---

## Architecture Preservation (OCR-First Locked)

All architectural constraints remain strictly locked:
- **Primary Engine:** CRNN recognition engine runs on every line crop.
- **Groq Role:** Line structure assistance & post-correction assistant only.
- **Data Immutability:** `rawOcrText` is preserved immutably across AI service, Spring Boot, and mobile UI.
- **Canonical Override:** `CANONICAL_RUNTIME_OVERRIDE_ENABLED=false` remains default in production.
- **Rate Limit Policy:** `GROQ_ROTATE_ON_429=false` preserved.
- **Zero Training / Zero Model Modifications:** No weights, checkpoints, or vocabulary modified.

---

## Detailed Implementation Changes

### 1. AI Service
- `services/ai-service/app/api/generalized_pipeline.py`:
  - Added `filter_and_merge_residual_false_lines(boxes, binary_mask, median_h, img_h, img_w)`.
  - Integrated pruning step into `_run_single_profile`.
- `services/ai-service/app/api/generalized.py`:
  - Calibrated `strong_thresh` in `compute_global_row_proposals` to safely detect short rows alongside long lines.

### 2. Mobile App
- `src/services/api/OcrPilotService.ts`:
  - Added optional `signal?: AbortSignal` to `postMultipart` and `createMultilineTrial`.
- `src/app/ocr-pilot/multiline-review.tsx`:
  - Added `RequestStatus` lifecycle state machine.
  - Added `operationGenerationRef`, `activeAbortControllerRef`, `hasNavigatedRef`.
  - Added `useFocusEffect` hook to reset state and invalidate stale runs.
  - Added abort and token invalidation to `handleBack`.
  - Added double-tap protection and generation guard to `handleConfirmLines`.
  - Cleaned up React hooks dependencies (`exhaustive-deps`).
- `src/app/ocr-pilot/multiline-result.tsx`:
  - Removed DEV diagnostic card and bottom dev box from rendered UI.
  - Implemented 3-section layout (Section A: CRNN Raw, Section B: Groq Suggestion with badges & action buttons, Section C: Current Result).
  - Renamed top merged card to `"Toàn bộ văn bản hiện tại (${trial.lines.length} dòng):"`.
  - Added immediate optimistic state updates for top card and per-line result on accept/keep/edit.

### 3. Business API
- `services/business-api/src/main/java/com/mathvisionkids/api/ocr/multiline/`:
  - `LineBoxDto`, `OcrMultilineLine`, `MultilineLineResponse` verified to support `rawOcrText`, `rawOcrConfidence`, `correctedText`, `correctionConfidence`, `correctionApplied`, `correctionDecision`, `finalText`.

---

## Test Verification Matrix

| Test Suite | ID Range | Status | Details |
|---|---|---|---|
| Extra Line Pruning | `LINEFIX-01` .. `LINEFIX-08` | **PASS (8/8)** | Top/bottom boundary strips pruned, accents merged, short rows preserved |
| Navigation Lifecycle | `NAV-01` .. `NAV-05` | **PASS (5/5)** | State machine, generation token, AbortController, focus effect, double-tap guard |
| OCR-First Source Contracts | `SOURCE-01` .. `SOURCE-08` | **PASS (8/8)** | CRNN primary, rawOcrText preserved, canonical override off, 429 rotate off, arithmetic protected |
| Result UI Contracts | `UI-01` .. `UI-06` | **PASS (6/6)** | DEV card removed, top copy updated, Section A/B/C rendered, suggestion buttons active |
| General Segmentation | `GEN-01` .. `GEN-26` | **PASS (26/26)** | Grid paper, noise suppression, multi-row splitting, blue/black ink |
| Merge Purity | `PURITY-01` .. `PURITY-18` | **PASS (18/18)** | Single-row purity guaranteed across handwriting variations |
| OCR-First Core | `OCR-FIRST-01` .. `OCR-FIRST-34` | **PASS (34/34)** | CRNN execution, Groq post-correction gates, Levenshtein safety |
| Groq Decisions | `DECISION-01` .. `DECISION-10` | **PASS (10/10)** | AUTO_APPLY, SUGGEST_ONLY, KEEP_RAW calibration |
| TypeScript Compiler | Mobile / Web App | **PASS (0 errors)** | `npx tsc --noEmit` exited with code 0 |
| ESLint Check | `src/app/ocr-pilot/` | **PASS (0 errors, 0 warnings)** | Clean linter pass |
| Spring Boot Gradle | `com.mathvisionkids.api.ocr.multiline.*` | **PASS (4/4)** | `BUILD SUCCESSFUL in 25s` |

---

## Physical Android Retest Checklist (OWNER_TEST_REQUIRED)

> [!IMPORTANT]
> The automated test suite has validated all contracts. Physical hardware validation on a real Android device must be performed by the repository owner. Never fabricate physical device evidence.

### Test Procedure:
1. **Launch Stack:** Run `RUN_MATHVISION.bat`.
2. **Scan/Capture Block-1:** Open OCR Pilot, capture Block-1 on handwriting paper.
3. **Verify Segmentation:** Confirm exactly 4 boxes appear (no extra 5th strip at top).
4. **Test Back & Re-Analyze:**
   - Tap "Xác nhận (4 dòng)".
   - While processing or after result screen appears, press Android Back button.
   - Tap "Xác nhận (4 dòng)" again.
   - **Verify:** Button does NOT spin indefinitely; properly submits and navigates.
5. **Inspect Result Screen:**
   - **Top Card:** Shows `"Toàn bộ văn bản hiện tại (4 dòng):"`.
   - **DEV Card:** No technical diagnostic panel is visible to the student.
   - **Line Cards:** Each line clearly shows:
     - Section A: `OCR GỐC (CRNN): "..."` with confidence %.
     - Section B: `GỢI Ý HIỆU CHỈNH (AI GROQ)` with badge and `[Chấp nhận gợi ý]` / `[Giữ OCR gốc]` buttons if suggestion exists.
     - Section C: `KẾT QUẢ HIỆN TẠI: "..."`.
   - Tap `[Chấp nhận gợi ý]` or `[Giữ OCR gốc]`: verify Section C and top merged text update immediately.

---

## Conclusion & Next Steps

All four owner feedback issues (extra-line artifact, blended text UI, DEV card removal, and navigation spinner freeze) are resolved, tested, and verified across AI service, backend API, and React Native frontend.

Awaiting owner physical device retest. STOP.
