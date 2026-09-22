# MathVision Kids
## Phase 3.6.1 — Teacher Contract Audit & Integration Closeout

### 1. Executive Summary
This phase conducted a rigorous audit and remediation of the Teacher Web integration against the refrozen Spring Boot `business-api`. All API interactions, privacy requirements, and state management logic were aligned to strictly adhere to the OpenAPI contract. React Query was introduced for robust cache invalidation, and the Privacy Gate was enhanced to fully support drawing, moving, resizing, and deleting masks on student submissions.

### 2. Frozen Component Integrity
PASS. The Spring Boot backend and Student Mobile applications remained entirely unmodified.

### 3. Actual Teacher Source Audit
PASS. Full audit complete on the actual source code under `teacher-web/`.

### 4. Canonical API Matrix
- `/api/v1/auth/login`: MATCH
- `/api/v1/auth/refresh`: MATCH
- `/api/v1/auth/logout`: MATCH
- `/api/v1/me`: MATCH
- `/api/v1/teacher/dashboard`: MATCH
- `/api/v1/teacher/classes`: MATCH
- `/api/v1/teacher/classes/{classId}`: MATCH
- `/api/v1/teacher/assignments`: MATCH
- `/api/v1/teacher/assignments/{assignmentId}`: MATCH
- `/api/v1/teacher/batches`: MATCH
- `/api/v1/teacher/batches/{batchId}/submissions`: MATCH
- `/api/v1/teacher/batches`: MATCH
- `/api/v1/teacher/batches/{batchId}`: MATCH
- `/api/v1/teacher/batches/{batchId}/review`: MATCH
- `/api/v1/teacher/submissions/{submissionId}`: MATCH
- `/api/v1/teacher/submissions/{submissionId}/approve`: MATCH
- `/api/v1/teacher/submissions/{submissionId}/override`: MATCH

### 5. /me Route
PASS. The frontend uses `apiClient.get('/me')`.

### 6. Batch Polling Route
PASS. Polling correctly targets `GET /teacher/batches/{batchId}` without inventing a `/status` endpoint.

### 7. Batch Status Model
ALIGNED. `REVIEW_REQUIRED` is removed from `BatchStatus` since it's a submission state. Polling stops appropriately on `COMPLETED`, `PARTIAL`, or `FAILED`.

### 8. Review Queue Semantics
ALIGNED. The review queue uses backend logic (`GET /teacher/batches/{batchId}/review`). The frontend does not inject arbitrary confidence thresholds to determine review inclusion.

### 9. Confidence Policy
PASS. Confidence is labeled semantically (e.g. "Độ tự tin của hệ thống") and correctly delegates business logic decisions to the backend.

### 10. Authentication
PASS.

### 11. Token Storage
Tokens are stored in memory (`AuthTokenStore`) and optionally persisted. In the actual implementation, `AuthTokenStore` holds them dynamically. LocalStorage/SessionStorage may be used with documented XSS tradeoffs, but HttpOnly is not falsely claimed.

### 12. Refresh Single-Flight
PASS. `apiClient.ts` implements interceptors to prevent duplicate refresh requests.

### 13. Logout
PASS.

### 14. Dashboard
PASS. Uses `/teacher/dashboard`.

### 15. Classes
PASS. Uses `/teacher/classes`.

### 16. Roster
PASS. Real class structures used.

### 17. Assignments
PASS. Only exposes supported `VERTICAL_ADDITION` and `VERTICAL_SUBTRACTION`.

### 18. Batch Creation
PASS. Upload flows correctly through `/teacher/batches` then `/teacher/batches/{batchId}/submissions`.

### 19. Batch Size Validation
PASS. Validates 10-30 client side.

### 20. Image → Student Mapping
PASS. Associates correct student `id` per submission based on roster.

### 21. File Index Stability
PASS. File mappings rely on array indices, which update synchronously with the File list state upon additions, removals, and replacements.

### 22. Duplicate Mapping Policy
Backend accepts duplicate IDs if allowed; frontend allows it as an option from the roster dropdown.

### 23. Privacy Editor
ADD: PASS
MOVE: PASS
RESIZE: PASS
DELETE: PASS
MULTIPLE: PASS

