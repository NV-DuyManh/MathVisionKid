# Local setup

[README](../README.md) · [Tiếng Việt](HUONG_DAN_CAI_DAT.md) · [Troubleshooting](TROUBLESHOOTING.md)

This guide covers the repository's Windows launcher. It distinguishes starting the ecosystem from enabling real recognition. Run commands from the repository root unless a step says otherwise.

## 1. Prerequisites

| Tool | Version / requirement |
| :--- | :--- |
| Windows | PowerShell and Command Prompt available |
| Git | Installed and available on PATH |
| Node.js | 22.13 or newer compatible with the locked dependencies; the inspected environment uses Node 22 |
| Python | 3.12; Windows `py -3.12` launcher available |
| Java | JDK 21; `java` available on PATH |
| Docker Desktop | Running engine, Linux containers, and Docker Compose |
| Phone, optional | Compatible Expo Go client; same Wi-Fi as the computer for LAN testing |

The Gradle wrapper is included. You do not need global Gradle. Internet access is needed for the first dependency installation, container pulls, detector download, and cloud capabilities. The [versioned Expo SDK 57 reference](https://docs.expo.dev/versions/v57.0.0/) documents its React Native and Node.js compatibility.

## 2. Clone and install

~~~powershell
git clone https://github.com/NV-DuyManh/MathVisionKid.git
cd MathVisionKid
npm ci
py -3.12 -m venv ai\runtime\.venv
.\ai\runtime\.venv\Scripts\python.exe -m pip install --upgrade pip
.\ai\runtime\.venv\Scripts\python.exe -m pip install -r ai\runtime\requirements.txt
~~~

The root lockfile installs all JavaScript workspaces. Avoid separate installs in each app. If `py` is unavailable, use a verified Python 3.12 executable to create the virtual environment.

## 3. Choose your capabilities

### Start with the local defaults

A clean clone uses development defaults for the local database and object store. You do not need to copy every `.env.example` just to launch the stack.

- The async arithmetic grader defaults to `RUNTIME_MODE=FIXTURE`, which produces synthetic fixture results.
- Real handwriting OCR needs a trained checkpoint.
- The main math guide's photo transcription needs configured cloud vision.
- Supported built-in lesson patterns can run without a cloud-generated plan, but still need the local backend and AI runtime.

Fixture grading is a developer integration tool. It does not enable real handwriting recognition or a general offline photo tutor.

### Enable real recognition and guidance

**Vietnamese handwriting OCR**

Request the trained artifact from the project owner and place it here:

~~~text
ai/runtime/models/ocr/crnn_vi_handwriting_v1/
├── best_cer.pth           required, not stored in Git
├── vocab.json            included in Git
└── model_manifest.json   included in Git
~~~

Verify the checkpoint:

~~~powershell
Get-FileHash ai\runtime\models\ocr\crnn_vi_handwriting_v1\best_cer.pth -Algorithm SHA256
~~~

The current expected hash is `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`. Compare against the [manifest](../ai/runtime/models/ocr/crnn_vi_handwriting_v1/model_manifest.json) if artifacts change. This checkpoint is used by handwriting OCR endpoints; the main math-guide photo transcription follows a separate cloud path.

**Optional local text detector**

~~~powershell
.\ai\runtime\.venv\Scripts\python.exe ai\runtime\scripts\setup_text_detector.py
~~~

The setup script downloads its pinned artifact and verifies the checksum. It does not train a model or guarantee perfect line separation.

**Cloud notebook reading and assistance**

Create `ai/runtime/.env.local` with a text editor. Enable only the provider you actually configured; keep the file outside Git. A minimal Groq configuration is:

~~~dotenv
GROQ_ENABLED=true
GROQ_API_KEYS="REPLACE_WITH_YOUR_VALID_KEY"
GEMINI_ENABLED=false
GEMINI_API_KEYS=""
~~~

To use Gemini instead, disable Groq and set `GEMINI_ENABLED=true` with valid `GEMINI_API_KEYS`. To configure fallback, enable both with valid keys. Provider model settings and optional advisor settings are listed in [the AI example](../ai/runtime/.env.example); confirm your provider account supports the configured model.

Do not use placeholder keys. The AI `.env.example` also contains storage placeholders and an enabled Gemini example, so copying it unchanged is not a working configuration. Service-local `.env.local` overrides corresponding base `.env` values; process environment variables take precedence.

**YOLO arithmetic grading, optional**

Place the owner-supplied `yolov8n_mathvision_det_v1.pt` under `ai/runtime/models/`, verify it against the [model manifest](../ai/runtime/models/model_manifest.json), and set `RUNTIME_MODE=MODEL` in `ai/runtime/.env.local`. Its current expected hash is `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`. This changes the async arithmetic grading engine, not the math-guide transcription provider.

Restart local services after changing AI configuration or artifacts.

## 4. Launch the complete ecosystem

Start Docker Desktop, then run:

~~~powershell
.\RUN_MATHVISION.bat
~~~

The launcher checks prerequisites, starts PostgreSQL, MinIO, and Redis through Docker, then starts the business API, host AI runtime, worker, web workspaces, and student server. It opens the portal and prints a QR code.

**Keep the launcher window open while scanning.** It pauses at the end so the QR remains visible. The student server runs in a separate visible terminal. Closing a launcher window does not stop background services; use the stop command below.

Do not also run the complete Compose file with all services: it includes containerized AI services that can conflict with the launcher's host runtime.

### Core stack without the student server

~~~powershell
.\scripts\start-all.bat
~~~

To start the student app separately afterward:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-student-metro.ps1
~~~

## 5. Open the apps

| Service | Local address |
| :--- | :--- |
| Unified portal | `http://localhost:5172` |
| Teacher web | `http://localhost:5173` |
| Admin web | `http://localhost:5174` |
| Student web preview | `http://localhost:8081` |
| Business API health | `http://localhost:8080/actuator/health` |
| Business API documentation | `http://localhost:8080/swagger-ui.html` |
| AI readiness | `http://localhost:8000/ready` |

For a physical phone, scan the QR using an Expo Go client compatible with **Expo SDK 57**. The phone and computer must share Wi-Fi. The phone uses the computer's LAN address, not localhost. See [phone troubleshooting](TROUBLESHOOTING.md#phone-cannot-open-the-app).

The student API resolver normally derives the development host from the server URL. For an explicit override, use `EXPO_PUBLIC_API_OVERRIDE=http://YOUR_COMPUTER_LAN_IP:8080/api/v1` in `apps/student-mobile/.env.local`, then restart the student server. Keep the `/api/v1` prefix. `EXPO_PUBLIC_API_BASE_URL` is a fallback and does not take priority over a detected development host. Do not put private service keys in `EXPO_PUBLIC_` variables.

### Development-only accounts

These accounts are seeded by the backend's dev profile. They are local examples, not production credentials.

| Role | Account | Password |
| :--- | :--- | :--- |
| Student | `minh.student@mathvision.local` | `MathVision123!` |
| Teacher | `lan.teacher@mathvision.local` | `MathVision123!` |
| Admin | `admin.demo@mathvision.local` | `MathVision123!` |

The backend owns authentication and roles. Existing database records can differ from a fresh seeded installation.

## 6. Verify and stop

~~~powershell
.\scripts\health-check.bat
.\scripts\stop-all.bat
~~~

Run health check while the stack is running; run stop when finished. Logs and PID files live under `infra/local-runtime/logs/` and `infra/local-runtime/pids/`. The normal stop command preserves database and image-storage volumes.

Readiness checks connectivity and worker/runtime availability. It does not verify the CRNN checkpoint, cloud quota, every transcription, or every lesson type. Use a real sample and review its content as described in the [demo guide](DEMO_GUIDE.md).

Local development defaults are not a production deployment recipe. Production requires separate secrets, access controls, networking, and storage policies.
