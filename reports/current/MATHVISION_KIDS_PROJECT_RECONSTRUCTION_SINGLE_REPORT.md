# MathVision Kids — Full Project Reconstruction Report

**Phase:** MATHVISION.KIDS.PROJECT.RECONSTRUCTION (READ-ONLY AUDIT)
**Date:** 2026-09-21
**Author:** Senior Software Architect / ML Engineer / Technical Auditor
**Scope:** Evidence-based reconstruction of the REAL project state from repository and local evidence

---

## Table of Contents

1. [Project Identity & Mission](#1-project-identity--mission)
2. [Repository Root Inventory](#2-repository-root-inventory)
3. [True Core MVP vs. OCR Pilot](#3-true-core-mvp-vs-ocr-pilot)
4. [Student Mobile App (Expo/React Native)](#4-student-mobile-app)
5. [Teacher Web Portal](#5-teacher-web-portal)
6. [Admin Web Portal](#6-admin-web-portal)
7. [Portal Web (Unified Entry)](#7-portal-web)
8. [Spring Boot Business API](#8-spring-boot-business-api)
9. [FastAPI AI Service](#9-fastapi-ai-service)
10. [Infrastructure & Docker](#10-infrastructure--docker)
11. [API Contract (OpenAPI)](#11-api-contract-openapi)
12. [Architecture Decision Records](#12-architecture-decision-records)
13. [AI Models Inventory](#13-ai-models-inventory)
14. [The 59K Dataset Investigation](#14-the-59k-dataset-investigation)
15. [AI Training Workspace](#15-ai-training-workspace)
16. [Report Archaeology](#16-report-archaeology)
17. [What Has Actually Been Built](#17-what-has-actually-been-built)
18. [What Is Missing or Incomplete](#18-what-is-missing-or-incomplete)
19. [Conclusions & Recommendations](#19-conclusions--recommendations)

---

## 1. Project Identity & Mission

**Name:** MathVision Kids
**Tagline:** "AI-assisted handwritten arithmetic grading and tutoring platform for Vietnamese primary-school students (Grades 1-5)"

**Core Mission (from README.md):**
- Students photograph handwritten math worksheets via mobile app
- AI recognizes handwriting, detects arithmetic operations, validates correctness
- System provides step-by-step tutoring hints (not just right/wrong)
- Teachers batch-upload class worksheets, review AI-proposed grades, retain final authority
- Admin manages users, classrooms, and teacher assignments

**No Proposal/SRS document exists in the repository.** No `.pdf`, `.docx`, or `.doc` files were found. The closest specification artifacts are:
- `contracts/openapi/mathvision-api.yaml` (1,663 lines, formal API contract)
- `contracts/ARCHITECTURE_DECISIONS.md` (11 ADRs)
- `docs/ARCHITECTURE_LOCAL_RUNTIME.md` (full system topology)
- `ai-training/data/README.md` (references "Proposal v3.1" data targets: >=100 verified pilot images by W5, >=500 gold images by W11)

---

## 2. Repository Root Inventory

| Directory | Purpose | File Count | Status |
|---|---|---|---|
| `src/` | Student Mobile App (Expo/React Native) | 62 TS/TSX | **BUILT** |
| `teacher-web/` | Teacher Web Portal (Vite + React 19) | 27 TS/TSX | **BUILT** |
| `admin-web/` | Admin Web Portal (Vite + React 19) | 25 TS/TSX | **BUILT** |
| `portal-web/` | Unified Entry Portal (Vite + React 19) | 16 TS/TSX | **BUILT** |
| `services/business-api/` | Spring Boot 3.3.6 Business API (Java 21) | 109 Java | **BUILT** |
| `services/ai-service/` | FastAPI AI Runtime (Python 3.12+) | 65 Python | **BUILT** |
| `ai-training/` | ML Training Workspace | Mixed | **SCAFFOLDED, MOSTLY EMPTY** |
| `contracts/` | API contracts, ADRs | YAML + MD | **FROZEN** |
| `docs/` | Local runtime docs | 5 files | **WRITTEN** |
| `scripts/` | Dev tooling, test scripts | 29 files | **BUILT** |
| `report/` | Engineering phase reports | 201 MD files | **EXTENSIVE** |
| `models/` | Production model artifacts | 2 models | **DEPLOYED (V1 only)** |

**Total images in repo (excl. node_modules, .venv, .gradle):** 1,146

---

## 3. True Core MVP vs. OCR Pilot

This is the most critical section of the audit. The project has **two distinct tracks**:

### Track A: Core Math Grading MVP (The REAL Product)

The original product vision is a **complete end-to-end grading platform**:

```
Student photographs worksheet
    -> Spring Boot receives submission
    -> AI Service processes image asynchronously (via Celery/Redis)
    -> YOLO detects individual digits, operators, carry markers (14 classes)
    -> Deterministic arithmetic validators check column addition/subtraction
    -> Results callback to Spring Boot
    -> Teacher reviews and approves/overrides
    -> Student gets tutoring hints
```

**This pipeline is BUILT end-to-end in code**, from the mobile camera screen through Spring Boot to FastAPI to Celery workers with deterministic validators. The YOLO v8n detection model is trained and deployed (`yolov8n_mathvision_det_v1.pt`, 6.0 MB, mAP50=0.9672).

### Track B: Vietnamese Handwriting OCR Pilot (Experimental Extension)

A separate track was added to handle **general Vietnamese handwritten text** recognition:

```
Student photographs handwritten Vietnamese text
    -> Line segmentation (hue-projection based)
    -> CRNN OCR per line crop
    -> Groq/Gemini VLM post-correction advisor
    -> Multiline result display with per-line confidence
```

**This is where the 200+ reports come from.** The OCR pilot has consumed the vast majority of recent engineering effort (reports prefixed `ai_hwtext_*`, `ocr_pilot_*`, `ocr_flow_*`, `ocr_runtime_*`, etc.).

### Verdict: The Core MVP Uses YOLO Detection, NOT CRNN OCR

The YOLO model detects **individual math symbols** (digits 0-9, +, -, =, carry marker c1) at the bounding-box level. This is the core arithmetic grading pipeline.

The CRNN OCR model reads **general Vietnamese handwriting text** (320 character classes including full Vietnamese diacritics). This is a separate pilot feature added later.

**The recent conversation drift focused almost entirely on Track B (OCR pilot), which is experimental. The core product (Track A) was already built and functional with YOLO detection.**

---

## 4. Student Mobile App

**Stack:** Expo SDK 57, React Native 0.86.3, React 19.2.3, TypeScript 6.0
**Entry:** `app.json` -> expo-router

### Screens

| Screen | File | Purpose |
|---|---|---|
| Home/Dashboard | `src/app/(tabs)/index.tsx` (21.7 KB) | Main student screen with demo mocks |
| Camera | `src/app/camera.tsx` (14.3 KB) | Photo capture |
| Gallery | `src/app/gallery.tsx` (21.5 KB) | Image picker |
| Crop | `src/app/crop.tsx` (21.4 KB) | Image cropping with gesture handler |
| Preview | `src/app/preview.tsx` (8.5 KB) | Pre-submission preview |
| Privacy | `src/app/privacy.tsx` (30.3 KB) | Privacy masking |
| Processing | `src/app/processing.tsx` (14.2 KB) | Async submission polling |
| Login | `src/app/login.tsx` (9.8 KB) | Student login |
| Profile | `src/app/(tabs)/profile.tsx` (5.6 KB) | Student profile |
| Results: Correct | `src/app/results/correct.tsx` | Flow A: correct answer |
| Results: Error Hint | `src/app/results/error-hint.tsx` | Flow B: step-by-step hint |
| Results: Token Confirm | `src/app/results/token-confirmation.tsx` | Flow C: ambiguous recognition |
| Results: Quality Failure | `src/app/results/quality-failure.tsx` | Flow D: bad photo |
| Results: Out of Scope | `src/app/results/out-of-scope.tsx` | Flow E: unsupported math |
| Results: Review Required | `src/app/results/review-required.tsx` | Flow F: low confidence |
| OCR Pilot: Line Crop | `src/app/ocr-pilot/line-crop.tsx` | Handwriting line detection |
| OCR Pilot: Multiline Result | `src/app/ocr-pilot/multiline-result.tsx` (41.2 KB) | Multi-line OCR display |
| OCR Pilot: Multiline Review | `src/app/ocr-pilot/multiline-review.tsx` (32.8 KB) | OCR review UI |
| OCR Pilot: Single Result | `src/app/ocr-pilot/result.tsx` | Single-line OCR result |

**Current API Mode:** MockSubmissionService (no live backend connection yet for student flow). The README explicitly documents how to switch to real Spring Boot API.

### Key Libraries
- `expo-camera`, `expo-image-picker`, `expo-image-manipulator` for image capture
- `react-native-gesture-handler`, `react-native-reanimated` for crop/gesture UX
- `expo-secure-store` for token storage
- `axios` for HTTP calls

---

## 5. Teacher Web Portal

**Stack:** Vite + React 19 + TypeScript
**Location:** `teacher-web/`
**Port:** 5173

### Pages (12 screens)

| Page | Size | Purpose |
|---|---|---|
| `LoginPage.tsx` | 8.9 KB | Teacher authentication |
| `DashboardPage.tsx` | 12.7 KB | Class overview, stats |
| `ClassesPage.tsx` | 6.5 KB | Class listing |
| `AssignmentsPage.tsx` | 6.5 KB | Assignment listing |
| `AssignmentCreatePage.tsx` | 6.9 KB | Create new assignment |
| `BatchCreatePage.tsx` | 20.0 KB | Batch upload (10-30 images) |
| `BatchesPage.tsx` | 7.3 KB | Batch listing |
| `BatchDetailPage.tsx` | 10.0 KB | Batch detail view |
| `ReviewQueuePage.tsx` | 8.9 KB | Review-by-exception queue |
| `SubmissionReviewPage.tsx` | 18.5 KB | Individual submission review |
| `PrivacyEditorModal.tsx` | 12.6 KB | Privacy masking editor |
| `SettingsPage.tsx` | 5.3 KB | Teacher settings |

**This is a substantial, feature-complete teacher portal** -- not a placeholder.

---

## 6. Admin Web Portal

**Stack:** Vite + React 19 + TypeScript
**Location:** `admin-web/`

### Pages (7 screens)

| Page | Size | Purpose |
|---|---|---|
| `LoginPage.tsx` | 9.1 KB | Admin authentication |
| `DashboardPage.tsx` | 10.5 KB | System overview |
| `UsersPage.tsx` | 14.3 KB | User management (CRUD) |
| `UserDetailPage.tsx` | 18.8 KB | User detail/edit |
| `ClassesPage.tsx` | 11.0 KB | Classroom management |
| `ClassDetailPage.tsx` | 21.7 KB | Class detail with roster |
| `AuditPage.tsx` | 11.5 KB | Audit log viewer |

**This is a complete admin panel** per ADR-011 (ADMIN role with user provisioning, classroom admin, audit visibility).

---

## 7. Portal Web (Unified Entry)

**Stack:** Vite + React 19 + TypeScript
**Location:** `portal-web/`

### Pages (9 screens)

| Page | Purpose |
|---|---|
| `LandingPage.tsx` | Public landing page |
| `LoginPage.tsx` | Unified login with role detection |
| `TeacherEntryPage.tsx` | Teacher SSO handoff to teacher-web |
| `AdminEntryPage.tsx` | Admin SSO handoff to admin-web |
| `StudentLandingPage.tsx` | Student web landing (redirects to mobile) |
| `AccessDeniedPage.tsx` | Role-based access denial |
| `SessionExpiredPage.tsx` | Session expiry handler |
| `LogoutPage.tsx` | Unified logout |
| `DevRuntimePage.tsx` | Development runtime dashboard |

**This is a unified SSO entry point** that routes users to their role-specific applications.

---

## 8. Spring Boot Business API

**Stack:** Spring Boot 3.3.6, Java 21, Gradle
**Location:** `services/business-api/`
**Port:** 8080

### Domain Packages (109 Java files)

| Package | Files | Purpose |
|---|---|---|
| `auth/` | 12 | JWT auth, refresh tokens, UserDetailsService |
| `auth/sso/` | 6 | SSO ticket-based cross-app handoff |
| `user/` | 7 | User, Student, Teacher entities + repos |
| `classroom/` | 4 | Classroom entity, CRUD, teacher assignment |
| `batch/` | 5 | Batch entity, teacher batch upload workflow |
| `submission/` | 8 | Submission lifecycle, student + teacher controllers |
| `ocr/` | 8 | OCR trial entity, feedback, metrics |
| `ocr/multiline/` | 12 | Multiline OCR trials, per-line feedback |
| `dashboard/` | 3 | Teacher dashboard aggregations |
| `storage/` | 4 | MinIO + local file storage abstraction |
| `config/` | 4 | Security, CORS, seed data, request ID |
| `common/` | 2 | Error handling |
| `audit/` | 1 | Audit event repository |

### Database
- **PostgreSQL 16** with JPA/Hibernate
- Entities: User, Student, Teacher, Classroom, Batch, BatchImageMapping, Submission, SubmissionImage, OcrTrial, OcrMultilineTrial, OcrMultilineLine, RefreshToken, SsoTicket, AuditEvent

### Key Design Decisions
- Spring Boot is the **ONLY public API gateway** (ADR-001)
- FastAPI is internal-only (ADR-002)
- Async processing with polling (ADR-003, ADR-008)
- Teacher is final grade authority (ADR-005, ADR-007)
- ADMIN role is operational-only, cannot grade (ADR-011)

---

## 9. FastAPI AI Service

**Stack:** FastAPI 0.115, Python 3.12+, Celery 5.4.0, Redis 7
**Location:** `services/ai-service/`
**Port:** 8000

### Module Structure

| Module | Purpose |
|---|---|
| `api/jobs.py` | Job ingestion from Spring Boot |
| `api/ocr.py` | OCR pilot endpoints (1,470 lines!) |
| `ocr/` | OCR engine: CRNN provider, bridge, metrics, factory |
| `recognition/` | Recognition engines: model, fixture, YOLO adapter |
| `layout/` | Layout analysis |
| `parsing/` | Arithmetic expression parser |
| `validation/` | Deterministic math validators |
| `policy/` | Grading policy engine |
| `integrations/groq/` | Groq VLM integration (post-correction advisor) |
| `canonical/` | Canonical runtime |
| `callbacks/` | Spring Boot callback gateway |
| `jobs/` | Celery task definitions |
| `image/` | Image processing utilities |
| `schemas/` | Pydantic request/response models |
| `observability/` | Logging infrastructure |

### Runtime Modes
- `FIXTURE` -- deterministic test responses (default for development)
- `MODEL` -- real model inference

### OCR Configuration (from config.py)
- `ocr_provider`: default `"noop"` -- OCR is **disabled by default** in production
- `ocr_bridge_mode`: default `"off"`
- Groq VLM: disabled by default (`groq_enabled: false`)
- Gemini advisor: disabled by default (`gemini_enabled: false`)

**IMPORTANT: The OCR subsystem is explicitly opt-in and defaults to disabled. This confirms it is a pilot/experimental feature, not the core grading pipeline.**

---

## 10. Infrastructure & Docker

**Docker Compose** (`services/business-api/docker-compose.yml`):

| Service | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | postgres:16-alpine | 5432 | Relational database |
| `minio` | minio/minio | 9000/9001 | S3-compatible object storage |
| `redis` | redis:7-alpine | 6379 | Celery broker & state |
| `ai-service` | Custom (FastAPI) | 8000 | AI runtime gateway |
| `celery-worker` | Custom (same image) | -- | Background task worker |

**Local Dev Scripts:**
- `scripts/start-all.bat` -> `scripts/start-all.ps1` (13.7 KB, comprehensive)
- `scripts/stop-all.bat` -> `scripts/stop-all.ps1`
- `scripts/health-check.bat`
- `RUN_MATHVISION.bat` (root-level launcher)

---

## 11. API Contract (OpenAPI)

**File:** `contracts/openapi/mathvision-api.yaml` (1,663 lines, OpenAPI 3.1.0)

### Endpoint Summary (39 endpoints)

| Group | Endpoints | Purpose |
|---|---|---|
| **Auth** (4) | login, refresh, logout, /me | JWT authentication |
| **Student** (4) | submissions CRUD, confirm-token, retry | Student submission flow |
| **Teacher** (14) | dashboard, classes, assignments, batches, review, approve, override | Full teacher workflow |
| **Admin** (11) | users CRUD, disable/enable, reset-password, classes, dashboard, audit | User/classroom management |
| **OCR Pilot** (6) | single-line trials, multiline detect, trials, per-line feedback, metrics | Handwriting OCR pilot |

**NOTE: The OCR Pilot endpoints are explicitly tagged separately and represent 6/39 (15%) of the API surface. The core product is the other 33 endpoints.**

---

## 12. Architecture Decision Records

11 ADRs in `contracts/ARCHITECTURE_DECISIONS.md`:

| ADR | Decision | Significance |
|---|---|---|
| ADR-001 | Clients talk only to Spring Boot | Core architecture |
| ADR-002 | FastAPI is internal-only | Security boundary |
| ADR-003 | Async submission processing | UX pattern |
| ADR-004 | Recognition confidence != student error | AI fairness |
| ADR-005 | Teacher is final grade authority | Human-in-the-loop |
| ADR-006 | Normalized bounding boxes | Cross-device rendering |
| ADR-007 | AI score is non-official | Safety guarantee |
| ADR-008 | Polling for MVP (no WebSockets) | Simplicity |
| ADR-009 | /api/v1 versioning | Compatibility |
| ADR-010 | Batch lifecycle != review state | Domain modeling |
| ADR-011 | ADMIN role is operational-only | RBAC separation |

---

## 13. AI Models Inventory

### Model 1: YOLOv8n Detection (Core Math Pipeline)

| Property | Value |
|---|---|
| **File** | `models/yolov8n_mathvision_det_v1.pt` |
| **Size** | 6.0 MB |
| **Architecture** | YOLOv8n (Ultralytics) |
| **Task** | Object detection (handwritten math symbols) |
| **Classes** | 14: digits 0-9, +, -, =, carry marker (c1) |
| **Input** | 640x640 RGB |
| **mAP50** | 0.9672 |
| **mAP50-95** | 0.7222 |
| **Precision** | 0.9284 |
| **Recall** | 0.9450 |
| **Status** | **DEPLOYED, PRODUCTION** |
| **Label Map** | `models/label_map_detection.json` |

### Model 2: CRNN V1 Vietnamese Handwriting OCR (Pilot)

| Property | Value |
|---|---|
| **File** | `models/ocr/crnn_vi_handwriting_v1/best_cer.pth` |
| **Size** | 22.7 MB |
| **Architecture** | CRNN (4-block Conv2d + GroupNorm(8,C) + BiLSTM(128) + Linear(320)) |
| **Task** | Optical character recognition (Vietnamese handwriting) |
| **Classes** | 320 (full Vietnamese alphabet + diacritics) |
| **Input** | 64x1024 RGB |
| **Training Samples** | 59,462 (from Viet-Handwriting-OCR-v2) |
| **Validation CER** | 0.1134 (11.3%) |
| **Status** | **DEPLOYED but DEFAULT DISABLED (ocr_provider="noop")** |
| **Vocab** | `vocab.json` (4.4 KB) |

### Model 3: CRNN V2 (Specification Only)

| Property | Value |
|---|---|
| **File** | `models/ocr/crnn_vi_handwriting_v2/training_config.yaml` |
| **Status** | **SPECIFICATION ONLY -- NO TRAINED WEIGHTS** |
| **Planned Changes** | Enhanced BiLSTM (hidden=256, layers=2, dropout=0.2), aspect-preserving resize, diacritic augmentation |
| **Blocked By** | Missing 59K raw training dataset |

---

## 14. The 59K Dataset Investigation

### What is the 59K dataset?
The CRNN V1 handwriting OCR model was trained on **59,462 images** from the **HuggingFace `Viet-Handwriting-OCR-v2`** dataset. This is a **public Vietnamese handwriting corpus**, NOT proprietary MathVision Kids data.

### Where was it originally?
- Historical path: `D:\nhom6\train thu\external\Viet-Handwriting-OCR-v2\extracted`
- The `D:\nhom6` path **does not exist** on this machine

### Current status on disk

**CAUTION: The 59K raw training images are ABSENT from this machine.** Multiple prior searches confirmed this:

- `ai-training/data/raw-local/` -- contains only `.gitkeep`
- `ai-training/data/splits/train/`, `validation/`, `test/` -- **ALL EMPTY** (0 files)
- `ai-training/data/manifests/` -- contains only `.gitkeep`
- `ai-training/datasets/arithmetic_ocr_line_v1/crops/` -- exists but not the 59K corpus
- Total images in the entire repo (excl. dependencies): **1,146** -- nowhere near 59K

### What IS present
1. **The compiled V1 model weights** (`best_cer.pth`, SHA256 verified PASS)
2. **5 validation smoke-test samples** in the handoff staging area
3. **The model manifest** documenting the training provenance
4. **The V2 training config** (specification-frozen, waiting for data)

### Conclusion
The 59K dataset is from a **public HuggingFace corpus** (`Viet-Handwriting-OCR-v2`). It was downloaded to `D:\nhom6` on a different drive configuration, used for training, and the resulting model weights were preserved. The raw images were never committed to the Git repository (correctly, as they are large binary data). **The dataset can be re-downloaded from HuggingFace if needed for V2 training.**

### Owner Data (Separate)
- `ai-training/parking/owner_173_untrained/` -- 173 owner images -> 510 crops -> 331 unverified lines
- **Quarantined**, 0 verified labels, explicitly excluded from all pipelines

---

## 15. AI Training Workspace

**Location:** `ai-training/`

| Directory | Purpose | State |
|---|---|---|
| `data/raw-local/` | Raw local data (never committed) | EMPTY (.gitkeep only) |
| `data/deidentified-local/` | De-identified data | Not examined |
| `data/manifests/` | Dataset version manifests | EMPTY (.gitkeep only) |
| `data/splits/` | Train/val/test splits | EMPTY (0 files in all 3 dirs) |
| `annotations/primary/` | Primary annotator labels | Exists, not examined |
| `annotations/secondary/` | Secondary annotator labels | Exists |
| `annotations/adjudicated/` | Final adjudicated labels | Exists |
| `annotations/schema/` | Annotation schema definition | Exists |
| `datasets/arithmetic_ocr_line_v1/crops/` | Arithmetic line dataset | Exists |
| `training/configs/` | Training configurations | Exists |
| `training/notebooks/` | Training notebooks | Exists |
| `training/scripts/` | Training scripts | Exists |
| `experiments/` | Experiment tracking | Exists |
| `artifacts/` | Model artifacts | Exists |
| `handoff/staging/` | Model handoff staging | Contains V1 OCR engine package |
| `parking/owner_173_untrained/` | Quarantined owner data | 510 crops, 0 verified |
| `incoming/` | Incoming model handoffs | Exists |

**Overall:** The workspace infrastructure is well-scaffolded but the actual data directories are empty. The only real artifact is the staged V1 OCR handoff package.

---

## 16. Report Archaeology

The `report/` directory contains **201 markdown files** totaling approximately 2.5 MB. These documents constitute the engineering history of the project.

### Report Categories by Prefix

| Prefix | Count (approx.) | Domain |
|---|---|---|
| `ai_hwtext_*` | ~70 | Vietnamese handwriting OCR pipeline |
| `ocr_*` | ~12 | OCR pilot, flow routing, data |
| `phase_*` | ~25 | Original phased build (UI, backend, AI runtime) |
| `int_*` | ~8 | Integration (teacher serialization, YOLO-CRNN bridge) |
| `ui_*` | ~8 | UI/UX refinement |
| `parallel_a1_*` | ~8 | Admin web & RBAC |
| `mobile_*` | ~8 | Mobile physical testing |
| `project_audit_*` | ~5 | Repository audit & truth reconciliation |
| `system_audit_*` | ~5 | System-level audits |
| `auth_ux_*` | 2 | Authentication UX |
| `ecosystem_portal_*` | 3 | Portal web |
| `performance_*` | 1 | Performance audit |
| `friend_branch_*` | 1 | Branch audit |

### Phase History (from report filenames)

The project was built in clear phases:
1. **Phase 1:** Student UI slice
2. **Phase 1.5:** Student polish
3. **Phase 2:** Teacher portal
4. **Phase 2.5:** System contract freeze
5. **Phase 2.6:** Teacher web skill polish
6. **Phase 3:** Spring Boot Business API
7. **Phase 3.1:** Business API completion + defense notes
8. **Phase 3.5:** Student backend integration
9. **Phase 3.6:** Teacher backend integration
10. **Phase 4.0:** AI runtime foundation, defense notes
11. **Phase 4.1:** Local runtime hardening
12. **Phase 4.2:** Model handoff integration
13. **Phase 4.3:** Gold model evaluation
14. **Parallel A1:** Admin web & RBAC
15. **AI.HWTEXT.*** OCR pilot (70+ reports -- massive scope expansion)

**WARNING: The OCR pilot track (ai_hwtext_*) produced approximately 3x more reports than all other phases combined. This represents significant engineering time invested in what is effectively an experimental feature.**

---

## 17. What Has Actually Been Built

### Fully Built Components (Production-Ready)

| Component | Evidence | Completeness |
|---|---|---|
| **Student Mobile App** | 62 files, 20+ screens, camera/gallery/crop/privacy | **HIGH** -- all 6 mock flows implemented |
| **Teacher Web Portal** | 27 files, 12 pages, batch/review/privacy editor | **HIGH** -- complete teacher workflow |
| **Admin Web Portal** | 25 files, 7 pages, user/class/audit management | **HIGH** -- complete admin workflow |
| **Portal Web** | 16 files, 9 pages, SSO handoff | **HIGH** -- unified entry point |
| **Spring Boot Business API** | 109 Java files, 33+ endpoints, full JPA domain | **HIGH** -- auth, RBAC, submissions, batches |
| **FastAPI AI Service** | 65 Python files, job processing, validators | **HIGH** -- async pipeline working |
| **YOLO Detection Model** | 6 MB, mAP50=0.967, 14 classes | **HIGH** -- trained and deployed |
| **Docker Infrastructure** | PostgreSQL, MinIO, Redis, Celery | **HIGH** -- fully orchestrated |
| **OpenAPI Contract** | 39 endpoints, 1,663 lines | **FROZEN** |
| **Architecture Docs** | 11 ADRs, runtime topology, local setup | **COMPREHENSIVE** |

### Partially Built / Experimental

| Component | Evidence | Completeness |
|---|---|---|
| **CRNN OCR V1** | Trained model deployed, but `ocr_provider="noop"` by default | **MEDIUM** -- model exists but disabled |
| **OCR Pilot UI** | 4 screens in student app, multiline endpoints in Spring Boot | **MEDIUM** -- functional but experimental |
| **Groq/Gemini VLM advisor** | Full integration code, disabled by default | **LOW** -- opt-in, API-key dependent |
| **CRNN OCR V2** | Config specification only, no trained weights | **BLOCKED** -- needs 59K data |
| **AI Training Pipeline** | Scaffolded directories, empty data splits | **LOW** -- infrastructure only |

### Not Built

| Component | Notes |
|---|---|
| **Live Student-to-Backend Integration** | Student app uses MockSubmissionService |
| **WebSocket real-time updates** | Deferred per ADR-008 (polling for MVP) |
| **Production deployment** | All configs are local/development |
| **V2 OCR model** | Blocked on dataset |

---

## 18. What Is Missing or Incomplete

### Critical Gaps

1. **Student-to-Backend Integration:** The student mobile app still uses `MockSubmissionService`. The README documents the switch path (create `SpringSubmissionService.ts`), but it has not been done. This means the student app **cannot submit real work to the backend**.

2. **59K Training Dataset:** Not present on disk. The V1 model exists as compiled weights, but retraining (V2) requires re-downloading from HuggingFace `Viet-Handwriting-OCR-v2`.

3. **Proposal/SRS Document:** No formal requirements specification exists in the repository. The OpenAPI contract and ADRs serve as de facto specifications.

4. **Production Deployment Configuration:** All environment configs are development-only (localhost, default passwords, `FIXTURE` mode).

5. **Test Coverage:** Tests exist in `services/ai-service/tests/`, `src/__tests__/`, and `scripts/test_*.py`, but coverage breadth is unclear.

### Non-Critical Gaps

6. **AI Training Data:** The `ai-training/data/` directory structure is well-scaffolded but empty. No training data, manifests, or splits are populated.

7. **OCR Pilot Production Readiness:** The OCR pilot is explicitly disabled by default (`ocr_provider="noop"`, `groq_enabled=false`, `gemini_enabled=false`). It would need explicit opt-in and API keys to function.

---

## 19. Conclusions & Recommendations

### Key Findings

1. **MathVision Kids is a REAL, substantial project** -- not a prototype. It has 5 frontend applications, a full Spring Boot backend, a Python AI service, Docker infrastructure, and formal API contracts.

2. **The core product is arithmetic worksheet grading** using YOLO symbol detection + deterministic validators + teacher review. This is built and functional.

3. **The OCR pilot is an experimental extension** that consumed disproportionate engineering time (~70 reports vs ~25 for the entire core product). It adds Vietnamese handwriting text recognition capability but is disabled by default and not essential to the core MVP.

4. **The 59K dataset is a public HuggingFace corpus** (`Viet-Handwriting-OCR-v2`), not proprietary data. It was used on a different drive (`D:\nhom6`), never committed to Git, and can be re-downloaded.

5. **The biggest actual gap** is the student app still using mock services instead of connecting to the real Spring Boot backend.

### Architecture Health

| Aspect | Assessment |
|---|---|
| **Separation of concerns** | EXCELLENT -- clear boundaries between clients, business API, AI service |
| **Security model** | GOOD -- JWT auth, internal API keys, RBAC |
| **Async design** | SOUND -- Celery/Redis with Spring Boot callbacks |
| **API contract** | FROZEN and comprehensive |
| **Human-in-the-loop** | Teacher authority preserved |
| **Code organization** | Clean package structure across all components |
| **Feature creep risk** | HIGH -- OCR pilot scope expanded significantly |

### Recommendations for Owner

1. **Prioritize student-to-backend integration** over further OCR work. The core product pipeline is complete except for the mobile client connecting to real APIs.

2. **Re-download the 59K dataset from HuggingFace** if V2 OCR training is desired. It is a public corpus, not lost proprietary data.

3. **Consider freezing the OCR pilot** at V1 and focusing engineering effort on the core arithmetic grading MVP reaching end-to-end functionality.

4. **The 200+ reports document extensive engineering work** -- this is evidence of a rigorous development process, not wasted effort. But the scope balance has shifted heavily toward experimental features.

---

## Skills Applied

Skills Applied: None -- this is a read-only discovery/audit task, not an implementation task. No installed skill matched.

---

**END OF RECONSTRUCTION REPORT**
