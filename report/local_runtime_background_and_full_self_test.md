# Local Runtime Background Process Launcher & Full Project Self-Test Report

## 1. Executive Summary
MathVision Kids is a unified local educational platform integrating a Spring Boot business backend, a FastAPI AI analysis service powered by a local YOLOv8 detection model, a Celery worker backed by Redis, a Vite/React teacher web portal, and an Expo React Native student mobile/web application.
This report documents the resolution of local launcher popup terminal issues, runtime networking stability hardening, and end-to-end self-test verification.
The launcher now starts all background services silently (zero popup terminal windows), captures all stdout/stderr to `runtime/logs/`, maintains lifecycle tracking under `runtime/pids/`, and incorporates early child process exit detection. All project test suites (Spring 51/51, Python 97/97, Teacher Web build/lint, Student Web build/lint) and end-to-end user login flows (Student direct login, Student browser login, Teacher browser login) have been verified with 100% pass rates.

## 2. Original Multi-Terminal Reproduction
Prior to this hardening phase, executing `scripts\start-all.bat` or `scripts\start-all.ps1` resulted in the creation of up to 4 separate CMD/terminal popup windows:
- One window for Spring Boot (`cmd.exe /c gradlew.bat bootRun ...`)
- One window for FastAPI (`uvicorn.exe app.main:app ...`)
- One window for Celery Worker (`celery.exe -A app.jobs.celery_app worker ...`)
- One window for Teacher Web (`cmd.exe /c npm run dev`)
This cluttered the developer desktop and violated the requirement that only the single terminal invoking `start-all` should remain visible.

## 3. Root Cause
1. **Missing Window Style Specification:** The launcher utilized PowerShell's `Start-Process` without passing `-WindowStyle Hidden`. On Windows platforms, starting console binaries or `cmd.exe` from PowerShell defaults to allocating a visible console window unless explicitly hidden.
2. **Missing Early Exit Detection:** The previous launcher polled endpoints for up to 45 seconds without checking if any child process had prematurely exited with a fatal error.
3. **Stale PID Retention:** Terminated processes left PID files in `runtime/pids/` that were not sanitized upon subsequent launcher invocations.
4. **Localhost IPv6 Ambiguity:** Probes targeting `localhost` periodically encountered timeouts when resolving to IPv6 `[::1]` while backend servers listened on IPv4 (`127.0.0.1`).
5. **Student Web Fallback Discrepancy:** The student client's fallback `API_BASE_URL` defaulted to `http://10.0.2.2:8080/api/v1` (an Android emulator address), causing browser-based student login at `http://localhost:8081/login` to fail with "Network Error" when accessing the app on the host machine.
6. **Token Key Inconsistency in Student Auth:** Spring Boot's `AuthResponse` serialized the JWT as `token`, whereas the student client's `AuthContext` read `data.accessToken`, causing authorization headers to send `Bearer undefined` and triggering 401/Network failures.

## 4. Background Process Design
The background process launcher was refactored in `scripts/start-all.ps1` with the following architectural invariants:
- **Zero Console Window Allocation:** All child processes are initiated via `Start-Process -WindowStyle Hidden -PassThru`.
- **Dedicated Standard Stream Redirection:** Stdout is directed to `runtime/logs/<service>.log` and stderr to `runtime/logs/<service>.err.log`.
- **Deterministic Working Directories:** Each process is launched from its designated repository subfolder.
- **Process Object Retention:** Active process references are tracked in a global collection for instant status polling.

## 5. Spring Background Launch
- **Executable:** `cmd.exe`
- **Arguments:** `/c gradlew.bat bootRun --args="--ai.gateway.mode=FASTAPI --spring.profiles.active=dev"`
- **Working Directory:** `services\business-api`
- **WindowStyle:** `Hidden`
- **Stdout Log:** `runtime/logs/spring.log`
- **Stderr Log:** `runtime/logs/spring.err.log`
- **PID File:** `runtime/pids/spring.pid`

