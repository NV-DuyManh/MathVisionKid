# Phase 4.0.4 — Final AI Contract Hardening, Regression Verification & Documentation Refreeze Report

**Date:** September 8, 2026  
**Status:** READY_FOR_REVIEW  
**Target Environment:** Spring Boot 3.3.6 (Java 21) ↔ FastAPI 0.115 (Python 3.12) ↔ Celery 5.4.0 ↔ Redis 7 ↔ PostgreSQL 16 ↔ MinIO S3 Object Storage  

---

## 1. Executive Summary

Phase 4.0.4 successfully executed targeted contract hardening across the AI subsystem and the Spring Boot Business API, validated zero test loss through an exhaustive Gradle discovery audit, aligned teacher grading policy documentation with runtime semantics, bounded the role of future Vision-Language Models (VLMs), scrubbed all production credentials from project artifacts, and finalized the refreeze of both the AI Runtime and Spring Boot services.

All acceptance criteria are satisfied with zero test regressions:
- Spring Boot clean test suite: **49/49 tests passed (100%)** across 8 test suites.
- Python AI subsystem suite: **76/76 tests passed (100%)**.
- True cross-process real-stack E2E flows (Student, Teacher Confident Invalid, Teacher Uncertain): **3/3 passed (100%)** with HTTP 200 callbacks.
- Student Mobile, Teacher Web, and AI Training workspaces remain completely untouched.

---

## 2. Canonical Job Ownership

The canonical job ownership rule established in Phase 4.0.3 was hardened:
- **Authority:** Spring Boot owns the `AiJob` entity lifecycle and generates the canonical `jobId` (`UUID`).
- **Data Flow:** Spring Boot persists `AiJob` synchronously via `TransactionTemplate` before initiating the outbound network call to FastAPI.
- **Pipeline Preservation:** The canonical `jobId` travels identically through:
  ```
  Spring Boot (creates & commits AiJob)
    → POST /internal/v1/jobs (FastAPI receives required jobId: UUID)
    → Redis broker (Celery task process_submission(job_id, ...))
    → Celery worker (executes pipeline under correlation context)
    → POST /internal/v1/ai/jobs/{jobId}/callback (sends callback using Spring jobId)
    → Spring Boot InternalAiCallbackController (locates AiJob, updates state, persists AnalysisResult)
  ```
- **Prohibition:** FastAPI never silently generates or replaces a `jobId` in production.

---

## 3. Required jobId Contract

The FastAPI `JobRequest` schema was updated to strictly require `jobId: UUID`:

```python
class JobRequest(BaseModel):
    jobId: UUID = Field(..., description="Spring-owned canonical jobId (required)")
    submissionId: str
    imageReference: str
    allowedOperations: List[str]
    maxDigits: int = 3
    oneExerciseOnly: bool = True
    policyVersion: str = "v1.2"
    policyMode: str = "STUDENT"
```

- If `jobId` is omitted from `POST /internal/v1/jobs`, FastAPI automatically rejects the request with `HTTP 422 Unprocessable Entity`.
- If `jobId` is malformed (not a valid UUID string), FastAPI rejects the request with `HTTP 422 Unprocessable Entity`.

---

## 4. jobId Correlation Tests

Automated regression tests in `tests/test_api.py` verify the hardened `jobId` contract:
- `test_submit_job_missing_job_id_fails_validation`: omitting `jobId` triggers HTTP 422 with location pointer `['body', 'jobId']`.
- `test_submit_job_invalid_job_id_fails_validation`: malformed UUID strings trigger HTTP 422.
- `test_submit_job_with_spring_job_id`: verifies that a Spring-supplied UUID string is accepted, returned in `JobResponse(jobId=...)`, and forwarded identically to `process_submission.delay(job_id, request_data)`.

---

## 5. Teacher Policy

Teacher policy in `app/policy/teacher_policy.py` and documentation in `report/phase_4_0_ai_defense_notes.md` (Sections 24–26) are fully aligned:

```
VALID_STRUCTURE + is_valid = True   → PROPOSED_GRADE (suggestedScore: 10, clean pass)
VALID_STRUCTURE + is_valid = False  → PROPOSED_GRADE (suggestedScore: 0, advisory error reason, error evidence, isOfficial: False)
UNCERTAIN_STRUCTURE                 → REVIEW_REQUIRED (uncertainty evidence, teacher review of raw image)
OUT_OF_SCOPE                        → OUT_OF_SCOPE
```

