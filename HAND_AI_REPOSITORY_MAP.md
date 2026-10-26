# HandAI — Repository Map & Architectural File Breakdown
## Complete Inventory of HandAI Code Artifacts

---

## 1. Directory Tree & Structural Overview

The HandAI module resides across dedicated directories within the `MathVisionKid` repository. Below is the structural layout isolating HandAI components from unrelated modules:

```
MathVisionKid/
│
├── apps/
│   └── student-mobile/                          # Frontend Mobile Application (React Native / Expo)
│       └── src/
│           ├── app/
│           │   ├── handai-analytics.tsx         # [HandAI] Global Research Analytics Dashboard Screen
│           │   ├── handai-trial-analytics.tsx   # [HandAI] Per-Trial Real-Time Evaluation Dashboard Screen
│           │   ├── handai-review.tsx            # [HandAI] Line Confirmation & Correction Interface
│           │   └── handai-camera.tsx            # [HandAI] Handwriting Capture Screen
│           ├── services/
│           │   ├── analytics/
│           │   │   └── handAiAnalyticsStore.ts  # [HandAI] Core Analytics Store, Algorithms & Exporters
│           │   └── api/
│           │       ├── handAiGuestApi.ts        # [HandAI] Guest Demonstration Mode HTTP Client
│           │       └── ocrApi.ts                # [HandAI] Base OCR API Client
│           └── __tests__/
│               └── handAiAnalyticsAndFlow.test.ts # [HandAI] 168+ Automated Unit & Integration Tests
│
├── backend/
│   └── business-api/                            # Backend Business Layer (Spring Boot 3.3 / Java 21)
│       ├── src/main/java/com/mathvisionkids/api/ocr/
│       │   ├── multiline/                       # [HandAI] Core Multi-Line Handwriting Package
│       │   │   ├── HandAiOcrController.java    # Public / Guest Endpoints (/api/v1/handai/ocr/multiline/*)
│       │   │   ├── HandAiHealthController.java # Health & Readiness Endpoint
│       │   │   ├── OcrMultilineController.java  # Authenticated OCR Controller
│       │   │   ├── OcrMultilineService.java     # Orchestration, MinIO S3 & AI Forwarding Service
│       │   │   ├── OcrMultilineTrial.java       # JPA Entity: Multi-line Scan Session
│       │   │   ├── OcrMultilineLine.java        # JPA Entity: Individual Line Crop & Predictions
│       │   │   ├── OcrMultilineTrialRepository.java # Spring Data JPA Trial Repository
│       │   │   ├── OcrMultilineLineRepository.java  # Spring Data JPA Line Repository
│       │   │   ├── OcrDatasetVersion.java       # JPA Entity: Dataset Version Provenance
│       │   │   ├── OcrModelExperiment.java      # JPA Entity: Model Experiment Provenance
│       │   │   ├── OcrErrorRecord.java          # JPA Entity: Error Taxonomy Log
│       │   │   ├── OcrAiImpactMetric.java       # JPA Entity: AI Contribution & Rescue Rate
│       │   │   ├── OcrConfidenceCalibration.java # JPA Entity: Confidence Reliability Bins
│       │   │   ├── OcrErrorRootCause.java       # JPA Entity: Error Root Cause Failures
│       │   │   └── dto/                         # DTOs: LineBoxDto, MultilineDetectResponse, etc.
│       │   └── OcrPilotService.java             # Legacy Single-Line OCR Orchestrator
│       └── src/main/resources/db/migration/     # Database Schema Evolution (Flyway)
│           ├── V11__create_ocr_multiline_tables.sql            # Base HandAI Trials & Lines Tables
│           ├── V14__add_handai_research_analytics_tables.sql   # Research Provenance & Dataset Tracking
│           └── V15__add_handai_phase3_validation_tables.sql    # AI Impact, Calibration & Root Cause Tables
│
├── ai/
│   └── handoff/
│       └── staging/
│           └── ocr_engine_handoff_final/        # Core Offline / Internal CRNN Engine (PyTorch)
│               └── ocr_engine/
│                   ├── __init__.py              # Export module for predict_text & predict_batch
│                   ├── model.py                 # PyTorch CRNN Architecture (CNN + BiLSTM + CTC)
│                   ├── predict.py               # Preprocessing, Micro-batching & CTC Greedy Decoder
│                   ├── test_predict.py          # Unit test verification suite for CRNN engine
│                   ├── vocab.json               # 320-Token Vocabulary (Characters, Tones, Math)
│                   └── best_cer.pth             # Production Checkpoint (5.96M params, SHA256 verified)
│
├── contracts/
│   └── ai/
│       └── ai-contract.md                       # Contract between Spring Boot and AI Inference Engine
│
└── infra/                                       # [Shared Infrastructure] Container & Runtime Orchestration
    ├── docker/
    │   └── docker-compose.yml                   # PostgreSQL 16, MinIO S3, Redis 7
    └── local-runtime/                           # Runtime Process PIDs and Local Logs
```

