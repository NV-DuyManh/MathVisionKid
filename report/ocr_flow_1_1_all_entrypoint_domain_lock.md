# OCR.FLOW.1.1 — Lock All Student Entry Points to the Correct Domain, Make Handwriting the Default, Eliminate Arithmetic Fallback

**Status:** PASS (Runtime Closure Complete — Physical Owner Test Required)  
**Date:** 2026-09-13  
**Project:** MathVision Kids  
**Skill Applied:** `ponytail` (Senior minimalist engineering: YAGNI, eliminate redundant branches, fail-closed canonical resolver, single source of truth)

---

## 1. Executive Summary

During physical runtime testing on Android, the owner provided unambiguous evidence that selecting a clear machine-printed Vietnamese text image still reached the arithmetic evaluation pipeline, showing arithmetic-specific copy (*"kiểm tra từng chữ số"*, *"so sánh từng hàng"*) and producing:
```json
{
  "flowDomain": "ARITHMETIC",
  "status": "REVIEW_REQUIRED",
  "reasonCode": "OUT_OF_SCOPE",
  "detectorInvoked": true,
  "detectorTokenCount": 31,
  "ocrInvoked": true,
  "ocrTextLength": 0,
  "parserStatus": "OUT_OF_SCOPE"
}
```

This directly contradicted the design invariant from OCR.FLOW.1 that handwriting should never trigger arithmetic review or token confirmation.

In **OCR.FLOW.1.1**, we conducted a full audit of all Student image acquisition entry points, identified the root causes, introduced a canonical fail-closed domain resolver (`resolveFlowDomain`), removed every implicit fallback to `ARITHMETIC`, installed hard defensive guards at `/preview` and `/processing` preventing accidental arithmetic submissions, fixed the Expo Router nested `camera` route warning cleanly without suppression, and verified that explicit arithmetic remains fully preserved.

---

## 2. Physical Evidence

The owner physical evidence established the following:
1. **Machine-printed Vietnamese text image** was processed through the arithmetic pipeline rather than the OCR pipeline.
2. **Submission Payload Sent to Arithmetic Backend**: The mobile client dispatched `POST /api/v1/student/submissions`, invoking the arithmetic YOLO detector and parser instead of the OCR multiline pilot.
3. **Arithmetic Copy Displayed**: The processing screen displayed arithmetic verification steps (*"kiểm tra từng chữ số"*, *"so sánh từng hàng"*).
4. **Conclusion**: `flowDomain: ARITHMETIC` was stamped onto the submission draft during image acquisition before the user ever reached the privacy gate or review screens.

---

## 3. Entry-Point Matrix Before Fix

| Entry Point | Initial Stamped Mode | Mode Stored? | Mode Preserved Through Privacy? | Destination After Privacy | Could Fall Back to Arithmetic? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Home "Chọn ảnh" (Gallery)** | `'ARITHMETIC'` *(hardcoded)* | Yes (`draft.mode = 'ARITHMETIC'`) | Yes | `/preview` | **YES (Always ARITHMETIC)** |
| **Home "Chụp bài" (Hero Camera)** | `undefined` -> `mode \|\| 'ARITHMETIC'` | Yes in camera/draft | Yes | `/preview` | **YES (Implicit fallback)** |
| **Bottom Tab Camera** | No route / `undefined` | No params passed | Falling back | `/preview` | **YES (Implicit fallback)** |
| **Retry from Handwriting Result** | `mode: 'HANDWRITING_TEXT'` | Preserved | Yes | `/ocr-pilot/line-crop` or multiline | No (only if params intact) |
| **Explicit "Phép tính"** | Not present on Home | N/A | N/A | N/A | N/A |
| **Missing/Corrupted Draft Mode** | `undefined` | Stored as `undefined` | `null` | `/preview` | **YES (Defaulted to ARITHMETIC)** |

---

## 4. Root Cause

1. **Smoking Gun in Home Gallery Action (`src/app/(tabs)/index.tsx`)**:
   In `handlePickImage()`:
   ```typescript
   // BEFORE (defect):
   draft.mode = 'ARITHMETIC';
   ```
   Selecting an image directly from the student home screen hardcoded `ARITHMETIC` onto the draft store.
2. **Implicit Fallback in Camera (`src/app/camera.tsx`)**:
   `mode = (params.mode as FlowDomain) || 'ARITHMETIC';`
   Any generic capture action routed to `/camera` without explicit params defaulted to arithmetic.
3. **Routing in Privacy Gate (`src/app/privacy.tsx`)**:
   In `handleDone()`, any mode other than explicit `'HANDWRITING_TEXT'` fell through to `/preview` and subsequently to `/processing`, which dispatched `POST /api/v1/student/submissions`.
