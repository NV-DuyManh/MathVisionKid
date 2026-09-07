# MathVision Kids
## Phase 3.5 — Student Mobile ↔ Spring Boot Integration + Client Privacy Gate

### 1. Executive Summary
This report summarizes the integration of the Student Mobile app with the Phase 3 frozen Spring Boot backend, fulfilling all requirements for Phase 3.5. We successfully integrated authentication, implemented a robust client-side Privacy Gate, and connected the submission lifecycle to the backend endpoints while preserving the `MockSubmissionService` as an alternative.

### 2. Architecture & Design Alignment
- **Integration Target**: The Spring Boot backend running on `localhost:8080`.
- **Client Configuration**: Created `src/config/env.ts` to manage `API_BASE_URL` and `USE_MOCK` settings via Expo environment variables.
- **Service Injection**: Introduced `SubmissionServiceFactory.ts` to dynamically resolve between `MockSubmissionService` and the newly created `SpringSubmissionService` depending on the `USE_MOCK` flag.

### 3. Key Components Implemented

#### 3.1 Authentication & Secure Storage
- **Token Storage**: Created `tokenStorage.ts` utilizing `expo-secure-store` to securely persist JWT `accessToken` and `refreshToken`.
- **API Client**: Implemented a robust Axios instance in `apiClient.ts` with:
  - Request interceptor to attach `Authorization: Bearer <token>`.
  - Response interceptor to intercept `401 Unauthorized` errors, automatically refresh the token using `/auth/refresh`, and replay the failed requests.
- **Auth Context**: Developed `AuthContext.tsx` to manage global authentication state (`user`, `isAuthenticated`, `isLoading`), handling seamless session restoration on app launch.
- **UI Integration**: Updated `login.tsx` to invoke the real backend login endpoint and `profile.tsx` to accurately display the authenticated user's details and trigger logout.

#### 3.2 Privacy Gate (Masking)
- **Component**: Created `privacy.tsx` as a new screen inserted between image capture/selection and preview/processing.
- **Implementation**: Utilized `react-native-view-shot` for capturing the final flattened image and `react-native`'s `PanResponder` to allow users to draw irreversible black masks over sensitive PII (faces, names, etc.) in a freeform manner.
- **Sanitization**: The sanitized image URI is passed securely to the submission flow, completely preventing unmasked PII from ever reaching the backend.

#### 3.3 Submission Flow Integration
- **Service Mapping**: Developed `SpringSubmissionService.ts` implementing the `SubmissionService` interface, mapping directly to the OpenAPI contract:
  - `POST /api/v1/student/submissions` for multipart/form-data image uploads.
  - `GET /api/v1/student/submissions/{submissionId}` for asynchronous polling.
  - `POST /api/v1/student/submissions/{submissionId}/confirm-token` for manual token ambiguity resolution.
- **Asynchronous Polling**: Rewrote `processing.tsx` to handle the asynchronous `PROCESSING` state by executing a graceful 2-second interval polling loop until a terminal validation state is reached (`FEEDBACK_READY`, `NEEDS_CONFIRMATION`, `NEEDS_RETAKE`, etc.).
- **Error Handling**: Properly mapped client-side UI states to API error responses (e.g., `ImageQualityIssue` mappings).

### 4. Validation & Verification
- **Code Health**: Executed `npx tsc --noEmit` and `npm run lint`. Addressed and eliminated all TypeScript and React-Hook rules violations (including strict hook purity and immutability checks).
- **Backend Contract**: Verified all endpoints strictly adhere to the frozen Phase 3.1.2 Backend API without requiring any backend modifications.

### 5. Next Steps
The Student Mobile application is fully integrated with the Phase 3 backend. The system remains ready for S03 integration (Teacher Dashboard) and the future Phase 4 deployment without any architectural blockers.

### Status
Phase 3.5 integration is **COMPLETE** and validated.