---

## 6. PROPOSED_GRADE Semantics

`PROPOSED_GRADE` is a confident advisory grading proposal emitted for both confidently correct and confidently incorrect supported work:
- **Correct Work:** `suggestedScore=10`, `maxScore=10`, `confidence=0.97`, reason confirms arithmetic correctness, `isOfficial=False`.
- **Incorrect Work:** `suggestedScore=0`, `maxScore=10`, `confidence=0.93`, reason identifies earliest error column (e.g. "Hàng chục"), accompanied by deterministic error evidence (`ADD_COL_MISMATCH`), `isOfficial=False`.
- In neither case is `isOfficial` set to `True` automatically. Human teacher action is required.

---

## 7. REVIEW_REQUIRED Semantics

`REVIEW_REQUIRED` is emitted **ONLY** when the system lacks sufficient safe evidence for a confident automated proposal (e.g., ambiguous handwritten digits, occluded numbers, irregular layout).
- **Critical Semantic Invariant:** `REVIEW_REQUIRED` does **NOT** mean "student answer is mathematically incorrect."
- If an arithmetic calculation error is confidently diagnosed, the system emits `PROPOSED_GRADE` with score 0 and error evidence so the teacher can review the exception in one click.

---

## 8. VLM Boundary

Section 32 of `report/phase_4_0_ai_defense_notes.md` strictly delimits the architectural scope of future Vision-Language Models:
1. **Permitted Roles:**
   - Zero-shot comparison experiments against the dedicated OCR + Deterministic Validator pipeline.
   - Constrained hint/context wording assistance under strict pedagogical templates.
2. **Prohibited Roles:**
   - **Mathematical Correctness Authority:** VLMs hallucinate reasoning steps and cannot serve as the source of arithmetic truth. Pure deterministic Python rules serve as the sole mathematical authority.
   - **Required Layout Authority:** Column alignment, carry/borrow detection, and spatial tokens are resolved by deterministic structured parsing; VLMs are never a required dependency for layout authority.

---

## 9. Secret Scrub

An audit of all reports, documentation, and configuration files was completed:
- `report/phase_4_0_3_ai_runtime_freeze.md`: replaced cleartext MinIO credentials with `<redacted>` and environment variable references.
- `report/phase_4_0_ai_defense_notes.md`: verified zero cleartext passwords or keys.
- `.env.example`: verified all credentials use template placeholders (`your_minio_access_key`, `secret-key-default`).
- `docker-compose.yml`: documented that local container passwords are for isolated local development only.

---

## 10. MinIO Configuration

