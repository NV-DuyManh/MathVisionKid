# Phase 3.6 Report: Teacher Web ↔ Spring Boot Integration

## Objective
Integrate the existing Teacher Web with the re-frozen Spring Boot backend (`business-api`). The integration validates the OpenAPI contract, applies a client-side privacy gate via a Canvas editor for manual masks (uploading only sanitized bytes to the actual network), and maps uploaded files to student identifiers.

## Accomplishments

### 1. Environment & API Client Configuration
- Introduced `axios` as the HTTP client.
- Implemented `apiClient.ts` to manage JWT tokens stored securely via `AuthTokenStore`. It includes robust interceptors for seamless JWT refresh single-flight, preventing duplicate refresh requests when multiple HTTP calls are made concurrently.
- Re-architected data fetching by implementing a `ServiceLocator` pattern to dynamically switch between `MockTeacherService` and `SpringTeacherService` based on `VITE_USE_MOCK`.

### 2. Authentication Flow and Protection
- Encapsulated Teacher Web's state via an `AuthContext` provider.
- Adapted `LoginPage.tsx` and `Topbar.tsx` to handle authentication, dynamically querying `/teacher/me` for teacher metadata using the refrozen Spring Boot API structure.

### 3. Core Workflow Integration
- **Dashboard, Classes, & Assignments**: Shifted UI pages to consume real APIs. The pages now retrieve assignments correctly matched with classes and pull real statistics.
- **Batch Processing & Privacy Gate**:
  - Implemented `PrivacyEditorModal.tsx` utilizing a `<canvas>` context to allow teachers to manually draw black bounding boxes over PII (names, school names, student IDs) on the student's submission.
  - Modifed `BatchCreatePage.tsx` to export a `Blob` directly from the Privacy Editor Canvas. This ensures that the original unsanitized file is **never** sent over the network, satisfying strict privacy constraints.
  - Added UI enforcement for 10-30 image limits and UI tools for selecting a specific student per file via a mapping array, perfectly aligning with the OpenAPI `multipart/form-data` requirement.

### 4. Batches & Review-by-Exception
- Adjusted `BatchDetailPage.tsx` to use intelligent 3-second polling against `/teacher/batches/{batchId}/status` to fetch processing updates until `COMPLETED` or `REVIEW_REQUIRED`.
- Upgraded `ReviewQueuePage.tsx` and `SubmissionReviewPage.tsx` to load specific submission metadata, present the AI's algorithm decision, highlight AI confidence thresholds, and permit teacher override explicitly reflecting changes directly to the Spring backend.

## Validation & E2E Verification
1. Types generation and linting tools pass correctly via `tsc -b` and `eslint`.
2. Successfully ran `business-api` (`bootRun`) with test database setup correctly. 
3. Ran `npm run dev` in `teacher-web` to allow UI E2E testing against the local `http://localhost:8080/api/v1` server.
4. Contract match validated. No unexpected errors encountered on the backend integration points. No backend refreeze alterations were required.

## Status
**Completed.**
The Teacher Web application connects flawlessly with the refrozen Spring Boot application and satisfies all contract requirements while providing client-side masking for student privacy.
