# PROJECT.AUDIT.1.2 — Final Truth Reconciliation

**Date:** 2026-09-13  
**Branch:** `Nam` | **Root:** `E:/MathVisionKid` | **Mode:** TARGETED FINAL CLOSURE ONLY

---

## 0. Repository Safety

- Branch: `Nam` (not switched), Working tree: DIRTY (17 modified + 3 untracked reports)
- Commit: NO | Push: NO

---

## 1. OCR Ground-Truth Reconciliation — CRITICAL

### Authoritative GT Source

`sample_manifest.json` → `"- quạt thép: có thể tạo ra những phi tiêu có tấm độc."` (53 chars)

### Two Valid Measurement Paths

| Path | Method | Prediction | Lev | CER |
|---|---|---|---|---|
| Standalone | `predict_text()` directly | `- quạt thép: có thể tạo ra những phì Tiêu có tẩm độc.` | 3 | 0.0566 |
| Live Pipeline | Spring→FastAPI→YOLO crop→CRNN | `- quạn thép: có thể tạo ra những phì Tiêu có tẩm độc.` | 4 | 0.0755 |

The pipeline adds a `quạt`→`quạn` error due to YOLO line cropping.

### Prior Report Errors Corrected

- **AUDIT.1.1 line 126**: GT said `"quận thép"` — FABRICATED. Correct: `"quạt thép"`
- **AUDIT.1.1 line 129**: Character diffs claimed `ạ` vs `ậ` — WRONG
- **AUDIT.1 CER 0.0755**: CORRECT for live pipeline path
- **int_1 CER 0.0566**: CORRECT for standalone path
- **verify_requirement_5.py**: Fixed fabricated error examples

### Live Verification (2026-09-13)

```
verify_requirement_5.py → exit 0
GT   : - quạt thép: có thể tạo ra những phi tiêu có tấm độc.
PRED : - quạn thép: có thể tạo ra những phì Tiêu có tẩm độc.
CER  : 4/53 = 0.0755 (live pipeline)
All 5 invariants: PASS
```

---

## 2. Metro LAN Binding — CRITICAL

### Prior Claim: `LISTENING (127.0.0.1:8081)` — WRONG

### Actual Evidence

```
Get-NetTCPConnection -LocalPort 8081
LocalAddress: ::    (all interfaces)
```

```
localhost:8081  = REACHABLE
192.168.1.12:8081 = REACHABLE
```

### Fix Applied

Rewrote `check_lan_diagnostics()` in `tools/diagnostics/check_runtime.py` to discover actual bind address via `Get-NetTCPConnection`, test LAN reachability, report `LAN_READY (bind=::, port=8081)`.

### Updated Output

```
Metro State ........... LAN_READY (bind=::, port=8081)
Metro Bind Address .... ::
Metro LAN Reach ....... REACHABLE
LAN Verdict ........... PASS
Overall ............... READY_FOR_FULL_DEMO
```

---

## 3. Flyway Migration Count — REPORT ERROR

AUDIT.1.1 line 229 said `"V1-V9"`. Actual: **10 migrations (V1 through V10)**.

```
V1__init_schema.sql
V2__add_refresh_token_and_ai_job.sql
V3__add_revoked_to_refresh_token.sql
V4__add_version_to_ai_jobs.sql
V5__add_admin_and_audit_indexes.sql
V6__add_ocr_trial_and_feedback.sql
V7__add_ocr_trial_integrity_and_provenance.sql
V8__privacy_fail_closed_and_tester_audit.sql
V9__add_ocr_multiline_tables.sql
V10__add_domain_to_ocr_multiline_trials.sql
```

---

## 4. Fixes Applied in AUDIT.1.2

| # | File | Change |
|---|---|---|
| 1 | `tools/diagnostics/check_runtime.py` | Rewrote `check_lan_diagnostics()` — actual bind detection, LAN reachability test, truthful verdicts |
| 2 | `tools/diagnostics/check_runtime.py` | Added `metro_bind_addr`, `metro_lan_reach`, `lan_verdict` output fields |
| 3 | `scripts/verify_requirement_5.py` | Fixed fabricated error examples to actual diffs (`phi`→`phì`, `tiêu`→`Tiêu`, `tấm`→`tẩm`) |
| 4 | `scripts/verify_requirement_5.py` | Removed unsupported CER range `(CER ~ 7.55% - 11.34%)` |

---

## 5. Tests Matrix

| Suite | Result |
|---|---|
| Spring Boot Gradle | BUILD SUCCESSFUL (all pass) |
| Runtime Diagnostics | PASS (READY_FOR_FULL_DEMO) |
| Live OCR Verification | PASS (exit 0, 5/5 invariants) |
| Duplicate Metro Guard | PASS |
| Dataset Export | PASS (exit 0) |

---

## 6. Contradiction Resolution

| Item | Prior | Reconciled | Verdict |
|---|---|---|---|
| OCR GT string | AUDIT.1.1 fabricated `"quận"` | Manifest: `"quạt"` | CORRECTED |
| OCR CER | 0.0755 vs 0.0566 | Both valid (pipeline vs standalone) | RECONCILED |
| Metro bind | Claimed `127.0.0.1` | Actual `::` (all interfaces) | CORRECTED |
| Migration count | Said V1-V9 | Actual V1-V10 (10 files) | CORRECTED |

---

## 7. Final Verdict

### PROJECT.AUDIT.1.2: PASS

All remaining contradictions resolved. No commit. No push.

## Skills Applied

- `ponytail` (`.agents/skills/ponytail/SKILL.md`) — minimal targeted fixes

**STOP.**
