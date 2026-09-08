# MathVision Kids -- Local Runtime Diagnostic Tool

This directory contains the unified local runtime diagnostic utility for the MathVision Kids project.

## Purpose

The diagnostic utility (`check_runtime.py`) provides an automated health and readiness check across the entire MathVision Kids stack without requiring manual endpoint probing or guessing.

## Components Checked

| Component | Target Checked | Success Criteria | Failure Remediation |
| :--- | :--- | :--- | :--- |
| **Docker** | Docker daemon version / CLI | Exit code 0 | Start Docker Desktop |
| **PostgreSQL** | `localhost:5432` & `pg_isready` | Connection accepted & DB exists | `docker compose -f services/business-api/docker-compose.yml up -d postgres` |
| **MinIO** | `localhost:9000` & `/minio/health/live` | HTTP 200 | `docker compose -f services/business-api/docker-compose.yml up -d minio` |
| **Redis** | `localhost:6379` | `PING` -> `+PONG` | `docker compose -f services/business-api/docker-compose.yml up -d redis` |
| **Spring Boot** | `http://localhost:8080/actuator/health` | HTTP 200 & `status == "UP"` | Run `scripts/start-all.bat` or inspect `runtime/logs/spring.log` |
| **FastAPI** | `http://localhost:8000/health` & `/ready` | HTTP 200 & `status == "ready"` | Run `scripts/start-all.bat` or inspect `runtime/logs/fastapi.log` |
| **Celery Worker** | Celery Control Ping | Active worker responds with pong | Run `scripts/start-all.bat` or inspect `runtime/logs/celery.log` |
| **Teacher Web** | `http://localhost:5173` | HTTP 200 from Vite dev server | Run `scripts/start-all.bat` or inspect `runtime/logs/teacher-web.log` |
| **Student Mobile** | `app.json` & port `8081` | Config valid; reports `RUNNING` or `CONFIGURED` | Run `npm start` from repository root |

## Diagnostic States

- **PASS**: Component is running, reachable, and healthy.
- **WARN**: Component is reachable but returned degraded state or non-critical notice.
- **FAIL**: Required component is down, unresponsive, or returning error.
- **NOT_RUNNING**: Process or container is not currently active.
- **CONFIGURED**: Client project configuration is valid, but optional client runtime is not currently listening.
- **BLOCKED**: Prerequisite dependency is missing or corrupt.

## Exit Codes

- `0`: All required local demo dependencies are healthy (`READY_FOR_DEMO`).
- `1`: One or more required components failed (`NOT_READY`). Actionable diagnosis and remediation commands are printed to stderr/stdout.

## Usage

From repository root:

```bash
# Using Python
python tools/diagnostics/check_runtime.py

# Using the Windows batch shortcut
scripts\health-check.bat
```
