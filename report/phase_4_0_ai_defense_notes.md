# AI Defense & Architecture Notes — Phase 4.0, 4.0.1, 4.0.2 & 4.0.3
**MathVision Kids | Updated: Phase 4.0.3 Final AI Runtime Freeze**

---

## 1. 30-Second AI Subsystem Explanation

The MathVision Kids AI Subsystem receives a reference to a student's handwritten arithmetic image. It validates image quality, then passes the reference through a two-layer pipeline:

**LEARNED MODEL LAYER** (currently a deterministic fixture; replaced by trained model at handoff):
- OCR recognition of handwritten digits and operators
- Spatial layout evidence: row/column positioning, bounding boxes

**PYTHON AI RUNTIME** (always deterministic, never learned):
- Quality gate (blur, crop, brightness, skew)
- Recognition wrapper (fixture or trained model adapter)
- Structured parser (tokens → ParsedExercise)
- Deterministic arithmetic validator (carries, borrows, column-by-column)
- Evidence and confidence assembly
- Policy engine (Student or Teacher output)
- Authenticated callback to Spring Boot

The validator — not the model — is the mathematical authority.

---

## 2. Why Python

Python provides the strongest ecosystem for deep learning inference (PyTorch, ONNX Runtime, PaddlePaddle) and rapid deterministic validation logic, while keeping ML developers in their native toolchain. JVM and JavaScript runtimes have no equivalent ML inference stack.

---

## 3. Why FastAPI

FastAPI handles asynchronous HTTP workloads with high throughput, provides automatic OpenAPI documentation, and uses Pydantic for rigid schema validation out-of-the-box. This ensures exact contract adherence with Spring Boot and early detection of integration regressions.

---

## 4. Why Separate Spring Boot / FastAPI

Spring Boot is the business authority: it manages users, assignments, submissions, privacy, batches, and teacher decisions. FastAPI is the ML orchestration engine. Separating them:
- Prevents ML dependency hell (CUDA, heavy PyTorch binaries) from polluting the JVM classpath
- Allows independent scaling of AI workers
- Isolates model-related failures from business logic failures
- Enables the AI team to work independently

---

## 5. Why Asynchronous Processing

AI inference — even with quantized models — takes 200ms–5s. If Spring Boot waited synchronously, it would exhaust HTTP connection pools and thread executors under concurrent student load. Async processing allows Spring Boot to respond immediately and receive a callback when the job completes.

---

## 6. Why Celery

Celery provides a battle-tested distributed task queue with:
- Configurable bounded retries with exponential backoff
- Decoupling of HTTP request time from ML execution time
- Worker failure tolerance (tasks remain in queue until a worker picks them up)
- Observable task lifecycle via events

---

## 7. Why Redis

Redis acts as an in-memory message broker between FastAPI (which accepts the HTTP job request) and Celery workers (which execute the ML pipeline). Redis provides:
- Sub-millisecond enqueue latency
- Persistent queue across short-term network blips
- Simple operational footprint suitable for the project scale

---

## 8. Job Lifecycle

```
Student submits → Spring Boot pre-creates AiJob (owns jobId) → HttpAiAnalysisGateway (determines policyMode)
→ POST /internal/v1/jobs (FastAPI receives Spring jobId) → Redis (enqueue Celery task with Spring jobId)
Celery worker picks up task → QualityGate → Recognition → Parser → Validator → Policy
→ HTTP callback /internal/v1/ai/jobs/{jobId}/callback (with Spring jobId)
→ Spring Boot marks AiJob COMPLETED, persists AnalysisResult, updates Submission state
```

---

## 9. Recognition Layer

The `RecognitionEngine` abstraction defines what the ML layer must produce:
- `ImageRecognitionResult`: a flat list of `Token` objects
- Each token: `tokenId`, `value`, `tokenClass` (digit/operator), `boundingBox [x,y,w,h]`, `row`, `column`, `confidence`, `alternatives`, `ambiguity`
- Bounding boxes are normalized 0–1 with origin top-left
- The recognition layer does NOT evaluate mathematical correctness

