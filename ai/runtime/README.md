# MathVision Kids AI Service

This is the FastAPI AI Runtime Foundation for MathVision Kids.

## Purpose
This service acts as the orchestration layer for processing student math submissions. It receives analysis jobs from the Spring Boot backend, orchestrates recognition (OCR), parses handwritten structures, performs deterministic mathematical validation (addition and subtraction), applies pedagogical logic (earliest error and hint generation), and invokes an authenticated callback to the Spring Boot backend with structured results.

## Architecture
- **FastAPI**: Provides `/internal/v1/jobs` for accepting jobs and `/health`, `/ready` for diagnostics.
- **Celery & Redis**: Provides an asynchronous queue to process ML tasks outside the HTTP lifecycle.
- **Deterministic Validation**: Pure Python structural logic that guarantees mathematical correctness.
- **Mock Recognition**: Uses `FixtureRecognitionEngine` for deterministic pipeline testing without a trained model.

## Runtime Modes
- `FIXTURE`: (Default) Deterministic engine for E2E testing without ML models.
- `MODEL`: Attempts to load actual trained model manifests (Currently returns MODEL_NOT_AVAILABLE until teammate handoff).

## Local Setup
1. `python -m venv .venv`
2. `.venv\Scripts\activate` (Windows)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in necessary details.
5. Start Redis (e.g. via Docker).
6. Start Celery worker: `celery -A app.jobs.celery_app worker --loglevel=info -P solo`
7. Start FastAPI server: `uvicorn app.main:app --reload`

## Lesson voices

Lesson narration and spoken Q&A explanations use pinned `edge-tts==7.3.1` with the Vietnamese voices `vi-VN-NamMinhNeural` (male, default) and `vi-VN-HoaiMyNeural` (female). Student narration accepts only these two voices and text already published in the authenticated lesson session/revision. Audio is returned as a complete private WAV so existing seeking and replay keep working; the private in-memory cache separates owners, sessions, revisions and voices. Generated movies retain their existing offline speech path: live online provider probes still include intermittent empty turns, so this change does not make movie rendering depend on that service.

The runtime needs outbound access to the Microsoft Edge speech service and `ffmpeg` for decoding. This community library uses an online service; it does not require an Azure key and has no guaranteed service availability. Empty turns are retried at most twice within one 25-second speech deadline. Persistent failures return a retryable error; the app keeps the transcript and does not switch language or voice silently. Raw provider errors, lesson text and request URLs are not logged. Temporary MP3/WAV files are removed after rendering or when the learner closes the player.
