# MathVision Kids
## Phase 4.1 — Local Runtime Hardening, Launcher & Diagnostics

**Date:** September 8, 2026  
**Environment:** Windows 11 (Primary Developer Environment)  
**Status:** READY_FOR_REVIEW  

---

### 1. Executive Summary

Phase 4.1 transformed the existing frozen MathVision Kids services into a polished, resilient, local-first developer and demonstration environment. A new developer cloning the repository can now configure environment variables, execute a single launcher command (`scripts\start-all.bat`), observe automatic infrastructure and service initialization, run automated diagnostics (`scripts\health-check.bat`), exercise deterministic math recognition and teacher batch review flows, and perform safe shutdowns or local data resets without cloud dependencies or guesswork.

All acceptance criteria are satisfied with zero test regressions:
- Spring clean test suite: **49/49 tests passed (100%)**.
- Spring build: **BUILD SUCCESSFUL**.
- Python AI subsystem test suite: **76/76 tests passed (100%)**.
- Teacher Web portal build: **Built in 4.56s without errors**.
- All failure-injection scenarios (Redis down, FastAPI down, Celery worker down, MinIO down) correctly produced actionable diagnostics.
- Student Mobile, Teacher Web business code, AI Training workspaces, and core arithmetic validators remain completely untouched.

---

### 2. Repository Root

The repository root was verified via canonical git command:
```bash
git rev-parse --show-toplevel
# Output: E:/MathVisionKid
```
All relative file paths in scripts, diagnostics, and documentation resolve against this confirmed root directory.

---

### 3. Existing Runtime Audit

An exhaustive audit of the workspace revealed:
- **Root Directory:** Contains the Expo React Native Student Mobile application (`package.json`, `app.json`, `src/`).
- **`services/business-api/`:** Spring Boot 3.3.6 application with Java 21, Flyway migrations, and `docker-compose.yml`.
- **`services/ai-service/`:** FastAPI 0.115 runtime, Celery 5.4.0 worker, and deterministic arithmetic validators.
- **`teacher-web/`:** React 19 + Vite frontend portal for teacher operations.
- **`ai-training/`:** Dedicated AI teammate training workspace (untouched).
- **Previous Launch Mechanism:** Fragmented, requiring manual invocation of Docker Compose and three separate long-running console windows.

---

### 4. Local Architecture

The local architecture follows a local-first, container-assisted topology:
- **Infrastructure in Docker:** PostgreSQL 16 (port 5432), MinIO S3 (ports 9000 & 9001), and Redis 7 (port 6379) run in Docker Compose containers.
- **Application Services on Host:** Spring Boot (port 8080), FastAPI (port 8000), Celery Worker (solo pool), and Teacher Web (port 5173) execute as native host processes. This preserves Windows debugging convenience, live reload, and avoids container networking impedance.

---

### 5. Windows Launcher

The Windows launcher suite is designed specifically for Windows environments (PowerShell and CMD compatibility):
- `scripts\start-all.bat` & `scripts\start-all.ps1`
- `scripts\stop-all.bat` & `scripts\stop-all.ps1`
- `scripts\restart-all.bat` & `scripts\restart-all.ps1`
- `scripts\health-check.bat`
- `scripts\reset-local-data.bat` & `scripts\reset-local-data.ps1`

---

### 6. start-all.bat

