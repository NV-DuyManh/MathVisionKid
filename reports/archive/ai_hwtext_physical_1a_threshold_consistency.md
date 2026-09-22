# AI.HWTEXT.PHYSICAL.1A — Threshold Consistency + Physical Test Pack Stabilization

## 1. Executive Summary

Phase **AI.HWTEXT.PHYSICAL.1A** reconciles documentation inconsistencies and stabilizes the physical test pack prior to real Android hardware testing by the project owner:
1. **Threshold Audit & Reconcile:** Audited runtime source files and confirmed that actual runtime thresholds strictly match the GROQ.6 validated values (`raw_confidence: 0.82`, `min_token: 0.40`, `p10: 0.50`, `mean_entropy: 1.20`). The contradictory numbers (`p10 < 0.70`, `entropy > 0.45`) in PHYSICAL.1 Section 28 were identified as a documentation typo and corrected. Zero unjustified threshold retuning remains.
2. **Generalization Wording Correction:** Audited fixture manifests and corrected the unproven claim of "2 distinct writers". Both physical evaluation fixtures (`OWNER_POEM_BLOCK_1.png` and `OWNER_POEM_BLOCK_1_VAR2.png`) are captures/variants of the same owner writing. Synthetic font fixtures are never counted as human writers. Truthful language ("Writer diversity is not yet established") is now documented.
3. **Trace Flag Production Safety:** Ensured `ocr_physical_trace_enabled: bool = False` by default in `services/ai-service/app/config.py` and documented it in `.env.example`. Verified that the runtime production guard (`app_env != "production"`) strictly prevents trace logging in production even if enabled in configuration.
4. **Physical Test Pack Stabilization:** Re-verified and structured `report/OWNER_ANDROID_OCR_TEST_CHECKLIST.md` to begin with the exact 10-step A–J workflow without requesting Groq API keys. Re-verified `report/OWNER_ANDROID_OCR_RESULTS_TEMPLATE.md` with complete case placeholders (`BLOCK1`, `BLOCK1_RECROP_1..6`, `UNKNOWN_1..5`, `SUGGEST_ONLY`, `AUTO_APPLY`, `KEEP_RAW`, `GROQ_OFFLINE`, `ARITHMETIC`).
5. **STAB Test Suite:** Created and passed 10/10 automated stabilization tests (`STAB-01` through `STAB-10`) in `services/ai-service/tests/test_groq_stab.py`.
6. **Full Suite Regression:** Verified that all 468 AI test suite items (461 passed, 7 skipped, 0 failed), 10 TRACE tests, 70 core/confidence/decision/mathsafe tests, Business API tests, Mobile TypeScript, Mobile Lint, and Expo Doctor are completely green.

---

## 2. Threshold Contradiction Found

In phase **AI.HWTEXT.PHYSICAL.1**, Section 28 (*Remaining Risks*) contained the following statement:
> *"2. Threshold Sensitivity: Uncertainty trigger thresholds (`p10 < 0.70`, `entropy > 0.45`) are provisional..."*

However, the GROQ.6 baseline and the actual implementation in `services/ai-service/app/integrations/groq/corrector.py` defined:
- `trigger_confidence`: `0.82`
- `min_token_confidence`: `< 0.40`
- `p10_confidence`: `< 0.50`
- `mean_entropy`: `> 1.20`

This discrepancy was investigated across the codebase and commit history.

---

## 3. Actual Runtime Thresholds

The actual running code uses the following exact thresholds:

| Parameter | Actual Value | Role |
|---|---|---|
| `raw_confidence_threshold` | **0.82** | Sequence mean confidence trigger point |
| `min_token_threshold` | **0.40** | High-uncertainty token override (triggers Groq if any token < 0.40) |
| `p10_threshold` | **0.50** | 10th percentile token confidence override (triggers Groq if p10 < 0.50) |
| `mean_entropy_threshold` | **1.20** | Sequence character probability entropy override (triggers Groq if entropy > 1.20) |
| `auto_apply_confidence` | **0.92** | Groq visual correction auto-apply safety threshold |
| `max_edit_ratio` | **0.35** | Maximum allowed Levenshtein edit distance ratio for correction |

---

## 4. Threshold Source Files

The runtime thresholds are declared and enforced in:
1. `services/ai-service/app/config.py:63`
   ```python
   groq_post_correction_trigger_confidence: float = 0.82
   groq_post_correction_auto_apply_confidence: float = 0.92
   groq_post_correction_max_edit_ratio: float = 0.35
   ```
2. `services/ai-service/app/integrations/groq/corrector.py:133-174`
   ```python
   def should_request_groq_correction(
       raw_ocr_text: Optional[str],
       raw_ocr_confidence: Optional[float],
       domain: str = "HANDWRITING_TEXT",
       trigger_confidence: float = 0.82,
       min_token_confidence: Optional[float] = None,
       p10_confidence: Optional[float] = None,
       mean_entropy: Optional[float] = None,
   ) -> bool:
   ...
       if min_token_confidence is not None and min_token_confidence < 0.40:
           return True
       if p10_confidence is not None and p10_confidence < 0.50:
           return True
       if mean_entropy is not None and mean_entropy > 1.20:
           return True
       if raw_ocr_confidence < trigger_confidence:
           return True
   ```
