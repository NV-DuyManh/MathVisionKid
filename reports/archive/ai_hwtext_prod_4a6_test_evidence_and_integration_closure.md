# AI.HWTEXT.PROD.4A.6 — Test Evidence Closure + Integration Green Before Physical

Phase: AI.HWTEXT.PROD.4A.6

---

## 1. Executive Summary

PROD.4A.6 closes all evidence contradictions from the PROD.4A.5 report:

1. **5 legacy test failures resolved** — Tests `test_source_01`, `test_source_02`, `test_ui_03`, `test_ui_04`, `test_ui_05` were grepping for obsolete JSX patterns removed during PROD.3B/3F refactor. Rewritten to verify the same business contracts against current `resolveLineDisplayState` architecture. **All 5 now PASS.**
2. **Direct 6-sample segmentation evaluation** — All 6 fixture images read directly and evaluated. No synthetic equivalents, no "same code path" substitution. **All 6 PASS with exact expected line counts.**
3. **Integration stack blocker documented** — Docker daemon is not running. HTTP4-01 through HTTP4-06 require Docker infrastructure (PostgreSQL, MinIO, Redis) → Spring Boot → FastAPI pipeline. Blocker is external (Docker daemon), not code.
4. **Test accounting corrected** — Every count is traceable to a specific command with exit code. No double-counting between suites.

---

## 2. Exact Files Changed