`scripts\start-all.bat` executes `scripts\start-all.ps1` via `powershell.exe -NoProfile -ExecutionPolicy Bypass`.
Workflow:
1. Validates prerequisites (Docker CLI, Docker daemon, Java 21, Node.js, npm, Gradle wrapper, Python venv).
2. Creates `runtime\logs\` and `runtime\pids\`.
3. Starts Docker infrastructure (`postgres`, `minio`, `redis`) with port verification.
4. Auto-creates MinIO bucket `mathvision` if missing.
5. Launches Spring Boot, FastAPI, Celery, and Teacher Web with PID tracking.
6. Polls endpoints until ready (up to 45s timeout).
7. Executes `tools\diagnostics\check_runtime.py` and displays service URLs.

---

### 7. stop-all.bat

`scripts\stop-all.bat` executes `scripts\stop-all.ps1`.
Workflow:
1. Reads PIDs from `runtime\pids\*.pid` and terminates tracked process trees using `taskkill /PID <pid> /T /F`.
2. Inspects ports 8080, 8000, 5173 and terminates lingering Java/Python/Node processes owned by MathVision.
3. Cleans up orphaned Celery worker processes matching `celery_app worker`.
4. Stops Docker containers (`docker compose stop postgres minio redis`).
5. Leaves unrelated user processes completely untouched.

---

### 8. restart-all.bat

`scripts\restart-all.bat` invokes `scripts\stop-all.ps1`, waits 2 seconds for complete socket release, and invokes `scripts\start-all.ps1`. Returns the exit code of the final startup diagnostic.

---

### 9. health-check.bat

`scripts\health-check.bat` locates Python (`services\ai-service\.venv\Scripts\python.exe` or system `python`) and invokes `tools\diagnostics\check_runtime.py`, passing through the diagnostic exit code (0 for healthy, 1 for degraded/down).

---

### 10. reset-local-data.bat

`scripts\reset-local-data.bat` provides a safe, interactive data wipe:
1. Displays prominent warning detailing affected volumes (PostgreSQL database, MinIO images, Redis state, runtime logs).
2. Requires explicit user confirmation (`Are you sure you want to proceed? [Y/N]`).
3. Shuts down the stack via `stop-all.ps1`.
4. Removes only MathVision Docker volumes via `docker compose -f services\business-api\docker-compose.yml down -v`.
5. Cleans `runtime\logs\`, `runtime\pids\`, and `.data\uploads\`.
6. Leaves unrelated workstation Docker volumes untouched.

---

### 11. Process Management

Background host processes are launched with explicit PID capture (`Start-Process -PassThru`), storing PIDs in `runtime\pids\<service>.pid`. Process cleanup avoids broad `taskkill /IM java.exe /F` commands and instead targets specific PIDs and port-bound processes.

---

### 12. Runtime Logs

Service outputs are redirected to dedicated log files under `runtime\logs\`:
- `runtime\logs\spring.log` (Spring Boot standard output)
- `runtime\logs\spring.err.log` (Spring Boot standard error)
- `runtime\logs\fastapi.log` / `fastapi.err.log` (FastAPI Uvicorn output)
- `runtime\logs\celery.log` / `celery.err.log` (Celery worker task processing output)
- `runtime\logs\teacher-web.log` (Vite dev server log)

---

### 13. Runtime PID/State

Process ID tracking files are stored in `runtime\pids\`:
- `runtime\pids\spring.pid`
- `runtime\pids\fastapi.pid`
- `runtime\pids\celery.pid`
- `runtime\pids\teacher-web.pid`

---

### 14. Diagnostics Tool

A centralized Python utility (`tools/diagnostics/check_runtime.py`) checks all 8 core services and 2 client states in under 3 seconds using standard library sockets, HTTP queries, and Celery control pings. Documented in `tools/diagnostics/README.md`.

---

### 15. Diagnostic Exit Codes

- `0`: All required local demo dependencies are healthy (`READY_FOR_DEMO`).
- `1`: One or more required components failed (`NOT_READY`). Detailed root-cause explanations and remediation commands are printed to stdout.

---

### 16. Docker Check

Executes `docker version --format '{{.Server.Version}}'`. If the daemon is unreachable or the command fails, status is `FAIL` with fix: "Start Docker Desktop and ensure Docker daemon is running."

---

### 17. PostgreSQL Check

Verifies TCP port 5432 connectivity and executes `docker exec mathvision-postgres pg_isready -U mathvision -d mathvision`. Confirms database is accepting connections.

---

### 18. MinIO Check

Verifies TCP port 9000 connectivity and issues HTTP GET to `http://localhost:9000/minio/health/live`. Returns `PASS` when HTTP 200 is received.

---

### 19. Redis Check

Opens a TCP socket connection to `localhost:6379`, sends `PING\r\n`, and verifies receipt of `+PONG\r\n`.

---

### 20. Spring Health

Queries `http://localhost:8080/actuator/health` with a 3-second timeout. Checks that JSON response contains `status: "UP"`.