4. **Phantom Tab Screen Warning in Expo Router (`src/app/(tabs)/_layout.tsx`)**:
   `<Tabs.Screen name="camera" />` was registered under `(tabs)/_layout.tsx`, but no `(tabs)/camera.tsx` existed in the nested children `["index", "profile"]`, throwing:
   `[Layout children]: No route named "camera" exists in nested children: ["index", "profile"]`.

---

## 5. Canonical Domain Resolver

Implemented in `src/services/draft/submissionDraftStore.ts`:
```typescript
export const VALID_FLOW_DOMAINS: FlowDomain[] = [
  'ARITHMETIC',
  'HANDWRITING_TEXT',
  'OCR_PILOT',
  'OCR_PILOT_MULTILINE',
];

export function resolveFlowDomain(
  explicitMode?: string | null,
  draftMode?: string | null
): FlowDomain {
  // 1. Explicit valid mode wins
  if (isValidFlowDomain(explicitMode)) {
    return explicitMode;
  }

  // 2. Persisted valid draft mode next
  if (isValidFlowDomain(draftMode)) {
    return draftMode;
  }

  // 3. Generic Student flow default = HANDWRITING_TEXT (Never default to ARITHMETIC)
  if (explicitMode || draftMode) {
    if (__DEV__) {
      console.warn(
        `[FLOW_DOMAIN][WARN] Unrecognized mode (explicit: "${explicitMode}", draft: "${draftMode}"). Failing closed to HANDWRITING_TEXT.`
      );
    }
  }

  return 'HANDWRITING_TEXT';
}
```

Standardized logging across every stage:
```typescript
export function logFlowDomain(stage: 'ACQUIRE' | 'PRIVACY' | 'POST_PRIVACY' | 'RESULT', domain: FlowDomain): void {
  console.log(`[FLOW_DOMAIN][${stage}] ${domain}`);
}
```

---

## 6. Entry-Point Fixes

1. **Home Screen (`src/app/(tabs)/index.tsx`)**:
   - Primary action: `"ĐỌC CHỮ VIẾT TAY"` / `"Chụp chữ viết tay tiếng Việt để MathVision nhận diện và giúp em sửa từng dòng."`
   - Stamped mode on gallery pick:
     ```typescript
     draft.mode = resolveFlowDomain(null, null); // Always resolves to 'HANDWRITING_TEXT'
     ```
   - Stamped mode on camera navigation:
     ```typescript
     navigateToCamera('HANDWRITING_TEXT');
     ```
   - Explicit secondary action added: `"Phép tính dọc"` / `"Kiểm tra phép cộng, trừ, nhân, chia đặt tính"`, passing `mode: 'ARITHMETIC'`.
2. **Camera Screen (`src/app/camera.tsx`)**:
   - Replaced `params.mode || 'ARITHMETIC'` with:
     ```typescript
     const flowDomain: FlowDomain = resolveFlowDomain(params.mode as string, draft?.mode);
     ```
   - Emits `[FLOW_DOMAIN][ACQUIRE] HANDWRITING_TEXT`.
3. **Bottom Tab Bar (`src/app/(tabs)/_layout.tsx` & `src/app/(tabs)/camera.tsx`)**:
   - Custom `tabPress` listener intercepts tap and routes to `/camera` with `params: { mode: 'HANDWRITING_TEXT' }`.
   - Created valid child screen `src/app/(tabs)/camera.tsx` redirecting with `mode: 'HANDWRITING_TEXT'`, resolving the Expo Router warning.
4. **Privacy Screen (`src/app/privacy.tsx`)**:
   - Emits `[FLOW_DOMAIN][PRIVACY]`.
   - On completion, emits `[FLOW_DOMAIN][POST_PRIVACY]`.
   - Strict branching: Only explicit `'ARITHMETIC'` routes to `/preview`; all other domains route directly to multiline handwriting review `/ocr-pilot/multiline-review` or `/ocr-pilot/line-crop`.

---

## 7. Preview/Processing Guards

Added defensive guards to ensure that even in the event of an anomalous route jump, handwriting images can never be submitted to the arithmetic pipeline:

1. **Preview Guard (`src/app/preview.tsx`)**:
   ```typescript
   if (flowDomain !== 'ARITHMETIC') {
     if (__DEV__) {
       console.warn(`[FLOW_DOMAIN][GUARD] HANDWRITING_PREVIEW_GUARD_TRIGGERED: mode "${flowDomain}" reached /preview. Redirecting to handwriting review.`);
     }
     router.replace({ pathname: '/ocr-pilot/multiline-review' as any, params: { imageUri } });
     return;
   }
   ```
