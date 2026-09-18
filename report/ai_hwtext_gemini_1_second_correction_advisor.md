# AI.HWTEXT.GEMINI.1 — SECOND OCR CORRECTION ADVISOR (GROQ + GEMINI, CRNN STILL PRIMARY)

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Dual-advisor mobile UX design, suggestion cards, agreement badges, and responsive accessibility controls.
  - Applied to: Multi-line result screen design (`src/app/ocr-pilot/multiline-result.tsx`), separate Groq (amber) and Gemini (purple) visual hierarchy, choice buttons, and responsive non-overflow layouts.
- `vercel-react-best-practices`
  - SKILL.md: `.agent/skills/react-best-practices/SKILL.md`
  - Why selected: React Native performance, state immutability, async concurrency, and late-response race guard management.
  - Applied to: Immutability of raw OCR state, user-edit locks, single-pass derivations, and zero-stutter rendering.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Minimal diff principle, YAGNI, standard library prioritization, avoiding redundant abstractions.
  - Applied to: Non-blocking async client using httpx, reusing existing OCR uncertainty trigger, and unified suggestions schema without database churn.

---

## 1. Executive Summary

Phase **AI.HWTEXT.GEMINI.1** establishes Google Gemini (`gemini-3.8-flash`) as an independent, second post-correction advisor for multi-line handwriting OCR, operating in parallel with Groq Vision (Advisor 1). The core architectural foundation remains strictly **OCR-FIRST**:
1. **CRNN READS**: The local CRNN model performs primary handwriting line recognition, emitting `rawOcrText` and granular sequence uncertainty metrics (`rawOcrConfidence`, `minTokenConfidence`, `p10TokenConfidence`, `meanEntropy`).
2. **GROQ SUGGESTS** (Advisor 1): If the line is uncertain, Groq Vision evaluates the physical line crop and proposes minimal visually justified corrections.
3. **GEMINI SUGGESTS** (Advisor 2): Concurrently, Gemini Multimodal API independently evaluates the line crop and uncertainty metrics without ever seeing Groq's proposal.
4. **USER / POLICY CONTROLS**: `rawOcrText` is permanently immutable. The student mobile UI presents both options clearly with single-tap selection (`[Chọn gợi ý Groq]`, `[Chọn gợi ý Gemini]`, `[Giữ OCR gốc]`). Late AI responses and manual student edits are strictly race-protected.

All 45 new tests (GEMCFG 8/8, GEMPROV 10/10, DUAL 15/15, GEMUI 12/12) and all 67 locked acceptance regression tests (STAB 10/10, TRACE 10/10, SOURCE 8/8, NAV 10/10, UI 10/10, LINEFIX 8/8, ACCEPT-ID 1/1) passed with zero failures. The full AI test suite passed 560/560 tests, Business API multiline tests passed, and mobile TypeScript/ESLint checks passed cleanly.

---

## 2. Architecture Lock

The end-to-end multi-line handwriting pipeline retains its locked OCR-first topology:

```
INPUT IMAGE
  │
  ├── Local CV / Optional Groq Line Assist (Segmentation)
  │     └── Final physical line crops
  │
  ├── CRNN Vietnamese Handwriting Engine (Primary OCR)
  │     ├── rawOcrText (IMMUTABLE)
  │     └── CRNN Uncertainty Signals (minTokenConfidence, p10, meanEntropy)
  │
  ├── Post-Correction Trigger Gate (Identical OCR-first evaluation)
  │     ├── High confidence clean line → No advisors called
  │     └── Uncertain/suspicious line → Invoke advisors in parallel
  │
  ├── Parallel Independent Advisors (Concurrent Execution via asyncio.gather)
  │     ├── Advisor 1: Groq Vision (qwen/qwen3.8-27b)
  │     └── Advisor 2: Gemini Multimodal (gemini-3.8-flash)
  │
  ├── Provider-Specific Safety Evaluation & Quota Protection
  │     ├── Levenshtein distance bounds (edit_ratio <= 0.35)
  │     ├── Length expansion checks (no hallucinated words)
  │     ├── Arithmetic protection (digits and math operators immutable)
  │     └── Quota respect (no aggressive sweeping on 429)
  │
  └── Mobile UI Presentation
        ├── OCR GỐC (CRNN): rawOcrText
        ├── GỢI Ý 1 — GROQ: [Chọn gợi ý Groq]
        ├── GỢI Ý 2 — GEMINI: [Chọn gợi ý Gemini]
        ├── [Giữ OCR gốc]
        └── KẾT QUẢ HIỆN TẠI: finalText
```

