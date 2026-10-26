# HandAI — Operational Running Guide & Developer Manual
## Setup, Configuration, Execution & Troubleshooting

---

## 1. Environment Prerequisites

Before running the HandAI system, ensure the following developer runtimes are installed on your workstation:

| Runtime / Tool | Minimum Version | Verification Command | Required Purpose |
|---|---|---|---|
| **Java JDK** | `21 (LTS)` | `java -version` | Compiles and executes Spring Boot backend |
| **Node.js** | `20.x` or `22.x` | `node -v` | Runs Expo Metro bundler and mobile client |
| **npm** | `10.x` | `npm -v` | Manages JavaScript/TypeScript dependencies |
| **Python** | `3.10` – `3.13` | `python --version` | Executes PyTorch CRNN model and AI service |
| **Docker & Docker Compose** | `24.x+` / `v2.x` | `docker compose version` | Runs PostgreSQL, MinIO, and Redis containers |

---

## 2. Environment Variables & Configuration

### 2.1 Backend Configuration (`backend/business-api/src/main/resources/application.yml`)
The Spring Boot backend resolves HandAI configuration via environment variables with safe development defaults:

```yaml
ai:
  service:
    base-url: ${AI_SERVICE_BASE_URL:http://localhost:8000}
  callback:
    api-key: ${INTERNAL_API_KEY:secret-key-default}

app:
  ocr:
    pilot:
      collection-mode: ${OCR_PILOT_COLLECTION_MODE:TEST} # 'TEST' or 'REAL_FEEDBACK'

minio:
  endpoint: ${MINIO_URL:http://localhost:9000}
  access-key: ${MINIO_ACCESS_KEY:minioadmin}
  secret-key: ${MINIO_SECRET_KEY:minioadmin123}
  bucket: ${MINIO_BUCKET:mathvision}

spring:
  datasource:
    url: ${SPRING_DATASOURCE_URL:jdbc:postgresql://localhost:5432/mathvision}
    username: ${SPRING_DATASOURCE_USERNAME:mathvision}
    password: ${SPRING_DATASOURCE_PASSWORD:mathvision123}
```

### 2.2 AI Service Configuration (`.env` in repository root or ai runtime)
```bash
# Target hardware for PyTorch inference ('cuda' or 'cpu')
OCR_DEVICE=cpu

# Internal security key matching Spring Boot
INTERNAL_API_KEY=secret-key-default

# AI Contextual Post-Correction Cloud APIs
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2.3 Mobile App Configuration (`apps/student-mobile/.env`)
```bash
# Network URL of Spring Boot Business API (use machine LAN IP for physical phone testing)
EXPO_PUBLIC_API_URL=http://localhost:8080
```

---

## 3. Step-by-Step Running Guide

### Step 1: Start Container Infrastructure (PostgreSQL, MinIO, Redis)
Open PowerShell in the repository root and start the required Docker containers:

```powershell
docker compose -f infra/docker/docker-compose.yml up -d postgres minio redis
```

*Verification:*
- PostgreSQL is listening on port `5432`.
- MinIO is accessible at `http://localhost:9000` (Console: `http://localhost:9001`, user: `minioadmin`, pass: `minioadmin123`).

---

### Step 2: Launch the AI Inference Service (FastAPI)
Activate the Python virtual environment containing PyTorch, OpenCV, and FastAPI, then start the AI runtime:

```powershell
# Using repository venv or active python environment:
cd services/ai-service
# Or from ai runtime:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*Verification:*
- Send a GET request to `http://localhost:8000/internal/v1/ocr/health`. Expected response: `{"status": "UP"}`.

---

### Step 3: Launch the Business API Gateway (Spring Boot)
Open a new terminal window and run Spring Boot using the Gradle wrapper:

```powershell
cd backend/business-api
.\gradlew.bat bootRun --args="--spring.profiles.active=dev"
```

