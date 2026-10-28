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

Lesson narration and spoken Q&A explanations default to pinned `edge-tts==7.3.1` with the Vietnamese voices `vi-VN-NamMinhNeural` (male, default) and `vi-VN-HoaiMyNeural` (female). Student narration accepts only these two voices and text already published in the authenticated lesson session/revision. Audio is returned as a complete private WAV so existing seeking and replay keep working; the private in-memory cache separates owners, sessions and voices, with every public read checked against the current revision. The Student lesson flow uses speech only. Lesson-video endpoints, encoders, players and packaged demonstration clips have been removed. Shared speech synthesis lives in `app/tutoring/speech_render.py`.

The runtime needs outbound access to the Microsoft Edge speech service and `ffmpeg` for decoding. This community library uses an online service; it does not require an Azure key and has no guaranteed service availability. Empty turns are retried at most twice within one 25-second speech deadline. Persistent failures return a retryable error; the app keeps the transcript and does not switch language or voice silently. Raw provider errors, lesson text and request URLs are not logged. Temporary MP3/WAV files are removed after rendering or when the learner closes the player.

### Reading-first lesson opening

After the learner explicitly confirms the source, `guidedUnderstanding=true` with `startWithReading=true` can open the existing three source-derived reading choices immediately. A response with `preparingMath=true` contains only those three choices, never an unreviewed mathematical step or a completed lesson. Unsupported source shapes keep the normal reviewed full-plan path.

The same planner, local arithmetic/teaching checks and independent semantic reviewer run in a bounded background task. Before accepting the final reading answer, the API waits for their successful result and rechecks owner/revision. Failure keeps the learner at the reading step with the source intact; an explicit retry may retry preparation. The new client/boundary explicitly validate the reading-only response shape; clients not opting in keep the earlier contract. A newer lesson cancels the same pupil's pending old plan, and late results cannot resurrect an abandoned speech queue. Speech preparation starts for reading immediately and refreshes the future scripts when the reviewed mathematics is ready, reusing cached speech and the chosen voice. Neither mathematical review nor speech preparation extends the public 45-second waiting limit.

### Optional official route with the same voices

The server can use Azure Speech through the existing `httpx` dependency. Set `SPEECH_PROVIDER=azure`, `AZURE_SPEECH_REGION` to the Speech resource's region, and `AZURE_SPEECH_KEY` in the server's private environment or secret store, then restart the runtime. Keep the key out of source control, client bundles and chat. The default remains `SPEECH_PROVIDER=edge`; installing this adapter does not activate paid requests or automatic paid failover.

Azure returns complete raw 16 kHz / 16-bit mono PCM, wrapped as WAV using Python's standard library. It uses the same two allowed voice identifiers and pronunciation preparation, with the same private background preparation, cache, ownership checks and 45-second public preparation limit. Its transport remains bounded to 25 seconds; no MP3 checkpoint or decoder is used for this route. An unfinished, empty, silent or oversized response is rejected. Live latency and voice availability must be measured after configuration; offline adapter tests do not establish a 1–3 second response time.

Background synthesis makes real speech requests even before the learner presses Play. It adds no model prompt for the already-created lesson script, but can consume the speech service's request/character allowance. Preparing both voices and checked-step reviews increases that usage; cached replay makes no further synthesis request. See Microsoft's [voice list](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=text-to-speech), [REST reference](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech) and [pricing](https://azure.microsoft.com/en-us/pricing/details/speech/). No unlimited service or zero-latency guarantee is implied.