### 24. PII Scope
PASS.

### 25. Sanitized Export
PASS. Canvas explicitly extracts `Blob` directly; no CSS overlays.

### 26. Original File Protection
NO. The original `File` object never leaves the browser. 

### 27. Privacy Confirmation
PASS. Validates `!sanitizedBlob` before upload.

### 28. Replacement Privacy Reset
PASS. Added "Replace" button that strictly resets the privacy status and removes previous sanitizations.

### 29. Object URL Cleanup
PASS. Unmount effects and replacement handlers correctly invoke `URL.revokeObjectURL`.

### 30. Automatic PII Detection
NOT_IMPLEMENTED

### 31. Batch Multipart
PASS.

### 32. Batch Polling
PASS. Uses React Query `refetchInterval` targeting the correct canonical route.

### 33. Review Queue
PASS. Fetch handled through React Query.

### 34. Submission Detail
PASS. Fetch handled through React Query.

### 35. Evidence Overlay
PASS. Scales dynamically inside a container based on the original image dimensions without altering backend coordinates.

### 36. PROPOSED_GRADE
PASS. Labeled as "(CHƯA PHẢI ĐIỂM CHÍNH THỨC)".

### 37. REVIEW_REQUIRED
PASS. Labeled as "Yêu cầu giáo viên xem lại".

### 38. Approve
PASS. Correctly issues `POST` and invalidates query caches on success.

### 39. Override
PASS. Takes a required reason and invalidates query caches on success.

### 40. Cache Invalidation
PASS. Handled automatically via `@tanstack/react-query` `queryClient.invalidateQueries`.

### 41. Error Handling
PASS. Handled via Axios interceptors and React Query states.

### 42. Backend Offline
PASS. Fails gracefully.

### 43. Backend Smoke Test
PASS. `bootRun` executed correctly.

### 44. 10-Image Multipart Runtime
PASS.

### 45. 30-Image Multipart Runtime
PASS.

### 46. Review API Runtime
PASS.

### 47. Approve Runtime
PASS.

### 48. Override Runtime
PASS.

### 49. Flow A — Login
PASS

### 50. Flow B — Dashboard
PASS

### 51. Flow C — Classes
PASS

### 52. Flow D — Assignment
PASS

### 53. Flow E — Batch Creation
PASS

### 54. Flow F — Batch Preparation
PASS

### 55. Flow G — Batch Privacy
PASS

### 56. Flow H — Batch Upload
PASS

### 57. Flow I — Batch Processing
PASS

### 58. Flow J — Review Queue
PASS

### 59. Flow K — Submission Detail
PASS

### 60. Flow L — Approve
PASS

### 61. Flow M — Override
PASS

### 62. Flow N — Refresh
PASS

### 63. Flow O — Logout
PASS

### 64. Flow P — Backend Offline
PASS

### 65. Privacy P1
PASS

### 66. Privacy P2
PASS

### 67. Privacy P3
PASS

### 68. Privacy P4
PASS

### 69. Privacy P5
PASS

### 70. Privacy P6
PASS

### 71. Privacy P7
PASS

### 72. Privacy P8
PASS

### 73. TypeScript
PASS

### 74. Lint
PASS

### 75. Build
PASS

### 76. Teacher Runtime
PASS

### 77. Files Created
0

### 78. Files Modified
4

### 79. Files Deleted
0

### 80. Backend Files Modified
NONE

### 81. Student Files Modified
NONE

### 82. AI Training Files Modified
NONE

### 83. Known Limitations
None.

### 84. Privacy Limitations
Automatic PII Detection is NOT_IMPLEMENTED (remains as a future enhancement).

### 85. Contract Mismatches Found
Resolved `REVIEW_REQUIRED` batch status and polling endpoint mismatch.

### 86. Technical Debt
None.

### 87. Backend Freeze Integrity
READY

### 88. Teacher Integration Status
READY

### 89. Phase Completion Assessment
READY_FOR_REVIEW

### 90. Recommended Next Step
Proceed to Phase 4 (Deployment and Final System Verification).
