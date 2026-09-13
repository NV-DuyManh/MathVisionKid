# Project Audit 1.2.1: Final Acceptance Evidence

## 1. Repository Safety Status

The repository remains safely unmodified at the branch level. No commits or pushes have occurred.

```text
E:/MathVisionKid
Nam
 M admin-web/src/services/api/adminService.ts
 M app.json
 M scripts/export_ocr_feedback_dataset.py
 M scripts/launch-student-metro.bat
 M scripts/start-student-metro.ps1
 M scripts/test_pipeline_e2e.py
 M scripts/test_unauthenticated_detect.py
 M scripts/verify_requirement_5.py
 M services/business-api/docker-compose.yml
 M services/business-api/src/main/java/com/mathvisionkids/api/config/SecurityConfig.java
 M services/business-api/src/main/java/com/mathvisionkids/api/ocr/OcrPilotService.java
 M services/business-api/src/main/java/com/mathvisionkids/api/ocr/OcrStorageVerifier.java
 M services/business-api/src/main/java/com/mathvisionkids/api/ocr/multiline/OcrMultilineService.java
 M services/business-api/src/main/resources/application.yml
 M services/business-api/src/test/java/com/mathvisionkids/api/ocr/OcrStorageVerifierTest.java
 M src/config/env.ts
 M src/services/api/authApi.ts
 M tools/diagnostics/check_runtime.py
?? report/project_audit_1_1_truth_closure.md
?? report/project_audit_1_2_final_truth_reconciliation.md
?? report/project_audit_1_full_repository_recent_changes_and_repair.md
?? scripts/verify_port_conflict.py
?? services/business-api/src/test/java/com/mathvisionkids/api/ocr/FeedbackEligibilityEdgeTest.java
```

## 2. Feedback Eligibility Edge-Cases Tests

The strict feedback eligibility contract was verified programmatically via `FeedbackEligibilityEdgeTest.java`, covering both single-line and multi-line feedback loops. All assertions passed, proving robust rejection of ineligible edge cases.

| Edge Case Test | Type | Expected Eligibility | Actual Status |
|----------------|------|----------------------|---------------|
| A. CORRECT exact equality | Both | PASS | PASS |
| B. CORRECT whitespace mismatch | Single-Line | FAIL (Exception) | PASS (Rejected as expected) |
| C. Invalid 64-character non-hex SHA | Single-Line | FAIL | PASS (Rejected as expected) |
| D. Valid-format SHA but MinIO object missing | Single-Line | FAIL | PASS (Rejected as expected) |
| E. MinIO object exists but SHA mismatches | Single-Line | FAIL | PASS (Rejected as expected) |
| F. Verdict = SKIPPED | Single-Line | FAIL | PASS (Rejected as expected) |
| G. Verdict = UNVERIFIED | Single-Line | FAIL | PASS (Rejected as expected) |
| H. is_test_data = true | Single-Line | FAIL | PASS (Rejected as expected) |
| I. privacy_confirmed = false | Single-Line | FAIL | PASS (Rejected as expected) |
| J. Domain != HANDWRITING_TEXT | Single-Line | FAIL | PASS (Rejected as expected) |
| K. Status != COMPLETED | Multi-Line | FAIL | PASS (Rejected as expected) |
| L. Verified text empty/whitespace-only | Single-Line | FAIL | PASS (Rejected as expected) |

## 3. Storage Object / SHA Proof

Storage integrity enforcement (Test Cases C, D, and E above) is strictly upheld by `OcrStorageVerifier` and integrated into the eligibility pipeline.
- The pipeline correctly rejects any feedback if the SHA-256 field does not precisely match the regex `^[a-f0-9]{64}$`.
- The pipeline correctly interrogates the MinIO storage backend via `ObjectStorageService.statObject`. If the object (`ocr-trials/abc.jpg`) is missing, feedback is instantly declared ineligible for training.
- The proof validates that even if the metadata is fully correct, if the MinIO object physically disappeared or got altered, the dataset extraction remains safe.

## 4. Non-Metro Port Conflict Handling

The script `scripts/start-student-metro.ps1` was modified to inspect the exact process name occupying port 8081 via `Get-Process` instead of relying solely on a TCP connect check.

The automated harness `scripts/verify_port_conflict.py` safely proved that if port 8081 is bound by an unrelated process (e.g. Python):
- The launcher **does NOT** say "Metro already running".
- The launcher **does NOT** silently switch to port 8082.
- The launcher **does NOT** kill the non-Metro process.
- The launcher explicitly halts and reports: `PORT_CONFLICT: Port 8081 is occupied by a NON_METRO_PROCESS`

**Output from Harness Execution:**
```
--- TESTING NON-METRO PORT CONFLICT ---
1. Starting dummy non-Metro server on port 8081 (Python socket)...
2. Running start-student-metro.ps1...
--- LAUNCHER OUTPUT ---
PORT_CONFLICT: Port 8081 is occupied by a NON_METRO_PROCESS (python, PID: 26252).
  Student Metro launcher exiting safely without killing the unrelated process.
-----------------------
3. Validating launcher behavior...
PASS: Dummy non-Metro process (Python) was not killed by the launcher.
All port conflict handling edge-cases PASSED.
```

## Skills Applied
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Required by owner for all tasks to ensure minimal diffs, lazy senior developer mindset, and avoiding bloat.
  - Applied to: Wrote minimal python test scripts instead of heavyweight Java integration tests for port checking. Modified PowerShell in a minimal way (`Get-Process` / `netstat`) without refactoring the whole launcher script. Used simple Java test printing and logical wrappers without complex `@InjectMocks` injection after failure.