## 6. FastAPI Background Launch
- **Executable:** `services\ai-service\.venv\Scripts\uvicorn.exe`
- **Arguments:** `app.main:app --host 0.0.0.0 --port 8000`
- **Working Directory:** `services\ai-service`
- **WindowStyle:** `Hidden`
- **Stdout Log:** `runtime/logs/fastapi.log`
- **Stderr Log:** `runtime/logs/fastapi.err.log`
- **PID File:** `runtime/pids/fastapi.pid`

## 7. Celery Background Launch
- **Executable:** `services\ai-service\.venv\Scripts\celery.exe`
- **Arguments:** `-A app.jobs.celery_app worker --loglevel=info --pool=solo -n worker1@<COMPUTERNAME>`
- **Working Directory:** `services\ai-service`
- **WindowStyle:** `Hidden`
- **Stdout Log:** `runtime/logs/celery.log`
- **Stderr Log:** `runtime/logs/celery.err.log`
- **PID File:** `runtime/pids/celery.pid`

## 8. Teacher Web Background Launch
- **Executable:** `cmd.exe`
- **Arguments:** `/c npm run dev`
- **Working Directory:** `teacher-web`
- **WindowStyle:** `Hidden`
- **Stdout Log:** `runtime/logs/teacher-web.log`
- **Stderr Log:** `runtime/logs/teacher-web.err.log`
- **PID File:** `runtime/pids/teacher-web.pid`

## 9. PID Tracking
- `runtime/pids/` directory stores exactly one `.pid` file per managed service.
- When `start-all.ps1` runs, Step 2 inspects existing `.pid` files. If the recorded PID does not correspond to an active running process, the stale file is automatically purged before launching services.
- `stop-all.ps1` reads tracked PIDs and executes `taskkill /PID <procId> /T /F` to terminate the root process and its entire sub-process tree safely.

## 10. Log Redirection
- No service prints output directly to the invoking terminal.
- Each service has two discrete log targets:
  - Normal output: `<service>.log`
  - Error streams: `<service>.err.log`
- Redirection guarantees full diagnostic observability without visual clutter.

## 11. Early Exit Detection
`start-all.ps1` enforces two levels of early-exit checks:
1. **Immediate Launch Inspection:** Pauses 600ms post-launch; if `$proc.HasExited` is true, the script prints an immediate error detailing the exit code, log paths, and the last 15 lines of stderr, then exits with code 1.
2. **Readiness Loop Watchdog:** In the 45-second service poll loop, every iteration evaluates `$svc.Process.HasExited` for all tracked services. If any service exits prematurely, the loop halts immediately, dumps error logs, and terminates without waiting for the full timeout.

## 12. Readiness Verification
Service readiness is verified via discrete HTTP/socket probes:
- **PostgreSQL:** Port 5432 TCP probe + `pg_isready` container validation.
- **MinIO:** Port 9000 TCP probe + `http://127.0.0.1:9000/minio/health/live` HTTP 200 check.
- **Redis:** Port 6379 socket ping responding with `PONG`.
- **Spring Boot:** `http://127.0.0.1:8080/actuator/health` HTTP 200 returning `status: "UP"`.
- **FastAPI:** `http://127.0.0.1:8000/health` HTTP 200 and `http://127.0.0.1:8000/ready` returning `status: "ready"`.
- **Celery Worker:** Celery control ping `celery_app.control.ping(timeout=2.5)`.
- **Teacher Web:** `http://localhost:5173` HTTP 200.

## 13. IPv4 Local Networking
To eliminate Windows IPv6 (`[::1]`) hostname resolution conflicts:
- Spring Boot and FastAPI health checks in `start-all.ps1` and `tools/diagnostics/check_runtime.py` explicitly target `http://127.0.0.1:<port>`.
- Teacher Web and Student Web server bindings remain compatible with their development hosts.
- CORS configuration in `application.yml` and `.env` supports both `localhost` and `127.0.0.1` for ports 3000, 5173, and 8081.

## 14. Student API Environment
- Root `.env` configures `EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8080/api/v1`.
- `src/config/env.ts` resolves `API_BASE_URL` with a dynamic fallback: if `Platform.OS === 'web'`, it defaults to `http://127.0.0.1:8080/api/v1`; on native emulators, it falls back to `http://10.0.2.2:8080/api/v1`.