3. `services/ai-service/app/api/ocr.py:824-832`
   Invokes `should_request_groq_correction` passing `line.minTokenConfidence`, `line.p10TokenConfidence`, and `line.meanEntropy`.

---

## 5. GROQ.6 Comparison

| Metric / Threshold | GROQ.6 Baseline | PHYSICAL.1 Code | PHYSICAL.1 Report Text | PHYSICAL.1A Reconciled |
|---|---|---|---|---|
| Raw confidence threshold | `0.82` | `0.82` | `0.82` | **0.82** (MATCH) |
| minTokenConfidence threshold | `0.40` | `0.40` | `0.40` | **0.40** (MATCH) |
| p10TokenConfidence threshold | `0.50` | `0.50` | `0.70` *(typo)* | **0.50** (CORRECTED) |
| meanEntropy threshold | `1.20` | `1.20` | `0.45` *(typo)* | **1.20** (CORRECTED) |

**Conclusion:** Zero code-level threshold drift occurred. The actual source code remained 100% faithful to the GROQ.6 validated architecture. The discrepancy was confined to documentation and has been reconciled.

---

## 6. Any Revert/Correction Performed

1. **Corrected Report:** Modified `report/ai_hwtext_physical_1_android_real_world_validation.md` Section 28 to accurately cite `(raw_confidence < 0.82, min_token < 0.40, p10 < 0.50, mean_entropy > 1.20)`.
2. **Safe Default for Trace:** Set `ocr_physical_trace_enabled: bool = False` in `services/ai-service/app/config.py` (previously defaulted to `True`).
3. **Environment Documentation:** Added `OCR_PHYSICAL_TRACE_ENABLED=false` to `services/ai-service/.env.example`.
4. **TRACE Suite Robustness:** Updated `services/ai-service/tests/test_groq_trace.py` to explicitly patch `ocr_physical_trace_enabled=True` during log inspection tests and verify that production mode suppresses logging.

---

## 7. Generalization Wording Audit

In `report/ai_hwtext_physical_1_android_real_world_validation.md`, Section 23 previously stated:
> *"Rationale: Verified evaluation lines currently cover 3 blocks and 2 distinct writers."*

Audit of `tests/fixtures/ocr_eval/manifest.json`:
- `poem_block_1_physical`: `source="OWNER_PHYSICAL"` (`OWNER_POEM_BLOCK_1.png`)
- `poem_block_1_physical_variant`: `source="OWNER_PHYSICAL"` (`OWNER_POEM_BLOCK_1_VAR2.png`)
- `poem_block_2_synthetic`: `source="SYNTHETIC"` (`SYNTHETIC_POEM_BLOCK_2.png`)
- `poem_block_3_synthetic`: `source="SYNTHETIC"` (`SYNTHETIC_POEM_BLOCK_3.png`)

Both physical fixtures originate from the same owner sample. The synthetic fixtures are generated font renderings and must not be counted as human writers.

**Correction applied:**
> *"Current physical validation contains 8 lines from two physical captures/variants. Writer diversity is not yet established. Synthetic benchmark lines are never counted as human writers. To achieve SUPPORTED, the pipeline requires testing against multi-page, varied handwriting styles from independent physical writers."*

---

## 8. Writer Diversity Evidence

- **Proven Distinct Physical Writers:** **NOT_PROVEN** (Only 1 physical handwriting source: Owner).
- **Physical Lines Evaluated:** 8 lines across 2 capture variants.
- **Synthetic Lines Evaluated:** 8 lines across 2 synthetic poems.
- **Generalization Status:** Remains **PROVISIONAL** until owner captures handwriting from diverse physical writers.

---

## 9. Trace Flag Safety

| Check | Expected | Actual | Verdict |
|---|---|---|---|
| `trace_default` | `false` | `false` (`app/config.py:69`) | **PASS** |
| `production_trace_possible` | `NO` | `NO` (blocked by `app_env != "production"`) | **PASS** |
| `dev_only_guard` | Active | Active (`app/api/ocr.py:952`) | **PASS** |
| Credential Redaction | Active | No keys / base64 in logs (`TRACE-02`, `TRACE-03`) | **PASS** |

---

## 10. Owner Test Pack Status

