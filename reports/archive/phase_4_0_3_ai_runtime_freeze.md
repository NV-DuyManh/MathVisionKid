# Phase 4.0.3 — Spring↔FastAPI Correlation, Teacher Policy Fix, Real Image Wiring & Final AI Runtime Freeze Report

**Date:** September 8, 2026  
**Status:** COMPLETED & FROZEN  
**Target Environment:** Spring Boot 3.3.6 (Java 21) ↔ FastAPI 0.115 (Python 3.12) ↔ Celery 5.4.0 ↔ Redis 7 ↔ PostgreSQL 16 ↔ MinIO S3 Object Storage  

---

## 1. Executive Summary

Phase 4.0.3 successfully resolved all remaining architectural and integration defects between the Spring Boot Business API and the FastAPI AI Runtime subsystem, achieved 100% verified cross-process E2E communication, corrected the teacher grading policy contract, and officially refroze the AI Runtime subsystem.

Key accomplishments:
1. **Spring-Owned Job ID Correlation:** Spring Boot generates and persists the canonical `jobId` (`AiJob` entity) before delegating to FastAPI. This UUID survives the entire pipeline: Spring Boot → FastAPI → Redis broker → Celery worker → HTTP callback → Spring Boot callback handler.
2. **Explicit `policyMode` Contract:** Spring's `HttpAiAnalysisGateway` explicitly transmits `policyMode` (`STUDENT` or `TEACHER`), never defaulting to ambiguous server-side behavior.
3. **Teacher Policy Correction:** The teacher policy was corrected to cleanly distinguish mathematical invalidity from model uncertainty. Confident invalid arithmetic produces `PROPOSED_GRADE` (with `suggestedScore=0`, rule-based error evidence, and `isOfficial=False`), whereas only unresolvable OCR ambiguity or structural uncertainty returns `REVIEW_REQUIRED`.
4. **Real Object Storage Wiring:** Configured private MinIO client resolution in `ImageSourceResolver`, confirming live S3 access (`REAL_IMAGE_ACCESS = PASS`) against the `mathvision-minio` container.
5. **Model Adapter Contract Boundary:** Created `ModelRecognitionEngine` implementing the exact ML handoff contract (manifest parsing, label map loading, preprocessing transformation, `ModelNotAvailableError` handling).
6. **Distributed Transaction Visibility Decoupling:** Eliminated the transaction visibility race condition between Spring's `BatchService` / `SubmissionService` and Celery's ultra-fast callbacks by committing entities prior to outbound network calls and utilizing `TransactionSynchronization.afterCommit` with async execution.
7. **True Cross-Process E2E Pass:** All three end-to-end scenarios executed against live, real processes without stubs, all callbacks returning `HTTP 200 OK`.
8. **Subsystem Freeze:** AI Runtime is refrozen. Handoff to AI/ML team is ready (`READY_FOR_MODEL`).

---

## 2. Frozen Integrity Verification

Strict immutability constraints were maintained throughout Phase 4.0.3:

| Component | Status | Files Modified in Phase 4.0.3 |
|---|---|---|
| **Student Mobile** (`assets/`, `src/`, `app.json`) | **FROZEN** | **0 files modified** |
| **Teacher Web** (`teacher-web/`) | **FROZEN** | **0 files modified** |
| **AI Training Workspace** (`ai-training/`) | **OWNED BY ML TEAM** | **0 files modified** |
| **AI Model Training** | **NOT TRAINED** | **No models fabricated or trained** |
| **VLM Experiments** | **NOT STARTED** | **No VLM models or API calls** |

---

## 3. Job Ownership Architecture

### Problem
Previously, FastAPI generated its own UUID for the job upon receiving an analysis request, while Spring Boot generated another UUID. This led to correlation mismatches and 404 errors when Celery reported callbacks back to Spring Boot.

### Solution
- **Spring Boot Owns the Job ID:** `AiJob` is instantiated and assigned a UUID by Spring Boot.
- **Payload Correlation:** The canonical `jobId` is passed in the JSON request body (`POST /internal/v1/jobs`).
- **FastAPI Passthrough:** FastAPI's `JobRequest` schema includes optional `jobId: UUID | None`. If provided, it uses Spring's `jobId`; otherwise it falls back to generating a UUID.
- **Celery Propagation:** Celery task `process_submission(job_id, request_data)` accepts Spring's `jobId` as its primary argument and sets correlation context for structured logging.
- **Callback Routing:** The Celery worker sends the HTTP callback to `http://localhost:8080/internal/v1/ai/jobs/{jobId}/callback` using the identical Spring-owned UUID.
- **Spring Verification:** Spring Boot callback controller looks up `aiJobRepository.findById(jobId)` and locates the job record.

