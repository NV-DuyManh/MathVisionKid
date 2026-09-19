# AI.HWTEXT.PROD.2C — Gemini Multi-Key Pool + Same-Model Failover

> [!NOTE]
> SUPERSEDED BY AI.HWTEXT.PROD.2E — HISTORICAL RECORD ONLY — CURRENT GEMINI MODEL: gemini-3.6-flash

**Phase**: PROD.2C  
**Date**: 2026-09-19  
**Baseline**: PROD.2B (711/711 PASS, TRIGGER8 12/12, PROD.2A 12/12)  
**Status**: PASS

---

## 1. Executive Summary

Implemented Gemini credential pooling with same-model failover, matching the spirit of the existing Groq multi-key mechanism. The system now parses `GEMINI_API_KEYS` (comma-separated), automatically deduplicates keys, and rotates credentials on 429/AUTH/5xx/timeout errors while keeping the model locked to `gemini-2.5-flash`. Payload errors (400) correctly stop rotation immediately.

The existing `GeminiKeyPool` already had parsing, dedup, round-robin, and per-key state tracking. The primary gap was in `corrector.py`, which returned `None` on the first 429/AUTH error instead of rotating to the next key. This was fixed by replacing the 2-attempt same-key loop with a proper multi-key failover loop.

**Result**: GEMKEY 18/18 PASS, full AI suite 729/729 PASS, PROD.2A integrity 12/12 PASS, Business API 17/17 PASS.

---

## 2. Previous Gemini Credential Behavior

Before PROD.2C:

| Behavior | Status |
|---|---|
| `GEMINI_API_KEYS` parsing | ✅ Existed — comma split, trim, dedup |
| Round-robin `lease_key()` | ✅ Existed |
| Per-key state (HEALTHY/COOLING_DOWN/DISABLED) | ✅ Existed |
| SHA-256 fingerprinting | ✅ Existed |
| **Multi-key failover on 429** | ❌ Corrector returned `None` immediately |
| **Multi-key failover on AUTH** | ❌ Corrector returned `None` immediately |
| **Multi-key failover on 5xx/timeout** | ⚠️ Retried same key once, not next key |
| **400 BAD_REQUEST classification** | ❌ Not classified (fell through to generic) |
| **Configured entries vs unique tracking** | ❌ Not tracked |
| **Cooldown from config** | ❌ Hardcoded 60s |

---

## 3. New GEMINI_API_KEYS Parsing Contract

Input format:
```
GEMINI_API_KEYS="key1,key2,key3,key4"
```

Parsing rules:
1. Split by comma
2. Trim leading/trailing whitespace per entry
3. Ignore empty/whitespace-only entries
4. Remove exact duplicate keys (preserving first-seen order)
5. Never expose raw keys in logs, reports, DTOs, or UI

Example:
```
Input:  "keyA, keyB, keyC, keyB, keyD, keyA, , keyC"
Result: [keyA, keyB, keyC, keyD]
configuredEntries=7, uniqueKeys=4, duplicatesRemoved=3
```

---

## 4. Duplicate Removal Proof

Live execution with owner's actual `GEMINI_API_KEYS` from `.env`:

```
configuredEntries=7
uniqueKeys=7
duplicatesRemoved=0

  sha256:13355492398b48cf  state=HEALTHY
  sha256:a6468b97f8de4765  state=HEALTHY
  sha256:65f2503c5bbd673e  state=HEALTHY
  sha256:5835d107fe190cf6  state=HEALTHY
  sha256:9a88050856cd0e33  state=HEALTHY
  sha256:897c88a5a33e87ef  state=HEALTHY
  sha256:d1bfeb7b013c4d68  state=HEALTHY
```

- 7 owner Gemini keys configured by owner
- 0 duplicates (all keys unique)
- 7 unique keys in pool, all HEALTHY
- Only SHA-256 fingerprints shown, never raw credentials

Dedupe mechanism validated separately with test input containing duplicates:
```
Input:  "testKeyA, testKeyB, testKeyC, testKeyB, testKeyD, testKeyA, , testKeyC"
configuredEntries=7, uniqueKeys=4, duplicatesRemoved=3
```

---

## 5. Key Pool Architecture