---

## 2. Frontend Layer (`apps/student-mobile/`)

| File Path | Component Type | Responsibility |
|---|---|---|
| `src/app/handai-analytics.tsx` | UI Screen | **Global Research Analytics Dashboard**: Displays the Active Model Experiment Card, Dataset Information & Quality Card, 7-column Model Experiment Tracking Table, AI Contribution Funnel, Confidence Reliability Gauges, and 1-Click Research Report Export. |
| `src/app/handai-trial-analytics.tsx` | UI Screen | **Per-Trial Evaluation Dashboard**: Displays immediate feedback for a single document scan, including the 8-metric Recognition Quality Report (LineAcc, CharAcc, CER, WordAcc, WER, RawAcc, FinalAcc, AIGain), Error Summary Card, and Line-by-line Ground Truth review. |
| `src/app/handai-review.tsx` | UI Screen | **Line Confirmation & Correction Interface**: Allows users or educators to review bounding boxes, toggle between Raw OCR, AI Suggestion, or Manual Correction, and input ground truth. |
| `src/app/handai-camera.tsx` | UI Screen | **Handwriting Capture Screen**: Camera viewfinder and image picker with guided aspect ratio overlay and contrast guide for primary notebook pages. |
| `src/services/analytics/handAiAnalyticsStore.ts` | State & Logic | **Central Analytics Store (Zustand)**: Implements dynamic programming Levenshtein distance, Word Error Rate (WER) edit distance, Unicode NFD tone decomposition, error taxonomy classification, dataset/model provenance models, and JSON/CSV/Markdown export utilities. |
| `src/services/api/handAiGuestApi.ts` | HTTP Client | **Guest API Gateway**: Provides unauthenticated access to HandAI detection and trial recognition endpoints (`/api/v1/handai/ocr/multiline/*`) for defense demonstrations without login friction. |
| `src/services/api/ocrApi.ts` | HTTP Client | **Base OCR Client**: Communicates with backend OCR endpoints for authenticated users. |
| `src/__tests__/handAiAnalyticsAndFlow.test.ts` | Automated Tests | **168 Unit & Integration Tests**: Validates CER/WER calculations, zero-division safeguards, tone error detection, lookalike confusion matrices, and report export schemas. |

---

## 3. Backend Business API (`backend/business-api/`)

| File Path | Component Type | Responsibility |
|---|---|---|
| `HandAiOcrController.java` | REST Controller | **Public Demonstration Controller**: Exposes `/api/v1/handai/ocr/multiline/detect` and `/api/v1/handai/ocr/multiline/recognize` with guest mode authorization, rate limiting, and size validation (10MB). |
| `HandAiHealthController.java` | REST Controller | **Health Check Controller**: Exposes `/api/v1/handai/health` for preflight readiness checks. |
| `OcrMultilineController.java` | REST Controller | **Authenticated Controller**: Exposes `/api/v1/ocr/multiline/*` for authenticated mobile users. |
| `OcrMultilineService.java` | Service Layer | **Core Business Orchestrator**: Handles multipart image uploads, computes SHA-256 hashes, stores raw pages in MinIO (`ocr-trials/multiline/`), forwards images to FastAPI `/internal/v1/ocr/detect-lines`, slices cropped lines, dispatches to `/internal/v1/ocr/recognize-line`, arbitrates AI suggestions, and persists trial records. |
| `OcrMultilineTrial.java` | JPA Entity | **Trial Persistence**: Maps to table `ocr_multiline_trials`. Stores session metadata, image dimensions, MinIO S3 object keys, and completion status. |
| `OcrMultilineLine.java` | JPA Entity | **Line Persistence**: Maps to table `ocr_multiline_lines`. Stores line coordinates $(x, y, w, h)$, raw OCR text, AI suggestion, final text, confidence, model metadata, and provenance tags. |
| `OcrDatasetVersion.java` | JPA Entity | **Dataset Registry**: Maps to table `ocr_dataset_versions`. Stores sample count, grade distributions, duplicate rate, and validation status. |
| `OcrModelExperiment.java` | JPA Entity | **Experiment Registry**: Maps to table `ocr_model_experiments`. Stores model name, checkpoint SHA, hyperparameters, and benchmark metrics. |
| `OcrErrorRecord.java` | JPA Entity | **Error Taxonomy Log**: Maps to table `ocr_error_records`. Stores character-level and line-level error classifications. |
| `OcrAiImpactMetric.java` | JPA Entity | **AI Contribution Log**: Maps to table `ocr_ai_impact_metrics`. Stores raw accuracy, final accuracy, accuracy gain, and error rescue rates. |
| `OcrConfidenceCalibration.java` | JPA Entity | **Confidence Calibration**: Maps to table `ocr_confidence_calibrations`. Stores empirical accuracy across 5 confidence intervals. |
| `OcrErrorRootCause.java` | JPA Entity | **Root Cause Audit**: Maps to table `ocr_error_root_causes`. Stores error categorization into 4 architectural failure modes. |