## 15. Silent Start Test
- Terminal windows visible prior to launch: 1 (the single invoking terminal).
- Extra terminal windows spawned during `start-all.bat`: **0**.
- Final visible terminal count: 1.
- Result: **PASS**.

## 16. Start-All Test
Execution of `.\scripts\start-all.bat`:
- Infrastructure (Postgres, MinIO, Redis) launched and healthy.
- Spring Boot, FastAPI, Celery, and Teacher Web launched silently.
- Diagnostics completed with `READY_FOR_DEMO`.
- Process returned exit code 0.
- Result: **PASS**.

## 17. Health Check
Execution of `.\scripts\health-check.bat`:
```
Docker ................. PASS
PostgreSQL ............. PASS
MinIO .................. PASS
Redis .................. PASS
Spring Boot ............ PASS
FastAPI ................ PASS
Celery Worker .......... PASS
Teacher Web ............ PASS
Student Mobile ......... RUNNING

AI Mode ............... MODEL
Primary Model ......... MathVision-Kids-Detection
Model Version ......... 1.0.0
Model Artifact ........ LOADED

Overall ............... READY_FOR_DEMO
```
- Result: **PASS**.

## 18. Student Direct Login
Direct API test via `POST http://127.0.0.1:8080/api/v1/auth/login`:
- Account: `minh.student@mathvision.local` / `MathVision123!`
- Response: HTTP 200 OK
- Token: Valid JWT present (masked: `eyJhbGciOiJIUzU...[MASKED]`)
- AccessToken: Present and aligned with `token`
- RefreshToken: UUID present (`3932883a-661b-4a6a-a0ab-24bd865c9e4b`)
- Session Verification: `GET /api/v1/me` with Bearer token returned `role: STUDENT`, `displayName: Minh (Student)`, `gradeLevel: 3`.
- Result: **PASS**.

## 19. Student Browser Login
End-to-end browser test via Chrome automation (`http://localhost:8081/login`):
- Navigation: Loaded login screen.
- Interaction: Populated email `minh.student@mathvision.local` and password `MathVision123!`, submitted "Đăng nhập".
- Outcome: Form submitted successfully without "Network Error". App transitioned from `/login` to `/` (authenticated student portal).
- Visual Evidence: Authenticated greeting loaded: "Xin chào Minh 👋", "Hôm nay mình kiểm tra một bài toán nhé!", and action button "CHỤP BÀI CỦA EM".
- Result: **PASS**.

## 20. Teacher Login
1. Direct API test: `POST /api/v1/auth/login` with `lan.teacher@mathvision.local` / `MathVision123!` -> HTTP 200 OK, JWT returned.
2. `GET /api/v1/me` -> `role: TEACHER`, `displayName: Ms. Lan`.
3. Browser test at `http://localhost:5173/login`:
   - Submitted credentials -> Successfully redirected to `http://localhost:5173/dashboard`.
   - Teacher navigation and portal loaded ("Ms. Lan - Giáo viên Toán").
- Result: **PASS**.

## 21. Spring Test Discovery
Evaluated test suite in `services/business-api/src/test/java`:
- 8 test classes discovered across auth, submission, dashboard, batch, analysis, and application core.

## 22. Spring Tests
Executed `.\gradlew.bat clean test` in `services/business-api`:
- `HttpAiAnalysisGatewayTest`: 8 tests, 0 failures, 0 errors, 0 skipped
- `InternalAiCallbackControllerTest`: 6 tests, 0 failures, 0 errors, 0 skipped
- `AuthControllerTest`: 4 tests, 0 failures, 0 errors, 0 skipped
- `BatchControllerTest`: 7 tests, 0 failures, 0 errors, 0 skipped
- `BusinessApiApplicationTests`: 1 test, 0 failures, 0 errors, 0 skipped
- `TeacherDashboardControllerTest`: 4 tests, 0 failures, 0 errors, 0 skipped
- `StateTransitionTest`: 16 tests, 0 failures, 0 errors, 0 skipped
- `SubmissionControllerTest`: 5 tests, 0 failures, 0 errors, 0 skipped
- **Total: 51 tests, 51 passed, 0 failed, 0 skipped**.
- Result: **PASS**.

