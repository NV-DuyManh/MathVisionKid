# AI.HWTEXT.PROD.2B — Real 8-Line Advisor Trigger Coverage + Physical Product Closure

**Phase**: PROD.2B  
**Date**: 2026-09-19  
**Baseline**: PROD.2A (architecture integrity restored, 699/699 PASS)  
**Status**: PARTIAL — code fix verified, Gemini quota-limited, physical retest required

---

## 1. Executive Summary

PROD.2A restored internal architecture integrity but left a critical product-behavior gap: on the owner 8-line handwriting sample, **every line reported `Triggered? = NO`**, including Line 3 (`"Mọc trên đổi quề"`) which contains incorrect diacritics (expected `"Mọc trên đồi quê"`). The high aggregate confidence (0.9128) masked acute per-token uncertainty, preventing the hybrid trigger from invoking Groq.

**Root cause**: The CRNN decoder emitted token-level probabilities and margins that revealed decoder ambiguity (`'ổ'` prob=0.4355, margin=0.0938; `'ề'` prob=0.5423, margin=0.2313), but:
1. No decoder-margin or token-aggregate-disagreement anomaly signal existed in the CRNN provider.
2. The Groq trigger function `should_request_groq_correction` had no `tokenAnomalyDetected` / `decoderAnomalyDetected` input parameters.
3. The OCR API route did not propagate these signals from CRNN to the trigger.

**Fix applied**: Three generic, deterministic OCR anomaly signals were added to `CrnnOcrProvider._decode_logits_with_uncertainty()`, propagated through the `LineBox` schema, and consumed by the hybrid trigger. No poem text, dictionary, or canonical lookup was introduced.

**Result**: Lines 1, 3, 4 now correctly trigger Groq. Line 3 receives Groq suggestion `"Mọc trên đồi quê"` (conf=0.98, decision=AUTO_APPLY). Lines 2, 5, 6, 7, 8 remain cleanly bypassed. All 711 AI tests pass. 12/12 TRIGGER8 tests pass.

---

## 2. PROD.2A Remaining Product Gap

| Item | PROD.2A Status | PROD.2B Goal |
|---|---|---|
| Architecture integrity | ✅ 12/12 PASS | Preserve |
| Full AI regression | ✅ 699/699 PASS | Preserve + extend |
| Owner 8-line segmentation | ✅ 8/8 detected | Preserve |
| Line 3 Groq suggestion | ❌ Not triggered | Fix |
| Gemini availability | ⚠️ 429 quota | Report truthfully |
| Physical Android proof | ❌ OWNER_RETEST_REQUIRED | Provide checklist |

The product gap was: a child writes Vietnamese poetry with a diacritic error that the CRNN recognizes incorrectly with high aggregate confidence. Without an advisor suggestion, the student sees the wrong text with no correction option.

---

## 3. 8-Line Uncertainty Metrics Table

Live data from `OWNER_POEM_8_LINES.png` through the real production `/internal/v1/ocr/detect-lines` endpoint:

| LINE | RAW TEXT | RAW_CONF | MIN_TOK | P10 | ENTROPY | ANOMALY | TRIGGER | REASON |
|------|----------|----------|---------|-----|---------|---------|---------|--------|
| 1 | Em yêu mùa hè | 0.8534 | 0.3333 | 0.5729 | 0.0828 | True | **YES** | `min_token < 0.40`, `token_anomaly` |
| 2 | Có hoa sim tím | 0.9584 | 0.8265 | 0.8775 | 0.0535 | False | NO | high_conf_clean (bypassed) |
| 3 | Mọc trên đổi quề | 0.9128 | 0.4355 | 0.7039 | 0.0609 | True | **YES** | `token_anomaly` (decoder/disagreement) |
| 4 | Rung rinh bướm lượn. | 0.8888 | 0.4762 | 0.7103 | 0.1003 | True | **YES** | `token_anomaly` (decoder/disagreement) |
| 5 | Thong thả dắt trâu | 0.9727 | 0.8722 | 0.9147 | 0.0444 | False | NO | high_conf_clean (bypassed) |
| 6 | Trong chiều nắng xế | 0.9561 | 0.7484 | 0.8470 | 0.0823 | False | NO | high_conf_clean (bypassed) |
| 7 | Em hái sim ăn | 0.8865 | 0.6170 | 0.6790 | 0.0853 | False | NO | high_conf_clean (bypassed) |
| 8 | Trời, sao ngọt thế! | 0.9349 | 0.6763 | 0.8186 | 0.0747 | False | NO | high_conf_clean (bypassed) |

