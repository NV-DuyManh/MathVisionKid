# MathVision Kids -- Local Troubleshooting Guide

This guide provides actionable solutions for common local development and runtime issues.

---

## Quick Diagnostic Check

Before troubleshooting individual services, always run the unified diagnostics tool:

```cmd
scripts\health-check.bat
```

Review the output table to pinpoint which specific service is in `FAIL` or `WARN` state.

---

## 1. Docker & Container Issues

### Issue 1.1: Docker daemon is not running
- **Symptom:** `scripts\health-check.bat` reports `Docker ................ FAIL`.
- **Cause:** Docker Desktop is closed, starting up, or WSL2 backend is stalled.
- **Actionable Fix:**
  1. Open Docker Desktop on Windows.
  2. Wait until the Docker icon indicates "Engine running".
  3. Re-run `scripts\health-check.bat`.

### Issue 1.2: Port already occupied (5432, 6379, 9000, 9001)
- **Symptom:** `docker compose up` fails with `port is already allocated` or `bind: address already in use`.
- **Cause:** A local PostgreSQL or Redis service installed on your host machine is occupying standard ports.
- **Actionable Fix:**
  ```powershell
  # Find which process is occupying the port (e.g. 5432):
  Get-NetTCPConnection -LocalPort 5432 | Select-Object LocalPort, OwningProcess
  
  # If local Postgres service is running, stop it:
  Stop-Service postgresql*
  ```

---

## 2. Database (PostgreSQL) Issues

### Issue 2.1: PostgreSQL not accepting connections
- **Symptom:** `PostgreSQL ............ FAIL`, Spring Boot logs `Connection to localhost:5432 refused`.
- **Actionable Fix:**
  ```powershell
  # Check container status
  docker ps -a --filter "name=mathvision-postgres"
  
  # Start container
  docker compose -f services/business-api/docker-compose.yml up -d postgres
  
  # Inspect container logs
  docker logs mathvision-postgres
  ```

### Issue 2.2: Database schema out of sync or migration failure
- **Symptom:** Spring Boot startup fails on Flyway migration.
- **Actionable Fix:**
  ```cmd
  scripts\reset-local-data.bat
  scripts\start-all.bat
  ```

---

## 3. Object Storage (MinIO) Issues

### Issue 3.1: MinIO port 9000 unreachable
- **Symptom:** `MinIO ................. FAIL`.
- **Actionable Fix:**
  ```powershell
  docker compose -f services/business-api/docker-compose.yml up -d minio
  docker logs mathvision-minio
  ```

### Issue 3.2: Bucket `mathvision` does not exist
- **Symptom:** Image uploads fail with `NoSuchBucket` or Spring logs S3 error.
- **Actionable Fix:**
  ```powershell
  docker exec mathvision-minio mc alias set local http://localhost:9000 minioadmin minioadmin123
  docker exec mathvision-minio mc mb --ignore-existing local/mathvision
  ```

---

## 4. Message Broker (Redis) & Celery Issues

### Issue 4.1: Redis unreachable
- **Symptom:** `Redis ................ FAIL`.
- **Actionable Fix:**
  ```powershell
  docker compose -f services/business-api/docker-compose.yml up -d redis
  ```

### Issue 4.2: Celery Worker offline while Redis is PASS
- **Symptom:** `Redis ................ PASS` but `Celery Worker ......... FAIL`.
- **Cause:** Celery worker crashed, was killed, or failed to start on Windows.
- **Note on Windows:** Celery on Windows requires `--pool=solo` to prevent billiard multiprocessing deadlocks.
- **Actionable Fix:**
  ```powershell
  cd services\ai-service
  .\.venv\Scripts\celery.exe -A app.jobs.celery_app worker --loglevel=info --pool=solo
  ```
  Inspect logs: `runtime\logs\celery.log`.

---

## 5. Spring Boot Business API Issues