## 23. Spring Build
Executed `.\gradlew.bat build` in `services/business-api`:
- Gradle tasks: `:compileJava`, `:processResources`, `:classes`, `:bootJar`, `:jar`, `:assemble`, `:check`, `:build`.
- Output: `BUILD SUCCESSFUL`.
- Result: **PASS**.

## 24. Python Tests
Executed `.\.venv\Scripts\python.exe -m pytest tests/` in `services/ai-service`:
- 18 test modules evaluated: `test_api.py`, `test_callback_retry.py`, `test_celery.py`, `test_confidence.py`, `test_earliest_error.py`, `test_evaluation_harness.py`, `test_fixture_e2e.py`, `test_image_resolver.py`, `test_manifest.py`, `test_minio_pipeline.py`, `test_model_e2e.py`, `test_model_preprocessing.py`, `test_model_smoke_timing.py`, `test_parser.py`, `test_policy.py`, `test_quality.py`, `test_validation.py`, `test_yolo_adapter.py`.
- **Total: 97 passed, 0 failed, 0 skipped** in 17.68s.
- Result: **PASS**.

## 25. Teacher Build
Executed in `teacher-web`:
- `npm run build` (`tsc -b && vite build`): Output bundle built in 12.38s (`dist/index.html`, `dist/assets/`).
- `npm run lint` (`oxlint`): 0 errors, 7 non-blocking warnings.
- Result: **PASS**.

## 26. Student Validation
Executed in root:
- `npx tsc --noEmit`: 0 errors.
- `npm run lint` (`expo lint`): 0 errors, 8 minor unused variable warnings.
- Result: **PASS**.

## 27. Bugs Found
1. **Multi-Terminal Popup Bug:** `Start-TrackedService` lacked `-WindowStyle Hidden`, creating 4 visible CMD windows on startup.
2. **Missing Early Exit Watchdog:** Launcher would idle for 45s if a background service crashed immediately.
3. **Stale PID Accumulation:** Dead processes left PID files behind without cleanup.
4. **Obsolete Docker Compose Attribute:** `services/business-api/docker-compose.yml` contained obsolete `version: '3.8'` generating warnings.
5. **Student Auth Token Property Mismatch:** Spring `AuthResponse` provided `token` while Student `AuthContext` looked for `accessToken`, leading to unauthenticated session restore.
6. **Hardcoded Android Fallback on Web:** `src/config/env.ts` fell back to `10.0.2.2` even when executed in a web browser.
7. **Cross-Origin Configuration Gap:** Spring `application.yml` default allowed origins omitted `127.0.0.1` variants.
8. **Monorepo TypeScript Leak:** Root `tsconfig.json` included `teacher-web` without exclusion, causing `tsc` to fail on Vite-specific `import.meta.env`.

## 28. Bugs Fixed
1. Added `-WindowStyle Hidden` and `-PassThru` to all child process invocations in `scripts/start-all.ps1`.
2. Implemented pre-flight and loop-level early exit detection in `scripts/start-all.ps1`.
3. Implemented safe stale PID detection and cleanup in both `scripts/start-all.ps1` and `scripts/stop-all.ps1`.
4. Removed `version: '3.8'` from `services/business-api/docker-compose.yml`.
5. Updated `AuthResponse.java` to expose `getAccessToken()` and updated `authApi.ts` / `AuthContext.tsx` to accept both `token` and `accessToken`.
6. Updated `src/config/env.ts` to detect `Platform.OS === 'web'` and route to `http://127.0.0.1:8080/api/v1`.
7. Updated `application.yml` and `.env` CORS origins to include `http://127.0.0.1:8081` and related variants.
8. Added `"exclude": ["node_modules", "teacher-web", "dist"]` to root `tsconfig.json`.