### Prohibitions Verified
- Gemini is NOT primary OCR.
- Groq is NOT primary OCR.
- CRNN is never bypassed or skipped.
- Groq is never replaced by Gemini; Gemini is additive.
- Groq output is never fed to Gemini; Gemini output is never fed to Groq.
- Gemini is never relabeled as Groq; Groq is never relabeled as Gemini.
- No model training, checkpoint modification, or vocab alterations.
- `CANONICAL_RUNTIME_OVERRIDE_ENABLED=false` and `GROQ_ROTATE_ON_429=false` stay locked.

---

## 3. Gemini Official API / Model Verification

- **Official Documentation Source**: Google GenAI API documentation (`https://ai.google.dev/api/generate-content`).
- **Catalog Model**: `gemini-3.8-flash` (current official multimodal fast-inference model for vision-to-text post-correction).
- **Catalog Verification Status**: `gemini_catalog_available: YES`.
- **Live Network Access Status**: `gemini_live_probe_available: OWNER_KEY_REQUIRED` (no local secret provisioned in development workspace).

---

## 4. SDK Choice

- **Selected SDK**: Current official Google Python SDK `google-genai` (version `2.24.0`) installed in the virtualenv.
- **Runtime Transport**: Asynchronous non-blocking HTTP via `httpx` to Gemini REST endpoint `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`.
- **Rationale**: Direct async execution avoids thread-pool saturation, guarantees precise HTTP status code isolation (401, 403, 429, 5xx), exact `Retry-After` header extraction, and non-blocking co-routines alongside Groq during `asyncio.gather`.

---

## 5. Gemini Configuration

Configured strictly backend-only in `services/ai-service/app/config.py`:

```python
# Gemini 2nd Advisor Integration
gemini_enabled: bool = False
gemini_api_keys: str = ""  # Raw comma-separated key list — never logged
gemini_model: str = "gemini-3.8-flash"
gemini_post_correction_enabled: bool = True
gemini_timeout_seconds: float = 10.0
gemini_rotate_on_429: bool = False
gemini_correction_prompt_version: str = "gemini-ocr-correction-v1"
gemini_correction_cache_ttl_seconds: int = 3600
```

### Single-Variable Requirement
- Mandatory single environment variable: `GEMINI_API_KEYS="key1,key2,..."`.
- Zero numbered variables (`GEMINI_API_KEY_01`, etc.).
- Parser trims whitespace, discards blanks, dedupes preserving initial order, and handles arbitrary key counts safely.
- `.env.example` documents only `GEMINI_API_KEYS=""`.

---

## 6. Gemini Key Pool

Implemented in `services/ai-service/app/integrations/gemini/key_pool.py` (`GeminiKeyPool`):
- **States**: `HEALTHY`, `COOLING_DOWN`, `DISABLED_AUTH`, `DEGRADED`.
- **401 Unauthorized**: Quarantines the bad credential into `DISABLED_AUTH`, logs masked safe ID, and fails over to the next healthy credential.
- **403 Forbidden**: Quarantines into `DISABLED_AUTH`.
- **5xx Server Errors & Timeouts**: Cooldown for 60s, bounded failover without permanent deactivation.
- **429 Rate Limit**: Respects `Retry-After` or default cooldown without aggressive key sweeping (`rotate_on_429=False`).

---

## 7. Secret Isolation

- Gemini credentials live strictly in the AI backend environment.
- Never transmitted to Spring Boot, React Native, Expo client bundle, MinIO storage, or PostgreSQL.
- Safe logging masks all credentials to `xxxx...yyyy` or `key_N`.
- Raw secret strings are verified absent from logs across all test suites (`GEMCFG-08`).

---

## 8. Live Probe

- Local Key Check: `ENV_GEMINI_LEN: 0`, `SETTINGS_GEMINI_LEN: 0`.
- As mandated by Section 25: `GEMINI_LIVE=OWNER_KEY_REQUIRED`.
- Zero synthetic or mock physical passes were fabricated.

---

## 9. Correction Prompt

Version: `gemini-ocr-correction-v1`
System prompt instructions enforce:
- Role: Second independent Vietnamese handwriting OCR post-correction advisor.
- Input comparison: Line crop image + raw CRNN text + CRNN uncertainty metrics.
- Smallest visually justified correction.
- Style rewriting, paraphrasing, hallucinated character insertions, and word deletions strictly forbidden.
- Arithmetic answers strictly protected (never solve or change student numeric answers).
- Image content treated as untrusted document data (defense against prompt injection).
- Canonical fixture answers strictly excluded.

