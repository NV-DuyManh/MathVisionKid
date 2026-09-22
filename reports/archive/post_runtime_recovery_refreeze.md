# Post-Runtime Recovery Contract & Default-Mode Refreeze

**Date:** 2026-09-09  
**Project:** MathVision Kids  
**Evaluation Mode:** TARGETED VERIFICATION ONLY  
**Assessment Status:** READY_FOR_REVIEW  

---

## 1. Executive Summary

Following recent local runtime background recovery work, an audit and contract refreeze was conducted across the authentication interfaces, AI runtime configuration, unified background launcher, process cleanup safety, and test suites. 

Key results:
- **Canonical Auth Field Established:** Verified authoritative OpenAPI specification (`contracts/openapi/mathvision-api.yaml`), which explicitly specifies `accessToken`. The temporary `token` / `accessToken` alias duplication introduced in `AuthResponse.java` during previous recovery was removed. Spring Boot and all client adapters (Student mobile and Teacher web) now strictly and consistently consume and emit `accessToken`.
- **Zero Duplicate Token Aliases:** `AuthResponse` serializes exactly `accessToken` and `refreshToken`. Redundant aliases were eliminated.
- **AI Mode Segregation:** Fresh-clone onboarding defaults to `FIXTURE` mode (`.env.example` and Pydantic `app/config.py`), requiring no Git-ignored weights. The current developer machine intentionally selects `MODEL` mode via local Git-ignored `.env`. In `MODEL` mode, missing weights produce an explicit `MODEL_NOT_AVAILABLE` failure without silent fallback to fixture mode.
- **Silent Launcher Integrity:** `scripts/start-all.bat` launches all 4 services and infrastructure with zero extra console windows, reaching `READY_FOR_DEMO` cleanly.
- **Stop-All Process Safety:** Enhanced `scripts/stop-all.ps1` fallback port checks (ports 8080, 8000, 5173) to verify MathVision process ownership via WMI/CIM command-line inspection before termination, preventing disruption to unrelated developer processes.
- **Full Test Suite & Validation:** All 51 Spring Boot tests, 97 Python tests, and Student static typecheck/lint pass cleanly.

---

## 2. Canonical Auth Contract

Inspection of canonical specification files and client consumers:

1. **`contracts/openapi/mathvision-api.yaml` (Lines 568–578):**
   ```yaml
   LoginResponse:
     type: object
     properties:
       accessToken:
         type: string
       tokenType:
         type: string
       expiresIn:
         type: number
       user:
         $ref: '#/components/schemas/User'
   ```
   **Evidence:** The authoritative OpenAPI specification explicitly names the JWT property `accessToken`. It does **not** define a `token` field in `LoginResponse`.

2. **Student Client (`src/context/AuthContext.tsx`, `src/services/api/authApi.ts`):**
   Originally designed to consume `data.accessToken` and store it via `tokenStorage.saveTokens(data.accessToken, data.refreshToken)`.

3. **Teacher Web Client (`teacher-web/src/services/api/SpringTeacherService.ts`, `apiClient.ts`):**
   Previously implemented a dual fallback (`accessToken || token`). Now aligned to strictly consume `accessToken`.

**Conclusion:** `CANONICAL_TOKEN_FIELD=accessToken`.

---

## 3. AuthResponse Audit

During recent runtime recovery, `AuthResponse.java` was modified to expose both `token` and `accessToken` via a getter:
```java
// Prior recovery state (duplicate fields):
public class AuthResponse {
    private String token;
    private String refreshToken;
    public String getAccessToken() { return token; }
}
```
This caused Jackson to serialize duplicate properties `{ "token": "...", "accessToken": "...", "refreshToken": "..." }`.

**Refreeze Refactor:**
Removed the duplicate `token` field and alias getter. `AuthResponse` is now refactored to:
```java
package com.mathvisionkids.api.auth;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AuthResponse {
    private String accessToken;
    private String refreshToken;
}
```
**Serialized Output:** Exactly `{ "accessToken": "...", "refreshToken": "..." }`. Duplicate aliases: **NO**.

---

## 4. Student Auth Mapping

- **`src/services/api/authApi.ts`:**
  ```typescript
  export interface LoginResponse {
    accessToken: string;
    refreshToken: string;
    user?: any;
  }
  ```