Runtime MinIO credentials in `app/config.py` are loaded dynamically via `BaseSettings`:
- Configured parameters: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`.
- Literal fallbacks in code are strictly annotated as local development defaults.
- Live production deployments inject credentials exclusively through environment variables.
- Secrets are never printed in logs or reports.

---

## 11. Model Preprocessing Contract

`ModelRecognitionEngine` in `app/recognition/model_engine.py` implements a manifest-driven preprocessing contract:
- Preprocessing pipelines are configured strictly based on `ModelManifest.preprocessing`.
- The engine does **not** force grayscale or Otsu thresholding unless the manifest explicitly requests `GRAYSCALE_OTSU`.
- If preprocessing is unspecified in the manifest, the engine configures a non-destructive `PASSTHROUGH` pipeline with original color mode.
- Supported strategies:
  - `GRAYSCALE_OTSU`: grayscale conversion, Otsu thresholding, `DIV_255` normalization, single channel.
  - `RGB_NORMALIZED` / `resize_224_normalize` / `normalize_imagenet`: RGB color mode, standard score / ImageNet normalization, 3 channels.
  - `RESIZE_ONLY`: RGB color mode, resize without binarization or normalization.

---

## 12. Preprocessing Tests

Automated regression suite `tests/test_model_preprocessing.py` verifies the contract:
- `test_two_different_manifests_produce_distinct_preprocessing_pipelines`: verifies `GRAYSCALE_OTSU` (28x28x1, Otsu, grayscale) produces a distinct pipeline from `RGB_NORMALIZED` (224x224x3, standard score, RGB) without frontend or Spring Boot changes.
- `test_unsupported_preprocessing_strategy_fails_clearly`: verifies that an unsupported strategy raises `UnsupportedPreprocessingError` with an actionable error message listing supported strategies.
- `test_unspecified_preprocessing_does_not_force_otsu`: verifies that omission of preprocessing defaults to `PASSTHROUGH` preserving RGB colors and avoiding Otsu binarization.

---

## 13. Spring Test Discovery Audit

Investigation into the historical test count reporting inconsistency:

### Finding
- Prior phase reports mentioned "41 Spring tests", while Phase 4.0.3 reported "14 full-suite tests + 8 gateway-specific tests".
- An exhaustive audit of `build/test-results/test/*.xml` was conducted without test filters.
- **Root Cause:** In Phase 4.0.3, "14 full-suite tests" was a typographical error from reading Gradle's task summary during a partial run.
- **Actual Discovery:** All 8 test suites were present, discovered, and executed.
- The 41 baseline tests + 8 newly added `HttpAiAnalysisGatewayTest` tests equal exactly **49 tests**.
- **Test Loss:** **ZERO**.

### Detailed Test Discovery Breakdown

| Test Suite Class | Tests | Failures | Skipped | Execution Time |
|---|---|---|---|---|
| `BusinessApiApplicationTests` | 1 | 0 | 0 | 11.16s |
| `HttpAiAnalysisGatewayTest` | 8 | 0 | 0 | 1.21s |
| `InternalAiCallbackControllerTest` | 4 | 0 | 0 | 4.54s |
| `AuthControllerTest` | 4 | 0 | 0 | 3.29s |
| `BatchControllerTest` | 7 | 0 | 0 | 2.77s |
| `TeacherDashboardControllerTest` | 4 | 0 | 0 | 0.18s |
| `StateTransitionTest` | 16 | 0 | 0 | 2.42s |
| `SubmissionControllerTest` | 5 | 0 | 0 | 0.19s |
| **Total** | **49** | **0** | **0** | **25.76s** |

---

## 14. Full Spring Regression

- Command: `.\gradlew.bat clean test`
- Results:
  - Discovered test classes: **8**
  - Total tests: **49**
  - Passed: **49**
  - Failed: **0**
  - Skipped: **0**
  - Status: **BUILD SUCCESSFUL**

---

## 15. Spring Build

- Command: `.\gradlew.bat build`
- Tasks: `compileJava`, `processResources`, `classes`, `bootJar`, `jar`, `assemble`, `compileTestJava`, `test`, `check`, `build`
- Status: **BUILD SUCCESSFUL** (0 errors, 7 actionable tasks)

---

## 16. Python Regression

- Command: `python -m pytest tests/ -v`
- Results:
  - Total tests: **76**
  - Passed: **76**
  - Failed: **0**
  - Skipped: **0**
  - Execution time: **0.77s**
  - Status: **100% PASS**

---

## 17. Student True E2E

- Flow: Student camera submission (`addition-carry-error.jpg`)
- Pipeline: Spring Boot (`AiJob` `989274df...`) → FastAPI → Celery → Callback (`HTTP 200`)
- Verification:
  - `AiJob.status`: `COMPLETED`
  - `Submission.status`: `FEEDBACK_READY`
  - `AnalysisResult.status`: `FEEDBACK_READY`
  - `studentFeedback.revealAnswer`: `false`
  - `studentFeedback.hint`: `"Hãy kiểm tra lại Hàng chục nhé. Phép tính này có nhớ/mượn không em?"`
  - `studentFeedback.focusEvidenceId`: `"err_add_1"`
- Status: **PASS**

---

## 18. Teacher Confident Invalid True E2E

- Flow: Teacher batch submission (10 images including `addition-carry-error.jpg`)
- Pipeline: Spring Boot (`AiJob` `7fbefc32...`) → FastAPI → Celery → Callback (`HTTP 200`)
- Verification:
  - `AiJob.status`: `COMPLETED`
  - `Submission.status`: `PROPOSED_GRADE`
  - `AnalysisResult.status`: `PROPOSED_GRADE`
  - `gradeProposal.suggestedScore`: `0`
  - `gradeProposal.maxScore`: `10`
  - `gradeProposal.isOfficial`: `false`
  - `gradeProposal.reason`: `"Phép tính không chính xác: 45 + 27 = 62. Lỗi được phát hiện ở cột sớm nhất."`
  - `evidence.items`: 1 item (`ADD_COL_MISMATCH`, "Hàng chục")
  - `TeacherDecision` count: `0` (absent as required)
- Status: **PASS**

---

## 19. Teacher Uncertain True E2E

- Flow: Teacher batch submission containing ambiguous digit (`ambiguous.jpg`)
- Pipeline: Spring Boot (`AiJob` `c190a6fd...`) → FastAPI → Celery → Callback (`HTTP 200`)
- Verification:
  - `AiJob.status`: `COMPLETED`
  - `Submission.status`: `REVIEW_REQUIRED`
  - `AnalysisResult.status`: `REVIEW_REQUIRED`
  - `TeacherDecision` count: `0` (absent as required)
  - Semantic invariant confirmed: `PROPOSED_GRADE` (invalid) ≠ `REVIEW_REQUIRED` (uncertain)
- Status: **PASS**

---

## 20. Callback Results

- Total callbacks received by Spring Boot during E2E verification: 11
- HTTP 2xx callbacks: **11/11 (100%)**
- HTTP 4xx errors: **0**
- HTTP 5xx errors: **0**

---

## 21. Model Artifact Status

`MODEL ARTIFACT: NOT_PROVIDED`

Trained weights (`.pt`, `.onnx`) have not been provided by the AI/ML training team. The runtime operates with deterministic fixtures in `FIXTURE` mode and raises graceful `ModelNotAvailableError` in `MODEL` mode.

---

## 22. Runtime Model Readiness

`RUNTIME: READY_FOR_MODEL`

The runtime environment is technically prepared to consume trained model artifacts:
1. Canonical `jobId` strictly required and propagated.
2. Real private MinIO S3 object storage verified (`minio://`).
3. `ModelManifest` schema and checksum verification implemented.
4. `ModelRecognitionEngine` adapter boundary established.
5. Preprocessing configuration strictly manifest-driven.
6. Missing artifacts fail gracefully without process crashes.
7. Unsupported formats fail clearly.
8. Zero changes required to Spring Boot, Student Mobile, or Teacher Web when model weights are introduced.

---

## 23. Student Files Modified

- Student Mobile files modified in Phase 4.0.4: **NONE (0 files)**
- Status: **FROZEN**

---

## 24. Teacher Files Modified

- Teacher Web files modified in Phase 4.0.4: **NONE (0 files)**
- Status: **FROZEN**

---

## 25. AI Training Files Modified

- AI training workspace files modified: **NONE (0 files)**
- Model training performed: **NO**

---

## 26. Remaining Limitations

1. **Model Weights Absent:** Real optical character recognition depends on delivery of trained weights from the AI training team.
2. **Quality Gate Heuristics:** Image quality analysis is currently tag-based; full OpenCV blur/brightness algorithms await trained image dataset characteristics.
3. **Multiplication/Division:** The validator currently supports vertical addition and vertical subtraction. Multiplication and division are marked `OUT_OF_SCOPE`.

---

## 27. Proposal Targets Unevaluated

Formal model evaluation metrics (precision, recall, F1, latency at scale) remain unevaluated until real model artifacts are trained and benchmarked against real student test datasets.

---

## 28. Defense Notes Status

`report/phase_4_0_ai_defense_notes.md` is updated and synchronized with Phase 4.0.4 contracts:
- Title updated to include Phase 4.0.4.
- Sections 24–26 updated with exact `PROPOSED_GRADE` and `REVIEW_REQUIRED` semantics.
- Section 32 updated with strict VLM role limitations.
- All credential exposures scrubbed.

---

## 29. AI Runtime Freeze Status

**FROZEN**

---

## 30. Spring Status

**REFROZEN**

---

## 31. Model Runtime Status

**READY_FOR_MODEL**

---

## 32. Phase Completion Assessment

**READY_FOR_REVIEW**

---

## 33. Recommended Next Step

Await delivery of the trained digit/operator recognition model artifact (`.onnx` or `.pt`) and `model_manifest.json` from the AI/ML training team. Verify model ingestion using `ModelRecognitionEngine` without altering business logic or frontends.