---

## 10. FixtureRecognitionEngine

A fully deterministic recognition engine used in `FIXTURE` runtime mode. It maps synthetic `fixture://` image references to predetermined `ImageRecognitionResult` objects for E2E pipeline testing without model weights. Supported fixtures:
- `fixture://valid-addition` — 12+34=46 (correct)
- `fixture://addition-carry-error` — 45+27=62 (carry error in tens)
- `fixture://subtraction-borrow-error` — 52-18=44 (borrow error)
- `fixture://ambiguous-digit` — uncertain token, confidence 0.4, `ambiguity=True`
- `fixture://out-of-scope-exercise` — not a supported operation
- `fixture://quality-dark-image` — triggers `NEEDS_RETAKE`
- `fixture://quality-incomplete-crop` — triggers `CROP_REQUIRED`

---

## 11. Future Trained RecognitionEngine

When the AI/ML team delivers a model artifact:
1. A `ModelRecognitionEngine` class is implemented that adapts `ModelManifest` → inference
2. `runtime_mode=MODEL` activates it via `tasks.py` dispatch
3. The downstream parser and validator are unchanged — no frontend or Spring Boot changes needed
4. The fixture pipeline is retained for CI regression testing

---

## 12. Structured Parser

`StructuredParser` takes a flat `ImageRecognitionResult` and produces a `ParsedExercise`:
- Groups tokens by `row` (operand 1, operand 2, result)
- Sorts each row by `column` (descending → left-to-right reading)
- Assembles operand strings from digit tokens
- Detects operator token to determine operation type
- Returns status: `VALID_STRUCTURE`, `UNCERTAIN_STRUCTURE`, `OUT_OF_SCOPE`, `INVALID_LAYOUT`

If any critical token is uncertain (`ambiguity=True` or `confidence < threshold`), the parser returns `UNCERTAIN_STRUCTURE` rather than forcing a parse.

---

## 13. Deterministic Validator

The supreme mathematical authority. It never uses the model's opinion on correctness. Uses pure Python arithmetic:
- Accepts `ParsedExercise` with `VALID_STRUCTURE`
- Returns `{"is_valid": bool, "evidence": [...]}`
- Evidence items contain `evidenceId`, `type`, `placeValue`, `ruleId`, `confidence`, `description`

---

## 14. Addition Validation

`VerticalAdditionValidator`:
- Processes columns right-to-left (units → tens → hundreds → ...)
- At each column: `expected_digit = (op1_digit + op2_digit + carry) % 10`
- If `student_digit != expected_digit` → first error found
- `carry = (op1_digit + op2_digit + carry) // 10` propagated left

---

## 15. Subtraction Validation

`VerticalSubtractionValidator`:
- Processes columns right-to-left
- At each column: if `top_digit - borrow < bottom_digit`, borrow = 1 and `top_digit += 10`
- `expected_digit = top_digit - borrow - bottom_digit`
- If `student_digit != expected_digit` → first error found

---

## 16. Carry

Detected dynamically when the column sum exceeds 9 during addition. A `CARRY_BORROW_ERROR` evidence type is emitted when the student failed to account for the carry in the next column.

---

## 17. Borrow

Detected dynamically when the top digit is smaller than the bottom digit during subtraction. A `CARRY_BORROW_ERROR` evidence type is emitted when the student failed to account for the borrow effect in the next column.

---

## 18. Earliest Supported Error

**Canonical definition:**
> Earliest supported error is the first mathematically invalid column/transition encountered in solving order after reliable preceding evidence.

For vertical addition and subtraction, solving order is **right-to-left** (units first, then tens, etc.).

**Safety invariant:** If a critical token in an earlier column (e.g., units digit) is uncertain (confidence below threshold or `ambiguity=True`), the system MUST NOT confidently report the tens column as the earliest student error. The system must escalate to `UNCERTAIN_STRUCTURE` / `NEEDS_CONFIRMATION` until the earlier critical evidence is resolved.