**Summary**: 3/8 lines trigger (Lines 1, 3, 4). 5/8 lines cleanly bypass. Zero false positives on clean lines.

---

## 4. Hybrid Trigger Runtime Audit

### Are token confidences generated for multiline CRNN inference?
**YES.** `CrnnOcrProvider._decode_logits_with_uncertainty()` computes per-character `char_probs` and `char_margins` from CTC softmax output for every decoded line. These are used to derive `minTokenConfidence`, `p10TokenConfidence`, `meanEntropy`, and (after PROD.2B) `tokenAnomalyDetected` and `decoderAnomalyDetected`.

### Are minTokenConfidence / p10 / entropy populated or defaulted/null?
**POPULATED.** All 8 lines have non-null values for all uncertainty metrics. Verified in the mandatory table above.

### Are those metrics lost during crop → inference → response mapping?
**NO.** The `uncertainty_data` dictionary from `CrnnOcrProvider` is mapped to `LineBox` fields in `app/api/ocr.py` (lines 808–830), preserving all metrics through the response.

### Is tokenAnomalyDetected ever evaluated on real production multiline data?
**YES (after PROD.2B fix).** Before PROD.2B, this field did not exist. Now it is computed in `CrnnOcrProvider` and passed to `should_request_groq_correction` with `require_token_metrics=True`.

### Are missing metrics treated as safe/non-triggering?
**NO (after PROD.2B fix).** With `require_token_metrics=True`, missing `min_token_confidence` or `p10_confidence` values now force a trigger (TRIGGER8-02 guard).

### Is a legacy raw-confidence-only branch bypassing the hybrid trigger?
**NO.** All paths through the multiline OCR endpoint use the single `should_request_groq_correction` function, which evaluates all hybrid signals.

---

## 5. Root Cause of Missing Groq Suggestions

### Primary root cause: Arithmetic mean masks acute local token errors

Line 3 (`"Mọc trên đổi quề"`) has 16 decoded characters. 14 characters have confidence ~0.99. Only two are uncertain:
- `'ổ'` (token prob = 0.4355, top-2 candidate `'ồ'` at 0.3420, margin = 0.0938)
- `'ề'` (token prob = 0.5423, top-2 candidate `'ê'` at 0.3110, margin = 0.2313)

The arithmetic mean of all 16 character probabilities yields `raw_conf = 0.9128`, which exceeds the 0.82 trigger threshold. The `minTokenConfidence = 0.4355` exceeds the 0.40 baseline threshold.

### Why existing thresholds were insufficient

The hybrid trigger baseline thresholds (raw < 0.82, minTok < 0.40, p10 < 0.50, entropy > 1.20) were designed for cases where multiple tokens are uncertain. In this case:
- `minTok = 0.4355` — just above 0.40
- `p10 = 0.7039` — well above 0.50
- `entropy = 0.0609` — well below 1.20

All thresholds pass because 14/16 tokens are near-perfect, pulling all aggregate statistics into safe ranges.

### The missing signal: decoder margin ambiguity

The critical diagnostic was the **top-1 to top-2 margin** for token `'ổ'`: only 0.0938. This means the decoder was nearly equally confident between two different diacritics. Combined with `prob < 0.50`, this constitutes a **decoder ambiguity anomaly** — a generic OCR uncertainty signal that does not require knowledge of the expected text.

---

## 6. Fix Applied

### 6.1 CrnnOcrProvider — Generic anomaly signals

**File**: `app/ocr/crnn_provider.py` (lines 140–222)

