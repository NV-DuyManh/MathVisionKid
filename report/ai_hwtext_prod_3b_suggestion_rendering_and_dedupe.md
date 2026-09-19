# AI.HWTEXT.PROD.3B — Suggestion Rendering + Dedupe + Student-Facing Cleanup Report

**Phase:** `AI.HWTEXT.PROD.3B`  
**Execution Date:** 2026-09-19  
**Target Platform:** Mobile (`src/app/ocr-pilot/multiline-result.tsx`, `src/utils/suggestionDedupe.ts`) & AI Service Tests  
**Verification Verdict:** **PASS (Code / Automated & Integration Tests: 100%)**  
**Physical Hardware Evidence:** **OWNER_RETEST_REQUIRED** (No physical device connected via ADB in build environment; no fabricated evidence)

---

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Required for student-facing UI/UX cleanup, eliminating visual clutter/bloat, ensuring high-contrast readable typography, subtle neutral empty states, and intuitive button hierarchies.
  - Applied to: Designed the compact `#F8FAFC` / `#64748B` neutral row (`"AI chưa có đề xuất khác cho dòng này."`), eliminated duplicate and provider-specific error cards, simplified suggestion card action buttons (`"Dùng gợi ý 1"`, `"Dùng gợi ý 2"`, `"Quay về OCR gốc"`).
- `vercel-react-best-practices`
  - SKILL.md: `.agent/skills/react-best-practices/SKILL.md`
  - Why selected: Optimization of React components, pure selector architecture, preventing redundant renders, and clean separation of concerns.
  - Applied to: Extracted pure selector helper `buildVisibleSuggestions(line)` outside the render cycle, preserving object identities and avoiding wasteful string mutations or state thrashing.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Senior developer anti-bloat and simplicity principles — minimal diffs, YAGNI, standard library features.
  - Applied to: Used native `String.prototype.normalize('NFC')` and regular expression `\s+` rather than importing external NLP or diffing libraries; avoided over-engineering normalization beyond equality checking.

---

## 1. Before / After UI Behavior

| Feature / Element | Before PROD.3B | After PROD.3B |
| :--- | :--- | :--- |
| **Suggestion Labels** | Tied to provider: `"Gợi ý 1"` (with blue "Groq" badge) and `"Gợi ý 2"` (with violet "Gemini" badge). | Strictly sequential and anonymous: `"Gợi ý 1"` and `"Gợi ý 2"`. Zero provider names. |
| **Provider Identity Badges** | Rendered visible chips: `styles.providerChipGroq` ("Groq") and `styles.providerChipGemini` ("Gemini"). | **Completely removed from student cards.** Provider identifiers preserved strictly in backend/audit fields. |
| **Provider Failure Cards** | Rendered ugly error cards taking up vertical height: `"Groq tạm thời chưa khả dụng."` / `"Gemini tạm thời chưa khả dụng."`. | **Completely removed.** Failed/unavailable providers render zero cards. No vertical space reserved. |
| **Suggestion == Raw OCR** | Rendered redundant suggestion card even when suggestion text was identical to OCR gốc. | **Filtered out.** Suggestions equal to raw OCR (normalized) are hidden. |
| **Identical Advisor Outputs** | Rendered two identical suggestion cards stacked vertically. | **Deduped.** Single card labeled `"Gợi ý 1"` is rendered. |
| **Zero Useful Suggestions** | Left empty gaps or failure cards on the screen. | Renders exactly one subtle, compact neutral row: `"AI chưa có đề xuất khác cho dòng này."` with an info icon in slate gray (`#64748B`). |
| **Action Buttons** | Generic or provider-tinted buttons. | Deterministic buttons: `"Dùng gợi ý 1"` (if Gợi ý 1 exists), `"Dùng gợi ý 2"` (if Gợi ý 2 exists), and `"Quay về OCR gốc"`. |
| **OCR Immutability** | CRNN raw text remained baseline, but UX lacked clean revert path on auto-apply. | `rawOcrText` strictly immutable; pressing `"Quay về OCR gốc"` restores `finalText` to `rawOcrText`. Manual edit always wins. |