- **`src/context/AuthContext.tsx`:**
  ```typescript
  const login = async (credentials: any) => {
    const data = await authApi.login(credentials);
    const token = data.accessToken;
    await tokenStorage.saveTokens(token, data.refreshToken);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    const userData = await authApi.getMe();
    setUser(userData);
    setIsAuthenticated(true);
    router.replace('/(tabs)' as any);
  };
  ```
- **`src/services/auth/tokenStorage.ts`:**
  Updated with a platform-aware fallback to `localStorage` when running under `Platform.OS === 'web'` to eliminate `ExpoSecureStore` errors in web browser environments while retaining secure keychain/Keystore storage on mobile.

---

## 5. Teacher Auth Regression

- **`teacher-web/src/services/api/SpringTeacherService.ts`:**
  Updated `login` method to unpack `const { accessToken, refreshToken } = res.data;` directly and store via `AuthTokenStore.setTokens(accessToken, refreshToken)`.
- **`teacher-web/src/services/api/apiClient.ts`:**
  Refresh interceptor aligned to unpack `const newAccessToken = data.accessToken;` directly.
- **Verification:** Browser login at `http://localhost:5173/login` using `lan.teacher@mathvision.local` successfully redirects to `/dashboard` and loads teacher metrics without error.

---

## 6. Fresh-Clone AI Mode

- **`services/ai-service/.env.example`:**
  ```dotenv
  APP_ENV=development
  RUNTIME_MODE=FIXTURE
  ```
- **`services/ai-service/app/config.py`:**
  ```python
  class Settings(BaseSettings):
      app_env: str = "development"
      runtime_mode: str = "FIXTURE"
  ```
- **Fresh-Clone Readiness:** A new clone copying `.env.example` starts immediately in `FIXTURE` mode without requiring model artifacts or external weights.

---

## 7. Current Local AI Mode

- **`services/ai-service/.env` (Local, Git-ignored):**
  ```dotenv
  APP_ENV=development
  RUNTIME_MODE=MODEL
  ```
- **Active Diagnostic Mode:** The local developer machine currently uses `MODEL` mode with local weights artifact `services/ai-service/models/best.pt` loaded and verified.

---

## 8. Model Artifact Requirement & Fail-Fast Guarantees

- **No Silent Fallback:** In `services/ai-service/app/jobs/tasks.py`:
  ```python
  if settings.runtime_mode == "FIXTURE":
      engine = FixtureRecognitionEngine()
  else:
      from app.recognition.model_engine import ModelRecognitionEngine
      engine = ModelRecognitionEngine()
      if not engine.is_ready:
          logger.error("MODEL mode active but ModelRecognitionEngine is not ready.")
          callback = AiCallbackRequest(status="MODEL_NOT_AVAILABLE")
          send_callback(job_id, callback)
          return "MODEL_NOT_AVAILABLE"
  ```
- **Explicit Exceptions:** `ModelRecognitionEngine.recognize()` raises `ModelNotAvailableError` if weights are absent. It never silently substitutes fixture synthetic responses when `MODEL` mode is active.

---

## 9. Silent Launcher Regression

- **Script:** `scripts/start-all.bat` (calls `scripts/start-all.ps1`).
- **Window Management:** All background processes (Spring Boot, FastAPI, Celery, Teacher Web) are invoked via `Start-Process -WindowStyle Hidden -PassThru` with redirected log streams.
- **Observed Behavior:** 0 extra command prompt / terminal windows opened.

---

## 10. Stop-All Safety Audit

- **Audit Target:** `scripts/stop-all.ps1` port fallback termination for ports 8080, 8000, 5173.
- **Confirmed Drift / Risk:** Previously, any process listening on ports 8080, 8000, or 5173 matching `java|python|node|cmd` was terminated via `taskkill` regardless of process ownership.
- **Safety Fix Applied:** Added verification of MathVision ownership by inspecting process command-line arguments (`Get-CimInstance Win32_Process`) before issuing `taskkill`:
  ```powershell
  $cimProc = Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction SilentlyContinue
  $cmdLine = if ($cimProc) { $cimProc.CommandLine } else { "" }
  $isMathVision = ($cmdLine -match "MathVision|mathvisionkids|mathvision|services[\\/]business-api|services[\\/]ai-service|teacher-web|gradlew\.bat bootRun")

  if ($isMathVision) {
      Write-Host "Releasing port $port (Process: $($p.ProcessName), PID: $($p.Id))..."
      & taskkill /PID $p.Id /T /F 2>$null | Out-Null
  } else {
      Write-Host "Port $port is in use by non-MathVision process (Process: $($p.ProcessName), PID: $($p.Id)). Skipping termination." -ForegroundColor DarkYellow
  }
  ```