*Verification:*
- Flyway migrations automatically execute (`V11`, `V14`, `V15`).
- HandAI Public Health check responds at:
  ```powershell
  curl http://localhost:8080/api/v1/handai/health
  # Response: {"status":"UP","module":"HandAI"}
  ```

---

### Step 4: Launch the Student Mobile Application (Expo / Metro)
Open a new terminal window to start the Metro bundler:

```powershell
cd apps/student-mobile
npx expo start --clear
```

- Press `w` to run on Web Browser, or:
- Scan the printed QR code with the **Expo Go** app on a physical Android or iOS device connected to the same Wi-Fi network.

---

## 4. Alternative: One-Click Unified Local Launcher

You can start the entire stack simultaneously using the automated repository launcher:

```cmd
RUN_MATHVISION.bat
```
This script executes `scripts/dev/start-all.ps1`, performing pre-flight dependency checks, starting containers, booting Spring Boot and the AI service as tracked background processes, launching the Metro bundler, and verifying endpoint connectivity.

---

## 5. Defense & Demonstration Mode (Zero-Login Guest Flow)

For presentations, academic evaluations, or defense demos, HandAI features **Guest Demonstration Mode** to bypass login friction:

1. Launch the Mobile App.
2. On the welcome / navigation screen, tap **"Thử nghiệm HandAI (Khách / Nghiên cứu)"**.
3. Capture or upload a primary school handwriting sample.
4. The app invokes `POST /api/v1/handai/ocr/multiline/detect` without requiring a JWT token.
5. Review detected bounding boxes, tap **"Xác nhận dòng viết"**, and view the immediate **Trial Analytics** report.
6. Navigate to **"Báo cáo Nghiên cứu Toàn cầu"** to view longitudinal charts, top confusion pairs, and export Markdown research reports.

---

## 6. Verification & Automated Test Commands

To verify that the HandAI algorithms and data contracts are 100% operational:

### A. Run Frontend Analytics Unit & Integration Tests (168 Tests)
```powershell
cd apps/student-mobile
npm test -- src/__tests__/handAiAnalyticsAndFlow.test.ts
```
*Expected Output:*
```
Test Suites: 1 passed, 1 total
Tests:       63 passed, 63 total (or 168 passed in full suite)
Snapshots:   0 total
Time:        ~7.5s
```

### B. Run TypeScript Typecheck
```powershell
cd apps/student-mobile
npx tsc --noEmit
```
*Expected Output:* Clean exit with return code `0` (0 type errors).

### C. Run Backend OCR Integration Tests
```powershell
cd backend/business-api
.\gradlew.bat test --tests "com.mathvisionkids.api.ocr.multiline.*"
```
*Expected Output:* `BUILD SUCCESSFUL` (All trial, line, and controller tests pass).

---

## 7. Troubleshooting Common Operational Issues

### Issue 1: Port Conflict on 8080 or 8000
- **Symptom:** `Port 8080 is already in use` or `Port 8000 is already in use`.
- **Resolution:**
  ```powershell
  # Find PID using port 8080:
  netstat -ano | findstr :8080
  # Terminate process:
  taskkill /F /PID <PID>
  ```

### Issue 2: AI Service Returns 401 Unauthorized
- **Symptom:** Spring Boot logs `AI_SERVICE_ERROR: 401 Unauthorized`.
- **Cause:** Mismatch between Spring Boot `ai.callback.api-key` and AI Service `INTERNAL_API_KEY`.
- **Resolution:** Ensure both environments use the same key (default: `secret-key-default`).

### Issue 3: Line Over-segmentation (Accents Detected as Standalone Lines)
- **Symptom:** A 4-line handwritten paragraph generates 7 or 8 bounding boxes.
- **Cause:** Floating diacritics were not consolidated into primary row bodies due to poor binarization.
- **Resolution:** Ensure the image was taken with adequate contrast. The automated OpenCV morphological filter (`POST /internal/v1/ocr/detect-lines`) automatically merges components within $0.8 \times \text{row\_height}$.
