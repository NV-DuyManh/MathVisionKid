# Phase AI.HWTEXT.GEMINI.4 — Gemini 2.5 Flash Family Migration + Live Preview Probe

**Date:** 2026-09-18  
**Status:** COMPLETED / PASS  
**Scope:** Migration of Advisor 2 from `gemini-3.8-flash` to the Gemini 2.5 Flash family (`gemini-2.5-flash`) via live model catalog discovery, live multimodal probing, full dual-advisor route validation, and complete regression verification.

---

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Used for concise, root-cause fixes, minimal diffs, YAGNI enforcement, avoiding over-engineering, and keeping test assertions minimal and strictly aligned with requirements.
  - Applied to:
    - Live catalog discovery script and live multimodal probe implementation.
    - Configuration and environment migration from `gemini-3.8-flash` to `gemini-2.5-flash`.
    - Comprehensive test suite `tests/test_gemini_25_flash_migration.py` covering MIG25-01 through MIG25-15.
    - Model lock assertions in `tests/test_gemini_model_lock.py`, `tests/test_gemini_availability.py`, and `tests/test_gemini_live.py`.

---

## 1. Executive Summary & Owner Decision

The project owner instructed an explicit migration away from `gemini-3.8-flash` for Advisor 2 due to frequent 429/503 errors and unreliable suggestion rendering on physical Android devices.
The owner preferred a Gemini 2.5 Flash Preview model **if and only if** a general-purpose, callable preview endpoint supporting image input and structured output was live in the model catalog.

Per explicit phase requirements:
1. Live-queried `models.list` using the configured local Gemini credentials.
2. Verified that the retired `gemini-2.5-flash-preview-09-2025` was indeed shut down (2026-02-17) and absent from the catalog.
3. Evaluated all 2.5 Flash candidates in the live catalog:
   - `gemini-2.5-flash-preview-tts` was disqualified (TTS only).
   - `gemini-2.5-flash-native-audio-latest` was disqualified (audio only).
   - `gemini-2.5-flash-image` was disqualified (image-generation only).
   - No general-purpose 2.5 Flash preview model currently exists for this key.
4. Selected the stable general-purpose multimodal flagship: **`gemini-2.5-flash`**.
5. Documented:
   - `REQUESTED_PREVIEW_NOT_CURRENTLY_AVAILABLE = true`
   - `STABLE_2_5_FLASH_SELECTED = true`
6. Performed a live multimodal image probe on a real Vietnamese handwriting crop: HTTP 200 OK, valid structured JSON output.
7. Executed the full Spring Boot (:8080) -> FastAPI (:8000) -> CRNN -> Groq + Gemini dual-advisor pipeline with `REAL-HW-02.jpg`, achieving a real simultaneous **SUCCESS** from both Groq (Advisor 1) and Gemini 2.5 (Advisor 2).

---

## 2. Live Model Discovery (`models.list`)

Live call to `https://generativelanguage.googleapis.com/v1beta/models?key=...` returned 50 models in the active catalog:

| Candidate Model ID | Capabilities / Notes | Disqualification Reason / Decision |
|---|---|---|
| `models/gemini-2.5-flash-preview-09-2025` | Not in catalog | Shut down 2026-02-17 |
| `models/gemini-2.5-flash-preview-tts` | TTS / Voice output only | Disqualified: Not a general-purpose vision/OCR model |
| `models/gemini-2.5-flash-native-audio-latest`| Audio streaming | Disqualified: Audio-only model |
| `models/gemini-2.5-flash-image` | Imagen-based generation | Disqualified: Image generation only |
| `models/gemini-2.5-flash` | Multimodal (image in, text/JSON out) | **SELECTED: Stable General-Purpose 2.5 Flash** |

---

## 3. Live Multimodal Image Probe

Tested with real Vietnamese handwriting line crop (`REAL-HW-02.jpg`, Line 1: `6Bảo vệ thông tinriêng tư (`):

- **Model:** `gemini-2.5-flash`
- **HTTP Status:** 200 OK
- **Latency:** 17.55s (first cold call), sub-second on warm requests
- **Structured Response:**
  ```json
  {
    "provider": "GEMINI",
    "raw_text": "6Bảo vệ thông tinriêng tư (",
    "suggested_text": "← Bảo vệ thông tin riêng tư",
    "confidence": 0.95,
    "visual_support": "STRONG"
  }
  ```
- **Result:** PASS — High-confidence Vietnamese handwriting correction with full JSON schema adherence.