### Issue 5.1: Spring Boot health DOWN
- **Symptom:** `Spring Boot ........... FAIL` or `/actuator/health` returns `{"status":"DOWN"}`.
- **Actionable Fix:**
  Check `runtime\logs\spring.log` or run manually to see full stack trace:
  ```powershell
  cd services\business-api
  .\gradlew.bat bootRun --args="--ai.gateway.mode=FASTAPI --spring.profiles.active=dev"
  ```
  Verify that PostgreSQL (5432) and MinIO (9000) are healthy prior to starting Spring Boot.

### Issue 5.2: Spring cannot reach FastAPI
- **Symptom:** Submission creation triggers `HttpAiAnalysisGateway` exception: `Connection refused: localhost:8000`.
- **Actionable Fix:**
  1. Verify FastAPI is running: `Invoke-RestMethod http://localhost:8000/health`.
  2. If down, start FastAPI:
     ```powershell
     cd services\ai-service
     .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
     ```

### Issue 5.3: Wrong AI Gateway Mode
- **Symptom:** Submissions are completed instantly with dummy mock data without reaching FastAPI.
- **Cause:** Spring Boot is running in `STUB` mode instead of `FASTAPI` mode.
- **Actionable Fix:**
  Launch Spring with `--ai.gateway.mode=FASTAPI`:
  ```powershell
  .\gradlew.bat bootRun --args="--ai.gateway.mode=FASTAPI --spring.profiles.active=dev"
  ```

---

## 6. FastAPI AI Runtime Issues

### Issue 6.1: FastAPI /ready reports false
- **Symptom:** `GET http://localhost:8000/ready` returns `{"ready":false,...}`.
- **Cause:** Redis broker is disconnected.
- **Actionable Fix:**
  Start Redis container: `docker compose -f services/business-api/docker-compose.yml up -d redis`.

### Issue 6.2: Status `MODEL_NOT_AVAILABLE`
- **Symptom:** Submissions return status `MODEL_NOT_AVAILABLE`.
- **Cause:** `RUNTIME_MODE=MODEL` is set in environment, but trained model artifact has not been provided.
- **Actionable Fix:**
  Ensure `RUNTIME_MODE=FIXTURE` in `services/ai-service/.env`.

---

## 7. Callback & Security Issues

### Issue 7.1: Callback authentication error (HTTP 401 / 403)
- **Symptom:** Celery worker log displays `HTTP 401 Unauthorized` or `HTTP 403 Forbidden` when posting to `http://localhost:8080/internal/v1/ai/jobs/.../callback`.
- **Cause:** `INTERNAL_API_KEY` in `services/ai-service/.env` does not match `app.ai.callback.api-key` in Spring Boot `application.yml`.
- **Actionable Fix:**
  Ensure both environments use the same key:
  - Spring: `INTERNAL_API_KEY=secret-key-default`
  - AI Service: `INTERNAL_API_KEY=secret-key-default`

---

## 8. Frontend & Mobile Issues

### Issue 8.1: Teacher Web cannot reach backend (Network Error)
- **Symptom:** Login or batch requests in Teacher Web show Network Error or Failed to fetch.
- **Cause:** Spring Boot is not running on port 8080, or CORS origin is blocked.
- **Actionable Fix:**
  1. Confirm Spring Boot is listening on port 8080.
  2. Confirm `teacher-web\.env` contains `VITE_API_BASE_URL=http://localhost:8080/api/v1`.
  3. Ensure Spring Boot `CORS_ALLOWED_ORIGINS` includes `http://localhost:5173`.

### Issue 8.2: Android Emulator or Device cannot connect to `localhost:8080`
- **Symptom:** Mobile app hangs on network requests.
- **Cause:** `localhost` inside an Android emulator or phone refers to the Android device itself, not your Windows workstation.
- **Actionable Fix:**
  - **Android Studio Emulator:** Use `http://10.0.2.2:8080/api/v1` in mobile configuration.
  - **Physical Device (Expo Go):** Use your Windows workstation's LAN IP (e.g., `http://192.168.1.50:8080/api/v1`).