---

### 21. FastAPI Health

Queries `http://localhost:8000/health`. Verifies HTTP 200 and `status: "ok"`.

---

### 22. FastAPI Readiness

Queries `http://localhost:8000/ready`. Verifies `status: "ready"` and `redis_connected: true`. In `FIXTURE` mode, model artifact absence is expected and allowed.

---

### 23. Celery Worker Check

Invokes `celery_app.control.ping(timeout=2.5)` via the Python virtual environment. Returns `PASS` only when active workers reply with pong (e.g. `[{'worker1@DUY-MANH': {'ok': 'pong'}}]`). Independently distinguishes worker liveness from Redis broker reachability.

---

### 24. Teacher Web Check

Issues HTTP GET to `http://localhost:5173` using basic parsing. Verifies HTTP 200 from the Vite dev server.

---

### 25. Student Mobile Status

Checks for presence of `app.json` at repository root. If port 8081 is listening, reports `RUNNING`; otherwise reports `CONFIGURED`. Does not fail overall demo status if Metro is not currently running.

---

### 26. Environment Configuration

Central environment template created at `.env.example` documenting all configuration options for Spring Boot, FastAPI, Celery, MinIO, Teacher Web, and Student Mobile.

---

### 27. Secret Safety

All committed reports, documentation files, and `.env.example` templates use non-secret placeholders (`<redacted>`, `password123`, `minioadmin123`, `secret-key-default`). Live production credentials are never stored in source control.

---

### 28. Demo Mode

Demo mode operates with `AI_GATEWAY_MODE=FASTAPI` in Spring Boot and `RUNTIME_MODE=FIXTURE` in FastAPI. It provides a real-stack demonstration across all microservices and queues using deterministic recognition fixtures.

---

### 29. Fixture Scenarios

Supported deterministic scenarios:
1. `clean-addition` (or default): Valid addition (`12 + 34 = 46`) -> `PROPOSED_GRADE` (10/10)
2. `addition-carry-error`: Missed carry (`45 + 27 = 62`) -> `PROPOSED_GRADE` (0/10 + evidence)
3. `subtraction-borrow-error`: Missed borrow (`52 - 18 = 44`) -> `PROPOSED_GRADE` (0/10 + evidence)
4. `ambiguous`: Digit confidence `< 0.5` -> `REVIEW_REQUIRED`
5. `quality-blur` / `quality-dark`: Image quality failure -> `NEEDS_RETAKE`
6. `quality-incomplete-crop`: Incomplete bounding box -> `CROP_REQUIRED`
7. `out-of-scope`: Unsupported operations -> `OUT_OF_SCOPE`

---

### 30. Demo Seed/Data

`services/business-api/src/main/java/com/mathvisionkids/api/config/SeedDataInitializer.java` initializes dev seed data automatically under profile `dev` inside a transactional boundary (`TransactionTemplate`).

---

### 31. Demo Accounts

- **Teacher:** `lan.teacher@mathvision.local` / `MathVision123!` (Ms. Lan)
- **Student:** `minh.student@mathvision.local` / `MathVision123!` (Minh)

---

### 32. Demo Classroom

`SeedDataInitializer` automatically creates demo classroom **"Lớp 3A"** (Grade 3, academic year 2025-2026) containing 11 synthetic students:
- Nguyễn Bình Minh, Trần Văn An, Lê Thanh Bình, Phạm Quốc Cường, Hoàng Ngọc Dũng, Vũ Hương Giang, Đỗ Thu Hà, Bùi Anh Khoa, Ngô Phương Linh, Đặng Tuyết Mai, Dương Nhật Nam.
Provides ample student records to support batch upload demonstrations (10–30 image packs).

---

### 33. Demo Assignment

`SeedDataInitializer` automatically creates two active assignments for "Lớp 3A":
- **Bài tập Phép Cộng Dọc** (`VERTICAL_ADDITION`, max score 10)
- **Bài tập Phép Trừ Dọc** (`VERTICAL_SUBTRACTION`, max score 10)

---

### 34. Demo Images

Synthetic sample images in repository root (`test_image.jpg`, `retry_image.jpg`) can be used for batch uploads and test submissions. No real child data is included in the repository.

