# MathVision Kids
## Phase 2.5.1 — Final Contract Audit & Freeze Preparation

### 1. Executive Summary
Conducted a final audit of the canonical contracts before Spring Boot backend development begins. Expanded the OpenAPI specification to cover all required endpoints, normalized shared typescript definitions, standardized error handling via `ApiErrorResponse`, and created comprehensive valid JSON examples. The contracts are now aligned with architectural decisions.

### 2. Project Relocation Reference
Reference: `report/project_relocation_F_to_D.md`

### 3. Previous Contract Gaps
The previous contracts missed multiple Teacher and Student endpoints, lacked explicit models for domain entities (User, Student, Teacher, etc.) in OpenAPI, had incomplete batch lifecycle management, used raw JSON in multipart payloads for batch upload, and lacked valid JSON examples. 

### 4. Contract Files Reviewed
- `contracts/openapi/mathvision-api.yaml`
- `contracts/ai/ai-contract.md`
- `contracts/ARCHITECTURE_DECISIONS.md`
- `contracts/BREAKING_CHANGES.md`
- `contracts/examples/*.json`
- `packages/shared-contracts/src/*.ts`

### 5. Canonical Domain Model
Added `User`, `Student`, `Teacher`, `ClassRoom`, and `Assignment` interfaces to `shared-contracts` and OpenAPI components.

### 6. Canonical Enums
Validated `SubmissionStatus`, `Decision`, `OperationType`, `ErrorType`, `ImageQualityIssue`, `ReviewReason`, `TeacherDecisionType`, and `BatchStatus`.

### 7. Submission State Machine
- `CREATED` -> `IMAGE_UPLOADED` -> `PROCESSING`
- `PROCESSING` -> `FEEDBACK_READY` | `NEEDS_CONFIRMATION` | `NEEDS_RETAKE` | `CROP_REQUIRED` | `REVIEW_REQUIRED` | `OUT_OF_SCOPE` | `FAILED`
- `NEEDS_CONFIRMATION` -> `PROCESSING`
- `NEEDS_RETAKE` | `CROP_REQUIRED` -> `IMAGE_UPLOADED` -> `PROCESSING`
- `FEEDBACK_READY` | `REVIEW_REQUIRED` -> `TEACHER_APPROVED` | `TEACHER_OVERRIDDEN`

### 8. Batch State Model
Normalized to: `CREATED`, `UPLOADING`, `QUEUED`, `PROCESSING`, `COMPLETED`, `PARTIAL`, `FAILED`. Removed `REVIEW_REQUIRED` as a state; replaced with `reviewRequiredCount`.

### 9. Student API
Added `POST /api/v1/student/submissions/{submissionId}/retry`.

### 10. Teacher API
Added endpoints for dashboard, classes, classes/{classId}, assignments, assignments/{assignmentId}, and submissions/{submissionId}. Updated multipart upload for batches.

### 11. Authentication API
Added `GET /api/v1/me`. Verified `POST /api/v1/auth/login`.

### 12. Retry Contract
`POST /api/v1/student/submissions/{submissionId}/retry` added for resuming failed states.

### 13. Evidence Contract
Evidence model and example JSON are provided.

### 14. Bounding Box Convention
Defined in ADR-006: normalized floats `[0.0, 1.0]`, top-left origin.

### 15. Confidence Contract
Defined as a probability from 0.0 to 1.0, isolated from `ErrorType`.

### 16. Student Feedback Contract
Added `StudentFeedback` interface with `title`, `hint`, `focusEvidenceId`, `revealAnswer`, `answer`.

### 17. Grade Proposal
`GradeProposal` requires `isOfficial: false` before teacher action.

### 18. Teacher Decision
Includes `APPROVE` and `OVERRIDE` types with explicit reason fields.

### 19. AuditEvent
Added `AuditEvent` schema in TS and OpenAPI for action tracking.

### 20. Error Contract
Standardized all endpoints to return `ApiErrorResponse` wrapping `error: { code, message, requestId, details }`.

### 21. Image Contract
`imageReference` is isolated to internal AI endpoints. Clients use temporary `displayUrl`.

### 22. Batch Upload Contract
Updated `POST /teacher/batches/{batchId}/submissions` to use `images` array and optional `association_metadata` string instead of base64 JSON.

### 23. AI Internal Contract
Updated `contracts/ai/ai-contract.md` to define `POST /internal/v1/analyze-submission`.

### 24. OpenAPI Changes
Major restructuring to include all required APIs, correct request bodies, and consistent error schemas.

### 25. OpenAPI Validation
Validation executed using `@redocly/cli`. All syntax errors resolved.

### 26. JSON Example Validation
Total files: 10
Passed: 10
Failed: 0

### 27. Shared TypeScript Validation
Command: `npx tsc --noEmit`
Exit code: 0
Result: PASS

### 28. Student Mock Compatibility
Documented in `BREAKING_CHANGES.md`. Mismatches identified for future migration.

### 29. Teacher Mock Compatibility
Documented in `BREAKING_CHANGES.md`. Mismatches identified for future migration.

### 30. Breaking Changes
Major breaking changes include endpoint `v1` prefix, Batch lifecycle update, and Error schemas.

### 31. Architecture Decisions
Added ADR-008 (Polling), ADR-009 (v1 prefix), and ADR-010 (Batch review separation).

### 32. Security Boundaries
FastAPI remains strictly internal. Spring Boot manages all client requests.

### 33. Files Created
- `contracts/examples/*.json` (10 files)
- `packages/shared-contracts/src/domain.ts`
- `packages/shared-contracts/src/audit.ts`
- `packages/shared-contracts/src/api.ts`

### 34. Files Modified
- `contracts/openapi/mathvision-api.yaml`
- `contracts/ai/ai-contract.md`
- `contracts/ARCHITECTURE_DECISIONS.md`
- `contracts/BREAKING_CHANGES.md`
- `packages/shared-contracts/src/index.ts`

### 35. Files Deleted
None.

### 36. Commands Executed
- Git validations (`git status`, `git rev-parse`)
- Relocation via `robocopy`
- PowerShell JSON schema parsing
- `npx tsc --noEmit`
- `npx @redocly/cli lint`

### 37. Validation Results
- JSON Check: PASS
- TypeScript: PASS
- OpenAPI Lint: PASS

### 38. Known Limitations
Mock implementations in current frontends are deliberately allowed to temporarily remain incompatible until the backend integration phase.

### 39. Unresolved Contract Questions
None at this time.

### 40. Backend Readiness
Ready for Spring Boot schema generation.

### 41. Reviewer Guide
Please inspect `mathvision-api.yaml` for structural completeness. Note the BatchStatus simplifications.

### 42. Contract Freeze Recommendation
READY_TO_FREEZE

### 43. Phase Completion Assessment
READY_FOR_REVIEW

### 44. Recommended Next Step
Proceed to Phase 3 Backend Architecture initialization once manual contract freeze approval is granted.
