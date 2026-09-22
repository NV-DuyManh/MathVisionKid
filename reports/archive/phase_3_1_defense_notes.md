# MathVision Kids
## Phase 3.1 Defense Notes

### 1. 30-Second System Explanation
MathVision Kids is an educational platform designed to streamline the grading of handwritten math assignments for grades 1–5. Students or teachers photograph completed math exercises, which are uploaded to a backend service. The system then orchestrates an AI-driven recognition pipeline to transcribe the handwritten equations, evaluates their correctness deterministically, and presents a proposed grade to the teacher for final approval or manual override.

### 2. High-Level Architecture
The system consists of three main boundaries:
- **Clients**: A web frontend for teachers and a mobile frontend for students. These handle authentication, PII masking (cropping out names), and image capture.
- **Business API (Spring Boot)**: A modular monolith that manages core business logic, RBAC authentication, persistence (PostgreSQL for metadata, MinIO for images), orchestration of the grading workflow, and exposing REST APIs.
- **AI/ML Subsystem (FastAPI)**: A dedicated python-based inference service that processes images asynchronously (via Celery/Redis) and calls back to the Business API with recognized text and bounding boxes.

### 3. Why Modular Monolith
A modular monolith was chosen for the Spring Boot application because the domain is cohesive and does not yet exhibit scaling requirements that justify the operational complexity of microservices. It ensures strict transactional boundaries (e.g. between file uploads and database records), simplifies deployment, and keeps domain logic localized while maintaining strong logical separation of components.

### 4. Why Spring Boot
Spring Boot provides mature ecosystem tooling, robust transaction management (Spring Data JPA), out-of-the-box security (Spring Security), and seamless integration with relational databases. Its enterprise capabilities perfectly suit the requirements of state machines, authentication, and REST API generation needed for this domain.

### 5. Why FastAPI Is Separate
FastAPI is used exclusively for the AI/ML subsystem because the python ecosystem dominates machine learning (PyTorch, ONNX). Mixing ML inference into the JVM is inefficient and difficult to maintain. Keeping FastAPI separate allows the AI logic to scale asynchronously on GPU-enabled hardware independently of the core business traffic.

### 6. Why Celery / Redis Are AI-Internal
Celery and Redis are used to decouple HTTP request ingestion from heavy GPU inference within the FastAPI boundary. They manage the internal queuing of inference jobs so that the Python service does not drop requests or block waiting for inference. The Spring Boot application is entirely unaware of this internal AI architecture, treating the FastAPI gateway as a standard async callback service.

### 7. AI/ML Teammate Responsibility
The AI/ML teammate owns the dataset preparation, annotation, model training, evaluation, and export. Their work occurs entirely within the `ai-training/` workspace, independently of the backend engineering.

### 8. AI Training Handoff
The backend provides a clear, documented workspace (`ai-training/`) with a defined annotation schema, label map, and model export manifest. This contract allows the AI teammate to deliver trained artifacts (such as models and evaluation metrics) directly into the deployment pipeline without needing to write Java code.

### 9. Why Model Export Is Manifest-Driven
Model exports are driven by a manifest to decouple the business logic from specific model architectures. Potential formats may include ONNX, TorchScript, PyTorch artifact, or Paddle export. The final format belongs to AI/ML experiment results, so no specific format is mandatory. The manifest defines input/output tensor shapes, normalization parameters, and versioning. This allows the AI engineer to swap models seamlessly without requiring backend code changes.

### 10. Recognition vs Correctness
- **Recognition**: "What did the student write?" - Handled by the AI model (OCR), which outputs transcription and layout evidence from an image.
- **Deterministic validator**: "Given the recognized supported arithmetic structure, does each step satisfy the mathematical rules?" - Handled by the Python AI subsystem, where recognition/layout output can be passed directly into deterministic arithmetic rules. Spring Boot receives and persists the structured result. Spring Boot does not execute the deterministic arithmetic engine.

### 11. Why Deterministic Validator Is Authority
The AI model is prone to hallucinations and arithmetic errors. Therefore, the AI is only trusted for OCR (transcription and layout evidence). The Deterministic Python Validator serves as the mathematical correctness authority, ensuring students are not incorrectly penalized by a neural network's inability to do math.

### 12. VLM Role
Vision Language Models (VLMs) may be utilized for an optional zero-shot comparison baseline and generating constrained hint wording. They are never used as the correctness authority. If the VLM conflicts with deterministic validation on critical evidence, the VLM must not override it. The system must use an abstention / confirmation / review policy instead.