2. **Processing Guard (`src/app/processing.tsx`)**:
   ```typescript
   if (flowDomain !== 'ARITHMETIC') {
     if (__DEV__) {
       console.warn(`[FLOW_DOMAIN][GUARD] HANDWRITING_PROCESSING_GUARD_TRIGGERED: mode "${flowDomain}" reached /processing. Blocking submission upload.`);
     }
     router.replace({ pathname: '/ocr-pilot/multiline-review' as any, params: { imageUri } });
     return;
   }
   ```
   Under no circumstances is `POST /api/v1/student/submissions` invoked for handwriting flows.

---

## 8. Expo Router Warning Fix

- **Problem**: `[Layout children]: No route named "camera" exists in nested children: ["index", "profile"]`.
- **Resolution**:
  1. Created `src/app/(tabs)/camera.tsx` as a valid nested route component that redirects to `/camera` with `mode: 'HANDWRITING_TEXT'`.
  2. In `src/app/(tabs)/_layout.tsx`, attached `listeners={{ tabPress: (e) => { e.preventDefault(); router.push({ pathname: '/camera' as any, params: { mode: 'HANDWRITING_TEXT' } }); } }}`.
- **Verification**: Zero missing route warnings emitted during Metro startup and tab navigation.

---

## 9. Handwriting Pipeline Verification

For `HANDWRITING_TEXT`:
1. Image acquired (Camera / Gallery / Bottom Tab).
2. Logs: `[FLOW_DOMAIN][ACQUIRE] HANDWRITING_TEXT`.
3. Privacy Masking Gate (optional masks applied).
4. Logs: `[FLOW_DOMAIN][PRIVACY] HANDWRITING_TEXT`.
5. Post-Privacy:
   - Logs: `[FLOW_DOMAIN][POST_PRIVACY] HANDWRITING_TEXT`.
   - Routes to `/ocr-pilot/multiline-review`.
6. User selects line crop -> `/ocr-pilot/line-crop`.
7. Client creates OCR trial and calls CRNN offline inference.
8. Displays recognized Vietnamese text with actions: `[Đúng]`, `[Sửa]`, `[Bỏ qua]`.
9. Logs: `[FLOW_DOMAIN][RESULT] HANDWRITING_TEXT`.
10. `POST /api/v1/student/submissions` is **NEVER** called.
11. Arithmetic copy (*"kiểm tra từng chữ số"*, *"so sánh từng hàng"*) is **NEVER** shown.

---

## 10. Arithmetic Preservation

Arithmetic evaluation remains fully functional through explicit user invocation:
1. Student selects `"Phép tính dọc"` on the home screen.
2. Mode is explicitly passed as `'ARITHMETIC'`.
3. Camera / gallery records `[FLOW_DOMAIN][ACQUIRE] ARITHMETIC`.
4. Privacy gate logs `[FLOW_DOMAIN][PRIVACY] ARITHMETIC` and `[FLOW_DOMAIN][POST_PRIVACY] ARITHMETIC`.
5. Routes to `/preview` and `/processing`.
6. Submission uploaded to `/api/v1/student/submissions`.
7. Arithmetic grading and review displays as expected.

---

## 11. Automated Tests

### 1. `scripts/test_all_entrypoints_domain_lock.js`
- **Test A:** Home -> Gallery defaults to `HANDWRITING_TEXT`, never visits `/preview`, no arithmetic upload. -> **PASS**
- **Test B:** Home -> Camera defaults to `HANDWRITING_TEXT`, post-privacy routes to multiline review. -> **PASS**
- **Test C:** Bottom tab capture action routes to `HANDWRITING_TEXT`. -> **PASS**
- **Test D:** Retry from handwriting result preserves `HANDWRITING_TEXT`. -> **PASS**
- **Test E:** Explicit "Phép tính" routes cleanly to `ARITHMETIC` pipeline through `/preview` and `/processing`. -> **PASS**
- **Test F:** Missing/corrupted mode triggers DEV warning and fails closed to `HANDWRITING_TEXT`, never `ARITHMETIC`. -> **PASS**
- **Test G:** Hard defensive guards at `/preview` and `/processing` intercept non-arithmetic and make upload impossible. -> **PASS**
- **Test H:** Stage logging matches required format `[FLOW_DOMAIN][<STAGE>] <DOMAIN>` across all 4 stages. -> **PASS**

### 2. Regression Suites
- `scripts/test_ocr_flow_routing.js`: **6/6 PASS**
- `scripts/test_ocr_runtime_contract_reconciliation.js`: **7/7 PASS**
- `npx tsc --noEmit`: **0 errors**
- `npm run lint`: **0 errors, 0 warnings**

---

## 12. Files Modified