```
GeminiKeyPool (module-level singleton)
├── entries: List[GeminiKeyEntry]
│   ├── raw_key (never logged/exposed)
│   ├── safe_id = sha256:<first 16 hex chars>
│   ├── state: HEALTHY | COOLING_DOWN | DISABLED_AUTH | DEGRADED
│   ├── cooldown_until: float
│   ├── failure_count: int
│   └── last_used_at: float
├── _current_index: int (round-robin cursor)
├── configured_entries_count: int
├── duplicates_removed: int
└── cooldown_seconds: float (from config)
```

**Selection**: `lease_key()` uses round-robin among eligible keys, recovering expired cooldowns automatically.

**Singleton**: Pool is initialized once per process via `init_gemini_pool()` and shared across all requests. State persists across multiline OCR calls.

---

## 6. Error Classification

| Error Class | HTTP Status | Key Action | Rotate? |
|---|---|---|---|
| AUTH_ERROR | 401, 403 | DISABLED_AUTH (permanent) | ✅ Yes |
| RATE_LIMIT_429 | 429 | COOLING_DOWN (configurable duration) | ✅ Yes |
| SERVER_ERROR_5XX | 500, 502, 503, 504 | COOLING_DOWN | ✅ Yes |
| TIMEOUT | Connect/Read timeout | COOLING_DOWN | ✅ Yes |
| NETWORK_ERROR | Connection failure | COOLING_DOWN | ✅ Yes |
| BAD_REQUEST | 400 | No state change | ❌ No — payload error |
| MALFORMED_RESPONSE | Parse error | No state change | ❌ No — same response expected |
| RESPONSE_VALIDATION_ERROR | Schema error | No state change | ❌ No |

---

## 7. Rotation / Cooldown / Disable Rules

| Rule | Implementation |
|---|---|
| Round-robin among eligible keys | `lease_key()` advances `_current_index` |
| HEALTHY keys preferred | `is_available()` checks state + cooldown expiry |
| DISABLED_AUTH permanent | Key never re-used until process restart |
| COOLING_DOWN duration | `GEMINI_KEY_COOLDOWN_SECONDS` (default 300s) |
| Cooldown recovery | Automatic on next `lease_key()` if `time >= cooldown_until` |
| Max attempts per request | Each unique key tried at most once |
| Duplicate key guard | `attempted_keys` set prevents re-trying same fingerprint |

**Request-level failover loop**:
```
for each unique eligible key (max = pool.total_keys):
    call_gemini(model="gemini-2.5-flash", key=current_key)
    if SUCCESS → return result, stop
    if BAD_REQUEST → stop immediately (payload error)
    if MALFORMED_RESPONSE → stop immediately
    if AUTH_ERROR → disable key, try next
    if RATE_LIMIT_429 → cooldown key, try next
    if 5xx/TIMEOUT → cooldown key, try next
return UNAVAILABLE
```

---

## 8. Same-Model Lock Proof

GEMKEY-15 test verifies model remains `gemini-2.5-flash` across all key rotation attempts:

```
Test: key1 429 → key2 429 → key3 SUCCESS
Models used: ["gemini-2.5-flash", "gemini-2.5-flash", "gemini-2.5-flash"]
All 3 attempts: gemini-2.5-flash ✅
```

Config enforcements:
- `gemini_model: str = "gemini-2.5-flash"` in Settings
- `gemini_fallback_enabled: bool = False`
- No model substitution code in corrector failover loop
- OCR API route passes `model=getattr(settings, "gemini_model", "gemini-2.5-flash")`

---

## 9. Security / Secret Handling Proof

| Check | Result |
|---|---|
| Raw keys in logs | ❌ Never — only `sha256:` fingerprints logged |
| Raw keys in reports | ❌ Never |
| Raw keys in DTOs | ❌ Never — mobile sees `geminiModel`, `geminiStatus`, not key info |
| Raw keys in exceptions | ❌ Never — `GeminiError` uses safe_id only |
| `.env` committed | ❌ In `.gitignore` |
| `.env.example` contains real keys | ❌ Placeholder values only |
| Key prefix/suffix exposed | ❌ Never — SHA-256 hash only |

GEMKEY-16 test explicitly validates no raw key appears in any log output.

---

## 10. GEMKEY 18/18 Results