### 13. Student End-to-End Flow
The student logs in, receives a JWT, selects an assignment, captures an image of their homework, masks PII locally, and uploads. The backend creates a submission, stores the image in MinIO, persists metadata in PostgreSQL, and submits an async job to the AI service. Once processed, the student can review the AI's transcribed equations and proposed grade. The student can then either confirm the submission or retry if the image was blurry or incorrectly cropped.

### 14. Teacher Batch End-to-End Flow
Teachers collect multiple student assignments, select a classroom, and upload a batch of 10-30 images at once. The frontend maps each image index to a student ID. The backend processes the upload transactionally, creating submissions for each student and forwarding the jobs to the AI service. The teacher can then review the batch results in their dashboard.

### 15. Async AI Job Flow
When a submission is created, Spring Boot registers an `AiJob` in the database with status `PROCESSING` and sends an async HTTP request to FastAPI. FastAPI enqueues the task via Celery. Once the inference completes, FastAPI sends a POST request with the results to the Spring Boot internal callback endpoint.

### 16. Authenticated FastAPI Callback
The callback endpoint (`/internal/v1/ai/jobs/{jobId}/callback`) is secured via a shared secret (`X-Internal-API-Key`). This internal credential prevents unauthorized external manipulation of grading outcomes, avoiding the reuse of standard JWTs which are scoped to users.

### 17. Callback Idempotency and Concurrency
If the AI service re-attempts a callback due to network timeouts, the Spring Boot endpoint leverages the `jobId` to guarantee idempotency. A basic status check provides idempotency semantics. If the `AiJob` status is already `COMPLETED`, the callback immediately returns a `200 OK` without duplicating state transitions or database records. Furthermore, `AiJob` uses optimistic locking (`@Version`) to protect against simultaneous duplicate callbacks (concurrent races). The system does not claim distributed exactly-once delivery.

### 18. Submission State Machine
Submissions flow through defined states. Invalid state transitions (e.g. retrying an approved submission) are explicitly rejected by the business logic.
- **Teacher confident grading**: `PROCESSING` -> `PROPOSED_GRADE` -> `TEACHER_APPROVED` or `TEACHER_OVERRIDDEN`
- **Teacher uncertain grading**: `PROCESSING` -> `REVIEW_REQUIRED` -> `TEACHER_APPROVED` or `TEACHER_OVERRIDDEN`
- **Student tutoring**: `PROCESSING` -> `FEEDBACK_READY` (or `NEEDS_CONFIRMATION`, `NEEDS_RETAKE`, `CROP_REQUIRED` as appropriate)

### 19. Batch State Model
Batches aggregate submission statuses. A batch transitions from `CREATED` -> `UPLOADING` -> `QUEUED` -> `PROCESSING` -> `COMPLETED` / `PARTIAL` / `FAILED`. Teacher attention is represented separately through `reviewRequiredCount` and submission-level states. Batch completion is determined when all associated submissions reach terminal states.

### 20. Image → Student Mapping
In batch uploads, images are associated with students via a `BatchImageMapping` DTO. This strictly relies on the frontend providing correct `studentId` references verified against the teacher's classroom roster. Filenames are ignored for identity to prevent injection or mismatched PII.

### 21. Authentication
Authentication is handled via Spring Security using stateless JWTs. Clients POST email and password to `/api/v1/auth/login` and receive short-lived access tokens and long-lived refresh tokens.

### 22. JWT Access Token
The access token is a signed JWT containing the user's subject (email) and role claims (`ROLE_STUDENT`, `ROLE_TEACHER`). It is sent in the `Authorization: Bearer` header and validated by `JwtAuthenticationFilter` on every protected request.

### 23. Refresh Token Rotation
Refresh tokens are stored as SHA-256 hashes in PostgreSQL to mitigate database breach impacts. When a client uses a refresh token at `/api/v1/auth/refresh`, the system issues a new JWT, revokes the used refresh token, and issues a new refresh token (rotation).

### 24. Logout / Revocation
Logging out (`/api/v1/auth/logout`) deletes all active refresh tokens for the user in the database. If a revoked refresh token is ever reused, the system treats it as a compromised session and revokes all active tokens for that user immediately.

### 25. RBAC
Role-Based Access Control (RBAC) ensures logical separation. Spring Security enforces `hasRole("TEACHER")` for teacher endpoints and `hasRole("STUDENT")` for student endpoints. Additionally, business logic validates that users only access resources (submissions, classrooms) they explicitly own.

### 26. PostgreSQL
PostgreSQL is the primary operational database, storing normalized relational data including Users, Classrooms, Assignments, Submissions, AiJobs, and AuditEvents. Migrations are managed via Flyway.

