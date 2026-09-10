# Parallel A1.2.5 — Security Regression Rollback & Final Evidence Closure

## 1. Executive Summary
During task A1.2.5, the temporary debugging modification in `GlobalExceptionHandler.java` (which had introduced client-facing stack trace details into API JSON responses during A1.2.4 diagnosis) was completely rolled back and replaced with a hardened security pattern. The error handler now logs full exception stack traces strictly on the server-side via SLF4J, while returning an opaque, canonical safe error response to clients (`INTERNAL_ERROR`, safe user message, correlation `requestId`, `details: null`).

A dedicated automated security regression test (`GlobalExceptionHandlerSecurityTest`) was created, verifying that unexpected 500 exceptions disclose zero internal details (classes, line numbers, file paths, SQL statements, Spring/Hibernate internals) while preserving helpful 4xx domain validation messages. Full E2E security verification of Admin Web password reset, refresh token revocation, Teacher batch roster validation, Admin RBAC, full test suites across Spring Boot (74 tests), Python (97 tests), and frontends confirmed complete system stability.

Parallel Track A1.2 is now fully frozen and ready for final review. Track A1.3 has not been started. Phase 4.3 remains `BLOCKED_DATASET`.

---

## 2. Stack Trace Exposure Regression
* **Incident Description**: In task A1.2.4, while diagnosing an unexpected 500 Internal Server Error during Teacher batch submissions, `GlobalExceptionHandler.java` was modified to populate the JSON response `details` map with `ex.getMessage()`, `ex.getClass().getName()`, and `ex.getStackTrace()[0].toString()`.
* **Security Risk**: Exposing internal Java class names, exception messages, line numbers, and file paths to API clients violates OWASP A05:2021 (Security Misconfiguration) and Information Disclosure principles. Attackers could leverage these internals to reconstruct backend filesystem layouts, framework versions, and data schemas.

---

## 3. Root Cause
* The 500 error in A1.2.4 was caused by a malformed synthetic test payload in `scratch/teacher_roster.py` where the required field `fileIndex` was missing from the manifest JSON objects, triggering a `NullPointerException` in `BatchService.java:105`.
* Rather than relying solely on server logs, the exception handler was temporarily augmented to output error details to the client to expedite diagnosis.

---

