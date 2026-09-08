# Phase 4.0: FastAPI AI Runtime Foundation

## Overview
Phase 4.0 establishes the Python-based AI microservice for MathVision Kids. This service orchestrates OCR recognition, structural parsing, deterministic mathematical validation, and pedagogical policy execution. 

Crucially, **no AI model was trained during this phase.** The service utilizes a `FixtureRecognitionEngine` for deterministic End-to-End testing and establishes boundaries for future model integration (via the Manifest Schema and `PaddleOCRAdapter`).

## Architecture
- **Framework:** FastAPI (Python 3.12)
- **Job Pipeline:** Celery workers backed by a Redis broker.
- **Contract Boundary:** Bidirectional HTTP integration with Spring Boot.
  - Job Intake: `POST /internal/v1/jobs` (FastAPI)
  - Result Callback: `POST /internal/v1/ai/jobs/{jobId}/callback` (Spring Boot)
- **Validation Engine:** Deterministic python logic simulating "Earliest Error" detection (iterating right-to-left columns to verify carry, borrow, and digit accuracy).

## Key Components Implemented
1. **Pydantic Contracts (`app/schemas/`)**: Strongly typed data boundaries representing Jobs, Exercises, Tokens, and Evidence.
2. **Recognition Boundary (`app/recognition/`)**: 
   - `FixtureRecognitionEngine`: Returns deterministic errors/successes based on `imageReference` strings (e.g. `fixture://valid-addition`, `fixture://addition-carry-error`).
   - `PaddleOCRAdapter`: Empty stub with manifest loading capability.
3. **Deterministic Validation (`app/validation/`)**:
   - `VerticalAdditionValidator`: Validates single exercises up to 6 digits, enforcing carry logic.
   - `VerticalSubtractionValidator`: Validates single exercises up to 6 digits, enforcing borrow logic.
4. **Policy Engine (`app/policy/`)**:
   - `StudentPolicy`: Generates a single, targeted Socratic hint based on the earliest error. Does not leak the full correct answer.
   - `TeacherPolicy`: Confidently proposes a grade (`PROPOSED_GRADE`) or flags the submission for manual review (`REVIEW_REQUIRED`) backed by `Evidence`.
5. **Spring Boot Gateway (`services/business-api`)**:
   - Implemented `HttpAiAnalysisGateway` alongside `StubAiAnalysisGateway`, toggleable via `ai.gateway.mode=FASTAPI` in `application.yml`.
   - Updated `docker-compose.yml` to include Redis, FastAPI, and Celery Worker containers.

## Testing & Validation
- Comprehensive `pytest` suite added for validators, celery task execution flow, and API endpoints.
- Tests executed locally and passing successfully.

## Next Steps
- ML Teammate handoff: Models trained against the manifest schema can now be plugged into the `PaddleOCRAdapter` or equivalent adapter.
