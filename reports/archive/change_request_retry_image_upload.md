# Change Request: Retry Image Upload

## 1. Overview
The initial frozen backend contract for the retry submission process assumed that a retry would create a completely new `Submission` entity. However, this broke the audit trail and the relationship between the initial failure and the subsequent retries. Furthermore, the `SubmissionService` retry signature did not accept the physical image file.

## 2. Description of Changes
**Contract Update**: 
*   Added `multipart/form-data` request body to `/api/v1/submissions/{id}/retry` in OpenAPI spec.
*   Updated `StudentSubmissionController` to accept `MultipartFile` and a `source` parameter on the retry endpoint.

**Business Logic Update**:
*   Modified `SubmissionService.retrySubmission(UUID id, MultipartFile file, String source)` to accept the file.
*   The system now uploads the new image to storage and creates a new `SubmissionImage` associated with the *existing* `Submission`.
*   The `Submission` status is reset from `NEEDS_RETAKE` to `PROCESSING`.
*   All temporary analysis hints, text zones, and previous validation flags are cleared to ensure a fresh processing pipeline cycle.

**Test Updates**:
*   Updated `StateTransitionTest` to mock `ObjectStorageService` and provide `MockMultipartFile` during the retry transition tests.

## 3. Impact
This change request enables the Student mobile client to correctly upload retry images while allowing the backend to preserve the continuous audit trail of a student's single homework submission effort. The backend is now refrozen.
