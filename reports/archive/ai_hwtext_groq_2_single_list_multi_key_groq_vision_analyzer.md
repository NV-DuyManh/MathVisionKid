# AI.HWTEXT.GROQ.2 — Single-List Multi-Key Groq Vision Analyzer + Hybrid Line Detection + Safe Auto-Failover Report

## Executive Summary
This phase implements Groq Vision as a semantic handwriting line analyzer and assistant into MathVision Kids' handwriting detection pipeline. It resolves chronic over-segmentation issues (8/11/14 candidate boxes collapsing into 4 true physical handwriting rows) using structured vision analysis while preserving deterministic local fallback and strict secret isolation.

---

## Skills Applied

Skills Applied: None — no installed skill matched the backend AI service Groq integration and test regression task.

---

## 1. Single-List Multi-Key Architecture

### Configuration Mandate
All Groq API keys are supplied through a single comma-separated environment variable `GROQ_API_KEYS` in `services/ai-service/.env`:
- No numbered environment variables (`GROQ_API_KEY_01`, `GROQ_API_KEY_02`, etc.) were introduced.
- In `.env.example`, only the safe placeholder `GROQ_API_KEYS=""` is committed.
- The actual keys reside solely in `services/ai-service/.env`, which is verified to be `.gitignore`d.
- Keys are sanitized: whitespace trimmed, empty entries discarded, quotes handled safely.

### Key Pool State Machine (`GroqKeyPool`)
- **Round-Robin Selection**: Each request picks the next available `HEALTHY` key.
- **Transience & Cooldown**: On 429 (Rate Limit) or 503, the key enters `COOLING_DOWN` with backoff; it transitions back to `HEALTHY` once cooldown expires.
- **Authentication Quarantine**: On 401/403 (`AUTH_INVALID`), the key enters `DISABLED_AUTH` for `GROQ_AUTH_DISABLE_SECONDS` (default 1800s) to prevent hammering invalid keys.
- **Degradation**: If a key suffers 3 consecutive transient failures, it transitions to `DEGRADED`.
- **Zero Raw Key Exposure**: Logs only emit `safe_id` (first 8 hex characters of SHA-256 hash). Raw keys never appear in logs, error payloads, diagnostics, or mobile responses.

---

## 2. Model Routing & Structured Output

### Vision Models
- **Primary Model**: `meta-llama/llama-4-scout-17b-16e-instruct`
- **Fallback Model**: `meta-llama/llama-4-maverick-17b-128e-instruct`
- **Model Unavailable Fallback**: If both primary and secondary models are unavailable (or in mock/offline mode), the system safely falls back to local OpenCV line detection with zero disruption to the client.

### Structured Schemas (`GroqLineAnalysis`)
- Pydantic v2 schemas: `GroqLineAnalysis`, `GroqLine`, `BboxNorm`.
- Validates normalized bounding boxes (`[ymin, xmin, ymax, xmax]`), overall confidence, line count, and text proposals.
- Strict confidence gates: results below `GROQ_ACCEPT_CONFIDENCE_THRESHOLD` (0.80) are dropped in favor of local boxes.

---

## 3. Reconcile Engine (`reconcile_groq_lines`)
- Merges Groq's semantic line detection with local OpenCV candidate boxes.
- Eliminates over-segmentation: 8, 11, or 14 raw morphology fragments and horizontal ruling artifacts are grouped into the true 4 handwritten text lines.
- Diacritics (acute, grave, hook, tilde, dot) and descenders/ascenders are preserved and merged into the primary line row.
- Preserves genuine single-line and multi-line structures (e.g. 1-row, 4-row, 6-row) without hardcoded line counts.

---

## 4. Full Automated Test Suite Results

### A. Groq Test Suites (54/54 PASS)
| Test Suite | File | Tests | Status | Description |
|---|---|---|---|---|
| **KEYLIST** | `tests/test_groq_keylist.py` | 8/8 | **PASS** | Comma-separated parsing, whitespace trimming, quotes, empty entries, duplicates, single key, missing var |
| **POOL** | `tests/test_groq_pool.py` | 12/12 | **PASS** | Round-robin rotation, 429 cooldown, 401 disable, retry budget, concurrent access, thread safety |
| **MODEL** | `tests/test_groq_model.py` | 5/5 | **PASS** | Primary model execution, fallback model switch on 404, dual failure fallback, cache dedup |
| **SCHEMA** | `tests/test_groq_schema.py` | 8/8 | **PASS** | Pydantic response validation, bbox normalization, confidence thresholds, error resilience |
| **RECON** | `tests/test_groq_reconcile.py` | 14/14 | **PASS** | 8→4, 11→4, 14→4 row collapse, accent grouping, 1-row / 6-row preservation, confidence gate |
| **PRIV** | `tests/test_groq_privacy.py` | 7/7 | **PASS** | Secret isolation: no key in mobile/spring, safe logging, no raw key in exceptions, .env gitignored |

### B. Complete AI Service Regression (340/340 PASS)
```
pytest -q --tb=short tests/
340 passed, 2 warnings in 22.72s
```
- 0 failures, 0 regressions.
- All legacy contract suites (`test_live_path_contracts.py`, `test_segmentation_contracts.py`, `test_physical_regression.py`, `test_generalized_segmentation.py`, `test_ocr_pilot_endpoint.py`) fully verified and green.

---

## 5. Security & Privacy Audit Verification
- `GROQ_API_KEYS` is located strictly in `services/ai-service/.env`.
- `git check-ignore -v services/ai-service/.env` confirms the file is ignored by `.gitignore:51`.
- `services/ai-service/.env.example` has only safe dummy placeholders (`GROQ_API_KEYS=""`).
- Spring Boot and Student Mobile bundles contain 0 references to `GROQ_API_KEYS`.
- All Groq HTTP logging masks API keys with safe 8-character SHA256 hashes.