Added computation of `char_margins` (top-1 minus top-2 probability at each CTC timestep) during CTC decoding, and three generic anomaly detectors:

1. **Decoder ambiguity** (`decoderAnomalyDetected`): Any emitted character with `prob < 0.50` AND `margin < 0.15`.
   - Captures: decoder is unsure between two visually similar characters (e.g., `ổ` vs `ồ`).

2. **Disagreement anomaly** (component of `tokenAnomalyDetected`): `raw_conf >= 0.82` AND `min_conf < 0.50` AND `spread >= 0.40`.
   - Captures: high aggregate confidence masking an acute local failure.

3. **Replacement/repetition anomaly** (component of `tokenAnomalyDetected`): `?` characters or `>=4` character repetitions in decoded text.

`tokenAnomalyDetected = decoder_anomaly OR disagreement_anomaly OR replacement_anomaly`

### 6.2 LineBox schema

**File**: `app/schemas/ocr_pilot.py` (lines 30–31)

Added two `Optional[bool]` fields:
- `tokenAnomalyDetected`
- `decoderAnomalyDetected`

### 6.3 Groq trigger function

**File**: `app/integrations/groq/corrector.py` (lines 133–211)

Extended `should_request_groq_correction` with:
- `token_anomaly_detected: Optional[bool]` parameter
- `decoder_anomaly_detected: Optional[bool]` parameter
- `require_token_metrics: bool` parameter
- TRIGGER8-02 guard: missing token metrics → trigger (not bypass)
- TRIGGER8-04 rule: explicit anomaly → trigger regardless of raw confidence

### 6.4 OCR API route

**File**: `app/api/ocr.py` (lines 849–860)

Propagates `tokenAnomalyDetected` and `decoderAnomalyDetected` from `LineBox` to `should_request_groq_correction`, with `require_token_metrics=True`.

### What was NOT changed

- No thresholds modified (0.82, 0.40, 0.50, 1.20 all preserved)
- No poem text, dictionary, or canonical lookup
- No ground truth used in runtime decisions
- No CRNN model, checkpoint, or vocabulary modified
- No segmentation changes
- No Groq model change (remains `qwen/qwen3.8-27b`)
- No Gemini model change (remains `gemini-2.5-flash`)
- No hidden fallback added

---

## 7. Owner 8-Line Groq Live Proof

Live Groq results for the 3 triggered lines (model=`qwen/qwen3.8-27b`):

| Line | Raw Text | Trigger Reason | Groq Suggestion | Groq Conf | Decision | Status | Latency |
|------|----------|---------------|-----------------|-----------|----------|--------|---------|
| 1 | Em yêu mùa hè | `min_token < 0.40` | Em yêu mùa hè | 0.95 | KEEP_RAW | SUCCESS | 0.94s |
| 3 | Mọc trên đổi quề | `token_anomaly` | **Mọc trên đồi quê** | **0.98** | **AUTO_APPLY** | SUCCESS | 1.25s |
| 4 | Rung rinh bướm lượn. | `token_anomaly` | Rung rinh bướm lượn. | 0.95 | KEEP_RAW | SUCCESS | 0.92s |

**Critical result**: Line 3 receives the correct suggestion `"Mọc trên đồi quê"` with high confidence (0.98) and AUTO_APPLY decision. This closes the product-behavior gap for the owner sample.

Lines 1 and 4: Groq confirms the CRNN output is correct (KEEP_RAW). The trigger cost is justified — these lines had genuine uncertainty signals, and Groq validation provides user confidence.

---

## 8. Gemini Live Status

| Metric | Value |
|---|---|
| Model | `gemini-2.5-flash` |
| Live request result | **RATE_LIMIT_429** |
| Fallback enabled | **NO** |
| Automatic model substitution | **DISABLED** |
| Key pool status | 1 key, 60s backoff after 429 |

```
[GeminiKeyPool] Key sha256:13355492398b48cf 429 backoff for 60.0s (no sweep)
[GeminiCorrector] 429 quota on gemini-2.5-flash; automatic substitution is disabled by policy
```