---

### 35. Local Setup Documentation

Comprehensive setup instructions documented in `docs/LOCAL_SETUP.md`.

---

### 36. Demo Guide

Complete 12-step teacher batch and student demo walkthrough documented in `docs/DEMO_GUIDE.md`.

---

### 37. Troubleshooting Guide

Actionable failure remedies for Docker, PostgreSQL, MinIO, Redis, Celery, Spring, FastAPI, and CORS documented in `docs/TROUBLESHOOTING.md`.

---

### 38. Runtime Architecture Documentation

Local runtime topology, Mermaid architecture diagram, component boundaries, and asynchronous correlation flow documented in `docs/ARCHITECTURE_LOCAL_RUNTIME.md`.

---

### 39. Maintenance Guide

Configuration map, port reallocation, log reading commands, database inspection, and model handoff procedures documented in `docs/MAINTENANCE_GUIDE.md`.

---

### 40. Docker Compose Hardening

Lightweight, robust healthchecks added to `services/business-api/docker-compose.yml`:
- `postgres`: `["CMD-SHELL", "pg_isready -U mathvision -d mathvision"]`
- `minio`: `["CMD", "mc", "ready", "local"]`
- `redis`: `["CMD", "redis-cli", "ping"]`

---

### 41. Git Hygiene

`.gitignore` updated to ignore `runtime/logs/`, `runtime/pids/`, `runtime/`, `.env`, `*.env.local`, Python virtual environments (`.venv/`), and scratch scripts.

---

### 42. Clean Start Test

- Executed `scripts\start-all.bat` from stopped state.
- Successfully booted Docker containers, Spring Boot, FastAPI, Celery, and Teacher Web.
- Diagnostic concluded with `Overall ............... READY_FOR_DEMO` (exit code 0).

---

### 43. Health Check Test

- Executed `scripts\health-check.bat`.
- Diagnostic output:
  ```
  ============================================
   MathVision Kids -- Local Runtime Diagnostic
  ============================================

  Docker ................. PASS
  PostgreSQL ............. PASS
  MinIO .................. PASS
  Redis .................. PASS
  Spring Boot ............ PASS
  FastAPI ................ PASS
  Celery Worker .......... PASS
  Teacher Web ............ PASS
  Student Mobile ......... CONFIGURED

  AI Mode ............... FIXTURE
  Model Artifact ........ NOT_PROVIDED

  Overall ............... READY_FOR_DEMO
  ============================================
  ```
- Exit code: 0.

---

### 44. Stop Test

- Executed `scripts\stop-all.bat`.
- Terminated tracked PIDs, released ports 8080, 8000, 5173, killed Celery worker processes, and stopped Docker containers.
- Exit code: 0.

---

### 45. Restart Test

- Executed `scripts\restart-all.bat`.
- Stopped stack, restarted containers, launched host services, polled health, and executed diagnostics.
- Diagnostic concluded with `Overall ............... READY_FOR_DEMO` (exit code 0).

---

### 46. Redis Failure Test

- Stopped Redis container: `docker stop mathvision-redis`.
- Ran `scripts\health-check.bat`.
- Diagnostic reported `Redis .................. FAIL` with remediation: `docker compose -f services/business-api/docker-compose.yml up -d redis`.
- FastAPI and Celery degraded accordingly; Spring Boot remained independently diagnosable.
- Restored Redis container: `docker start mathvision-redis`.

---

### 47. FastAPI Failure Test

- Stopped FastAPI process.
- Ran `scripts\health-check.bat`.
- Diagnostic reported `FastAPI ................ FAIL` with remediation: `Start FastAPI: scripts/start-all.bat or cd services/ai-service && .\.venv\Scripts\uvicorn app.main:app --port 8000`.
- Spring Boot, PostgreSQL, MinIO, Redis, and Celery remained independently diagnosable.
- Restored FastAPI process.

---

### 48. Celery Failure Test

- Stopped Celery worker process while keeping Redis running.
- Ran `scripts\health-check.bat`.
- Diagnostic reported:
  - `Redis .................. PASS`
  - `FastAPI ................ PASS`
  - `Celery Worker .......... FAIL`
