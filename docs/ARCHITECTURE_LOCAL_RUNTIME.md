# Architecture and recognition boundaries

[README](../README.md) · [Local setup](LOCAL_SETUP.md) · [Contributing](../CONTRIBUTING.md)

MathVision Kids separates the student experience, business authority, and AI processing. The local Windows launcher runs infrastructure in Docker and application services on the host.

## System map

~~~mermaid
flowchart TD
    Student["Student · Expo / React Native"]
    Web["Portal · Teacher · Admin"]
    API["Business API · Spring Boot / Java 21"]
    AI["AI runtime · FastAPI / Python"]
    PG[("PostgreSQL · Records")]
    Images[("MinIO · Images")]
    Queue[("Redis · Queue and state")]
    Worker["Celery worker"]
    Local["Local geometry · CRNN · YOLO"]
    Cloud["Configured Groq / Gemini"]

    Student -->|Authenticated requests| API
    Web -->|Authenticated requests| API
    API --> PG
    API --> Images
    API -->|Internal requests| AI
    AI --> Local
    AI -->|Optional cloud operations| Cloud
    AI -->|Async grading jobs| Queue
    Queue --> Worker
    Worker --> Images
    Worker --> Local
    Worker -->|Authenticated callback| API
~~~

The business API owns authentication, roles, records, and job identity. Clients do not decide their own role or invoke internal AI services directly.

## Three different recognition tasks

| Task | Pipeline | Meaning |
| :--- | :--- | :--- |
| Find lines | OpenCV geometry with optional local PP-OCR detector inputs | Locates plausible text regions; does not prove the words were read correctly |
| Read handwriting lines | Vietnamese CRNN checkpoint; optional advisor correction | Converts a line crop into text |
| Read a photographed math page | Main tutor inspection calls cloud vision; local geometry maps rows | Distinguishes a question, a worked solution, or mixed content |

The main math guide's photographed-question transcription is **not** an inference from the local CRNN checkpoint. These paths coexist, but they have different dependencies.

## Tutoring and arithmetic

A validated lesson plan contains a small sequence of reasoning steps. Supported question patterns have built-in plans; other requests need a valid cloud-generated plan. Students choose an explanation or calculate an answer. Answer checking and session ownership remain on the server.

The asynchronous arithmetic grading pipeline uses fixture recognition by default. Setting `RUNTIME_MODE=MODEL` switches that engine to the configured YOLO artifact. It does not switch the notebook inspection pipeline to local OCR.

A worked solution without its original question can be read, but cannot reliably be judged against the intended task. The student flow asks for missing problem context.

## Repository responsibilities

| Directory | Responsibility |
| :--- | :--- |
| `apps/student-mobile/` | Camera, photo editing, privacy, review, lessons, and local learning history |
| `apps/portal-web/` | Unified web entry point |
| `apps/teacher-web/` | Classroom, assignment, and submission review workflows |
| `apps/admin-web/` | Administrative UI |
| `backend/business-api/` | Spring Security/JWT, JPA/Flyway records, storage, and AI orchestration |
| `ai/runtime/` | OCR endpoints, geometry, arithmetic engine, tutoring, and worker |
| `packages/`, `contracts/` | Shared definitions and contracts |
| `scripts/`, `infra/docker/` | Owned-process launch, health, stop, and infrastructure |

## Privacy and configuration

Images go through a privacy review before the student sends them. Cloud-enabled operations can send image or text content to the configured provider. Masking information reduces what is sent; it is not an automatic guarantee that all private information was removed.

Keep secrets server-side, outside version control. Mobile variables prefixed `EXPO_PUBLIC_` are public client configuration and must not contain private keys. Model weights, datasets, private student images, and runtime logs are excluded from Git.

Local development credentials and seeded accounts are examples. The Windows setup guide does not establish a production deployment.

## Quality and current limits

- Line localization, transcription quality, and math reasoning need separate evaluation.
- Skew, faint ink, grids, overlapping strokes, diagrams, multi-column pages, and incomplete crops remain difficult.
- An empty or failed read should lead to review or recapture, not invented text.
- Notebook and OCR endpoints have bounded content limits. A dense page may need to be split into smaller crops.
- Cloud operations can be unavailable because of configuration, network, provider quota, or unsupported requests.
- The lesson library is a selected practice collection, not complete coverage of every textbook question.

The [line polish report](../report/DRIVE_LINE_POLISH_20261005.md) and [refinement report](../report/DRIVE_LINE_REFINEMENT_20261005.md) record development evidence and unresolved cases. Reported batch execution counts are not equivalent to a held-out recognition accuracy benchmark.

Runtime readiness checks Redis/worker availability and the selected grading artifact where applicable. It does not certify cloud access or the CRNN checkpoint. Validate those with a reviewed sample after installation.

## Version references

Use the repository's lockfiles and manifests for reproducibility. For mobile framework behavior, consult the exact [Expo SDK 57 reference](https://docs.expo.dev/versions/v57.0.0/). Installation, ports, and development accounts are maintained in [LOCAL_SETUP.md](LOCAL_SETUP.md).