```
tests/test_gemini_multikey.py::test_gemkey_01_parse_comma_separated_keys          PASSED
tests/test_gemini_multikey.py::test_gemkey_02_trim_whitespace                     PASSED
tests/test_gemini_multikey.py::test_gemkey_03_ignore_empty_entries                PASSED
tests/test_gemini_multikey.py::test_gemkey_04_remove_exact_duplicates             PASSED
tests/test_gemini_multikey.py::test_gemkey_05_preserve_first_seen_order           PASSED
tests/test_gemini_multikey.py::test_gemkey_06_duplicate_key_not_attempted_twice   PASSED
tests/test_gemini_multikey.py::test_gemkey_07_first_key_success_stops_rotation    PASSED
tests/test_gemini_multikey.py::test_gemkey_08_key1_401_key2_success               PASSED
tests/test_gemini_multikey.py::test_gemkey_09_key1_403_key2_success               PASSED
tests/test_gemini_multikey.py::test_gemkey_10_key1_429_key2_success               PASSED
tests/test_gemini_multikey.py::test_gemkey_11_key1_timeout_key2_success           PASSED
tests/test_gemini_multikey.py::test_gemkey_12_key1_503_key2_success               PASSED
tests/test_gemini_multikey.py::test_gemkey_13_bad_request_no_rotation             PASSED
tests/test_gemini_multikey.py::test_gemkey_14_all_keys_unavailable                PASSED
tests/test_gemini_multikey.py::test_gemkey_15_model_remains_gemini_25_flash       PASSED
tests/test_gemini_multikey.py::test_gemkey_16_raw_key_never_in_logs               PASSED
tests/test_gemini_multikey.py::test_gemkey_17_concurrent_selection_no_corruption   PASSED
tests/test_gemini_multikey.py::test_gemkey_18_pool_state_persists_across_calls    PASSED
```

**18 passed in 0.48s**

---

## 11. Live Multi-Key Failover Proof

### Owner Key Pool — Live Init
```
configuredEntries=7
uniqueKeys=7
duplicatesRemoved=0
All 7 keys: HEALTHY
Model: gemini-2.5-flash
```

### 429 Cooldown + Credential Rotation (simulated)
```
Attempt 1:
  keyFingerprint=sha256:fa361077e494437e
  model=gemini-2.5-flash
  result=RATE_LIMIT_429
  -> state=COOLING_DOWN

Attempt 2:
  keyFingerprint=sha256:2b0e708ffb80e98e
  model=gemini-2.5-flash
  result=SUCCESS
  -> state=HEALTHY

key rotated: True
```

### AUTH Disable + Credential Rotation (simulated)
```
Attempt 1:
  keyFingerprint=sha256:45a98e338e6c3091
  model=gemini-2.5-flash
  result=AUTH_ERROR
  -> state=DISABLED_AUTH

Attempt 2:
  keyFingerprint=sha256:460c79c9d3b540f7
  model=gemini-2.5-flash
  result=SUCCESS
  -> state=HEALTHY
```

### Round-Robin Distribution (simulated)
```
lease #1: sha256:8504906f4a67a3ad
lease #2: sha256:070aff2b58355033
lease #3: sha256:4bc4ceb22cb94c17
lease #4: sha256:aca174e6c14f58b5
lease #5: sha256:8504906f4a67a3ad  (wraps around)
lease #6: sha256:070aff2b58355033
```

**rawKeysExposed=NO**

---

## 12. OCR-First Invariant Proof

| Principle | Status |
|---|---|
| CRNN is primary OCR engine | ✅ Unchanged |
| `rawOcrText` immutable | ✅ Unchanged |
| `finalText` defaults to `rawOcrText` | ✅ Unchanged |
| Groq = Advisor 1 | ✅ Unchanged |
| Gemini = Advisor 2 | ✅ Unchanged |
| Groq model = `qwen/qwen3.8-27b` | ✅ Unchanged |
| Gemini model = `gemini-2.5-flash` | ✅ Unchanged |
| Gemini key failover does not alter rawOcrText | ✅ |
| Gemini key failover does not overwrite finalText | ✅ |
| Gemini key failover does not change Groq behavior | ✅ |
| All keys exhausted → Gemini UNAVAILABLE, CRNN+Groq preserved | ✅ |

---

## 13. Regression Results

| Suite | Passed | Failed | Skipped | Collected |
|---|---|---|---|---|
| **GEMKEY** | 18 | 0 | 0 | 18 |
| **PROD.2A Integrity** | 12 | 0 | 0 | 12 |
| **Full AI Suite** | **729** | **0** | **0** | **729** |
| **Business API** | 17 | 0 | 0 | 17 |

| Mobile Check | Result |
|---|---|
| TypeScript (`npx tsc --noEmit`) | ✅ PASS |
| ESLint (`npm run lint`) | ✅ PASS |
| Expo Doctor | ⚠️ 1 check failed: 18 packages out of date (pre-existing) |

