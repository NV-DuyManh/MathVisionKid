# HandAI — Vietnamese Primary School Handwriting Recognition System
## Project Overview & Mission Statement

---

## 1. Executive Summary

**HandAI** is a specialized, research-grade Artificial Intelligence and Computer Vision system designed specifically for the automated recognition, transcription, and pedagogical evaluation of Vietnamese handwritten text produced by primary school students (Grades 1 to 5). 

Operating within the Ministry of Education & Training (MOET) primary school penmanship curriculum standards, HandAI addresses the unique challenges of Vietnamese handwriting—including complex diacritical tone markings, non-standard cursive ligatures, varying letter stroke widths, and child motor skill variance.

HandAI combines classical morphological computer vision for horizontal line segmentation, a deep Convolutional Recurrent Neural Network (CRNN) with Connectionist Temporal Classification (CTC) for acoustic/visual line transcription, an automated multi-consensus Large Language Model (LLM) post-correction arbitration engine, and an enterprise Big Data analytics platform that tracks recognition quality, error taxonomies, and experiment provenance.

```
+----------------------------------------------------------------------------------------------------+
|                                      HandAI System Overview                                        |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   +-----------------------+     +-----------------------+     +--------------------------------+   |
|   |   Student Mobile UI   |     |   Spring Boot API     |     |   FastAPI AI Service           |   |
|   |  - Camera capture     | --> |  - Guest Demo Auth    | --> |  - OpenCV Line Segmentation    |   |
|   |  - Line box preview   |     |  - S3 Object Storage  |     |  - PyTorch CRNN (best_cer.pth) |   |
|   |  - Real-time Analytics|     |  - Relational Schema  |     |  - AI Post-Correction          |   |
|   +-----------------------+     +-----------------------+     +--------------------------------+   |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Educational & Technical Problem Statement

### 2.1 The Challenge of Vietnamese Primary Penmanship
Vietnamese is a tonal language using the Latin-based *Quốc Ngữ* script, enriched with:
- **5 Tone Diacritics**: Acute (*sắc* - ´), Grave (*huyền* - `), Hook above (*hỏi* - ̉), Tilde (*ngã* - ˜), and Dot below (*nặng* - ̣).
- **Vowel Modifiers**: Circumflex (*mũ* on `â, ê, ô`), Breve (*trăng* on `ă`), and Horn (*móc* on `ơ, ư`).
- **Consonant Modifiers**: Strikethrough consonant `đ / Đ`.

In primary education (Grades 1–5), students transition from large, blocky, isolated print characters (*chữ in hoa, chữ tập viết lớp 1*) to fluid, slanted, joined cursive scripts (*chữ nghiêng, chữ liền nét*). This creates critical computer vision challenges:
1. **Diacritical Detachment & Floating Accents**: Tone marks frequently detach from their base vowels, hovering between lines or colliding with ascenders/descenders of adjacent rows.
2. **Homologous Glyph Ambiguity**: Visually lookalike handwriting patterns (e.g., `u` vs. `v`, `n` vs. `m`, `s` vs. `x`, `tr` vs. `ch`, `b` vs. `d`, `r` vs. `d`).
3. **Stroke Width & Pressure Variation**: Primary students use varying writing tools (pencils, fountain pens, gel pens) on ruled notebook paper (*vở ô ly*), creating background grid interference and ink bleeding.
4. **Irregular Geometry**: Uneven baseline tilt, irregular word spacing, and curved lines that break conventional OCR assumptions.

### 2.2 Shortcomings of Generic OCR Engines
Standard commercial OCR solutions (such as generic Tesseract, cloud document parsers, or generic Latin character recognizers) perform poorly on Vietnamese primary notebooks because:
- They assume standard typographical fonts or adult handwriting.
- They lack Vietnamese phonotactic language models tailored to MOET primary vocabulary.
- They over-segment detached tone marks into separate, spurious lines or noise artifacts.

---

## 3. HandAI Scope & Capabilities

### 3.1 In-Scope Capabilities
- **Multi-line Handwriting Image Capture**: Uploading or photographing notebook pages with arbitrary orientations and page aspect ratios.
- **Page Geometry & Line Segmentation**: Automated detection of horizontal handwriting rows using OpenCV morphology and projection profile analysis, filtering out grid lines and noise.
- **Line-Level Visual Transcription**: Normalization of image slices to $[3 \times 64 \times 1024]$ and sequential decoding using a 5.96M-parameter CRNN model.
- **Connectionist Temporal Classification (CTC)**: Alignment-free sequence decoding across a 320-class vocabulary containing complete Vietnamese diacritics and primary school math/text tokens.
- **AI Contextual Correction Arbitration**: Dual-model LLM arbitration (Groq Llama-3.3-70b-versatile and Google Gemini-4B) to evaluate whether raw OCR or AI suggestion is pedagogically superior, achieving a 67% error recovery rate and +12.0% net accuracy gain.
- **Pedagogical Error Taxonomy**: Automated classification of discrepancies into 8 categories (Tone Errors, Lookalike Character Confusion, Missing Characters, Extra Characters, Low Image Quality, Segmentation Failures, Word Substitutions) and 4 architectural root causes.
- **Real-time Trial & Global Analytics**: Session-level and longitudinal tracking of Character Error Rate (CER), Word Error Rate (WER), Line Accuracy, Character Accuracy, and Word Accuracy.
- **Research Experiment Tracking**: Bidirectional data provenance linking dataset versions (`HandAI-v1.0` to `v1.2`), model checkpoints (`best_cer.pth`), evaluation sessions, and exportable research reports (JSON, CSV, Academic Markdown).