---

## 4. Canonical `JobRequest` Schema Alignment

Both Spring Boot and FastAPI schemas are aligned:

```json
{
  "jobId": "3819f1fa-75ee-4889-be86-a88e4e5c004b",
  "submissionId": "9b81e7bb-ec19-4419-b450-583014a4fe4d",
  "imageReference": "minio://mathvision/batches/0c01a004.../error.jpg",
  "allowedOperations": ["VERTICAL_ADDITION"],
  "maxDigits": 6,
  "oneExerciseOnly": true,
  "policyVersion": "v1.2",
  "policyMode": "TEACHER"
}
```

- **Pydantic Schema:** `app/schemas/jobs.py` (`JobRequest`)
- **FastAPI Endpoint:** `app/api/jobs.py` (`POST /internal/v1/jobs`)
- **Spring Gateway:** `HttpAiAnalysisGateway.java`

---

## 5. PolicyMode Implementation

Spring Boot's `HttpAiAnalysisGateway` dynamically determines and explicitly sets `policyMode`:

```java
String determinePolicyMode(Submission submission) {
    if (submission.getBatch() != null) {
        return "TEACHER";
    }
    return "STUDENT";
}
```

- **Student Flow (`STUDENT`):**
  - Generates pedagogical Socratic hints.
  - Strict privacy invariant: `revealAnswer = false`.
  - Focuses on the earliest error place value (e.g., "Hàng chục").
  - Transitions submission state to `FEEDBACK_READY` (or `NEEDS_CONFIRMATION` on uncertainty).
- **Teacher Flow (`TEACHER`):**
  - Evaluates batch homework submissions.
  - Distinguishes diagnostic correctness from confidence.
  - Returns advisory grade proposals (`PROPOSED_GRADE`) or flags raw image for manual review (`REVIEW_REQUIRED`).
  - Strict privacy invariant: Batch privacy gate enforces 10–30 submissions.

---

## 6. Teacher Policy Refinement

### Problem
Previously, when the deterministic validator identified an arithmetic carry error, the teacher policy returned `status: "REVIEW_REQUIRED"`. This conflated model uncertainty with arithmetic invalidity, defeating the purpose of automated grading proposals.

### Solution
The contract distinction is codified in `app/policy/teacher_policy.py`:

```
VALID_STRUCTURE + is_valid = True   → PROPOSED_GRADE (suggestedScore: 10, clean pass)
VALID_STRUCTURE + is_valid = False  → PROPOSED_GRADE (suggestedScore: 0, error evidence, isOfficial: False)
UNCERTAIN_STRUCTURE                 → REVIEW_REQUIRED (uncertainty evidence)
OUT_OF_SCOPE                        → OUT_OF_SCOPE
```

- **Confident Invalid (`PROPOSED_GRADE`):** The engine identified the digits with high confidence and deterministically verified that the student made an arithmetic error. The teacher receives an advisory grade proposal (`suggestedScore=0`) accompanied by rule-based error evidence (e.g. `ADD_COL_MISMATCH` at "Hàng chục") so the teacher can approve or override the proposal in one click.
- **Uncertain Structure (`REVIEW_REQUIRED`):** The engine cannot read the digits or detect layout with sufficient confidence. The raw image is flagged for human intervention.
- **Teacher Decision Guard:** In neither case is a `TeacherDecision` record generated automatically. Official decisions require human teacher action.

---

## 7. Real Image Access Verification (MinIO)

Real MinIO object storage access was implemented and verified:

1. **MinIO Configuration (`app/config.py`):**
   - `minio_endpoint: "${MINIO_ENDPOINT:-localhost:9000}"`
   - `minio_access_key: "<redacted> (configured via MINIO_ACCESS_KEY)"`
   - `minio_secret_key: "<redacted> (configured via MINIO_SECRET_KEY)"`
   - `minio_bucket: "${MINIO_BUCKET:-mathvision}"`
   - `minio_secure: False`
2. **Factory Method (`app/image/resolver.py`):**
   `create_configured_resolver()` instantiates an `ImageSourceResolver` wired with a configured `MinioStorageBackend` alongside `FixtureStorageBackend` and `LocalStorageBackend`.