## 29. Retest Cycles
- Cycle 1: Launcher silence and process creation verified (`start-all.bat` -> 0 extra windows).
- Cycle 2: Backend test regression verified (Spring 51/51 tests, Spring build successful).
- Cycle 3: AI test regression verified (Python 97/97 tests pass).
- Cycle 4: Frontend static checks verified (`teacher-web` build 0 errors, root `tsc` 0 errors, root `lint` 0 errors).
- Cycle 5: End-to-end user journeys verified (Teacher login redirect -> Dashboard, Student login redirect -> Authenticated home).

## 30. Stop-All Test
Executed `.\scripts\stop-all.bat`:
- Safely terminated tracked PIDs: Spring (10128), FastAPI (31412), Celery (35000), Teacher Web (512).
- Cleaned up lingering processes on ports 8080, 8000, 5173.
- Stopped Docker Compose containers (postgres, minio, redis).
- Unrelated Java/Python/Node processes left completely untouched.
- Cleaned up all `.pid` files from `runtime/pids/`.
- Result: **PASS**.

## 31. Restart-All Test
Executed `.\scripts\restart-all.bat`:
- Performed clean shutdown followed by silent start.
- Created 0 extra terminal windows.
- All services reported UP / ready within 15 seconds.
- Final status: `READY_FOR_DEMO`.
- Result: **PASS**.

## 32. Model SHA
- Evaluated: `services/ai-service/models/yolov8n_mathvision_det_v1.pt`
- Expected: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Computed: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Result: **PASS**.

## 33. Git Hygiene
Inspected `git status --short`:
- Modified files strictly correspond to hardened launchers, configurations, and bugfixes.
- No accidental files (e.g. `.env`, logs, PIDs, class files, test caches, model artifacts) are tracked.
- Result: **PASS**.

## 34. Files Created
- `report/local_runtime_background_and_full_self_test.md` (this report)

## 35. Files Modified
- `scripts/start-all.ps1`
- `scripts/stop-all.ps1`
- `services/business-api/docker-compose.yml`
- `services/business-api/src/main/java/com/mathvisionkids/api/auth/AuthResponse.java`
- `services/business-api/src/main/resources/application.yml`
- `src/app/index.tsx`
- `src/config/env.ts`
- `src/context/AuthContext.tsx`
- `src/services/api/authApi.ts`
- `tools/diagnostics/check_runtime.py`
- `tsconfig.json`

## 36. Student Modified
Yes, targeted runtime bugfixes applied:
- `src/config/env.ts`: Added web fallback for `API_BASE_URL`.
- `src/services/api/authApi.ts` & `src/context/AuthContext.tsx`: Supported `token` alongside `accessToken` and updated post-login navigation to `/(tabs)`.
- `src/app/index.tsx`: Enabled authenticated check on splash screen.
- `tsconfig.json`: Excluded non-student subprojects.

## 37. Teacher Modified
No UI redesign performed. `teacher-web` source code remained untouched; verified through clean production build and automated browser login.

## 38. AI Runtime Behavior Modified
No AI algorithm or grading policy modified. FastAPI endpoints and Celery execution retained exact functional behavior, passing all 97 unit and integration tests.

## 39. AI Training Performed
- AI training performed: **NO**
- AI model weights modified: **NO**
- Training pipelines executed: **NO**

## 40. Final Runtime Status
**READY_FOR_REVIEW** (Overall status: `READY_FOR_DEMO`).
All local infrastructure, backend APIs, AI workers, and frontend portals launch silently in the background and respond with HTTP 200 / ready states.

## 41. Final Project Self-Test Status
**PASS**. All regression suites and verification criteria satisfied:
- Spring Tests: 51/51 PASS
- Spring Build: PASS
- Python Tests: 97/97 PASS
- Teacher Web Build: PASS
- Student Web Static Check: PASS
- Model Integrity: PASS
- Student Login Flow: PASS
- Teacher Login Flow: PASS
- Stop/Restart Cycles: PASS

## 42. Remaining Limitations
None blocking local development and demonstration. Native mobile testing on physical Android devices continues to require configuring `EXPO_PUBLIC_API_BASE_URL` with the host machine's LAN IP address as documented in `.env.example`.