---

## 10. Structured Schema

Response model defined via Pydantic (`GeminiOcrCorrectionResponse`):
```json
{
  "provider": "GEMINI",
  "raw_text": "em đp gại",
  "suggested_text": "em đẹp gái",
  "correction_needed": true,
  "confidence": 0.94,
  "visual_support": "STRONG",
  "changes": [
    {
      "raw_span": "đp",
      "suggested_span": "đẹp",
      "reason": "visual_character_evidence",
      "confidence": 0.92
    }
  ],
  "uncertain": false
}
```

---

## 11. Independent Advisor Design

- Groq and Gemini run as completely independent advisors.
- Both receive identical inputs: line crop, `rawOcrText`, and CRNN uncertainty metrics.
- Gemini is **advisory-first**: Even with high confidence, Gemini suggestions are submitted to the student UI as proposals (`SUGGEST_ONLY`), never silently overriding `finalText` without user confirmation or explicit auto-apply rules.

---

## 12. Parallel Execution

Triggered lines launch Groq and Gemini concurrently:
```python
coros = [run_groq(), run_gemini()]
raw_results = await asyncio.gather(*coros, return_exceptions=True)
```
- Independent timeouts (Groq 25s, Gemini 10s).
- Independent circuit breakers and key pools.
- Concurrent execution saves ~50% latency compared to sequential chaining.

---

## 13. No Cross-Provider Anchoring

- Gemini prompt and API payload contain zero Groq suggestions or metadata.
- Groq prompt and API payload contain zero Gemini suggestions or metadata.
- Preserves genuine, uncorrelated second opinions (`DUAL-03`, `DUAL-04`).

---

## 14. Failure Isolation

Matrix of failure modes:
1. **Both Succeed**: Both cards rendered (`GỢI Ý 1 — GROQ`, `GỢI Ý 2 — GEMINI`).
2. **Groq Succeeds, Gemini Fails**: Groq suggestion shown; Gemini shows compact non-breaking unavailable status or omitted.
3. **Groq Fails, Gemini Succeeds**: Gemini suggestion clearly labeled `GEMINI`, never relabeled as Groq.
4. **Both Fail**: Line defaults safely to `rawOcrText`; no crashes, zero regressions.

---

## 15. Raw CRNN Immutability

- `line.rawOcrText` is strictly immutable from the moment the CRNN model produces it.
- Selecting Groq suggestion mutates `finalText` only.
- Selecting Gemini suggestion mutates `finalText` only.
- Selecting `[Giữ OCR gốc]` resets `finalText` to `rawOcrText`.
- Verified by automated tests `DUAL-11`, `DUAL-12`, `DUAL-13`, `GEMUI-01`, `GEMUI-05`, `GEMUI-06`, `GEMUI-07`.

---

## 16. Two-Suggestion Mobile UX

Implemented in `src/app/ocr-pilot/multiline-result.tsx`:
- **Card 1 (Section A)**: `OCR GỐC (CRNN)` — Displays `rawOcrText` and confidence.
- **Card 2 (Section B1)**: `GỢI Ý 1 — GROQ` — Displays Groq suggestion and `[Chọn gợi ý Groq]` button.
- **Card 3 (Section B2)**: `GỢI Ý 2 — GEMINI` — Displays Gemini suggestion and `[Chọn gợi ý Gemini]` button.
- **Action**: Dedicated `[Giữ OCR gốc]` button to restore raw OCR text.
- **Card 4 (Section C)**: `KẾT QUẢ HIỆN TẠI` — Displays current active `finalText`.

---

## 17. Agreement / Disagreement

- **Agreement**: When normalized Groq and Gemini suggestions match (`groq.trim().toLowerCase() == gemini.trim().toLowerCase()`), an informational badge is rendered: `"Hai AI cùng đề xuất ✓"`.
- **Disagreement**: When suggestions differ, both cards remain visible with respective selection buttons. The system never silently arbitrates between providers.

---

## 18. User Selection

- Tapping `[Chọn gợi ý Groq]` triggers `handleFeedback(line, 'CORRECTED', groqText)`.
- Tapping `[Chọn gợi ý Gemini]` triggers `handleFeedback(line, 'CORRECTED', geminiText)`.
- Tapping `[Giữ OCR gốc]` triggers `handleFeedback(line, 'CORRECT', rawText)`.
- All choices mutate only `finalText` and `predictedText`.