**External limitation**: Gemini 429 rate limiting is a provider-side quota constraint. It cannot be resolved in application code without changing credentials, quota tier, or billing. The system correctly:
- Reports 429 without substituting models
- Does not add hidden fallback
- Logs the exact quota status
- UI should show compact unavailable state for Gợi ý 2

---

## 9. OCR-First Integrity

| Principle | Status |
|---|---|
| CRNN is primary OCR engine | ✅ |
| `rawOcrText` is immutable | ✅ Verified — raw text never modified after CRNN decode |
| `finalText` defaults to `rawOcrText` | ✅ |
| Advisors never silently overwrite `finalText` | ✅ |
| Groq model = `qwen/qwen3.8-27b` | ✅ |
| Gemini model = `gemini-2.5-flash` | ✅ |
| Hidden Gemini fallback | ❌ DISABLED |
| No poem/canonical text in runtime | ✅ |
| No ground truth in trigger logic | ✅ |

---

## 10. Segmentation Status

| Metric | Value |
|---|---|
| Owner 8-line sample | 8/8 lines detected |
| Detector | `runtime6-hue-projection-20260914` |
| Profile | `PROFILE_A` |
| Structural quality | 100.0 |
| Order | Top-to-bottom, correct |
| Segmentation changes in PROD.2B | **NONE** |

---

## 11. TRIGGER8 Test Results — 12/12 PASS

```
tests/test_prod2b_trigger.py::test_trigger8_01_all_8_lines_expose_complete_uncertainty_metrics    PASSED
tests/test_prod2b_trigger.py::test_trigger8_02_missing_token_metrics_cannot_silently_default      PASSED
tests/test_prod2b_trigger.py::test_trigger8_03_hybrid_trigger_used_in_real_multiline_path         PASSED
tests/test_prod2b_trigger.py::test_trigger8_04_high_confidence_anomaly_triggers_via_generic_signal PASSED
tests/test_prod2b_trigger.py::test_trigger8_05_clean_high_confidence_lines_remain_bypassed        PASSED
tests/test_prod2b_trigger.py::test_trigger8_06_no_poem_or_canonical_text_used_in_trigger          PASSED
tests/test_prod2b_trigger.py::test_trigger8_07_live_groq_request_succeeds_for_triggered_line      PASSED
tests/test_prod2b_trigger.py::test_trigger8_08_groq_model_remains_qwen38_27b                      PASSED
tests/test_prod2b_trigger.py::test_trigger8_09_gemini_model_remains_gemini_25_flash               PASSED
tests/test_prod2b_trigger.py::test_trigger8_10_gemini_429_truthful_unavailable_no_fallback        PASSED
tests/test_prod2b_trigger.py::test_trigger8_11_raw_ocr_text_immutable                            PASSED
tests/test_prod2b_trigger.py::test_trigger8_12_final_text_defaults_to_raw                        PASSED
```

**12 passed in 20.62s**

---

## 12. Full AI Regression

```
711 passed, 4 warnings in 95.38s (0:01:35)
```

| Metric | Value |
|---|---|
| Passed | 711 |
| Failed | 0 |
| Skipped | 0 |
| Collected | 711 |
| Warnings | 4 (deprecation, unrelated to PROD.2B) |

**Warnings** (all pre-existing deprecation notices):
1. `httpx` with `starlette.testclient` deprecated
2. `anyio.abc.BlockingPortal` alias deprecated
3. `on_event` deprecated (use lifespan events)
4. FastAPI `on_event` deprecated

---

## 13. Business API

```
BUILD SUCCESSFUL in 25s
17 tests, 0 failures, 100% success rate
```

| Metric | Value |
|---|---|
| Passed | 17 |
| Failed | 0 |
| Skipped | 0 |

---

## 14. Mobile Checks

| Check | Result |
|---|---|
| TypeScript (`npx tsc --noEmit`) | ✅ PASS (exit 0) |
| ESLint (`npm run lint`) | ✅ PASS (exit 0) |
| Expo Doctor (`npx expo-doctor`) | ⚠️ 1 check failed: 18 packages out of date |

