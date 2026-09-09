# Breaking Changes & Mock Compatibility Audit

## Student App Mismatches

| Area | Current Student | Canonical Target | Migration Needed |
|------|-----------------|------------------|------------------|
| Status | `FEEDBACK_READY`, `CROP_REQUIRED` | Same, mapped cleanly | **Minor**: Mostly aligned, but need to adapt to new target strings. |
| Validation | `Validation.columns` | `ValidationResult.columnResults` | **Rename**: Update property references in Student app. |
| Evidence | Implicit in `ColumnValidation` | Explicit `Evidence` model | **Major**: `ColumnValidation` now references `evidenceIds`. Need to update UI to read `Evidence` array. |
| Error Enum | `ErrorType` | `ErrorType` | **Keep**: Enum values match exactly. |
| Result Output | `ambiguousToken` | `confirmation` (ConfirmationCandidate) | **Rename & Structure**: Change how UI reads alternative candidates. |

## Teacher Web Mismatches

| Area | Current Teacher | Canonical Target | Migration Needed |
|------|-----------------|------------------|------------------|
| Status | `AI_CONFIDENT`, `OVERRIDDEN` | `FEEDBACK_READY`, `TEACHER_OVERRIDDEN` | **Rename**: Need to update `TeacherService` mapping. |
| Confidence | Flat `recognitionConfidence` | `ConfidenceBundle` | **Structure**: Migrate UI to read `confidence.recognition`. |
| Score | `suggestedScore`, `teacherScore` | `gradeProposal`, `teacherDecision` | **Major Structure**: Move from root fields into complex nested models. |
| Submission | `decision: string` | `validation.decision: Decision` | **Structure**: Read decision from `validation` instead of root. |

## State Mismatches

| Area | Change | Classification |
|------|--------|----------------|
| Endpoints | Endpoints must now map to `/api/v1` namespace. | **BREAKING** |
| Batch Lifecycle | `REVIEW_REQUIRED` is no longer a Batch status. It uses `reviewRequiredCount` while status is `COMPLETED`. | **BREAKING** |
| Multipart Upload | Batch upload includes optional JSON association_metadata rather than base64 JSON payload. | **MIGRATION_REQUIRED** |
| Errors | API returns standard `ApiErrorResponse` wrapping standard status codes. | **MIGRATION_REQUIRED** |

## Next Steps for Frontend Teams
Do NOT immediately rewrite the UI components. The next phase will implement the Spring Boot Backend. Once the backend is running, we will perform a dedicated "Integration Phase" to update both frontends to consume these exact canonical types.

## Track A1.1 Additive Role Extension: ADMIN
- Role enum extended from `[STUDENT, TEACHER]` to `[STUDENT, TEACHER, ADMIN]`.
- Classification: **NON_BREAKING (ADDITIVE)**. Existing Student and Teacher authentication, authorizations, and client contracts remain 100% backward-compatible. Admin endpoints are strictly isolated under `/api/v1/admin/**` with dedicated `hasRole('ADMIN')` authorization.