---

## 4. Database Schema Migrations (`backend/.../db/migration/`)

| Migration File | Target Database | Schema Responsibility |
|---|---|---|
| `V11__create_ocr_multiline_tables.sql` | PostgreSQL 16 | Creates base tables: `ocr_multiline_trials` (session metadata, image keys) and `ocr_multiline_lines` (bounding box coordinates, OCR texts, decision source). |
| `V14__add_handai_research_analytics_tables.sql` | PostgreSQL 16 | Creates research tracking tables: `ocr_dataset_versions`, `ocr_model_experiments`, and `ocr_error_records`. Adds foreign keys linking trials to dataset and model versions. |
| `V15__add_handai_phase3_validation_tables.sql` | PostgreSQL 16 | Creates validation tables: `ocr_ai_impact_metrics`, `ocr_confidence_calibrations`, `ocr_error_root_causes`. Extends dataset versions with grade and handwriting characteristics. |

---

## 5. AI Engine & Deep Learning Components (`ai/.../ocr_engine/`)

| File Path | Technology | Responsibility |
|---|---|---|
| `model.py` | PyTorch `nn.Module` | **CRNN Architecture**: Defines the 4-block Conv2d + GroupNorm + MaxPool2d visual extractor, Bidirectional LSTM (hidden size 128), and linear output layer for CTC decoding. |
| `predict.py` | PyTorch / Pillow | **Inference Engine**: Preprocesses input line images to RGB $[3 \times 64 \times 1024]$, applies ImageNet normalization, runs forward inference, and applies greedy CTC decoding. |
| `test_predict.py` | PyTest / PyTorch | **CRNN Test Suite**: Verifies prediction repeatability, greedy CTC collapse rules, and blank token handling. |
| `best_cer.pth` | PyTorch Weights | **Trained Model Checkpoint**: Binary weights file (5,962,560 parameters, SHA-256: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`). |
| `vocab.json` | JSON Dictionary | **Character Vocabulary**: 320 token mappings (0: `<blank>`, 1..318: Vietnamese letters, tone combinations, numerals, punctuation, math symbols, 319: `<unk>`). |

---

## 6. Shared Infrastructure Components

The following repository components provide shared environmental capabilities and are classified as **Shared Infrastructure**:

| Component | Physical Location | Shared Capability |
|---|---|---|
| **Docker Compose** | `infra/docker/docker-compose.yml` | Manages container lifecycle for PostgreSQL 16 (`5432`), MinIO (`9000`), and Redis (`6379`). |
| **MinIO S3 Storage** | MinIO Container (`mathvision` bucket) | Object storage used for both HandAI handwriting images and parent system assets. |
| **Database Engine** | PostgreSQL 16 Container | Hosts HandAI tables alongside parent user and authentication tables. |
| **System Diagnostics** | `tools/diagnostics/check_runtime.py` | Python diagnostic script checking network ports, DB connections, and process health. |
| **Local Launcher** | `RUN_MATHVISION.bat` & `scripts/dev/start-all.ps1` | Orchestrates startup of infrastructure, backend, AI service, and frontend bundler. |
