# HandAI — Technology Stack & Framework Inventory
## Technical Components, Libraries, Frameworks & Tooling

---

## 1. Complete Technology Stack Matrix

| Architectural Layer | Technology / Library | Version | Role in HandAI | Shared / Independent |
|---|---|---|---|---|
| **Mobile Client** | React Native | `0.74.x` | Cross-platform mobile UI engine | HandAI Independent |
| **Mobile Runtime** | Expo SDK | `51.x` | Native tooling, camera, file system, sharing | HandAI Independent |
| **Language (Client)** | TypeScript | `5.3.x` | Strict typing for evaluation stores and DTOs | HandAI Independent |
| **Client State** | Zustand | `4.5.x` | High-performance state management & persistence | HandAI Independent |
| **Client Icons** | lucide-react-native | `0.383.x` | Clean vector iconography for evaluation UI | HandAI Independent |
| **Client Testing** | Jest / React Native Testing | `29.x` | 168 automated unit & integration tests | HandAI Independent |
| **Backend Framework** | Spring Boot | `3.3.0` | Enterprise REST gateway and orchestration | Shared Infrastructure |
| **Language (Backend)**| Java (JDK) | `21` (LTS) | Modern virtual threads and typed processing | Shared Infrastructure |
| **ORM & Data** | Spring Data JPA / Hibernate | `6.5.x` | Relational persistence & entity mapping | HandAI Independent Tables |
| **Database Migrations**| Flyway | `10.x` | Version-controlled DDL scripts (`V11, V14, V15`)| HandAI Dedicated Scripts |
| **JSON Serialization** | Jackson Databind | `2.17.x` | DTO and JSON export serialization | Shared Infrastructure |
| **Object Storage API** | MinIO Java SDK / S3 Client | `8.5.x` | Storage of full pages and line crop slices | Shared Infrastructure |
| **AI Inference API** | FastAPI / Uvicorn | `0.110.x` | Asynchronous REST service for line detection | HandAI Independent |
| **Language (AI)** | Python | `3.10` – `3.13` | Deep learning, computer vision & scripting | HandAI Independent |
| **Deep Learning** | PyTorch | `2.3.x` | Convolutional Recurrent Neural Network (CRNN) | HandAI Independent |
| **Vision Transforms** | Torchvision | `0.18.x` | Tensor normalization and image resizing | HandAI Independent |
| **Computer Vision** | OpenCV (`opencv-python`) | `4.9.x` | Morphological line segmentation & binarization | HandAI Independent |
| **Image Processing** | Pillow (PIL) | `10.3.x` | Raw image format decoding and conversion | HandAI Independent |
| **Scientific Math** | NumPy | `1.26.x` | Array operations & projection profiles | HandAI Independent |
| **LLM Provider 1** | Groq Cloud API | Llama-3.3-70b | Primary contextual correction model | HandAI Independent |
| **LLM Provider 2** | Google Gemini API | Gemini-4B/Flash | Secondary fallback & arbitration consensus | HandAI Independent |
| **Relational Database**| PostgreSQL | `16-alpine` | ACID storage of trials, lines, experiments | Shared Infrastructure |
| **Object Storage** | MinIO | `RELEASE.2024`| S3-compatible image blob store | Shared Infrastructure |
| **Container Engine** | Docker Compose | `v2.x` | Orchestrates PostgreSQL, MinIO, and Redis | Shared Infrastructure |

---

## 2. Layer-by-Layer Architectural Responsibilities

### 2.1 Mobile Application Stack (`apps/student-mobile/`)
- **Expo Camera (`expo-camera`):** Captures high-resolution raw notebook photographs.
- **Expo FileSystem (`expo-file-system`):** Manages local temporary image caches and ensures URI stability.
- **Expo Sharing (`expo-sharing`):** Powers native mobile share-sheet exports for generated Markdown, JSON, and CSV evaluation reports.
- **Zustand (`handAiAnalyticsStore.ts`):** 
  - Tracks live session state (`currentTrial`, `lineMetrics`, `globalData`).
  - Executes dynamic programming Levenshtein distance for CER.
  - Executes token-level Levenshtein distance for Word Error Rate (WER).
  - Performs Unicode Normalization Form D (NFD) regex filtering for tone error detection.
  - Persists multi-session evaluation history locally across app reboots.

### 2.2 Backend Business API Stack (`backend/business-api/`)
- **Spring Boot 3.3 / Java 21:**
  - `HandAiOcrController`: Exposes unauthenticated demonstration endpoints (`/api/v1/handai/ocr/multiline/*`) with rate-limiting and file size validation.
  - `OcrMultilineService`: Orchestrates the multipart ingestion pipeline, dispatches images to the FastAPI AI service, slices sub-images in memory via `BufferedImage`, computes SHA-256 hashes, and handles database persistence.
  - `RestTemplate`: Connects backend services via HTTP with internal security headers (`X-Internal-API-Key`).
- **Flyway Migrations:**
  - `V11`: Defines `ocr_multiline_trials` and `ocr_multiline_lines`.
  - `V14`: Defines `ocr_dataset_versions`, `ocr_model_experiments`, and `ocr_error_records`.
  - `V15`: Defines `ocr_ai_impact_metrics`, `ocr_confidence_calibrations`, and `ocr_error_root_causes`.

### 2.3 AI & Computer Vision Stack (`ai/.../ocr_engine/`)
- **PyTorch 2.3+ (`torch`, `torch.nn`):**
  - Defines the 5.96M parameter CRNN architecture (`model.py`).
  - Executes greedy CTC decoding (`predict.py`).
  - Supports both CUDA GPU acceleration (`OCR_DEVICE=cuda`) and multi-threaded CPU inference (`OCR_DEVICE=cpu`).
- **OpenCV (`cv2`):**
  - CLAHE contrast enhancement for low-light camera captures.
  - Otsu binarization and horizontal projection profiling (HPP).
  - Rectangular morphological structuring elements for line grouping and satellite diacritic consolidation.
- **Large Language Models (Cloud APIs):**
  - **Groq Cloud API (`llama-3.3-70b-versatile`):** High-speed LLM inference (<400ms) for primary Vietnamese diacritic restoration.
  - **Google Gemini API (`gemini-2.5-flash` / `gemini-4b-heuristic`):** Multi-consensus validation to arbitrate ambiguous cursive substitutions.

---

## 3. Shared vs. Dedicated Boundary Declaration

In compliance with strict architectural boundary principles, components are categorized as:

### A. Dedicated HandAI Components (100% HandAI Domain)
- All frontend UI code under `apps/student-mobile/src/app/handai-*.tsx`.
- All analytics algorithms and stores in `apps/student-mobile/src/services/analytics/`.
- All controller and service files under `backend/.../ocr/multiline/`.
- Flyway database migration scripts `V11`, `V14`, and `V15`.
- PyTorch CRNN model checkpoint `best_cer.pth` and vocabulary `vocab.json`.
- OpenCV line segmentation scripts and API handlers.

### B. Shared Infrastructure (Supporting Monorepo Services)
- PostgreSQL 16 database server (running on port `5432`).
- MinIO S3 object storage server (running on port `9000`).
- Spring Boot web server application container (running on port `8080`).
- Docker Compose configuration (`infra/docker/docker-compose.yml`).
- Developer local launcher script (`scripts/dev/start-all.ps1`).