Expo Doctor finding is a pre-existing dependency version advisory, not related to PROD.2B changes. No new warnings introduced.

---

## 15. Physical Android Retest Checklist

Status: **OWNER_RETEST_REQUIRED**

The following checklist must be verified on the physical Android device by the owner:

### A. Home Screen
- [ ] Single handwriting entry point visible
- [ ] No separate single-line / multiline cards

### B. Editor Screen
- [ ] Exactly 8 input boxes displayed for owner 8-line poem
- [ ] Boxes aligned with each real handwritten line

### C. Result Screen
- [ ] Raw CRNN text visible for each line
- [ ] Line 3: Gợi ý 1 visible with suggestion `"Mọc trên đồi quê"`
- [ ] If Gemini succeeds: Gợi ý 2 visible with suggestion
- [ ] If Gemini 429: compact unavailable text visible (not error dump)
- [ ] No DEV panel or debug information visible

### D. User Choice Buttons
- [ ] "Dùng gợi ý 1" changes finalText to Groq suggestion only
- [ ] "Dùng gợi ý 2" changes finalText to Gemini suggestion (when available)
- [ ] "Giữ OCR gốc" restores rawOcrText
- [ ] "Tự sửa" opens manual edit (wins over all)

### E. Invisible to Student
- [ ] No Expo, Metro, LAN, localhost, ports visible
- [ ] No Spring Boot, FastAPI, MinIO, Redis, PostgreSQL, API URLs visible
- [ ] No developer instructions or terminal commands visible
- [ ] No demo/test account emails visible
- [ ] No architecture/debug information visible

---

## 16. Files Modified

| File | Change Type | Description |
|---|---|---|
| `app/ocr/crnn_provider.py` | MODIFIED | Added `char_margins` computation, `decoderAnomalyDetected`, `tokenAnomalyDetected` |
| `app/schemas/ocr_pilot.py` | MODIFIED | Added `tokenAnomalyDetected` and `decoderAnomalyDetected` to `LineBox` |
| `app/integrations/groq/corrector.py` | MODIFIED | Added anomaly params and TRIGGER8-02/04 guards to `should_request_groq_correction` |
| `app/api/ocr.py` | MODIFIED | Propagated anomaly signals to trigger with `require_token_metrics=True` |
| `tests/test_prod2b_trigger.py` | NEW | 12 TRIGGER8 tests |

**Files NOT modified**: CRNN checkpoint, vocabulary, segmentation, Groq model config, Gemini model config, mobile app code.

---

## 17. Remaining External Limitations

| Limitation | Impact | Resolution Path |
|---|---|---|
| Gemini 429 rate limit | Gợi ý 2 unavailable | Upgrade quota tier or rotate credentials |
| Expo Doctor 18 packages out of date | Advisory only | Run `npx expo install --check` in dependency phase |
| Physical Android verification | Cannot be proven without owner device | Owner executes Section 15 checklist |

---

## 18. Final Verdict

### What PROD.2B achieved
- **Root cause identified**: Arithmetic mean confidence (0.9128) masked acute per-token decoder ambiguity (token `'ổ'` margin = 0.0938) on Line 3.
- **Generic fix applied**: Three deterministic anomaly signals added without poem text, dictionary, or canonical lookup.
- **Line 3 now triggers Groq**: Receives correct suggestion `"Mọc trên đồi quê"` (conf=0.98, AUTO_APPLY).
- **Zero false positives**: Clean lines (2, 5, 6, 7, 8) remain bypassed.
- **All regressions pass**: 711/711 AI, 12/12 TRIGGER8, 12/12 PROD.2A integrity, 17/17 Business API.

### What PROD.2B cannot close
- **Gemini**: 429 quota exhaustion is an external provider limitation, not a code bug.
- **Physical Android**: Requires owner device evidence (OWNER_RETEST_REQUIRED).

### Verdict: **PARTIAL**
Code fix verified and regression-clean. Blocked only on external Gemini quota and physical device verification.