This is verified by `test_earliest_error.py::test_uncertain_units_prevents_tens_earliest_error`.

---

## 19. Recognition Uncertainty

If the ML model cannot confidently read a token (e.g., is it a `1` or a `7`?):
- Token is marked `ambiguity=True`, `confidence < 0.5`
- `ImageRecognitionResult.status = "UNCERTAIN_RECOGNITION"`
- Parser returns `UNCERTAIN_STRUCTURE`
- Student policy: `NEEDS_CONFIRMATION`
- Teacher policy: `REVIEW_REQUIRED`
- **Uncertainty is NOT a computation error.** No fabricated error evidence is generated.

---

## 20. Quality Gate

`QualityGate` is an early-exit boundary before recognition. In fixture mode, checks for synthetic tags in the image reference. In real mode (future), uses OpenCV/image analysis:

| Check | Status | Implementation |
|---|---|---|
| READABLE IMAGE | PASS | PARTIAL (fixture tags only) |
| MINIMUM DIMENSIONS | PASS | NOT_IMPLEMENTED |
| BLUR | NEEDS_RETAKE | PARTIAL (fixture tag) |
| DARK / BRIGHTNESS | NEEDS_RETAKE | PARTIAL (fixture tag) |
| GLARE | NEEDS_RETAKE | NOT_IMPLEMENTED |
| SKEW | NEEDS_RETAKE | NOT_IMPLEMENTED |
| INCOMPLETE_CROP | CROP_REQUIRED | PARTIAL (fixture tag) |

Real image quality analysis (OpenCV-based) is owned by the AI/ML team and will be added at model handoff.

---

## 21. Evidence

Canonical `Evidence` schema:
```
evidenceId      — unique identifier for this evidence item
type            — COMPUTATION_ERROR | CARRY_BORROW_ERROR | UNCERTAINTY | LAYOUT_ERROR
boundingBox     — [x, y, width, height], normalized 0–1, origin top-left
placeValue      — human-readable column name (e.g. "Hàng chục")
ruleId          — machine-readable rule identifier (e.g. "ADD_COL_MISMATCH")
observedText    — what the student wrote
expectedRelation — relationship that should hold
observedRelation — relationship that was observed
confidence      — system certainty in this evidence item [0.0–1.0]
description     — human-readable explanation in Vietnamese
```

---

## 22. Confidence Bundle

Canonical system-certainty values (NOT student performance scores):
```
recognition  — confidence in OCR/layout recognition layer output [0.0–1.0]
structure    — confidence that ParsedExercise has valid structure [0.0–1.0]
diagnosis    — confidence in deterministic validation/diagnosis result [0.0–1.0]
```

Values are deterministic in fixture mode. They are always included in the `AiCallbackRequest` payload.

---

## 23. Student Policy

`generate_student_feedback()`:
- `VALID_STRUCTURE` + valid → `FEEDBACK_READY` with positive feedback
- `VALID_STRUCTURE` + invalid → `FEEDBACK_READY` with exactly **one Socratic hint**, `focusEvidenceId` pointing to the first error, `revealAnswer=False` (always)
- `UNCERTAIN_STRUCTURE` → `NEEDS_CONFIRMATION`
- `OUT_OF_SCOPE` → `OUT_OF_SCOPE`

`revealAnswer` is structurally enforced to `False` in the `StudentFeedback` schema. The policy never provides the correct answer to the student.

---

## 24. Teacher Policy

`generate_teacher_feedback()`:
- **Confident valid arithmetic** → `PROPOSED_GRADE` with `GradeProposal` (`suggestedScore=10`, `maxScore=10`, `isOfficial=False`, reason populated)
- **Confident invalid arithmetic** → `PROPOSED_GRADE` with `GradeProposal` (`suggestedScore=0`, `maxScore=10`, advisory error reason, deterministic error evidence, `isOfficial=False`)
- **Uncertain recognition / structure / diagnosis** → `REVIEW_REQUIRED` (uncertainty evidence, flags raw image for teacher inspection)
- **`OUT_OF_SCOPE`** → `OUT_OF_SCOPE`