| File | Change | Lines |
|---|---|---|
| [`test_multiline_physical_2a.py`](file:///e:/MathVisionKid/services/ai-service/tests/test_multiline_physical_2a.py) | Rewrite 5 obsolete JSX-grep tests to verify current `resolveLineDisplayState` contracts | 24–44, 438–462 |
| [`eval_6_sample_segmentation.py`](file:///e:/MathVisionKid/services/ai-service/tests/eval_6_sample_segmentation.py) | [NEW] Direct evaluation script reading 6 fixture images | All |

No production code changed. No segmentation code changed. No arbitration logic changed.

---

## 3. Legacy 5-Failure Root Cause + Replacement Tests

All 5 tests were in [`test_multiline_physical_2a.py`](file:///e:/MathVisionKid/services/ai-service/tests/test_multiline_physical_2a.py) and shared the same root cause: they grepped for literal JSX patterns that were removed during the PROD.3B/3F refactor to `resolveLineDisplayState`.

### test_source_01 (SOURCE-01)

| | |
|---|---|
| **Old assertion** | `assert "const rawText = line.rawOcrText \|\| line.predictedText;" in content` and `assert "OCR GỐC (CRNN):" in content` |
| **Why obsolete** | Component no longer uses inline `const rawText = ...` assignment. Raw OCR text is now sourced via `resolveLineDisplayState().ocrText`. Label changed from "OCR GỐC (CRNN):" to "OCR gốc". |
| **Replacement assertion** | Verifies `resolveLineDisplayState` import, `ocrText` usage, `"OCR gốc"` label, `sectionABox`/`sectionAText` elements, plus unchanged `LineBox.rawOcrText` schema check. |
| **New result** | **PASS** |

### test_source_02 (SOURCE-02)

| | |
|---|---|
| **Old assertion** | `assert "{line.correctedText && (" in content` and `assert "GỢI Ý HIỆU CHỈNH (AI GROQ):" in content` |
| **Why obsolete** | Component no longer uses `line.correctedText` directly for rendering. AI suggestions are sourced via `resolveLineDisplayState().aiSuggestions` array. Label changed from "GỢI Ý HIỆU CHỈNH (AI GROQ):" to "Gợi ý 1" / "Gợi ý 2". |
| **Replacement assertion** | Verifies `aiSuggestions` usage, `sectionBBox` container, `sugg.text` rendering. |
| **New result** | **PASS** |

### test_ui_03 (UI-03)

| | |
|---|---|
| **Old assertion** | `assert "OCR GỐC (CRNN):" in content` and `assert "const rawText = line.rawOcrText \|\| line.predictedText;" in content` |
| **Why obsolete** | Duplicate of SOURCE-01's old contract. Same refactor reason. |
| **Replacement assertion** | Verifies `"OCR gốc"` label, `resolveLineDisplayState` import, `sectionAText`/`sectionABox` elements. |
| **New result** | **PASS** |

### test_ui_04 (UI-04)

| | |
|---|---|
| **Old assertion** | `assert "{line.correctedText && (" in content` and `assert "GỢI Ý HIỆU CHỈNH (AI GROQ):" in content` |
| **Why obsolete** | Component uses `aiSuggestions.map()` / `aiSuggestions.length` instead of `line.correctedText &&` guard. |
| **Replacement assertion** | Verifies `aiSuggestions.map` or `aiSuggestions.length` pattern, `sectionBBox` container. |
| **New result** | **PASS** |

### test_ui_05 (UI-05)

| | |
|---|---|
| **Old assertion** | `assert "{line.correctedText && (" in content` |
| **Why obsolete** | Guard condition changed from `line.correctedText &&` to `aiSuggestions.length === 0`. |
| **Replacement assertion** | Verifies `aiSuggestions.length === 0` guard pattern in content. |
| **New result** | **PASS** |

### Business contract preservation

The underlying business contracts remain identical:
- **Raw OCR is always visible** (Section A with "OCR gốc" label) ✅
- **AI suggestions are only shown when they exist** (guard on `aiSuggestions.length`) ✅
- **When no suggestions exist, appropriate fallback is shown** (AI_CONFIRMED notice or outage notice) ✅
- **Raw and final are separately visible** (`sectionABox` and `sectionCBox`) ✅
- **Suggestion text comes from verified sources** (`sugg.text` from `resolveLineDisplayState.aiSuggestions`) ✅

---

## 4. Integration Stack Startup Evidence

### Attempt

Tried to start local stack to run HTTP4 integration tests.

### Infrastructure check

| Component | Status | Detail |
|---|---|---|
| Docker daemon | ❌ NOT RUNNING | `docker version` → `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine` |
| Java 21 | ✅ Available | `java version "21.0.9" 2025-10-21 LTS` |
| Node.js | ✅ Available | v22.19.0 |
| Python venv | ✅ Available | Python 3.12.13 with all deps |

### Blocker

The integration stack requires Docker for infrastructure services:
- **PostgreSQL** (port 5432) — required by Spring Boot for user authentication (`_get_student_token()`)
- **MinIO** (port 9000) — object storage
- **Redis** (port 6379) — caching

Without Docker daemon running, `docker compose up -d postgres minio redis` cannot start. This prevents Spring Boot from starting on port 8080, which prevents HTTP4-01 through HTTP4-06 from executing.

**Root cause: Docker Desktop daemon is not running on this workstation. This is an external infrastructure dependency, not a code issue.**

---

## 5. HTTP4-01..06 Direct Results

| Test | Fixture | Status | Reason |
|---|---|---|---|
| HTTP4-01 (`test_http4_01_block1_spring_production_route`) | OWNER_POEM_BLOCK_1 | **SKIP** | Docker daemon not running → Spring Boot not available on port 8080 |
| HTTP4-02 (`test_http4_02_block2_spring_production_route`) | REAL-HW-02.jpg | **SKIP** | Same |
| HTTP4-03 (`test_http4_03_block3_spring_production_route`) | REAL-HW-03.jpg | **SKIP** | Same |
| HTTP4-04 (`test_http4_04_unknown_handwriting_spring_production_route`) | Unknown HW sample | **SKIP** | Same |
| HTTP4-05 (`test_http4_05_metadata_survives_fastapi_to_spring`) | — | **SKIP** | Same |
| HTTP4-06 (`test_http4_06_recognition_source_survives_to_client`) | — | **SKIP** | Same |

**All 6 skips share the same external blocker: Docker daemon is not running.**

---

## 6. Direct 6-Sample Segmentation Evaluation

Evaluated using [`eval_6_sample_segmentation.py`](file:///e:/MathVisionKid/services/ai-service/tests/eval_6_sample_segmentation.py) — reads each fixture image directly via `cv2.imread` and calls `detect_text_lines`.

**Command:** `python tests/eval_6_sample_segmentation.py`
**Exit code:** 0

| Sample ID | Expected | Detected | Phantoms | Merges | Splits | Result |
|---|---|---|---|---|---|---|
| OWNER_POEM_BLOCK_1 | 4 | 4 | 0 | 0 | 0 | **PASS** |
| OWNER_POEM_8_LINES | 8 | 8 | 0 | 0 | 0 | **PASS** |
| WIDE_NOTEBOOK_SAMPLE | 9 | 9 | 0 | 0 | 0 | **PASS** |
| REAL_HW_01 | 4 | 4 | 0 | 0 | 0 | **PASS** |
| REAL_HW_02 | 3 | 3 | 0 | 0 | 0 | **PASS** |
| REAL_HW_03 | 2 | 2 | 0 | 0 | 0 | **PASS** |

**Overall: ALL 6 PASS** — all fixture images read directly, no synthetic equivalents.

---

## 7. Provenance / Arbitration Regression

All PROD.4A.1–4A.5 contracts verified via Node test suite (51 cases). No regression:

| Contract | Test Cases | Result |
|---|---|---|
| One-way provenance invariant (no IFF) | A1–A5, Cases 28, 33, 43 | **PASS** |
| Single provider → OCR default | Cases 31, 36, 39 | **PASS** |
| Multi-provider consensus → auto-select | Cases 34, 40, D1 | **PASS** |
| Duplicate/non-SUCCESS provider → no consensus | D2, D3 | **PASS** |
| Manual edit precedence | Cases 7, 16, 41, A1 | **PASS** |
| Provider outage → no fake confirmation | Cases 13, 19, 29, A3.2 | **PASS** |
| Hidden re-OCR = 0 | H1 | **PASS** |
| Third synthetic string rejection | Cases 28, 43 | **PASS** |

---

## 8. Final Test Accounting

| Suite | Pass | Fail | Skip | Command | Exit Code |
|---|---|---|---|---|---|
| **Node suggestion/invariant** (Cases 1–43, A1–A5, D1–D3, H1) | 51 | 0 | 0 | `node src/utils/__tests__/suggestionDedupe.test.mjs` | 0 |
| **TypeScript** | — | 0 errors | — | `npx tsc --noEmit` | 0 |
| **ESLint** | — | 0 warnings | — | `npx eslint src/utils/suggestionDedupe.ts` | 0 |
| **Python: groq_production_route** | 21 | 0 | 6 | See combined below | — |
| **Python: multiline_physical_2a** | 38 | 0 | 0 | See combined below | — |
| **Python: generalized_segmentation** | 26 | 0 | 0 | See combined below | — |
| **Python: segmentation_contracts** | 19 | 0 | 0 | See combined below | — |
| **Python: prod2a_integrity** | 12 | 0 | 0 | See combined below | — |
| **Python: physical_regression** | 2 | 0 | 0 | See combined below | — |
| **Python combined** | **118** | **0** | **6** | `.venv\Scripts\python -m pytest tests/test_groq_production_route.py tests/test_multiline_physical_2a.py tests/test_generalized_segmentation.py tests/test_segmentation_contracts.py tests/test_prod2a_integrity.py tests/test_physical_regression.py -v` | 0 |
| **Python: direct 6-sample eval** | 6 | 0 | 0 | `python tests/eval_6_sample_segmentation.py` | 0 |
| **Spring Boot multiline** | 18 | 0 | 0 | `gradlew.bat test --tests "*OcrMultiline*"` | 0 |

### Totals

| | Count |
|---|---|
| Total test assertions PASS | **193** (51 Node + 118 Python + 6 direct eval + 18 Spring) |
| Total FAIL | **0** |
| Total SKIP | **6** (HTTP4-01..06 — Docker daemon blocker) |
| TypeScript errors | **0** |
| ESLint warnings | **0** |

### Count verification

- 21 + 38 + 26 + 19 + 12 + 2 = **118** (matches pytest `collected 124 items`, `118 passed, 6 skipped`)
- 124 − 6 = 118 ✅
- No test is counted in multiple suites ✅

---

## 9. Holdout Status

`No independent holdout set available.`

The `hw_matrix/` directory contains 12 images whose provenance as truly independent holdout cannot be guaranteed. No claim of generalization to unseen data.

---

## 10. Physical Status

| Aspect | Status |
|---|---|
| Code-level unit/integration tests (non-HTTP4) | **ALL PASS (0 FAIL)** |
| HTTP4 integration tests | **6 SKIP** (Docker daemon not running — external blocker) |
| Physical Android device testing | **OWNER_RETEST_REQUIRED** |
| Physical privacy mask verification | **OWNER_RETEST_REQUIRED** |

---

## 11. Remaining Limitations

1. **HTTP4-01..06 integration tests** — 6 SKIP due to Docker daemon not running. These require the full stack (Docker → PostgreSQL/MinIO/Redis → Spring Boot → FastAPI) to be running. The Docker daemon is not active on this workstation. This is the sole blocker preventing full integration closure.
2. **No independent holdout set** — generalization beyond 6 known regression samples is not proven.
3. **Physical device testing** — not performed in this phase. Owner retest required.

---

## 12. Final Verdict

| Verdict | Value | Rationale |
|---|---|---|
| **CodeLevelVerdict** | **PASS** | 0 FAIL across all unit test suites. All 6 direct segmentation evaluations PASS. All provenance/arbitration regressions PASS. |
| **IntegrationVerdict** | **PARTIAL** | 6 HTTP4 integration tests SKIP due to Docker daemon not running (external infrastructure blocker, not code issue). |
| **PhysicalVerdict** | **OWNER_RETEST_REQUIRED** | Owner has not provided physical device evidence. |
| **PhysicalPrivacyMask** | **OWNER_RETEST_REQUIRED** | Not tested. |
| **ReleaseVerdict** | **CODE_PASS_PHYSICAL_PENDING** | All code-level tests pass. Integration blocker is external (Docker daemon). Physical testing pending Owner. |

---

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Minimal changes — only rewrote obsolete tests to match current contracts, no unnecessary refactoring
  - Applied to: 5 legacy test rewrites (preserved business contract, changed only the assertion mechanism), no production code changes
