# MathVision Kids -- Local Maintenance Guide

This document explains configuration management, log inspection, service tuning, and operational maintenance for local development.

---

## 1. Configuration Map

| Layer | Primary Config File | Template / Defaults | Purpose |
| :--- | :--- | :--- | :--- |
| **System Overview** | `.env.example` | Repository root | Single reference for all environment variables |
| **Spring Boot** | `services/business-api/src/main/resources/application.yml` | `.env.example` | Database, JWT, storage, AI gateway settings |
| **FastAPI & Celery** | `services/ai-service/.env` | `services/ai-service/.env.example` | Runtime mode, Redis broker, MinIO keys |
| **Docker Compose** | `services/business-api/docker-compose.yml` | N/A | PostgreSQL, MinIO, Redis container declarations |
| **Teacher Web** | `teacher-web/.env` | N/A | Vite API target and mock toggles |
| **Student Mobile** | `app.json` | N/A | Expo app configuration |

---

## 2. Managing Environment Variables

### Adding a New Variable to Spring Boot:
1. Open `services/business-api/src/main/resources/application.yml`.
2. Define the property with fallback syntax: `${MY_NEW_VAR:default_value}`.
3. Document the variable in `.env.example`.

### Adding a New Variable to FastAPI:
1. Open `services/ai-service/app/config.py`.
2. Add the field to the `Settings` class (using Pydantic BaseSettings).
3. Document the variable in `services/ai-service/.env.example` and root `.env.example`.

---

## 3. Changing Local Ports

If a port conflict occurs on your workstation:
- **FastAPI (8000 -> 8001):** Update `PORT=8001` in `services/ai-service/.env` and `AI_SERVICE_URL=http://localhost:8001/internal/v1/jobs` in Spring's `application.yml`.
- **Spring Boot (8080 -> 8085):** Update `server.port: 8085` in `application.yml`, `SPRING_CALLBACK_BASE_URL` in `services/ai-service/.env`, and `VITE_API_BASE_URL` in `teacher-web/.env`.
- **Teacher Web (5173 -> 3000):** Add `server: { port: 3000 }` in `teacher-web/vite.config.ts`. Update `CORS_ALLOWED_ORIGINS` in Spring's `application.yml`.

---

## 4. Reading Runtime Logs

When running via `scripts\start-all.bat`, services stream output to `runtime\logs\`:

```powershell
# Tail Spring Boot log
Get-Content -Path runtime\logs\spring.log -Wait -Tail 30

# Tail FastAPI log
Get-Content -Path runtime\logs\fastapi.log -Wait -Tail 30

# Tail Celery Worker log
Get-Content -Path runtime\logs\celery.log -Wait -Tail 30

# Tail Teacher Web log
Get-Content -Path runtime\logs\teacher-web.log -Wait -Tail 30
```

---

## 5. Inspecting Redis & Celery

### Redis CLI via Docker:
```powershell
# Open redis-cli
docker exec -it mathvision-redis redis-cli

# Check Celery task queue depth
LLEN celery

# View registered keys
KEYS *
```

### Inspect Celery Workers:
```powershell
cd services\ai-service
.\.venv\Scripts\celery.exe -A app.jobs.celery_app inspect active
.\.venv\Scripts\celery.exe -A app.jobs.celery_app inspect stats
```

---

## 6. Inspecting PostgreSQL Database

```powershell
# Connect to PostgreSQL via psql inside container
docker exec -it mathvision-postgres psql -U mathvision -d mathvision

# Useful queries:
\dt                              -- List all tables
SELECT * FROM users;            -- View users
SELECT * FROM classrooms;       -- View demo classrooms
SELECT * FROM assignments;      -- View assignments
SELECT * FROM submissions;      -- View submissions
SELECT * FROM ai_jobs;          -- View AI analysis jobs
```

---

## 7. Inspecting MinIO Storage

- Open the web console at [http://localhost:9001](http://localhost:9001).
- Log in with `minioadmin` / `minioadmin123`.
- Browse bucket `mathvision` to inspect uploaded raw and processed images.

---

## 8. Switching Between FIXTURE and MODEL Modes

In `services/ai-service/.env`:

```ini
# Current default mode (deterministic demo, no weights required)
RUNTIME_MODE=FIXTURE

# Production / Experimental mode (requires trained model artifact)
# RUNTIME_MODE=MODEL
```

---

## 9. Future Model Handoff Integration Procedure

When the AI/ML training teammate delivers the trained model artifact:
1. Copy model artifact (e.g. `best_model.onnx` or `.pt`) and `model_manifest.json` into `services/ai-service/models/`.
2. Configure paths in `services/ai-service/.env`:
   ```ini
   RUNTIME_MODE=MODEL
   MODEL_MANIFEST_PATH=models/model_manifest.json
   MODEL_ARTIFACT_PATH=models/best_model.onnx
   ```
3. Restart the stack using `scripts\restart-all.bat`.
4. Run `tools\diagnostics\check_runtime.py` to confirm the model manifest and weights validate successfully.
5. No changes are required in Spring Boot or frontend applications.