---

## 19. Late-Response Safety

- Each line tracks user selection and edit status (`userEdited`, `verdict`).
- Late background responses from Groq or Gemini cannot overwrite a user selection or manual edit (`DUAL-14`, `DUAL-15`).

---

## 20. Arithmetic Safety

- If `domain == "ARITHMETIC"`, Gemini safety evaluation rejects any suggestions modifying numeric digits (`0-9`) or operators (`+ - * / = : ÷`).
- Prevents AI hallucinations from compromising deterministic grading.

---

## 21. Cache / Cost

- Dedicated in-memory cache keyed by:
  `SHA256("GEMINI|" + crop_bytes + "|" + rawOcrText + "|" + prompt_version + "|" + model)`
- Separate from Groq cache.
- TTL: 3600 seconds.
- Clean lines bypass advisors entirely, minimizing API quota consumption.

---

## 22. GEMCFG Tests (8/8 PASS)

- `GEMCFG-01`: Comma-list parsing into entries.
- `GEMCFG-02`: Whitespace trimming.
- `GEMCFG-03`: Empty and blank items discarded.
- `GEMCFG-04`: Duplicate keys deduped preserving initial order.
- `GEMCFG-05`: Single key works without failure.
- `GEMCFG-06`: Missing keys safely disable advisor without crashes.
- `GEMCFG-07`: No numbered env vars (`gemini_api_key_01`, etc.).
- `GEMCFG-08`: Raw keys absent from logs and safe IDs.

---

## 23. GEMPROV Tests (10/10 PASS)

- `GEMPROV-01`: Valid structured response parsed into Pydantic schema.
- `GEMPROV-02`: Malformed response rejected with validation error.
- `GEMPROV-03`: Request timeout isolated cleanly.
- `GEMPROV-04`: 401 failover disables bad key and uses healthy key.
- `GEMPROV-05`: 403 handling quarantines credentials.
- `GEMPROV-06`: 5xx bounded failover with cooldown.
- `GEMPROV-07`: 429 quota exhaustion respects `rotate_on_429=False`.
- `GEMPROV-08`: Cache hit avoids redundant network call.
- `GEMPROV-09`: Raw OCR change triggers cache miss.
- `GEMPROV-10`: Gemini errors never break CRNN result.

---

## 24. DUAL Tests (15/15 PASS)

- `DUAL-01`: CRNN runs before advisors.
- `DUAL-02`: Both advisors receive same raw CRNN evidence.
- `DUAL-03`: Groq output not sent to Gemini.
- `DUAL-04`: Gemini output not sent to Groq.
- `DUAL-05`: Both success -> both visible with correct provider tags.
- `DUAL-06`: Groq-only success works gracefully.
- `DUAL-07`: Gemini-only success labeled as GEMINI.
- `DUAL-08`: Both fail -> raw CRNN text remains intact.
- `DUAL-09`: Matching suggestions show agreement badge.
- `DUAL-10`: Disagreement preserves both suggestions without silent arbitration.
- `DUAL-11`: Choose Groq updates `finalText` only.
- `DUAL-12`: Choose Gemini updates `finalText` only.
- `DUAL-13`: Keep raw restores `finalText` to `rawOcrText`.
- `DUAL-14`: Late provider cannot overwrite user choice.
- `DUAL-15`: Manual edit protected from late responses.

---

## 25. GEMUI Tests (12/12 PASS)

- `GEMUI-01`: Section A binds strictly to `rawOcrText`.
- `GEMUI-02`: Section B1 title is `GỢI Ý 1 — GROQ:` and binds to `groqSuggestion`.
- `GEMUI-03`: Section B2 title is `GỢI Ý 2 — GEMINI:` and binds to `geminiSuggestion`.
- `GEMUI-04`: Provider labels are never swapped.
- `GEMUI-05`: Choose Groq updates `finalText` only.
- `GEMUI-06`: Choose Gemini updates `finalText` only.
- `GEMUI-07`: Keep raw resets `finalText` to `rawOcrText`.
- `GEMUI-08`: Clean lines render no empty Gemini cards.
- `GEMUI-09`: Provider unavailable state is non-breaking.
- `GEMUI-10`: Merged full text follows chosen `finalText`.
- `GEMUI-11`: DEV technical diagnostic panel remains absent.
- `GEMUI-12`: Flex styling prevents normal-width overflow.

---

## 26. Locked Acceptance Regression (67/67 PASS)