- **Result:** Primary shutdown relies on tracked PIDs in `runtime/pids/`; secondary port check safely verifies MathVision ownership before terminating.

---

## 11. Spring Tests

- **Command:** `gradlew.bat clean test`
- **Result:** 51 passed / 0 failed / 0 skipped
- **Test Execution:**
  - `HttpAiAnalysisGatewayTest`: 8 passed
  - `InternalAiCallbackControllerTest`: 3 passed
  - `AuthControllerTest`: 4 passed (updated to assert `accessToken`)
  - `BatchControllerTest`: 7 passed
  - `TeacherDashboardControllerTest`: 4 passed
  - `StateTransitionTest`: 15 passed
  - `SubmissionControllerTest`: 5 passed
  - `BusinessApiApplicationTests`: 5 passed

---

## 12. Spring Build

- **Command:** `gradlew.bat build`
- **Result:** BUILD SUCCESSFUL in 3s (7 actionable tasks: 3 executed, 4 up-to-date)

---

## 13. Python Tests

- **Command:** `python -m pytest tests/`
- **Result:** 97 passed / 0 failed / 0 skipped (in 11.55s)

---

## 14. Student Validation

- **TypeScript Typecheck:** `npx tsc --noEmit` — 0 errors (Exit code: 0).
- **ESLint:** `npm run lint` — 0 errors, 8 non-blocking warnings (Exit code: 0).
- **Browser Login Smoke Test:** Verified via Playwright browser subagent at `http://localhost:8081/login` logging in with `minh.student@mathvision.local` / `MathVision123!`. Successfully transitioned to the student dashboard (`/(tabs)`).

---

## 15. Files Modified

| File | Change Description |
|---|---|
| `services/business-api/src/main/java/com/mathvisionkids/api/auth/AuthResponse.java` | Refactored `token` to `accessToken`; removed duplicate getter method. |
| `services/business-api/src/test/java/com/mathvisionkids/api/auth/AuthControllerTest.java` | Updated assertions from `$.token` to `$.accessToken`. |
| `src/services/api/authApi.ts` | Updated `LoginResponse` interface to require `accessToken`. |
| `src/context/AuthContext.tsx` | Consumed `data.accessToken` without alias fallback. |
| `src/services/auth/tokenStorage.ts` | Added `Platform.OS === 'web'` fallback to `localStorage`. |
| `teacher-web/src/services/api/SpringTeacherService.ts` | Unpacked `res.data.accessToken` directly. |
| `teacher-web/src/services/api/apiClient.ts` | Unpacked `data.accessToken` directly in token refresh. |
| `scripts/stop-all.ps1` | Hardened port fallback checks with CIM command-line MathVision ownership validation. |

---

## 16. Final Refreeze Assessment

All requirements for post-runtime recovery contract and default-mode refreeze are verified and satisfied:
1. **Single Canonical Token Field:** `accessToken` is established across OpenAPI, backend, and all clients.
2. **No Duplicate Aliases:** Spring `AuthResponse` returns `{ accessToken, refreshToken }`.
3. **Logins Operational:** Both Student and Teacher direct HTTP API calls and browser logins succeed.
4. **Fresh Clone Safe:** Defaults to `FIXTURE` mode; no Git-ignored weights required.
5. **No Silent Fallback:** Missing model in `MODEL` mode fails explicitly with `MODEL_NOT_AVAILABLE`.
6. **Silent Launcher:** Opens 0 popup terminals; local stack reaches `READY_FOR_DEMO`.
7. **Stop-All Safe:** Verifies MathVision ownership before terminating processes on ports.
8. **Test Suites Passing:** 51 Spring tests, 97 Python tests, Student `tsc` and `lint` pass.

**Status:** READY_FOR_REVIEW