### 27. MinIO
MinIO provides S3-compatible object storage for all uploaded images. Images are kept separate from the PostgreSQL database to ensure high performance and scalability.

### 28. PostgreSQL + MinIO Consistency Problem
PostgreSQL and MinIO do not share one ACID transaction. If an image is successfully uploaded to MinIO but the subsequent PostgreSQL commit fails (e.g. constraint violation), the image becomes orphaned.
**Compensation Strategy**: The `BatchService` handles this via a programmatic try-catch block. The object is uploaded first. If the subsequent database `saveAndFlush()` fails, the catch block executes a best-effort `objectStorageService.delete()` to remove the orphaned file from MinIO before propagating the HTTP 500 error. This best-effort compensation reduces orphan risk but does not create true distributed atomicity (does not claim perfect consistency).

### 29. PII Privacy Boundary
The product requires Student Mobile and Teacher Web to perform privacy masking before image transmission. Relevant PII includes faces, student names, school names / school identifiers, and other obvious personal identifiers. The client flow may include automatic detection, blur/masking, manual correction, or retake depending on confidence.

Spring Boot receives the result after the client privacy gate, but does NOT independently guarantee that all visual PII has been removed. Images remain protected educational data.

### 30. Teacher Final Authority
Teachers maintain ultimate authority over the grading process. AI evaluations are always proposals. Submissions are not finalized until the teacher issues an explicit `approve` or `override` action.

### 31. Why AI Score Is Non-Official
The AI lacks pedagogical context (e.g., partial credit for a specific method). Its output (`GradeProposal.isOfficial = false`) is presented strictly as a recommendation. The `TeacherDecision` serves as the official record.

### 32. Teacher Overrides Are NOT Automatically Gold Labels
When a teacher overrides an AI grade, the new score represents the pedagogical outcome, not necessarily a ground-truth label for OCR retraining. The override may involve partial credit. Therefore, overrides are not automatically ingested as training data without explicit verification.

### 33. Audit Trail
All critical state transitions (AI processing started, teacher approved, student retried) are logged immutably in the `AuditEvent` table, linking the `Submission`, `User`, and `EventType` for debugging and accountability.

### 34. Error Handling
All API errors route through a `GlobalExceptionHandler` and return a canonical `ApiErrorResponse` (containing `errorCode`, `message`, `requestId`, and `details`). Native exceptions are wrapped in standard `ApiException` classes.

### 35. Request ID
A unique `RequestId` is generated for every incoming HTTP request and included in all log statements and error responses to facilitate trace correlation across the modular monolith.

### 36. OpenAPI
The API contract is exposed via `springdoc-openapi`. The OpenAPI JSON is available at `/api-docs` and a visual interface at `/swagger-ui.html`. The paths are explicitly whitelisted in the security configuration.

### 37. DVC
Data Version Control (DVC) is intended for the `ai-training/` workspace to version large image datasets and models without polluting the git history.

### 38. MLflow
MLflow will be used by the AI team to track training experiments, hyperparameter tuning, and evaluation metrics independently of the backend API.

### 39. If AI Service Is Offline
If the FastAPI service is unreachable during a batch upload, the `AiAnalysisGateway` handles the connection error, but the `AiJob` remains in the database in a `PROCESSING` state. This is a **CURRENT LIMITATION**, not the intended final behavior. The future AI subsystem should provide retry, timeout, failure classification, or a dead-letter/manual recovery policy.

### 40. If Duplicate Callback Arrives
Duplicate callbacks are safely ignored due to idempotency checks in `InternalAiCallbackController`. If the `AiJob` is already `COMPLETED`, the system returns `200 OK` and skips database updates.

### 41. Ambiguity States
Instead of generic low-confidence logic, the system uses specific states:
- `NEEDS_CONFIRMATION`: when a critical handwritten token is ambiguous and user confirmation can resolve it.
- `NEEDS_RETAKE`: when image quality is insufficient (blur, glare, severe skew, poor visibility).
- `CROP_REQUIRED`: when the selected exercise region is incomplete or must be adjusted.
- `REVIEW_REQUIRED`: when system evidence is insufficient for a safe automated teacher-grading conclusion.

### 42. If AI and Validator Disagree
The Deterministic Validator is the absolute authority. If the AI recognizes "2 + 2 = 5" but parses the math, the validator will mark it incorrect regardless of any LLM/VLM opinion.

### 43. If Teacher Disagrees With AI
The teacher can use the `/override` endpoint to supply a final score and a justification reason. This action finalizes the submission state and overrides any AI proposal.

