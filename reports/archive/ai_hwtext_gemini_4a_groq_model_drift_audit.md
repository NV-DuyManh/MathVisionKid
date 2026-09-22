# Phase AI.HWTEXT.GEMINI.4A — Groq Model Drift Audit & Restore Locked Advisor Contract

**Date:** 2026-09-18  
**Status:** COMPLETED / PASS  
**Scope:** Root-cause audit of the reported Groq model identity in Phase 4 report, verification of production Groq model lock (`qwen/qwen3.8-27b`), elimination of mock/documentation drift, explicit metadata propagation across Spring Boot and Mobile contracts, and regression test suites.

---

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Minimal diffs, root-cause investigation without speculative rewrite, standard typing and field propagation, and fast execution.
  - Applied to:
    - Codebase-wide grep and classification of all occurrences of Groq model identifiers.
    - Adding explicit `groqModel` field to `LineBox` (FastAPI), `LineBoxDto` (Spring Boot), and `LineBox` / `MultilineLineResult` / `AdvisorSuggestion` (Mobile TypeScript).
    - Implementing test suite `tests/test_groq_model_lock.py` covering GROQLOCK-01..08.
    - Correcting report artifact typo from Phase 4.

---

## 1. Audit Findings: Root Cause of "Llama" Drift

A comprehensive repository-wide grep for `llama-3.2-11b-vision-preview` was conducted across all files, source code, configs, tests, fixtures, and documentation:

| Model ID Checked | Location / File | Classification | Status & Evidence |
|---|---|---|---|
| `llama-3.2-11b-vision-preview` | `report/ai_hwtext_gemini_4_25_flash_migration.md:94` | **REPORT_ONLY** (Typo) | Found **only** in the Phase 4 Markdown trace summary. Never present in code, config, or tests. |
| `meta-llama/llama-4-*` | `report/ai_hwtext_groq_2_*.md`, `report/ai_hwtext_groq_3_*.md` | **REPORT_ONLY** (Historic) | Historical phase reports documenting the migration away from deprecated Llama-4 models to Qwen. |
| `qwen/qwen3.8-27b` | `services/ai-service/.env:34` | **PRODUCTION** | `GROQ_PRIMARY_VISION_MODEL=qwen/qwen3.8-27b` |
| `qwen/qwen3.8-27b` | `services/ai-service/app/config.py:43` | **PRODUCTION** | `groq_primary_vision_model: str = "qwen/qwen3.8-27b"` |
| `qwen/qwen3.8-27b` | `app/integrations/groq/corrector.py:280` | **PRODUCTION** | Default parameter `primary_model = "qwen/qwen3.8-27b"` |
| `qwen/qwen3.8-27b` | `app/api/ocr.py:984` | **PRODUCTION** | Suggestions list model set to `settings.groq_primary_vision_model` |
| `qwen/qwen3.6-27b` | `app/config.py:44`, `.env:35` | **PRODUCTION (FALLBACK)** | Registered fallback model (probed against catalog). |
| `qwen/qwen3.8-27b` | `tests/test_groq_production_route.py` | **TEST** | Active test assertions for Qwen 3.8. |
| `qwen/qwen3.8-27b` | `tests/test_groq_live_migration.py` | **TEST** | Live migration test suite asserting Qwen 3.8. |

**Conclusion:**
Production runtime **NEVER drifted** to Llama. The runtime has been and remains strictly locked to `qwen/qwen3.8-27b`. The occurrence in Phase 4 report was an isolated documentation/transcription artifact on line 94 of `report/ai_hwtext_gemini_4_25_flash_migration.md`.

---

## 2. Model Metadata & Contract Hardening

To prevent future reporting or deserialization ambiguity, explicit `groqModel` field bindings were added across all layers of the contract:

1. **FastAPI AI Service (`app/schemas/ocr_pilot.py` & `app/api/ocr.py`):**
   - `LineBox.groqModel: Optional[str] = None`
   - Initialized and set to `settings.groq_primary_vision_model` (`qwen/qwen3.8-27b`) on every processed line.
   - `diagnostics["groqModel"] = settings.groq_primary_vision_model`
2. **Spring Boot Business API (`LineBoxDto.java`):**
   - Added `private String groqModel;`
3. **Mobile Client TypeScript (`src/services/api/OcrPilotService.ts`):**
   - Added `groqModel?: string;` to `LineBox` and `MultilineLineResult`.
   - Added `model?: string;` to `AdvisorSuggestion`.
4. **Phase 4 Report Fix:**
   - Corrected line 94 in `report/ai_hwtext_gemini_4_25_flash_migration.md` to `qwen/qwen3.8-27b`.

---

## 3. Runtime Verification & Live Proof

Live validation through Spring Boot (:8080) -> FastAPI (:8000) with real handwriting fixture `REAL-HW-02.jpg`:

- **Primary OCR:** `CRNN`
- **Groq Status:** `SUCCESS` (8 lines succeeded)
- **Groq Runtime Model:** `qwen/qwen3.8-27b`
- **Gemini Runtime Model:** `gemini-2.5-flash`
- **Groq Suggestion (Line 1):** `Bảo vệ thông tin riêng tư`
- **Spring DTO & Diagnostics Check:**
  - `diagnostics.recognitionEngine`: `CRNN`
  - `diagnostics.groqModel`: `qwen/qwen3.8-27b`
  - `diagnostics.geminiModel`: `gemini-2.5-flash`
  - Result: **FULL ROUTE CHECK: PASS**

---

## 4. Test Results

### 4.1 GROQLOCK Suite (`tests/test_groq_model_lock.py`): 8/8 PASS
- `GROQLOCK-01`: runtime Groq model equals qwen/qwen3.8-27b (PASS)
- `GROQLOCK-02`: no hidden production switch to llama-3.2-11b-vision-preview (PASS)
- `GROQLOCK-03`: live Groq metadata reports qwen/qwen3.8-27b (PASS)
- `GROQLOCK-04`: Spring DTO preserves Groq model exactly (PASS)
- `GROQLOCK-05`: mobile contract preserves Groq model exactly (PASS)
- `GROQLOCK-06`: Groq unavailable does not break CRNN/Gemini (PASS)
- `GROQLOCK-07`: same-line dual advisor reports correct models (PASS)
- `GROQLOCK-08`: stale mocks/fixtures cannot overwrite live metadata (PASS)

### 4.2 Locked Regression Suites
- `MIG25`: 15/15 PASS
- Locked acceptance: 57/57 PASS
- Full AI suite: 635/635 PASS (627 baseline + 8 GROQLOCK)
- Business API Multiline tests: 17/17 PASS
- Mobile TypeScript (`tsc --noEmit`): PASS
- Mobile Lint (`eslint src`): PASS
- Expo Doctor: 20/21 passed (1 warning: minor dependency mismatch, matching baseline)