| File | Change Description |
| :--- | :--- |
| `src/services/draft/submissionDraftStore.ts` | Added `isValidFlowDomain`, `resolveFlowDomain`, and `logFlowDomain`. Removed implicit `ARITHMETIC` fallback. |
| `src/app/(tabs)/camera.tsx` *(NEW)* | Added valid nested tab route redirecting to `/camera` with `mode: 'HANDWRITING_TEXT'`. |
| `src/app/(tabs)/_layout.tsx` | Added tabPress interceptor routing to `/camera` with `mode: 'HANDWRITING_TEXT'`. |
| `src/app/(tabs)/index.tsx` | Changed gallery pick to `resolveFlowDomain(null, null)`. Updated hero CTA to child-friendly Vietnamese. Added explicit secondary action for arithmetic. |
| `src/app/camera.tsx` | Used `resolveFlowDomain` and added `logFlowDomain('ACQUIRE', flowDomain)`. |
| `src/app/privacy.tsx` | Added privacy stage logging and strict routing preventing non-arithmetic flows from entering `/preview`. |
| `src/app/preview.tsx` | Installed `HANDWRITING_PREVIEW_GUARD_TRIGGERED` defensive redirect. |
| `src/app/processing.tsx` | Installed `HANDWRITING_PROCESSING_GUARD_TRIGGERED` defensive redirect blocking arithmetic submission. |
| `src/app/ocr-pilot/result.tsx` | Added `logFlowDomain('RESULT', 'HANDWRITING_TEXT')`. |
| `src/app/ocr-pilot/multiline-result.tsx` | Added `logFlowDomain('RESULT', 'HANDWRITING_TEXT')`. |
| `src/app/results/correct.tsx` | Added `logFlowDomain('RESULT', 'ARITHMETIC')`. |
| `src/app/results/error-hint.tsx` | Added `logFlowDomain('RESULT', 'ARITHMETIC')`. |
| `src/app/results/review-required.tsx` | Added `logFlowDomain('RESULT', 'ARITHMETIC')`. |
| `src/app/results/quality-failure.tsx` | Ensured retake/retry explicitly passes `mode: 'ARITHMETIC'`. |
| `src/app/results/out-of-scope.tsx` | Ensured retake/retry explicitly passes `mode: 'ARITHMETIC'`. |
| `src/context/AuthContext.tsx` | Removed unused error param in catch block for compiler hygiene. |
| `scripts/test_all_entrypoints_domain_lock.js` *(NEW)* | Automated physical-style entry-point and guard verification test suite. |

---

## 13. Physical Owner Test Protocol

Clean restart Metro before physical verification:
```powershell
npx expo start --clear
```

### TEST A: Generic Gallery Pick (The Owner's Exact Previous Action)
1. On the Student Home screen, tap the main gallery button or **"Chọn ảnh từ máy"**.
2. Select a clear machine-printed Vietnamese image.
3. Observe DEV logs:
   - `[FLOW_DOMAIN][ACQUIRE] HANDWRITING_TEXT`
   - `[FLOW_DOMAIN][PRIVACY] HANDWRITING_TEXT`
   - `[FLOW_DOMAIN][POST_PRIVACY] HANDWRITING_TEXT`
4. Confirm:
   - Screen routes to multiline review (`/ocr-pilot/multiline-review`).
   - `/preview` is **NOT** entered.
   - `/processing` is **NOT** entered.
   - `POST /api/v1/student/submissions` is **NOT** called.
   - Arithmetic copy (*"kiểm tra từng chữ số"*, *"so sánh từng hàng"*) does **NOT** appear.

### TEST B: Generic Camera Capture
1. On the Student Home screen, tap **"Chụp ảnh chữ viết"** or the bottom camera tab.
2. Capture a Vietnamese handwritten line.
3. Confirm identical logs and routing to the OCR multiline review screen.

### TEST C: Explicit Arithmetic
1. On the Student Home screen, tap **"Phép tính dọc"**.
2. Capture or select an arithmetic problem (e.g., column addition).
3. Observe DEV logs:
   - `[FLOW_DOMAIN][ACQUIRE] ARITHMETIC`
   - `[FLOW_DOMAIN][PRIVACY] ARITHMETIC`
   - `[FLOW_DOMAIN][POST_PRIVACY] ARITHMETIC`
4. Confirm:
   - Screen routes to `/preview` and `/processing`.
   - Dispatches `POST /api/v1/student/submissions`.
   - Arithmetic review/result displays correctly.

---

## 14. Final Verdict

All generic Student entry points are locked to `HANDWRITING_TEXT`. All implicit fallbacks to `ARITHMETIC` have been eliminated. Hard defensive guards at `/preview` and `/processing` guarantee that no handwriting image can reach the arithmetic submission API. The Expo Router warning is resolved, and automated tests pass with zero TypeScript and lint errors. Physical on-device verification by the owner is ready to proceed.

---

## 15. Skills Applied

- `ponytail`: Senior developer mindset — identified the single line smoking gun (`draft.mode = 'ARITHMETIC'`), introduced a minimal single source of truth (`resolveFlowDomain`), added fail-closed defensive routing guards, and avoided over-engineering.