- **STAB (10/10 PASS)**: Line segmentation and grouping stability (`test_groq_stab.py`).
- **TRACE (10/10 PASS)**: Correlation ID preservation, diagnostic attribution, and secret masking (`test_groq_trace.py`).
- **SOURCE (8/8 PASS)**: Attribution contracts for raw OCR, Groq suggestion, and final text (`test_multiline_physical_2a.py`).
- **NAV (10/10 PASS)**: Re-analyze and back navigation lifecycle without stuck spinners (`test_multiline_physical_2a.py`).
- **UI (10/10 PASS)**: Visual result cards and action responsiveness (`test_multiline_physical_2a.py`).
- **LINEFIX (8/8 PASS)**: Residual top-strip filter and row preservation (`test_linefix_extra_lines.py`).
- **ACCEPT-ID (1/1 PASS)**: Immutability guard against test ID semantic drift (`test_accept_id_guard.py`).

---

## 27. Full AI Regression

- **Command**: `.venv\Scripts\python -m pytest tests/`
- **Result**: `560 passed, 0 failed, 4 warnings in 182.55s`
- **Pass Rate**: 100%.

---

## 28. Business API

- **Command**: `.\gradlew.bat test --tests "com.mathvisionkids.api.ocr.multiline.*"`
- **Result**: `BUILD SUCCESSFUL in 1m 11s` (all multiline controller, service, DTO tests passed).

---

## 29. Mobile Checks

- **TypeScript Compilation**: `npx tsc --noEmit` -> Exit Code 0 (PASS).
- **ESLint**: `npx eslint src` -> Exit Code 0 (PASS).
- **Expo Doctor**: `20/21 checks passed` (1 failure due to known package patch version mismatch, consistent with earlier phases).

---

## 30. Files Modified

| File | Nature of Change |
|---|---|
| `services/ai-service/app/config.py` | Added Gemini config attributes (`gemini_enabled`, `gemini_api_keys`, `gemini_model`, etc.). |
| `services/ai-service/.env.example` | Documented backend-only `GEMINI_API_KEYS=""` configuration. |
| `services/ai-service/app/schemas/ocr_pilot.py` | Added Gemini suggestion fields and `suggestions: List[dict]` to `LineBox`. |
| `services/ai-service/app/integrations/gemini/` | Created `client.py`, `key_pool.py`, `schemas.py`, `corrector.py`. |
| `services/ai-service/app/api/ocr.py` | Wired concurrent Groq + Gemini post-correction via `asyncio.gather`. |
| `services/business-api/src/main/java/com/mathvisionkids/api/ocr/multiline/LineBoxDto.java` | Added Gemini fields and suggestions list. |
| `src/services/api/OcrPilotService.ts` | Added `AdvisorSuggestion` interface and Gemini fields to `LineBox`. |
| `src/app/ocr-pilot/multiline-result.tsx` | Rendered `GỢI Ý 1 — GROQ`, `GỢI Ý 2 — GEMINI`, agreement badge, and choice buttons. |
| `services/ai-service/tests/test_gemini_config.py` | Created GEMCFG test suite (8/8). |
| `services/ai-service/tests/test_gemini_provider.py` | Created GEMPROV test suite (10/10). |
| `services/ai-service/tests/test_dual_advisors.py` | Created DUAL test suite (15/15). |
| `services/ai-service/tests/test_gemini_ui.py` | Created GEMUI test suite (12/12). |

---

## 31. Physical Android Status

`Physical two-advisor UI: OWNER_TEST_REQUIRED`
`Physical provider selection: OWNER_TEST_REQUIRED`

As per MathVision Kids project rules, no physical device execution evidence was fabricated. Automated contract tests and UI layout assertions have verified the contracts. The owner can test the physical dual advisor cards on the real Android device when a real `GEMINI_API_KEYS` is supplied.

---

## 32. Remaining Risks

1. **Gemini Live Quotas**: In production, Gemini Flash may encounter rate limits if high traffic surges occur; `GEMINI_ROTATE_ON_429=false` safely prevents quota sweeping, and Groq / CRNN continue without app failure.
2. **Provider Disagreement Cognitive Load**: If Groq and Gemini suggest different corrections, student must choose. Both cards are clearly labeled with dedicated buttons.

---

## 33. Final Verdict

All automated verification gates are **100% PASS**. Architecture lock, raw CRNN immutability, independent advisor isolation, concurrent execution, and regression integrity are fully verified. The implementation is complete and ready for owner physical testing.