- Verified diagnostic utility strictly differentiates Celery worker availability from Redis broker reachability.
- Restored Celery worker process.

---

### 49. MinIO Failure Test

- Stopped MinIO container: `docker stop mathvision-minio`.
- Ran `scripts\health-check.bat`.
- Diagnostic reported `MinIO .................. FAIL` with remediation: `docker compose -f services/business-api/docker-compose.yml up -d minio`.
- Restored MinIO container: `docker start mathvision-minio`.

---

### 50. Spring Regression

Ran full clean test suite without filters:
```bash
.\gradlew.bat clean test
```
Result:
- `HttpAiAnalysisGatewayTest`: 8 passed
- `InternalAiCallbackControllerTest`: 4 passed
- `AuthControllerTest`: 4 passed
- `BatchControllerTest`: 7 passed
- `BusinessApiApplicationTests`: 1 passed
- `TeacherDashboardControllerTest`: 4 passed
- `StateTransitionTest`: 16 passed
- `SubmissionControllerTest`: 5 passed
- **Total: 49 passed / 0 failed / 0 skipped** (100% pass rate).

---

### 51. Spring Build

Ran `.\gradlew.bat build`.
Result: `BUILD SUCCESSFUL in 2s`.

---

### 52. AI Regression

Ran complete pytest regression suite:
```bash
.\.venv\Scripts\python.exe -m pytest tests/ -v
```
Result: **76 passed / 0 failed / 0 skipped** in 0.91s.

---

### 53. Teacher Build

Ran `npm run build` in `teacher-web/`.
Result: `tsc -b && vite build` built successfully in 4.56s.

---

### 54. Student Validation

Inspected `package.json`, `app.json`, and TypeScript configuration. Diagnostic tool validates `app.json` presence and detects Metro bundler state.

---

### 55. Files Created

- `tools/diagnostics/check_runtime.py`
- `tools/diagnostics/README.md`
- `scripts/start-all.ps1`
- `scripts/start-all.bat`
- `scripts/stop-all.ps1`
- `scripts/stop-all.bat`
- `scripts/restart-all.ps1`
- `scripts/restart-all.bat`
- `scripts/health-check.bat`
- `scripts/reset-local-data.ps1`
- `scripts/reset-local-data.bat`
- `.env.example`
- `docs/LOCAL_SETUP.md`
- `docs/DEMO_GUIDE.md`
- `docs/TROUBLESHOOTING.md`
- `docs/ARCHITECTURE_LOCAL_RUNTIME.md`
- `docs/MAINTENANCE_GUIDE.md`
- `report/phase_4_1_local_runtime_hardening.md`

---

### 56. Files Modified

- `.gitignore`
- `README.md`
- `services/business-api/docker-compose.yml`
- `services/business-api/src/main/java/com/mathvisionkids/api/config/SeedDataInitializer.java`

---

### 57. Files Deleted

None.

---

### 58. Student Mobile Files Modified

**NONE** (0 files modified).

---

### 59. Teacher Business Files Modified

**NONE** (0 files modified).

---

### 60. AI Training Files Modified

**NONE** (0 files modified).

---

### 61. Core AI Validator Modified

**NONE** (0 files modified).

---

### 62. Known Limitations

- Model weights are not yet provided (`MODEL_ARTIFACT=NOT_PROVIDED`).
- Handwriting recognition is simulated via deterministic fixture keywords.
- Mobile testing on physical devices requires pointing API URLs to workstation LAN IP rather than `localhost`.

---

### 63. Model Artifact Status

**NOT_PROVIDED**

---

### 64. Proposal Targets Status

**UNEVALUATED** (Evaluation against production test sets will occur following real model delivery).

---

### 65. Demo Readiness

**READY_FOR_LOCAL_DEMO**

---

### 66. Phase Completion Assessment

**READY_FOR_REVIEW**

---

### 67. Recommended Next Step

Await delivery of the trained model checkpoint (`.onnx` or `.pt`) and `model_manifest.json` from the AI/ML teammate. Ingest the artifact into `services/ai-service/models/` and verify runtime inference in `MODEL` mode.