Canonical semantics:
- `PROPOSED_GRADE` is a confident advisory grading proposal emitted for both confidently correct and confidently incorrect supported work.
- `REVIEW_REQUIRED` does **NOT** mean "student answer is mathematically incorrect." It means the system lacks sufficient safe evidence for a confident automated proposal.
- `isOfficial` is always `False` until the teacher explicitly creates a `TeacherDecision`.

---

## 25. PROPOSED_GRADE

A confident advisory grading result emitted by the Teacher policy for both confidently correct and confidently incorrect supported student work:
- **For correct arithmetic:** contains `GradeProposal` with `suggestedScore=10`, `maxScore=10`, `confidence=0.97`, clean verification reason, `isOfficial=False`.
- **For incorrect arithmetic:** contains `GradeProposal` with `suggestedScore=0`, `maxScore=10`, `confidence=0.93`, earliest detected error column reason, accompanied by deterministic error evidence (e.g. `ADD_COL_MISMATCH` at "Hàng chục"), `isOfficial=False`.
- In all cases, `isOfficial` remains `False` until a human teacher explicitly confirms or adjusts the grade.

---

## 26. REVIEW_REQUIRED

Emitted by Teacher policy **ONLY** when recognition, spatial structure, or diagnosis has insufficient confidence (e.g. ambiguous handwriting, irregular vertical layout, occluded digits).
- **Critical Semantic Invariant:** `REVIEW_REQUIRED` does **NOT** mean "student answer is mathematically incorrect." If an arithmetic error is confidently diagnosed, `PROPOSED_GRADE` is emitted instead with score 0 and error evidence.
- `REVIEW_REQUIRED` signals that the system cannot safely produce an automated proposal, so the teacher must inspect the raw student image and grade manually.

---

## 27. NEEDS_CONFIRMATION

Emitted by Student policy when recognition is uncertain. Student is prompted to retake or clarify. No computation error is fabricated.

---

## 28. NEEDS_RETAKE

Emitted by `QualityGate` when image is too dark, blurry, or otherwise unreadable. Processing stops before recognition.

---

## 29. CROP_REQUIRED

Emitted by `QualityGate` when the image does not capture the full exercise. Processing stops before recognition.

---

## 30. OUT_OF_SCOPE

Emitted when the recognized exercise is not a supported arithmetic type (e.g., multiplication, division, or unrecognized content). Both student and teacher receive this status.

---

## 31. Socratic Hint Policy

The student policy produces exactly one Socratic hint per job:
- The hint is phrased as a question, not a correction
- It references the earliest detected error column
- It never reveals the correct answer
- `revealAnswer=False` is structurally enforced

---

## 32. VLM Scope & Architectural Boundaries

Future Vision-Language Models (VLMs) have strictly delimited, non-authoritative roles:
1. **Permitted Roles:**
   - **Zero-shot comparison experiments:** benchmarking raw multimodal zero-shot capabilities against the dedicated OCR + Deterministic Validator pipeline.
   - **Constrained hint/context wording assistance:** polishing Vietnamese Socratic pedagogical phrasing for students under strict templates.
2. **Strictly Prohibited Roles:**
   - **Mathematical Correctness Authority:** VLMs hallucinate reasoning steps and stochastic arithmetic. The Deterministic Validator applying pure Python arithmetic rules is the sole mathematical authority.
   - **Required Layout / Structure Authority:** Column alignment, carry/borrow detection, and spatial tokens are resolved by deterministic structured parsing; VLMs must never be a required dependency for structural layout authority.

---

## 33. Fixture Mode

`runtime_mode=FIXTURE` (default in development and CI):
- `FixtureRecognitionEngine` maps `fixture://` references to predetermined `ImageRecognitionResult` objects
- `ImageSourceResolver` allows `fixture://` references only in FIXTURE mode
- No model weights required
- Full pipeline tested end-to-end without ML infrastructure