### 44. Security Questions & Answers
- **Q**: How are passwords stored?
  - **A**: Passwords are hashed using BCrypt via Spring Security.
- **Q**: Are tokens vulnerable to XSS?
  - **A**: Tokens are returned in JSON payloads. Teacher Web should prefer a secure architecture such as HttpOnly/Secure/SameSite cookies where deployment design permits. Student native application should use secure device storage. Actual frontend integration strategy will be finalized in a later phase.
- **Q**: Why must PII masking occur before upload, not after storage in MinIO?
  - **A**: Because the backend boundary does not guarantee visual PII removal and images are protected educational data. Masking must occur at the client privacy gate.

### 45. Backend Questions & Answers
- **Q**: Is the database normalized?
  - **A**: Yes, the schema follows 3NF, separating users, classrooms, assignments, and submissions into distinct tables with foreign keys.
- **Q**: What is the difference between `PROPOSED_GRADE` and `REVIEW_REQUIRED`?
  - **A**: `PROPOSED_GRADE` means the system has a confident advisory grade, still awaiting teacher finalization. `REVIEW_REQUIRED` means the system cannot safely provide a confident automated conclusion, so teacher attention is specifically required.

### 46. AI Boundary Questions & Answers
- **Q**: Does the backend wait synchronously for inference?
  - **A**: No, the `aiAnalysisGateway` uses asynchronous background processing. The transaction completes immediately after enqueueing the job.
- **Q**: Why isn't Spring Boot responsible for checking the arithmetic?
  - **A**: Because the mathematical validation pipeline is part of the Python AI subsystem, where recognition/layout output can be passed directly into deterministic arithmetic rules. Spring Boot remains responsible for business state and orchestration.
- **Q**: Why not let a VLM decide whether the answer is correct?
  - **A**: Because the MVP arithmetic scope is deterministic. A rule engine is reproducible and auditable, while VLM outputs may vary or hallucinate.

### 47. Database Questions & Answers
- **Q**: How are migrations managed?
  - **A**: Flyway automatically executes `.sql` scripts located in `db/migration/` on startup.

### 48. Testing Questions & Answers
- **Q**: How are controller transactions isolated?
  - **A**: Integration tests use `@AutoConfigureMockMvc` which binds HTTP requests to the same thread as the JUnit `@Transactional` proxy, ensuring proper test data rollback.

### 49. Advanced Debugging Decisions

- **MockMvc transaction leakage**: Tests running with `SpringBootTest.WebEnvironment.RANDOM_PORT` launch the embedded Tomcat server in a separate thread. This separate thread creates its own Hikari connection pool connections which execute independently of the JUnit test runner's `@Transactional` wrapper, meaning test database rollbacks silently fail. Solution: We moved controller integration testing to `@AutoConfigureMockMvc` which runs in the same thread.
- **MinIO orphan risk**: If an image upload batch succeeds in uploading chunks to MinIO but fails to persist in the PostgreSQL database, MinIO houses orphaned images. Solution: A manual try-catch block deletes the object from MinIO if `saveAndFlush()` fails.
- **ApiException / HTTP 500 issue**: Broad `catch (Exception e)` blocks within the controller swallowed `ApiException` instances and re-wrapped them into `RuntimeException`, causing 500 errors instead of 400. Solution: Explicitly let Spring MVC implicitly throw `ApiException` to the `@ExceptionHandler(ApiException.class)`.
- **OpenAPI whitelist**: `springdoc-openapi-starter-webmvc-ui` failed to generate OpenAPI specs correctly because `/api-docs` was blocked by Spring Security. Solution: Updated `SecurityConfig` to use `.requestMatchers("/api-docs/**", "/swagger-ui/**").permitAll()`.
- **FK cleanup ordering**: Repositories throw DataIntegrityViolation when attempting to delete users linked to classrooms during test teardown. Solution: Hardened test teardowns to clear data in the correct topological order.

### 50. Live Coding Preparation
Team members should be familiar with important code areas:
- `TeacherDashboardController` / `DashboardService`
- `SubmissionService` state transitions
- `BatchService` image mapping and MinIO transaction compensation
- `RefreshTokenService`
- `InternalAiCallbackController`
- `AiJob` optimistic locking
- `ObjectStorageService` / `MinioObjectStorageService`
- `GlobalExceptionHandler`
- `SecurityConfig` / `JwtAuthenticationFilter`

### 51. Current Limitations
- The system currently uses an internal `AiAnalysisGateway` stub. The real FastAPI interface will require a true HTTP client.
- No production-readiness claims are made regarding distributed caching, rate limiting, or autoscaling.