Both owner guidance files were verified and stabilized:
1. **[report/OWNER_ANDROID_OCR_TEST_CHECKLIST.md](file:///e:/MathVisionKid/report/OWNER_ANDROID_OCR_TEST_CHECKLIST.md):**
   - Begins with exact steps **A through J**:
     - `A. Start services`
     - `B. Confirm Spring :8080 reachable from Android`
     - `C. Confirm FastAPI :8000 healthy from Spring`
     - `D. Confirm Metro / Expo app connected`
     - `E. Confirm OCR_PHYSICAL_TRACE_ENABLED=true only for dev test`
     - `F. Confirm diagnostic panel visible`
     - `G. Run Block 1`
     - `H. Copy requestId`
     - `I. Capture screenshot`
     - `J. Record raw/final OCR`
   - Explicitly instructs the owner **never** to expose API keys.
2. **[report/OWNER_ANDROID_OCR_RESULTS_TEMPLATE.md](file:///e:/MathVisionKid/report/OWNER_ANDROID_OCR_RESULTS_TEMPLATE.md):**
   - Populated with individual sections for `BLOCK1`, `BLOCK1_RECROP_1..6`, `UNKNOWN_1..5`, `SUGGEST_ONLY`, `AUTO_APPLY`, `KEEP_RAW`, `GROQ_OFFLINE`, and `ARITHMETIC`.
   - Each section includes placeholders for `Screenshot filename`, `Request ID`, `Expected text`, `Actual raw OCR`, `Actual final text`, and `Pass/Fail notes`.

---

## 11. STAB Tests

Created automated test suite `services/ai-service/tests/test_groq_stab.py` covering:

| Test ID | Description | Result |
|---|---|---|
| `STAB-01` | Actual runtime thresholds documented (0.82 / 0.92 / 0.35) | **PASS** |
| `STAB-02` | GROQ.6 vs current threshold drift resolved (0.82 / 0.40 / 0.50 / 1.20) | **PASS** |
| `STAB-03` | No unjustified threshold retune remains (0.70 / 0.45 not applied) | **PASS** |
| `STAB-04` | Synthetic fixtures not counted as human writers in manifest | **PASS** |
| `STAB-05` | Writer diversity wording truthful (owner captures only) | **PASS** |
| `STAB-06` | Trace default production-safe (`ocr_physical_trace_enabled == False`) | **PASS** |
| `STAB-07` | Trace dev-only guard verified (`app_env == "production"` suppresses logs) | **PASS** |
| `STAB-08` | Owner checklist exists with A–J steps and secret protection | **PASS** |
| `STAB-09` | Owner results template exists with required case placeholders | **PASS** |
| `STAB-10` | No OCR architecture change (CRNN primary, canonical override False) | **PASS** |

**STAB Suite Verdict:** **10/10 PASS (100%)** in 7.30s.

---

## 12. Regression

- **TRACE Tests (`test_groq_trace.py`):** 10/10 PASS in 10.72s.
- **Core Uncertainty & Decision Suites (`test_groq_confidence_calibration.py`, `test_groq_decisions.py`, `test_groq_ocr_first.py`, `test_groq_metrics.py`):** 70/70 PASS in 3.33s.
- **Full AI Suite (`services/ai-service/tests/`):** **461 passed, 7 skipped, 0 failed** in 188.36s.
- **Business API (`OcrMultilineServiceTest`):** **BUILD SUCCESSFUL** in 11s.
- **Mobile TypeScript (`npx tsc --noEmit`):** **PASS** (0 errors).
- **Mobile Lint (`npx eslint src`):** **PASS** (0 errors, 2 warnings).
- **Expo Doctor (`npx expo-doctor`):** **PASS** (20/21 passed; baseline version check).

---

## 13. Files Modified

- `services/ai-service/app/config.py`: Set `ocr_physical_trace_enabled: bool = False` for production safety.
- `services/ai-service/.env.example`: Added `OCR_PHYSICAL_TRACE_ENABLED=false` documentation.
- `services/ai-service/tests/test_groq_trace.py`: Explicitly enabled trace during log inspection tests; tested production guard in TRACE-10.
- `services/ai-service/tests/test_groq_stab.py`: Created 10 automated stabilization tests (`STAB-01` to `STAB-10`).
- `report/OWNER_ANDROID_OCR_TEST_CHECKLIST.md`: Structured with explicit A–J steps and secret protection.
- `report/OWNER_ANDROID_OCR_RESULTS_TEMPLATE.md`: Populated with complete case placeholders.
- `report/ai_hwtext_physical_1_android_real_world_validation.md`: Reconciled threshold typo and generalization wording.
- `report/ai_hwtext_physical_1a_threshold_consistency.md`: Created comprehensive phase report.

---

## 14. Final Verdict

Phase **AI.HWTEXT.PHYSICAL.1A** is **PASS**.
All configuration, documentation, and test pack inconsistencies are completely resolved. The codebase is frozen, verified, and ready for physical Android hardware validation by the owner.

---

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Direct, simplest root-cause resolution without over-engineering; audited exact code lines, preserved locked architecture, and fixed documentation inconsistencies with minimal diffs.
  - Applied to: Configuration audit, test pack stabilization, STAB test suite.