## 4. Security Fix
* Modified [GlobalExceptionHandler.java](file:///e:/MathVisionKid/services/business-api/src/main/java/com/mathvisionkids/api/config/GlobalExceptionHandler.java#L73-L86) to completely eliminate client-facing error details.
* Reverted `details` parameter in `handleGeneralException` to `null`:
```java
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiErrorResponse> handleGeneralException(Exception ex, HttpServletRequest request) {
    String requestId = getRequestId(request);
    logger.error("Unhandled exception requestId={}", requestId, ex);
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(buildError("INTERNAL_ERROR", "An unexpected error occurred", requestId, null));
}
```
* Removed client exposure of Java stack traces, exception class names, filenames, source line numbers, filesystem paths, SQL statements, and environment secrets.

---

## 5. Server-Side Exception Logging
* Implemented structured server-side logging using SLF4J:
  ```java
  private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(GlobalExceptionHandler.class);
  ```
* Every unhandled exception is logged with its unique `requestId`:
  `logger.error("Unhandled exception requestId={}", requestId, ex);`
* Full stack traces, root causes, and debugging context are preserved in server logs (`runtime\logs\spring.log`) without leaking to HTTP responses.

---

## 6. Client Error Response
* For all unhandled 500 Internal Server Errors, clients receive exclusively the canonical safe structure:
  ```json
  {
    "error": {
      "code": "INTERNAL_ERROR",
      "message": "An unexpected error occurred",
      "requestId": "3a005ee5-b541-477a-b9c1-4ba7ea0c156f",
      "details": null
    }
  }
  ```
* `details` is strictly `null`. No sensitive diagnostics are transmitted to browsers or external callers.

---

## 7. 500 Information Disclosure Test
* Created targeted automated security test in [GlobalExceptionHandlerSecurityTest.java](file:///e:/MathVisionKid/services/business-api/src/test/java/com/mathvisionkids/api/config/GlobalExceptionHandlerSecurityTest.java#L32-L61):
  - Method: `testUnexpectedExceptionHidesSensitiveDetailsAndStackTraces()`
  - Simulates an internal crash containing simulated SQL, repository paths, class names, line numbers, and secrets.
  - Verifications:
    - HTTP Status: `500 INTERNAL_SERVER_ERROR`
    - `error.code` == `"INTERNAL_ERROR"`
    - `error.message` == `"An unexpected error occurred"`
    - `error.requestId` is present
    - Response body asserted NOT to contain:
      - `"stackTrace"`
      - `"NullPointerException"`
      - `"org.springframework"`
      - `"org.hibernate"`
      - `"java.lang."`
      - `".java:"`
      - `"MathVisionKid"`
      - `"SQL"`
      - `"JDBC"`
* **Result**: **PASS** (Executed in 0.032s).

---

## 8. 4xx Validation Regression
* Created targeted test in [GlobalExceptionHandlerSecurityTest.java](file:///e:/MathVisionKid/services/business-api/src/test/java/com/mathvisionkids/api/config/GlobalExceptionHandlerSecurityTest.java#L63-L73):
  - Method: `testDomainValidationExceptionPreservesSafeMessage()`
  - Verifies that expected domain validation exceptions (e.g. `ApiException("VALIDATION_ERROR", "Student outside classroom for index 0", HttpStatus.BAD_REQUEST)`) are NOT swallowed or turned into generic 500s.
  - Confirms client receives safe domain code `VALIDATION_ERROR` and message `"Student outside classroom for index 0"`.
* **Result**: **PASS** (Executed in 0.274s).

---

## 9. Password Reset UI
* Reset action executed end-to-end through Admin Web UI (`http://localhost:5174/users`):
  1. Authenticated as Admin `admin.demo@mathvision.local`.
  2. Located synthetic user `syn_sec_student@mathvision.local` (`userId = 142b207f-131a-488a-9c93-2224255c6c7f`).
  3. Clicked "Đặt lại mật khẩu" -> Confirmation modal -> "Tạo mật khẩu tạm thời".
  4. One-time temporary password dialog rendered with temporary password: `[REDACTED]`.
  5. Captured dialog screenshot artifact: `temp_password_dialog_1789018506811.png`.
* **UI Flow**: **PASS**.

---

## 10. Old Password Rejection
* Tested authentication immediately after Admin UI reset:
  - `POST /api/v1/auth/login` with `syn_sec_student@mathvision.local` and initial password `[REDACTED]`.
  - HTTP Status: **401 Unauthorized**.
  - Response: `{"error":{"code":"UNAUTHORIZED","message":"Invalid credentials","requestId":"...","details":null}}`.
* **Result**: **REJECTED (PASS)**.

---

## 11. Temporary Password Login
* Tested authentication with generated temporary password:
  - `POST /api/v1/auth/login` with `syn_sec_student@mathvision.local` and temporary password `[REDACTED]`.
  - HTTP Status: **200 OK**.
  - Returned valid `accessToken` and `refreshToken`.
* **Result**: **LOGIN PASS**.

---

## 12. Old Refresh Token Rejection
* Retained pre-reset refresh token captured prior to Admin UI reset.
* Attempted token refresh:
  - `POST /api/v1/auth/refresh` with `{"refreshToken": "[REDACTED]"}`.
  - HTTP Status: **401 Unauthorized**.
  - Response: Token rejected / revoked.
* Confirmed `RefreshTokenService.revokeAllUserTokens(user)` invalidated all prior refresh tokens upon password reset.
* **Result**: **REJECTED (PASS)**.

---

## 13. /me Verification
* Called `/api/v1/me` using newly issued `accessToken` from temporary password login:
  - `GET /api/v1/me`
  - HTTP Status: **200 OK**
  - Payload:
    - `email`: `syn_sec_student@mathvision.local`
    - `role`: `STUDENT`
    - `displayName`: `Synthetic Security Student`
* **Result**: **PASS**.

---

## 14. Temporary Password Persistence
* Inspected browser client storage during and after dialog display:
  - `localStorage`: Confirmed 0 instances of temporary password or target credentials (only Admin's own session state/tokens).
  - `sessionStorage`: Confirmed 0 instances of temporary password.
  - `IndexedDB`: 0 temporary credentials stored.
  - `tokenStore`: Contains exclusively the logged-in Admin's credentials.
  - Console logs: Clean; 0 temporary passwords logged.
  - Post-refresh check: Dialog closed, page refreshed, storage re-inspected; temporary password was held strictly in transient component state and is completely unrecoverable.
* **Result**: `TEMP_PASSWORD_PERSISTED=NO`.

---

## 15. Teacher Batch In-Roster
* Re-ran real Teacher batch submission workflow:
  - Teacher: `syn_teacher@mathvision.local`
  - Classroom: Class X (`71c39122-9e2a-4e3d-a9a2-43692276c1d7`)
  - Enrolled Student A: `13a14c1e-89de-4a8f-ba4c-e3fcaa79d54c`
  - Assignment: `4c43b637-c21f-4f8a-a364-34c5f59c656c`
  - Batch: `13b7a271-4c1e-4d49-9165-0531eb7028f8`
  - Endpoint: `POST /api/v1/teacher/batches/{batchId}/submissions`
* HTTP Status: **202 ACCEPTED**.
* **Result**: **PASS**.

---

## 16. Teacher Batch Out-of-Roster
* Submitted mapping to Student B (`2fd0d1a8-fbfe-404c-8ac4-be844f93f724`), who is ACTIVE but NOT enrolled in Class X:
  - Endpoint: `POST /api/v1/teacher/batches/{batchId}/submissions`
* HTTP Status: **400 Bad Request**.
* Canonical error response:
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Student outside classroom for index 0",
      "requestId": "6b0a9bcd-55e9-428d-bf06-7e42ca64c6f9",
      "details": null
    }
  }
  ```
* **Result**: **REJECTED (PASS)**.

---

## 17. Admin RBAC
* Tested role segregation across Admin and Teacher endpoints:
  1. `ADMIN` -> `GET /api/v1/admin/dashboard`: **200 OK**
  2. `TEACHER` -> `GET /api/v1/admin/dashboard`: **403 FORBIDDEN**
  3. `STUDENT` -> `GET /api/v1/admin/dashboard`: **403 FORBIDDEN**
  4. `ADMIN` -> `POST /api/v1/teacher/submissions/{id}/approve`: **403 FORBIDDEN**
  5. `ADMIN` -> `POST /api/v1/teacher/submissions/{id}/override`: **403 FORBIDDEN**
* **Result**: **PASS**.

---

## 18. Spring XML Test Discovery
* Executed `./gradlew.bat clean test` in `services/business-api`.
* Parsed test XML report files in `build/test-results/test/`:
  - `AdminControllerTest`: 20 tests, 0 failures, 0 errors, 0 skipped
  - `HttpAiAnalysisGatewayTest`: 8 tests, 0 failures, 0 errors, 0 skipped
  - `InternalAiCallbackControllerTest`: 6 tests, 0 failures, 0 errors, 0 skipped
  - `AuthControllerTest`: 4 tests, 0 failures, 0 errors, 0 skipped
  - `BatchControllerTest`: 7 tests, 0 failures, 0 errors, 0 skipped
  - `BusinessApiApplicationTests`: 1 test, 0 failures, 0 errors, 0 skipped
  - `TeacherClassControllerTest`: 1 test, 0 failures, 0 errors, 0 skipped
  - `GlobalExceptionHandlerSecurityTest`: 2 tests, 0 failures, 0 errors, 0 skipped
  - `TeacherDashboardControllerTest`: 4 tests, 0 failures, 0 errors, 0 skipped
  - `StateTransitionTest`: 16 tests, 0 failures, 0 errors, 0 skipped
  - `SubmissionControllerTest`: 5 tests, 0 failures, 0 errors, 0 skipped
* **Total**: **74 tests passed, 0 failed, 0 skipped** (Baseline 72 + 2 new security regression tests).

---

## 19. Spring Plain Build
* Command: `gradlew.bat build` (strictly without `-x test`).
* Output:
  ```
  BUILD SUCCESSFUL in 5s
  7 actionable tasks: 3 executed, 4 up-to-date
  ```
* **Result**: **PASS**.

---

## 20. Admin Build/Lint
* Directory: `admin-web`
* Build: `npm run build`
  - Output: `✓ 11781 modules transformed. dist/index.html 0.70 kB, dist/assets/index-DulQUYfE.js 709.98 kB. ✓ built in 5.04s`.
* Lint: `npm run lint` (`oxlint`)
  - Output: `Found 0 warnings and 0 errors. Finished in 22ms on 26 files`.
* **Result**: **PASS**.

---

## 21. Teacher Regression
* Directory: `teacher-web`
* Build: `npm run build`
  - Output: `✓ 11783 modules transformed. dist/index.html 0.46 kB, dist/assets/index-BwhJZANm.js 665.69 kB. ✓ built in 4.03s`.
* **Result**: **PASS**.

---

## 22. Student Regression
* Directory: repository root (`packages/`, `src/`)
* Type Check: `npx tsc --noEmit`
  - Exit code: 0, 0 errors.
* Lint: `npm run lint` (`expo lint`)
  - Exit code: 0, 0 errors (8 unused variable warnings, 0 fatal errors).
* **Result**: **PASS**.

---

## 23. Python Regression
* Directory: `services/ai-service`
* Command: `.venv/Scripts/python.exe -m pytest tests/`
* Output:
  ```
  ======================= 97 passed, 2 warnings in 11.44s =======================
  ```
* **Passed**: 97, **Failed**: 0, **Skipped**: 0.
* **Result**: **PASS**.

---

## 24. Runtime
* Command: `scripts/restart-all.bat`
* Diagnostic output:
  ```
  Docker ................. PASS
  PostgreSQL ............. PASS
  MinIO .................. PASS
  Redis .................. PASS
  Spring Boot ............ PASS
  FastAPI ................ PASS
  Celery Worker .......... PASS
  Teacher Web ............ PASS
  Admin Web .............. PASS
  Student Mobile ......... CONFIGURED

  Overall ............... READY_FOR_DEMO
  ```
* **Result**: **READY_FOR_DEMO**.

---

## 25. Silent Launcher
* Launched processes managed silently in background with redirected logfiles and recorded PIDs in `runtime/pids/`.
* Additional popup terminal windows created: **0**.
* **Result**: **PASS**.

---

## 26. YOLO SHA
* Target artifact: `services/ai-service/models/yolov8n_mathvision_det_v1.pt`
* Expected SHA-256: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
* Actual SHA-256: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
* Model weights modified: **NO**.
* **Result**: **PASS**.

---

## 27. Demo Account Verification
* Tested authentication against active Spring backend for canonical dev accounts:
  - `minh.student@mathvision.local`: HTTP 200 OK (access token issued)
  - `lan.teacher@mathvision.local`: HTTP 200 OK (access token issued)
  - `admin.demo@mathvision.local`: HTTP 200 OK (access token issued)
* Documented dev accounts preserved intact; zero passwords mutated during verification.
* **Result**: **PASS**.

---

## 28. Secret Audit
* Audit of current Admin reports (`report/parallel_a1_*.md`):
  - Passwords and tokens redacted using `[REDACTED]`.
  - `audit_events` PostgreSQL metadata verified: contains 0 plaintext passwords, 0 access tokens, 0 refresh tokens.
  - Plaintext secrets in current Admin reports: **0**.
* **Result**: `PLAINTEXT_SECRET_IN_CURRENT_ADMIN_REPORTS=0`.

---

## 29. Files Modified
* Modified:
  - [GlobalExceptionHandler.java](file:///e:/MathVisionKid/services/business-api/src/main/java/com/mathvisionkids/api/config/GlobalExceptionHandler.java) — Removed client-facing stack trace exposure; retained server-side SLF4J logging.
* Added:
  - [GlobalExceptionHandlerSecurityTest.java](file:///e:/MathVisionKid/services/business-api/src/test/java/com/mathvisionkids/api/config/GlobalExceptionHandlerSecurityTest.java) — Automated security test for 500 information disclosure prevention and 4xx domain validation preservation.
  - [report/parallel_a1_2_5_security_final_freeze.md](file:///e:/MathVisionKid/report/parallel_a1_2_5_security_final_freeze.md) — Comprehensive evidence report.

---

## 30. Final Assessment
All requirements of Parallel Track A1.2.5 have been strictly satisfied. The client stack trace vulnerability introduced during A1.2.4 diagnosis has been eradicated, automated regression guards are permanently in place, full E2E security flows are re-verified, and every test suite passes across the repository.

* **Status**: **READY_FOR_REVIEW**
* **Parallel Track A1.3 Started**: **NO**
* **Phase 4.3**: Remains **BLOCKED_DATASET**