### 3.2 Explicit Exclusions (Out of Scope)
To ensure academic focus and architectural isolation, the following subsystems are **NOT** part of HandAI:
- **MathVision Arithmetic Expression Solving**: LaTeX math parsing, vertical arithmetic grid column solving, carrying/borrowing validation.
- **Teacher Assignment Grading**: Assignment submission workflows, teacher rubric evaluation, official grading sign-offs.
- **Student Gamification & Math Worksheets**: Math quiz generation, leaderboard points, avatar progression.

---

## 4. Relationship with the MathVisionKid Repository

The HandAI module is hosted within the `MathVisionKid` monorepo. The relationship between HandAI and the rest of the repository is defined as follows:

```
+----------------------------------------------------------------------------------------------------+
|                                    MathVisionKid Monorepo                                          |
|                                                                                                    |
|  +-----------------------------------------------------+  +-------------------------------------+  |
|  |             Shared Infrastructure                   |  |          MathVision Core            |  |
|  |  - PostgreSQL 16 (Port 5432, Flyway V1..V15)        |  |  - Arithmetic Expression Parser     |  |
|  |  - MinIO S3 Object Storage (Port 9000)              |  |  - YOLOv8 Digit/Operator Detector   |  |
|  |  - Redis 7 (Port 6379)                              |  |  - Teacher Grading Portal Web       |  |
|  |  - Docker Compose Runtime Configuration             |  |  - Celery Worker Async Math Jobs    |  |
|  |  - Common JWT Authentication Filter                 |  +-------------------------------------+  |
|  +-----------------------------------------------------+                                           |
|                             │                                                                      |
|                             ▼                                                                      |
|  +-----------------------------------------------------------------------------------------------+  |
|  |                        HandAI: Vietnamese Handwriting Recognition System                      |  |
|  |                                                                                               |  |
|  |  • Mobile App: apps/student-mobile/src/app/handai-*.tsx, handAiAnalyticsStore.ts               |  |
|  |  • Backend API: backend/business-api/.../api/ocr/multiline/ (HandAiOcrController, Service)    |  |
|  |  • Database Migrations: V11, V14, V15 (ocr_multiline_*, ocr_dataset_*, ocr_error_*)          |  |
|  |  • AI Model & Preprocessing: ai/handoff/staging/ocr_engine_handoff_final/ocr_engine/          |  |
|  |  • Model Checkpoint: best_cer.pth (SHA256: a807eaa7...), vocab.json (320 classes)             |  |
|  +-----------------------------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------------------------+
```

### Shared Infrastructure Components
The following modules provide supporting infrastructure for HandAI but are shared with the parent project:
- **PostgreSQL 16**: Relational storage engine hosting HandAI's research analytics tables alongside core users.
- **MinIO S3**: Object store managing raw page scans (`ocr-trials/multiline/`) and isolated line crops (`ocr-trials/multiline/crops/`).
- **Spring Boot 3.3 Gateway**: Dispatches HTTP requests, enforces payload size constraints, and manages database transactions.
- **Unified Local Launcher (`scripts/dev/start-all.ps1`)**: Orchestrates local startup of database, backend, and AI engine.

---

## 5. Summary of System Capabilities

| Capability | Module / Layer | Primary Metric / Output |
|---|---|---|
| **Image Ingestion** | Spring Boot / MinIO | SHA-256 deduplicated image store |
| **Line Detection** | FastAPI OpenCV | Morphological bounding box array |
| **Line Recognition** | PyTorch CRNN (`best_cer.pth`) | Raw text transcription (CER ~5.0%) |
| **AI Correction** | Groq / Gemini Multi-Consensus | Post-arbitration text (+12% accuracy gain) |
| **Trial Analytics** | Student Mobile Zustand Store | Real-time CER, WER, Accuracy, Line evaluation |
| **Global Analytics** | Student Mobile Persistent Store | Cross-session trends, Top confusion pairs |
| **Research Export** | TypeScript Export Engine | Standardized JSON, CSV, and Markdown reports |
