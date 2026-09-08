# MathVision Kids -- Developer Local Setup Guide

Welcome to MathVision Kids! This guide details the complete local setup process for new developers and contributors.

---

## 1. System Prerequisites

Ensure the following developer tools are installed on your machine:

| Tool | Recommended Version | Verification Command | Notes |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10/11 (Primary) or macOS/Linux | `[System.Environment]::OSVersion` | Windows PowerShell / CMD first-class support |
| **Git** | 2.40+ | `git --version` | Standard version control |
| **Docker Desktop** | 24+ | `docker version` | Required for PostgreSQL, MinIO, Redis |
| **Java JDK** | 21 (Eclipse Temurin / OpenJDK) | `java -version` | Required for Spring Boot Business API |
| **Python** | 3.12 | `python --version` | Required for FastAPI AI Runtime & Celery |
| **Node.js & npm** | Node 20+ (LTS), npm 10+ | `node -v` && `npm -v` | Required for Teacher Web & Student Expo app |

> **Note:** A globally installed Gradle is **not** required; the project includes Gradle Wrapper (`gradlew.bat`).

---

## 2. Clone & Initial Workspace Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/NV-DuyManh/MathVisionKid.git
cd MathVisionKid
```

Verify your workspace root:
```bash
git rev-parse --show-toplevel
# Expected output: .../MathVisionKid
```

---

## 3. Component Dependencies Installation

### A. Python AI Subsystem (FastAPI + Celery)

Set up the Python virtual environment and install dependencies:

```powershell
cd services\ai-service
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
cd ..\..
```

### B. Teacher Web Portal (React + Vite)

Install the frontend dependencies:

```powershell
cd teacher-web
npm install
cd ..
```

### C. Student Mobile App (Expo / React Native)

Install the mobile app dependencies at repository root:

```powershell
npm install
```

---

## 4. Environment Configuration

The repository includes a central configuration template: `.env.example`.

Copy and inspect local environment files:

```powershell
# AI Service
copy services\ai-service\.env.example services\ai-service\.env

# Teacher Web (pre-configured)
# Verify teacher-web\.env contains:
# VITE_API_BASE_URL=http://localhost:8080/api/v1
# VITE_USE_MOCK=false
```

All local development defaults (ports, demo credentials, non-secret HMAC keys) are pre-configured for instant out-of-the-box local operation.

---

## 5. One-Command System Startup

MathVision Kids provides a unified, single-command launcher that initializes Docker containers, starts background services, verifies health, and displays service URLs:

```cmd
scripts\start-all.bat
```

*(Alternatively in PowerShell: `.\scripts\start-all.ps1`)*

### What `start-all` does automatically:
1. Verifies installed tools (Docker, Java, Node, Python).
2. Creates transient `runtime\logs\` and `runtime\pids\` directories.
3. Starts Docker containers (`mathvision-postgres`, `mathvision-minio`, `mathvision-redis`) via Docker Compose.
4. Initializes the MinIO `mathvision` bucket if missing.
5. Launches **Spring Boot Business API** (port 8080) with tracked PID and log redirection.
6. Launches **FastAPI AI Runtime** (port 8000) with tracked PID.
7. Launches **Celery Solo Worker** with tracked PID.
8. Launches **Teacher Web Portal** (port 5173) with tracked PID.
9. Polls all service health endpoints until ready.
10. Executes the diagnostic suite and prints active service URLs.

---

## 6. Service URLs & Ports

When the local environment is healthy, access services at:

| Service | Port | Endpoint URL | Purpose |
| :--- | :--- | :--- | :--- |
| **Teacher Web** | `5173` | [http://localhost:5173](http://localhost:5173) | Web portal for batch upload, student mapping, review |
| **Spring Boot API** | `8080` | [http://localhost:8080](http://localhost:8080) | Core business backend REST API |
| **Spring Swagger UI** | `8080` | [http://localhost:8080/swagger-ui.html](http://localhost:8080/swagger-ui.html) | OpenAPI documentation & interactive client |
| **FastAPI AI Runtime** | `8000` | [http://localhost:8000](http://localhost:8000) | Async AI analysis & inference pipeline |
| **MinIO Web Console** | `9001` | [http://localhost:9001](http://localhost:9001) | S3 storage manager (`minioadmin` / `minioadmin123`) |
| **MinIO API** | `9000` | [http://localhost:9000](http://localhost:9000) | S3 object storage API |
| **PostgreSQL** | `5432` | `localhost:5432` | Relational database (`mathvision` db) |
| **Redis** | `6379` | `localhost:6379` | Celery message broker & state store |
| **Student Mobile** | `8081` | [http://localhost:8081](http://localhost:8081) | Metro bundler for Expo development |

---

## 7. Verifying Health

Run the diagnostic utility at any time:

```cmd
scripts\health-check.bat
```

Expected healthy output:
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

---

## 8. Starting Student Mobile (Optional)

To start the student mobile application:

```bash
npm start
```

- Press `a` to open Android Emulator (requires Android Studio).
- Or scan the displayed QR code with the **Expo Go** app on your physical mobile phone connected to the same Wi-Fi network.

---

## 9. Stopping the System

Stop all MathVision Kids processes safely:

```cmd
scripts\stop-all.bat
```

This stops only MathVision Kids-owned background processes and stops the Docker containers without wiping your database records.

---

## 10. Restarting the System

```cmd
scripts\restart-all.bat
```

Executes `stop-all.bat` followed by `start-all.bat`.

---

## 11. Resetting Local Data

To wipe local demo records (PostgreSQL tables, MinIO uploaded images, logs) and start completely fresh:

```cmd
scripts\reset-local-data.bat
```

> **Safety Confirmation:** The script will ask for explicit confirmation before removing Docker volumes. Unrelated Docker containers on your workstation are never touched.