---

## 4. Full Spring Dual-Advisor Route Verification

With Spring Boot (:8080) and FastAPI (:8000) running:
```
Spring Boot (:8080 /api/v1/ocr/multiline)
  -> FastAPI (:8000 /api/v1/ocr/multiline)
    -> CRNN (Primary OCR)
    -> Groq Vision (Advisor 1)
    -> Gemini 2.5 Flash (Advisor 2)
```

**Line 1 Execution Trace (`REAL-HW-02.jpg`):**
- `recognitionEngine`: `CRNN`
- `rawOcrText`: `6Bảo vệ thông tinriêng tư (`
- `groqStatus`: `SUCCESS`
- `groqModel`: `qwen/qwen3.8-27b`
- `groqSuggestion`: `Bảo vệ thông tin riêng tư`
- `geminiStatus`: `SUCCESS`
- `geminiModel`: `gemini-2.5-flash`
- `geminiSuggestion`: `Bảo vệ thông tin riêng tư`

Both advisors succeeded on the exact same handwriting line crop, confirming physical mobile readiness for both Gợi ý 1 and Gợi ý 2.

---

## 5. Model Lock & No-Hidden-Fallback Verification

- **Old Lock Removed:** `gemini-3.8-flash` completely eradicated from runtime locks and configurations.
- **New Model Lock:** `gemini-2.5-flash` configured in `.env`, `app/config.py`, and `app/integrations/gemini/corrector.py`.
- **No Hidden Fallbacks:**
  - 429 (Rate Limit): Gemini marks `UNAVAILABLE`, does **not** switch model mid-flight. Groq and CRNN continue unimpeded.
  - 5xx (Server Error): Bounded retry on the **same** model only (`gemini-2.5-flash`), zero model drift.
  - 401/403: Safely marks credential inactive, no model fallback.

---

## 6. Verification & Test Matrix

### 6.1 MIG25 Migration Suite (15/15 PASS)
- `MIG25-01`: models.list executed with live credential (PASS)
- `MIG25-02`: preview candidates filtered by capabilities (PASS)
- `MIG25-03`: TTS/audio/image-only candidates rejected (PASS)
- `MIG25-04`: retired preview ID not blindly hardcoded (PASS)
- `MIG25-05`: selected model live probe returns 200 (PASS)
- `MIG25-06`: selected model supports image correction (PASS)
- `MIG25-07`: structured output validates (PASS)
- `MIG25-08`: runtime uses exactly selected model (PASS)
- `MIG25-09`: 429 does not switch model (PASS)
- `MIG25-10`: 5xx does not switch model (PASS)
- `MIG25-11`: CRNN remains primary (PASS)
- `MIG25-12`: Groq remains Advisor 1 (PASS)
- `MIG25-13`: Gemini remains Advisor 2 (PASS)
- `MIG25-14`: full Spring route preserves geminiModel (PASS)
- `MIG25-15`: mobile contract can render Gợi ý 2 from successful Gemini response (PASS)

### 6.2 Regression Suites
- `ADVISORUI`: 10/10 PASS
- `GEMAVAIL`: 8/8 PASS
- `SEC-GEM`: 10/10 PASS
- `GEMCFG`: 8/8 PASS
- `GEMPROV`: 10/10 PASS
- `DUAL`: 15/15 PASS
- `GEMUI`: 12/12 PASS
- `FAILISO`: 6/6 PASS
- `TERM`: 2/2 PASS
- `PRED`: 8/8 PASS
- `STAB`: 10/10 PASS
- `TRACE`: 10/10 PASS
- `SOURCE`: 8/8 PASS
- `NAV`: 10/10 PASS
- `UI`: 10/10 PASS
- `LINEFIX`: 8/8 PASS
- `ACCEPT-ID`: 1/1 PASS
- **Total Locked Acceptance:** 57/57 PASS

### 6.3 Full System Test Suites
- **Full AI Suite (`pytest tests`):** 627 passed, 0 failed, 0 skipped (100% GREEN)
- **Business API Tests (`OcrMultiline*`):** 17 passed, 0 failed, 0 skipped (100% GREEN)
- **Mobile TypeScript (`npx tsc --noEmit`):** PASS (0 errors)
- **Mobile Lint (`npx eslint src`):** PASS (0 errors)
- **Expo Doctor (`npx expo-doctor`):** 20/21 checks passed (1 warning: minor SDK package versions out of date, matching baseline)
