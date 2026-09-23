# Decision Source Attribution Fix — Report

## Bug Description

The system incorrectly classified AI-assisted corrections as `MANUAL_EDIT`.

| Field | Value |
|-------|-------|
| CRNN Output | `Sm yêu mùa hè` |
| AI Candidate | `Em yêu mùa hè` |
| Ground Truth | `Em yêu mùa hè` |
| Final Result | `Em yêu mùa hè` |
| **Before (wrong)** | `decision_source = MANUAL_EDIT` ❌ |
| **After (correct)** | `decision_source = AI_CORRECTION` ✅ |

---

## Root Cause

Lines 1860–1875 of `computeTrialAnalytics` determined `decisionSource` solely from `selectedSource` UI metadata (e.g., `'OCR'`, `'SUGGESTION_1'`, `'MANUAL_EDIT'`). It **never compared actual text content** (`ocrText`, `aiCandidate`, `finalText`), so when a user accepted an AI suggestion via the OCR source UI pathway, the system classified it as `MANUAL_EDIT`.

---

## Fix: Content-Based `resolveDecisionSource()`

### New Exported Function

```typescript
export function resolveDecisionSource(
  ocrText: string,
  aiCandidate: string,
  finalText: string,
  uiSelectedSource?: string,
): { decisionSource, correctionOrigin, source, status, correctionType }
```

### 4 Strict Priority Rules

| Rule | Condition | Decision Source | Origin | Correction Type |
|------|-----------|----------------|--------|-----------------|
| 1 | `final == ocr` | `CRNN_RAW` | `MODEL` | `OCR_CORRECT` |
| 2 | `final == ai` AND `ai != ocr` | `AI_CORRECTION` | `AI` | `AI_CORRECTED` |
| 3 | `final != ocr` AND `final != ai` | `MANUAL_EDIT` | `HUMAN` | `MANUAL_CORRECTED` |
| 4 | AI acceptance → **never** MANUAL_EDIT | *(enforced by Rule 2)* | — | — |

All comparisons are normalized (lowercase, collapsed whitespace).

### New Type

```typescript
export type CorrectionOrigin = 'MODEL' | 'AI' | 'HUMAN';
```

Added to `LineMetric` interface as `correctionOrigin?: CorrectionOrigin`.

---

## IDE Errors Fixed

| # | Error | Fix |
|---|-------|-----|
| 1 | `'score' does not exist in type 'AdvisorSuggestion'` (×8) | `score:` → `confidence:` in all suggestion objects |
| 2 | `ts(2739)` missing `pageImageObjectKey`/`pageImageSha256` (×4) | Added required fields to 4 trial objects |
| 3 | `'dataSplit' is possibly 'undefined'` (×3) | Added optional chaining `?.` |
| 4 | `'line_results' is possibly 'undefined'` (×2) | Added optional chaining `?.` |

**Total: 10 errors → 0 errors**

---

## Files Changed

### Modified

| File | Changes |
|------|---------|
| [`handAiAnalyticsStore.ts`](file:///E:/MathVisionKid/apps/student-mobile/src/services/analytics/handAiAnalyticsStore.ts) | Added `CorrectionOrigin` type, `resolveDecisionSource()` helper, replaced buggy UI-only attribution logic in `computeTrialAnalytics`, added `correctionOrigin` to `LineMetric` |
| [`handAiAnalyticsAndFlow.test.ts`](file:///E:/MathVisionKid/apps/student-mobile/src/__tests__/handAiAnalyticsAndFlow.test.ts) | 5 new decision source tests, fixed 4 test fixtures with proper AI correction data, fixed all 10 IDE type errors |

### Not Modified (preserved)

- CRNN inference pipeline
- OCR engine / image processing
- Line segmentation
- AI correction prompt logic
- Recognition workflow

---

## Verification

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | **0 errors** ✅ |
| `npm test -- handAiAnalyticsAndFlow.test.ts` | **68/68 passed** ✅ |
| IDE Problems tab | **0 errors** ✅ |

### New Test Cases

| TC | Scenario | Expected | Result |
|----|----------|----------|--------|
| TC1 | CRNN `Sm...` → AI `Em...` → Final `Em...` | `AI_CORRECTION` | ✅ |
| TC2 | CRNN = AI = Final (all identical) | `CRNN_RAW` | ✅ |
| TC3 | AI accepted but UI says `OCR` (Rule 4) | `AI_CORRECTION` | ✅ |
| TC4 | Final differs from both CRNN and AI | `MANUAL_EDIT` | ✅ |
| Integration | Full `computeTrialAnalytics` pipeline | Correct `decisionSource` + `correctionOrigin` on all lines | ✅ |

---

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Bug fix task — minimal, targeted change to attribution logic
  - Applied to: Kept the fix surgical — one new helper, one replacement block, no refactoring of unrelated code