3. **Verification:**
   Tested against real Docker container `mathvision-minio` on port 9000. Confirmed that `minio://` references are fetched and verified without mock fallbacks.
   - Result: `REAL_IMAGE_ACCESS = PASS`

---

## 8. Model Adapter Skeleton (`ModelRecognitionEngine`)

The contract boundary for future learned model handoff was implemented in `app/recognition/model_engine.py`:

- **Inheritance:** Extends abstract `RecognitionEngine`.
- **Manifest Consumption:** Reads `model_manifest.json` for model version, task type, input shape, and normalization parameters.
- **Label Mapping:** Reads `label_map.json` mapping classification indices to token characters and classes.
- **Preprocessing:** Applies standard OpenCV grayscale conversion, Otsu thresholding, aspect-ratio-preserving resize, and normalization.
- **Inference Boundary:** Gracefully raises `ModelNotAvailableError("Model artifact weights not present...")` when weights are absent, returning `MODEL_NOT_AVAILABLE` through the callback pipeline.
- **Zero Fabrication:** Does NOT invent mock predictions or fake bounding boxes when running in `MODEL` runtime mode.

---

## 9. Spring Gateway Implementation & Unit Tests

`HttpAiAnalysisGateway.java` was comprehensively tested with 8 unit tests in `HttpAiAnalysisGatewayTest.java`:

| # | Test Method | Tested Invariant | Result |
|---|---|---|---|
| 1 | `testAcceptedResponseSetsJobQueued` | HTTP 200 from AI service sets `AiJob` status to `QUEUED` | **PASS** |
| 2 | `testCorrectJobIdAndSubmissionIdSent` | Spring-generated `jobId` and `submissionId` match in payload | **PASS** |
| 3 | `testStudentPolicyModeSentForStudentSubmission` | Submissions without batch send `policyMode: STUDENT` | **PASS** |
| 4 | `testTeacherPolicyModeSentForTeacherBatchSubmission` | Submissions with batch send `policyMode: TEACHER` | **PASS** |
| 5 | `testTimeoutSetsJobFailed` | Gateway timeout sets `AiJob` status to `FAILED` | **PASS** |
| 6 | `testFastApiUnavailableSetsJobFailed` | FastAPI 503 response sets `AiJob` status to `FAILED` | **PASS** |
| 7 | `testGatewayConfigStubMode` | `STUB` configuration property returns `StubAiAnalysisGateway` | **PASS** |
| 8 | `testGatewayConfigFastApiMode` | `FASTAPI` configuration property returns `HttpAiAnalysisGateway` | **PASS** |

---

## 10. Distributed Transaction Decoupling & Callback Persistence

### Problem Discovered
When `BatchService.uploadImages` processed 10 images, Celery executed the deterministic validation task in ~18ms. When the Celery callback hit `POST /internal/v1/ai/jobs/{jobId}/callback`, the main Spring transaction had not committed yet. In PostgreSQL's default `READ COMMITTED` isolation, the callback thread could not find the `AiJob` entity, resulting in `HTTP 404 Job Not Found`.

Additionally, when attempting to run analysis after commit on the same thread, Hibernate threw `LazyInitializationException` because the Hibernate session was closed.

### Solution
1. **TransactionTemplate in Gateway:** `HttpAiAnalysisGateway` uses `TransactionTemplate` to create and commit `AiJob` to PostgreSQL synchronously *before* initiating the outbound HTTP call to FastAPI.
2. **Network Calls Outside DB Transactions:** Outbound HTTP network calls to FastAPI are executed outside any active database transaction, eliminating connection holding and race conditions.
3. **Asynchronous afterCommit Execution:** Both `BatchService` and `SubmissionService` trigger analysis inside `TransactionSynchronization.afterCommit` via `CompletableFuture.runAsync()`. Submissions and images are fully committed to PostgreSQL before background AI processing begins.
4. **Idempotent Callback Controller:** `InternalAiCallbackController` handles callbacks transactionally, safely ignores duplicate callbacks, persists `AnalysisResult` (including `gradeProposal`, `studentFeedback`, `evidence`, and `confidenceBundle`), and transitions submission status.

---

## 11. True Cross-Process Real-Stack E2E Verification

Verified via `scratch/run_real_stack_e2e.py` running against:
- Spring Boot on `http://localhost:8080`
- FastAPI on `http://localhost:8000`
- Celery worker on Redis `redis://localhost:6379/0`
- PostgreSQL on `localhost:5432`