---

## 2. Exact Dedupe Algorithm

The deduplication logic is centralized in a pure, testable helper: [`src/utils/suggestionDedupe.ts`](file:///E:/MathVisionKid/src/utils/suggestionDedupe.ts).

### A. Normalization Contract (`normalizeForComparison`)
Strings are normalized **strictly for equality comparison**:
1. Check falsy / null / undefined -> return empty string `""`.
2. Trim outer leading and trailing whitespace: `str.trim()`.
3. Unicode standard normalization: `str.normalize('NFC')` (ensures precomposed and decomposed Vietnamese diacritics match, e.g. `òa` vs `oà`).
4. Internal whitespace collapse: `.replace(/\s+/g, ' ')` (collapses accidental double/multiple spaces or tabs).
5. **Critical Invariant:** The original suggestion string `cand.text` is **never modified or spell-corrected** by this function; it is retained intact for UI display and application.

### B. Selection and Ordering Contract (`buildVisibleSuggestions`)
Given a line result `line`:
1. Extract candidates in stable order: Advisor A (Groq) then Advisor B (Gemini).
2. Filter candidates with non-empty text and valid `SUCCESS` state.
3. Compare each candidate against `normRaw = normalizeForComparison(line.rawOcrText)`.
   - If `normCand === normRaw` -> **Skip** (candidate does not offer a distinct suggestion).
4. Check for duplicates against previously accepted suggestions in `seenNorms`:
   - If `seenNorms.includes(normCand)` -> **Skip** (candidate duplicates an earlier suggestion).
5. Enforce ceiling: Maximum **2 unique suggestions**.
6. Relabel remaining survivors sequentially without gaps:
   - Index 0 -> `id: 'sugg-1'`, `label: 'Gợi ý 1'`, `buttonLabel: 'Dùng gợi ý 1'`, `accessibilityLabel: 'Chọn gợi ý 1'`.
   - Index 1 -> `id: 'sugg-2'`, `label: 'Gợi ý 2'`, `buttonLabel: 'Dùng gợi ý 2'`, `accessibilityLabel: 'Chọn gợi ý 2'`.
7. Return `VisibleSuggestion[]`. If length is 0, the UI renders the compact neutral state.

---

## 3. Mandatory 10-Case Acceptance Matrix

All 10 cases required by the owner specification were implemented as deterministic tests in both TypeScript/JavaScript (`src/utils/__tests__/suggestionDedupe.test.mjs`) and Python/Pytest (`services/ai-service/tests/test_prod3b_suggestion_dedupe.py`).

| Case ID | Input Specification | Expected Behavior | Automated Test Result |
| :--- | :--- | :--- | :--- |
| **CASE 1** | RAW = `"Em yêu mùa hè"`<br>AI_A = `"Em yêu mùa hè"`<br>AI_B = `unavailable` | 0 suggestion cards; compact neutral state only (`"AI chưa có đề xuất khác cho dòng này."`). | **PASS** |
| **CASE 2** | RAW = `"m yêu mùa hè"`<br>AI_A = `"Em yêu mùa hè"`<br>AI_B = `unavailable` | Exactly 1 card labeled `"Gợi ý 1"`; button `"Dùng gợi ý 1"`; no `"Gợi ý 2"`. | **PASS** |
| **CASE 3** | RAW = `"m yêu mùa hè"`<br>AI_A = `"Em yêu mùa hè"`<br>AI_B = `"Em yêu mùa hè"` | Exactly 1 unique card labeled `"Gợi ý 1"`; no duplicate card. | **PASS** |
| **CASE 4** | RAW = `"Mọc trên đổi quề"`<br>AI_A = `"Mọc trên đồi quê"`<br>AI_B = `"Mọc trên đồi quê"` | Exactly 1 unique card labeled `"Gợi ý 1"`; no duplicate card. | **PASS** |
| **CASE 5** | RAW = `"Mọc trên đổi quề"`<br>AI_A = `"Mọc trên đồi quê"`<br>AI_B = `"Mọc trên đồi quê."` | Exactly 2 distinct cards: `"Gợi ý 1"` and `"Gợi ý 2"`. | **PASS** |
| **CASE 6** | RAW = `"Có hoa sim tím"`<br>AI_A = `"Có hoa sim tím"`<br>AI_B = `"Có hoa sim tím"` | 0 suggestion cards; compact neutral state only. | **PASS** |
| **CASE 7** | RAW = `"Trời, sao ngọt thế!"`<br>AI_A = `unavailable`<br>AI_B = `unavailable` | Zero provider failure text cards; compact neutral state only. | **PASS** |
| **CASE 8** | RAW distinct from 1 successful advisor; other advisor 429/403/UNAVAILABLE | Exactly 1 suggestion card labeled `"Gợi ý 1"`; zero error text or provider names. | **PASS** |
| **CASE 9** | Unicode-equivalent strings (NFC vs NFD) and whitespace variation (e.g., `"hoa  sim tím"`) | Deduped correctly for comparison; original displayed text retains exact original suggestion string. | **PASS** |
| **CASE 10** | User selects `"Dùng gợi ý 1"` then taps `"Quay về OCR gốc"` | `finalText` reverts cleanly to `rawOcrText`; `rawOcrText` remains immutable throughout. | **PASS** |

---

## 4. Physical / Screen Evidence

- **Physical Device Status:** `adb` command not present / no physical Android hardware attached in this terminal environment.
- **Physical Verdict:** **OWNER_RETEST_REQUIRED**
- **Fabrication Notice:** Per project rules, zero fake screenshots, simulated physical proofs, or mock hardware reports were generated.

### Owner Retest Steps on Physical Android Device:
1. Connect Android test device via USB with USB Debugging enabled.
2. Start Expo Metro bundler: `npx expo start --android`.
3. Navigate to OCR Pilot -> Scan poem / multiline handwriting.
4. Verify on physical screen:
   - **Case A (No distinct suggestions):** Ensure line renders `"AI chưa có đề xuất khác cho dòng này."` in a neat, light gray bar without any provider names or error strings.
   - **Case B (One distinct suggestion):** Ensure single card appears with header `"Gợi ý 1"` and button `"Dùng gợi ý 1"`. Ensure no `"Gợi ý 2"` card or empty space appears.
   - **Case C (Two distinct suggestions):** Ensure two cards appear labeled `"Gợi ý 1"` and `"Gợi ý 2"` respectively.
   - **Case D (Revert action):** Press `"Dùng gợi ý 1"`, then press `"Quay về OCR gốc"`, verify that KẾT QUẢ HIỆN TẠI reverts immediately to the original OCR text.
   - **Case E (Cleanliness):** Confirm no text mentioning `"Groq"`, `"Gemini"`, `"Rate limit"`, `"tạm thời chưa khả dụng"`, or HTTP codes appears in the student interface.

---

## 5. Test Commands and Exact Pass / Fail / Skip Counts

### 1. Node.js Deterministic Dedupe & 10-Case Matrix
```bash
node --experimental-strip-types src/utils/__tests__/suggestionDedupe.test.mjs
```
- **Total:** 10
- **Passed:** 10
- **Failed:** 0
- **Skipped:** 0
- **Duration:** 0.08s

### 2. TypeScript Static Compilation
```bash
npx tsc --noEmit
```
- **Result:** **0 errors, 0 warnings** (Clean compilation across mobile workspace)

### 3. ESLint Verification
```bash
npm run lint
```
- **Result:** **0 errors, 0 warnings** (Executed via `npx expo lint`)

### 4. Pytest PROD.3B Unit Suite (`test_prod3b_suggestion_dedupe.py`)
```bash
pytest services/ai-service/tests/test_prod3b_suggestion_dedupe.py -v
```
- **Total:** 15
- **Passed:** 15
- **Failed:** 0
- **Skipped:** 0
- **Duration:** 0.28s

### 5. Full Pytest Regression Suite (OCR Pilot & AI Service)
```bash
pytest services/ai-service/tests/test_prod3b_suggestion_dedupe.py \
       services/ai-service/tests/test_mobile_gemini_visibility.py \
       services/ai-service/tests/test_prod3a_gemini_physical.py \
       services/ai-service/tests/test_ui_acceptance_prod1.py \
       services/ai-service/tests/test_advisor_ui.py \
       services/ai-service/tests/test_gemini_model_migration.py \
       services/ai-service/tests/test_gemini_multikey.py \
       services/ai-service/tests/test_gemini_provider.py \
       services/ai-service/tests/test_gemini_security.py \
       services/ai-service/tests/test_ocr_pilot_endpoint.py -v
```
- **Total:** 146
- **Passed:** 146
- **Failed:** 0
- **Skipped:** 0
- **Warnings:** 4 (FastAPI/Starlette deprecation notices)
- **Duration:** 13.12s

---

## 6. Files Created and Modified

### Created:
1. `src/utils/suggestionDedupe.ts`: Pure TypeScript deduplication and normalization helper. Exports `normalizeForComparison`, `buildVisibleSuggestions`, `buildAdvisorView`.
2. `src/utils/__tests__/suggestionDedupe.test.mjs`: Test suite validating all 10 mandatory cases in Node environment.
3. `services/ai-service/tests/test_prod3b_suggestion_dedupe.py`: Pytest test suite containing 15 test cases (PROD3B-01 through PROD3B-15) for dedupe, UI source rules, accessibility labels, and OCR immutability.
4. `report/ai_hwtext_prod_3b_suggestion_rendering_and_dedupe.md`: This comprehensive verification report.

### Modified:
1. `src/app/ocr-pilot/multiline-result.tsx`:
   - Integrated `buildVisibleSuggestions(line)` into line result rendering.
   - Removed visible provider badges (`providerChipGroq`, `providerChipGemini`).
   - Removed provider failure cards (`"Groq tạm thời chưa khả dụng."`, `"Gemini tạm thời chưa khả dụng."`).
   - Added subtle compact neutral row (`noSuggestionRow` / `noSuggestionText`) when 0 suggestions exist.
   - Rendered explicit buttons with accessibility labels `"Chọn gợi ý 1"`, `"Chọn gợi ý 2"`, and `"Quay về OCR gốc"`.
2. `services/ai-service/tests/test_advisor_ui.py`:
   - Updated assertions (ADVISORUI-02, ADVISORUI-04) to reflect removal of provider badges from student-facing result cards while maintaining styling tokens.
3. `services/ai-service/tests/test_gemini_model_migration.py`:
   - Updated assertions (MIG25-12, MIG25-13) to verify that provider chips are excluded from student-facing suggestion cards.

---

## 7. Remaining Issues & External Constraints

1. **Gemini Live Availability (External Constraint):**
   - Current Gemini API keys in the key pool remain rate-limited (HTTP 429/403) by Google's free tier quotas.
   - As instructed, this is treated as an external provider condition and was not reopened in this phase. The UI cleanly accommodates unavailable advisors without any degradation or error leakage to the student.
2. **Physical Hardware Retest:**
   - Because no physical Android device was connected during execution, physical on-device screenshots require an owner re-test (`OWNER_RETEST_REQUIRED`).

---

## 8. Final Verdict

- **Code Implementation:** **PASS** (Pure helper, zero bloating, cleanly decoupled)
- **Design & Cleanliness:** **PASS** (Zero provider badges, zero failure cards, subtle neutral state)
- **10-Case Acceptance Matrix:** **10 / 10 PASS**
- **Automated Regression Suite:** **146 / 146 PASS**
- **TypeScript & ESLint:** **0 errors, 0 warnings (PASS)**
- **Hardware Status:** **OWNER_RETEST_REQUIRED**
- **Phase Overall:** **READY FOR OWNER PHYSICAL VERIFICATION**

*(Phase complete. Antigravity has stopped as instructed and will NOT start PROD.3C automatically).*