---

## 34. Model Mode

`runtime_mode=MODEL`:
- `ModelRecognitionEngine` loads a trained artifact specified in `ModelManifest`
- `ImageSourceResolver` resolves `minio://` references via private MinIO client
- `fixture://` references are rejected in MODEL mode
- Currently returns `MODEL_NOT_AVAILABLE` until the AI team delivers an artifact

---

## 35. Model Manifest

`ModelManifest` (Pydantic schema) required fields:
```
modelName           — canonical model identifier
modelVersion        — semver version string
task                — e.g. "arithmetic_recognition"
framework           — e.g. "pytorch"
artifactFilename    — filename of the model artifact
artifactFormat      — PYTORCH | TORCHSCRIPT | ONNX | PADDLE
sha256              — SHA-256 hex digest of the artifact file
```

Optional fields: `datasetVersion`, `annotationSchemaVersion`, `inputWidth`, `inputHeight`, `inputChannels`, `preprocessing`, `labelMapVersion`, `metrics`, `runtimeRequirements`, `createdAt`.

---

## 36. Model Handoff

The AI/ML team delivers:
1. A trained model artifact (`.pt`, `.onnx`, etc.)
2. A `model_manifest.json` matching the `ModelManifest` schema
3. A label map file matching `labelMapVersion`
4. Sample inference inputs/outputs

The runtime:
1. `ModelManifestLoader.load_and_verify_artifact()` validates format, label map version, and checksum
2. A `ModelRecognitionEngine` adapter is instantiated using manifest preprocessing config
3. No frontend or Spring Boot changes are required for this transition

---

## 37. Real Image Access

`ImageSourceResolver` resolves image references to bytes without exposing arbitrary paths or making MinIO public.

Accepted schemes:
- `fixture://tag` — synthetic fixture bytes (FIXTURE mode only)
- `minio://bucket/key` — private MinIO access via configured internal client

Rejected schemes:
- `http://` / `https://` — arbitrary external URLs
- `file:///` — local filesystem paths
- `/../` — path traversal
- Any unrecognized scheme

---

## 38. Callback

The Celery worker sends an authenticated HTTP POST to Spring Boot's internal callback endpoint upon job completion:
```
POST /internal/v1/ai/jobs/{jobId}/callback
Headers: X-Internal-API-Key: [configured internal key]
Body: AiCallbackRequest (JSON)
```

The callback payload includes: `status`, `recognizedExercise`, `gradeProposal`, `evidence`, `studentFeedback`, `confidenceBundle`.

---

## 39. Callback Authentication

The callback uses a pre-shared key (`X-Internal-API-Key`) over the internal network. This key is configured via environment variable (`INTERNAL_API_KEY`). Its value is never logged or exposed in reports.

---

## 40. Callback Retries

Retry behavior (3 max retries, exponential backoff: `2^retry` seconds):
- Network error (`httpx.RequestError`) → retry
- Server error (5xx) → retry
- Client error (4xx) → **no retry** (contract violation — retrying will not fix it)

Backoff sequence: 1s, 2s, 4s (then permanent failure after 3 retries).

---

## 41. Idempotency

Spring Boot's `InternalAiCallbackController` ignores subsequent callbacks for an `AiJob` that is already in `COMPLETED` or terminal state. This prevents duplicate evidence or grade proposal creation if a callback is retried.

---

## 42. Redis Failure

If Redis is unavailable, FastAPI cannot enqueue the Celery task. FastAPI returns an error to Spring Boot. The job is not queued. Spring Boot propagates a graceful error to the client.

---

## 43. Celery Worker Failure

If all Celery workers crash, tasks remain in the Redis queue with their message. When a worker restarts, it picks up unacknowledged tasks from where they left off (within the visibility timeout).

---

## 44. Spring Callback Unavailable

If Spring Boot is unreachable or returns 5xx, Celery retries with exponential backoff (max 3 retries). If Spring Boot is still unavailable after all retries, the job enters a `FAILED` state in Redis. No further automatic action is taken — an operator must investigate.