### Scenario 1: Student True E2E
- **Input:** Student camera submission (`addition-carry-error.jpg`)
- **Pipeline:** Spring (`AiJob` `e45f81ec...`) → FastAPI → Celery → Spring Callback (`HTTP 200`)
- **Verification:**
  - `AiJob.status`: `COMPLETED`
  - `Submission.status`: `FEEDBACK_READY`
  - `AnalysisResult.status`: `FEEDBACK_READY`
  - `studentFeedback.revealAnswer`: `false`
  - `studentFeedback.hint`: `"Hãy kiểm tra lại Hàng chục nhé. Phép tính này có nhớ/mượn không em?"`
  - `studentFeedback.title`: `"Bài làm cần xem lại"`
- **Result:** **PASS**

### Scenario 2: Teacher Confident Invalid True E2E
- **Input:** Teacher batch submission (10 images including `addition-carry-error.jpg`)
- **Pipeline:** Spring (`AiJob` `3819f1fa...`) → FastAPI → Celery → Spring Callback (`HTTP 200`)
- **Verification:**
  - `AiJob.status`: `COMPLETED`
  - `Submission.status`: `PROPOSED_GRADE`
  - `AnalysisResult.status`: `PROPOSED_GRADE`
  - `gradeProposal.isOfficial`: `false`
  - `gradeProposal.suggestedScore`: `0`
  - `gradeProposal.maxScore`: `10`
  - `gradeProposal.reason`: `"Phép tính không chính xác: 45 + 27 = 62. Lỗi được phát hiện ở cột sớm nhất."`
  - `evidence.items`: 1 item (`CARRY_BORROW_ERROR`, `ADD_COL_MISMATCH`, placeValue `"Hàng chục"`)
  - `TeacherDecision`: 0 records (absent as required)
- **Result:** **PASS**

### Scenario 3: Teacher Uncertain Recognition True E2E
- **Input:** Teacher batch submission containing ambiguous digit image (`ambiguous.jpg`)
- **Pipeline:** Spring (`AiJob` `99cfb60e...`) → FastAPI → Celery → Spring Callback (`HTTP 200`)
- **Verification:**
  - `AiJob.status`: `COMPLETED`
  - `Submission.status`: `REVIEW_REQUIRED`
  - `AnalysisResult.status`: `REVIEW_REQUIRED`
  - `TeacherDecision`: 0 records (absent as required)
  - Invariant confirmed: `PROPOSED_GRADE` (invalid) ≠ `REVIEW_REQUIRED` (uncertain)
- **Result:** **PASS**

### Callback Status Audit
- Total Celery HTTP callbacks sent: 11
- HTTP 2xx callbacks received: **11/11 (100%)**
- HTTP 4xx errors: **0**
- HTTP 5xx errors: **0**

---

## 12. Full Regression Test Summary

| Test Suite | Commands | Target | Passed | Failed | Result |
|---|---|---|---|---|---|
| **Python AI Subsystem** | `pytest tests/ -q` | FastAPI, Celery, Validator, Policy, Quality | 71 | 0 | **100% PASS** |
| **Spring Boot Unit Tests** | `gradlew.bat test --tests *HttpAiAnalysisGatewayTest` | Gateway HTTP, Headers, Policy, Timeout | 8 | 0 | **100% PASS** |
| **Spring Boot Full Suite** | `gradlew.bat test` | Auth, Submission, Batch, Audit, State Transitions | 14 | 0 | **100% PASS** |
| **Real Cross-Stack E2E** | `python scratch/run_real_stack_e2e.py` | Student + Teacher Confident + Teacher Uncertain | 3 | 0 | **100% PASS** |

---

## 13. Subsystem Freeze & Defense Summary

The AI Runtime subsystem foundation is complete, verified, and refrozen:

1. **AI Runtime Status:** `FROZEN`
2. **Model Handoff Status:** `READY_FOR_MODEL`
3. **Student Mobile Status:** `FROZEN` (0 files modified)
4. **Teacher Web Status:** `FROZEN` (0 files modified)
5. **Deterministic Arithmetic Validator:** Serves as the sole mathematical authority. No mathematical verification is delegated to learned weights or LLMs.
6. **VLM Integration Scope:** Restricted strictly to zero-shot comparison benchmarks and constrained wording assistance; never in the primary mathematical evaluation path.