The full AI suite includes all prior suites: GROQLOCK 8/8, MIG25 15/15, MOBGEM 15/15, GEMCFG, GEMPROV, FAILISO, TRIGGER8 12/12, PROD.2A 12/12, GEMKEY 18/18.

Two pre-existing tests were updated to match new multi-key failover behavior:
- `test_gemprov_04_401_failover` — AUTH_ERROR now fails over to next key (not returns None)
- `test_sec_gem_04_env_example_contains_placeholders_only` — `.env.example` now uses placeholder template values

---

## 14. Files Modified

| File | Change | Description |
|---|---|---|
| `app/config.py` | MODIFIED | Added `gemini_connect_timeout_seconds`, `gemini_key_cooldown_seconds`, `gemini_max_key_attempts_per_request` |
| `app/integrations/gemini/key_pool.py` | MODIFIED | Added `configured_entries_count`, `duplicates_removed` tracking; `init_gemini_pool` accepts `cooldown_seconds` |
| `app/integrations/gemini/client.py` | MODIFIED | Added HTTP 400 `BAD_REQUEST` error classification |
| `app/integrations/gemini/corrector.py` | MODIFIED | Replaced 2-attempt same-key loop with multi-key failover loop |
| `.env.example` | MODIFIED | Updated Gemini section with multi-key template and new config knobs |
| `tests/test_gemini_multikey.py` | NEW | 18 GEMKEY tests |
| `tests/test_gemini_provider.py` | MODIFIED | Updated GEMPROV-04 for new failover behavior |
| `tests/test_gemini_security.py` | MODIFIED | Updated SEC-GEM-04 for placeholder template values |

**Files NOT modified**: CRNN checkpoint, vocabulary, segmentation, Groq integration, mobile app, OCR API route.

---

## 15. Owner .env Status

Owner keys have been added to `services/ai-service/.env`:

```
GEMINI_ENABLED=true
GEMINI_API_KEYS="<7 owner keys, comma-separated>"
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_ENABLED=false
GEMINI_KEY_COOLDOWN_SECONDS=300
GEMINI_MAX_KEY_ATTEMPTS_PER_REQUEST=0
```

**Runtime verification:**
```
configuredEntries=7
uniqueKeys=7
duplicatesRemoved=0
All 7 keys: HEALTHY
```

`GEMINI_MAX_KEY_ATTEMPTS_PER_REQUEST=0` means: try each unique key at most once per request.

> **Note**: Never commit `.env` to version control. Raw keys are never shown in this report — only SHA-256 fingerprints.

---

## 16. Remaining Limitations

| Limitation | Impact | Resolution |
|---|---|---|
| Gemini 429 quota | All supplied keys may share same project quota | Upgrade quota tier or use keys from different projects |
| Expo Doctor 18 packages out of date | Advisory only | Run `npx expo install --check` |
| Pool state is in-memory | Lost on process restart | Acceptable for current deployment; keys recover to HEALTHY on restart |

---

## 17. Final Verdict

### Mandatory report fields

```
configuredEntries=7 (owner live .env)
uniqueKeys=7 (owner live .env)
duplicatesRemoved=0 (owner live .env)
rawKeysExposed=NO
model=gemini-2.5-flash
modelFallback=DISABLED
credentialRotation=ENABLED
```

### Verdict: **PASS**

All requirements met:
- ✅ `GEMINI_API_KEYS` supports multiple comma-separated keys
- ✅ Whitespace and blank entries normalized
- ✅ Exact duplicates automatically removed
- ✅ Each unique key attempted at most once per request
- ✅ Failover works for 429, AUTH, 5xx, timeout
- ✅ 400 payload errors do not rotate
- ✅ Model always `gemini-2.5-flash`
- ✅ No hidden model fallback
- ✅ CRNN OCR-first architecture unchanged
- ✅ Groq behavior unchanged
- ✅ Raw keys never exposed
- ✅ GEMKEY 18/18 PASS
- ✅ Full regression 729/729 PASS

---

## Skills Applied

- `ponytail` (`.agents/skills/ponytail/SKILL.md`)
  - Why selected: Credential pooling implementation should be minimal — the existing `GeminiKeyPool` already had 80% of the functionality
  - Applied to: Identified that only the corrector's failover loop needed rewriting, not a new pool architecture