---

## 45. Health vs Readiness

`GET /health` — liveness check. Returns `{"status": "ok"}` if the Python process is alive. Does not check dependencies.

`GET /ready` — readiness check. Verifies Redis connectivity via Celery broker connection. Returns `{"status": "ready", "redis_connected": true, "mode": "FIXTURE"}` when ready. Returns `{"status": "degraded", "redis_connected": false}` if Redis is unreachable.

Future: readiness will also check that model weights are loaded in MODEL mode.

---

## 46. Observability

`app/observability/logging.py` provides:
- `setup_logging()` — configures JSON-compatible structured logging
- `set_correlation_context(job_id, submission_id)` — injects `job_id` and `submission_id` into all log lines for the current Celery task

Every log line at INFO or above includes `[job:{id}] [sub:{id}]` for correlation across distributed workers.

---

## 47. DVC

Data Version Control (DVC) will track model artifact files (`.pt`, `.onnx`) outside Git. The `model_manifest.json` references artifact filenames that DVC manages. This prevents binary files from inflating the Git repository while maintaining reproducibility.

---

## 48. MLflow

MLflow tracks training metrics (F1 score, per-class precision, recall, confusion matrix) entirely in the AI training workspace. These metrics are exported to the `ModelManifest.metrics` field at handoff. The runtime does not access MLflow at inference time.

---

## 49. Current Limitations

1. **Quality gate is symbolic only** — checks fixture tags; real OpenCV analysis not implemented (owned by AI team)
2. **MODEL mode is blocked** — returns `MODEL_NOT_AVAILABLE` until artifact is delivered
3. **Checksum requires artifact** — `load_and_verify_artifact()` works only when the artifact file exists
4. **Evaluation targets unevaluated** — proposal evaluation targets (precision, recall, F1) remain unevaluated until the real recognition model and evaluation dataset are available

---

## 50. Defense Q&A

**Q: Why not just use a VLM to grade the math directly?**
A: VLMs hallucinate. 99% confidence does not mean mathematically correct. For supported arithmetic, given a correctly parsed structure, the deterministic validator provides reproducible, rule-based mathematical validation.
Future VLM roles are strictly restricted to zero-shot comparison and constrained wording assistance — never mathematical authority.

**Q: What if the model gets 99% accuracy on subtraction?**
A: It still passes through the Deterministic Validator. The model's opinion on correctness is irrelevant — only its token recognition output is used.

**Q: What happens if the student photograph is blurry?**
A: The QualityGate returns `NEEDS_RETAKE` before recognition, saving ML compute and providing actionable feedback immediately.

**Q: What if two students have identical handwriting and one image is misclassified?**
A: The recognition layer returns all per-token confidences. Low confidence triggers `NEEDS_CONFIRMATION` or `REVIEW_REQUIRED`, not a silent wrong answer.

**Q: Can a student manipulate the image reference to access arbitrary files?**
A: No. `ImageSourceResolver` rejects all `file://`, `http://`, `../`, and unrecognized schemes. Only `fixture://` and validated `minio://` references are accepted.

**Q: Why is `isOfficial=False` enforced at the Python layer?**
A: The Python runtime has no authority to issue official grades. Only an explicit `TeacherDecision` through the Spring Boot business API can set `isOfficial=True`.

---

## 51. Live Coding Preparation

1. **New validator rule**: Create a new `VerticalMultiplicationValidator` by implementing the `validate(parsed: ParsedExercise)` interface — no other file changes needed
2. **New fixture**: Add a new `if "new-scenario" in image_reference:` branch to `FixtureRecognitionEngine.recognize()`
3. **New quality check**: Extend `QualityGate.evaluate()` with an additional image analysis method
4. **Schema extension**: Add a new field to `AiCallbackRequest` using Pydantic — FastAPI automatically validates and documents it
5. **Policy adjustment**: Modify hint generation in `student_policy.py` without touching recognition, parsing, or validation
