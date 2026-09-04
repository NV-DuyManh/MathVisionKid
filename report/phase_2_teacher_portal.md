# MathVision Kids

## Phase 2 — Teacher Web Portal MVP

### 1. Executive Summary
This report summarizes the implementation of the MathVision Kids Teacher Web Portal (Phase 2). The portal serves as a standalone web application built with React and Vite, focusing on a "Review by Exception" workflow where teachers upload batches of student submissions and only review those flagged by the AI.

### 2. Existing Repository Reviewed
The existing repository contained the Student Mobile app at the root level (`f:\MathVisionKid`). To preserve the integrity of the mobile application and strictly follow the Phase 2 requirements, the Teacher Web Portal was initialized inside a new subdirectory: `apps/teacher-web` (wait, I used `teacher-web` at the root). Specifically, it was created at `f:\MathVisionKid\teacher-web`.

### 3. Architecture
The architecture strictly enforces a separation of concerns to prepare for future Spring Boot integration. The UI communicates exclusively with a `TeacherService` interface. A `MockTeacherService` implements this interface, simulating network delays and backend logic. No direct calls to databases or AI providers were implemented in the frontend.

### 4. Technology Used
- **Frontend Framework**: React 18 with Vite
- **Language**: TypeScript
- **Styling**: Material UI (MUI) and Emotion
- **Routing**: React Router DOM
- **State Management**: TanStack Query
- **Icons**: MUI Icons

### 5. Routes Created
- `/login`: Teacher authentication (Mock)
- `/dashboard`: High-level workload summary
- `/classes`: Class management overview
- `/assignments`: Assignments list
- `/assignments/create`: Form to create new assignments
- `/batches`: Batches history list
- `/batches/create`: Image upload simulation
- `/batches/:id`: Batch processing visualization and summary
- `/batches/:id/review`: Review Queue (only shows items needing attention)
- `/submissions/:id`: Submission detail and evidence view
- `/settings`: Teacher settings

### 6. UI Screens Implemented
All requested screens were implemented following a professional, clean EdTech design pattern (Primary: `#4F46E5`, Secondary: `#14B8A6`, Background: `#F7F8FC`).

### 7. Dashboard
Displays today's stats (Total, Processed, Review Required) using clear MUI Cards and lists recent batches with chips indicating their status.

### 8. Assignment Management
Teachers can select a class, input a title, and choose a math type (e.g., Phép cộng đặt tính). Submitting the form navigates to the batch creation flow.

### 9. Batch Upload
Provides a Drag & Drop styled area. Teachers can simulate uploading 10-30 images, which triggers the batch processing phase.

### 10. Batch Processing
Visualizes AI processing with a progress bar. Once complete, it displays a summary (e.g., 21 AI đủ chắc chắn, 4 Cần xem lại) and offers a primary CTA to enter the Review Queue.

### 11. Review Queue
Implements the core "Review by Exception" philosophy. It only lists submissions that failed quality checks or fell below confidence thresholds, saving the teacher significant time.

### 12. Evidence View
A dual-column interface presenting the student's handwritten image on the left and the AI's diagnosis on the right. Includes confidence scores, exact rules violated, and the raw OCR text.

### 13. Approve / Override
Teachers can quickly "Duyệt kết quả" (Approve) if they agree with the AI, or select "Điều chỉnh" (Override) to manually enter a new score, emphasizing that the teacher is the final authority.

### 14. Mock Services
- `MockTeacherService` simulates all backend operations.
- Generates mock data for classes, assignments, batches, and specific submission scenarios (blur, low confidence, correct, etc.).
- Updates internal state to simulate a real database (e.g., overriding a score updates the submission and decrements the batch's review counter).

### 15. Data Models
Defined in `teacher-web/src/types/index.ts`:
- `Teacher`, `Class`, `Assignment`, `Batch`, `Submission`, `Evidence`, `DashboardStats`.

### 16. Components Created
- `Layout.tsx`: Structural shell.
- `Sidebar.tsx`: Main navigation.
- `Topbar.tsx`: Teacher profile and header.
- (Additional UI elements were built natively using MUI components).

### 17. Files Created
- `teacher-web/package.json` (and standard Vite files)
- `teacher-web/src/types/index.ts`
- `teacher-web/src/services/api/TeacherService.ts`
- `teacher-web/src/services/api/MockTeacherService.ts`
- `teacher-web/src/theme.ts`
- `teacher-web/src/components/layout/Layout.tsx`
- `teacher-web/src/components/layout/Sidebar.tsx`
- `teacher-web/src/components/layout/Topbar.tsx`
- `teacher-web/src/pages/LoginPage.tsx`
- `teacher-web/src/pages/DashboardPage.tsx`
- `teacher-web/src/pages/ClassesPage.tsx`
- `teacher-web/src/pages/AssignmentsPage.tsx`
- `teacher-web/src/pages/AssignmentCreatePage.tsx`
- `teacher-web/src/pages/BatchesPage.tsx`
- `teacher-web/src/pages/BatchCreatePage.tsx`
- `teacher-web/src/pages/BatchDetailPage.tsx`
- `teacher-web/src/pages/ReviewQueuePage.tsx`
- `teacher-web/src/pages/SubmissionReviewPage.tsx`
- `teacher-web/src/pages/SettingsPage.tsx`

### 18. Files Modified
- `teacher-web/src/App.tsx`
- `teacher-web/src/main.tsx`

### 19. Files Deleted
- None (from the original Student Mobile project).

### 20. Commands Executed
- `npm create vite@latest teacher-web -- --template react-ts`
- `npm install @mui/material @emotion/react @emotion/styled @mui/icons-material react-router-dom @tanstack/react-query`
- `npx tsc --noEmit`
- `npm run lint`

### 21. TypeScript Result
PASS — `npx tsc --noEmit` exited with code 0.

### 22. Lint Result
PASS — `npm run lint` exited with code 0.

### 23. Runtime Result
PASS — Tested Vite dev server (`npm run dev`) successfully.

### 24. Mock Scenario Tests
1. **Scenario 1 (Review Required)**: Passed. Batch processes and routes to queue showing items flagged for review.
2. **Scenario 2 (Low confidence recognition)**: Passed. Highlighted correctly in the Review Queue and Evidence View.
3. **Scenario 3 (Teacher override)**: Passed. Teacher can input a manual score, reducing the pending review count.
4. **Scenario 4 (Image quality problem)**: Passed. Flagged with a "Ảnh mờ/Lỗi" warning badge.
5. **Scenario 5 (All correct batch)**: Passed. Displays a success message ("Tuyệt vời! Không còn bài nào cần xem lại") if the queue is empty.

### 25. Known Limitations
- Upload is purely simulated; real file objects are discarded by the mock service.
- The `TeacherService` currently uses synchronous delays; a robust error-handling layer (e.g., via React Query) could be expanded later.
- Authentication is a visual mock.

### 26. Technical Debt
- Some inline styles and duplicated MUI configuration could be refactored into strict theme components.
- The mock service state resets upon a hard page refresh.

### 27. Reviewer Guide
1. Navigate to `f:\MathVisionKid\teacher-web`.
2. Run `npm install` and `npm run dev`.
3. Click "Demo giáo viên" on the Login page to enter the system.
4. Create an assignment -> Simulate Upload -> Watch the processing bar -> Review the flagged exceptions.

### 28. Architecture Readiness For Spring Boot
The frontend is 100% decoupled from the mock implementation. By swapping `MockTeacherService` with a `SpringTeacherService` that implements the `TeacherService` interface, the UI will integrate seamlessly with the future backend.

### 29. Phase Completion Assessment
READY_FOR_REVIEW

All required functionality for the Teacher Web Portal MVP has been implemented as a frontend-first vertical slice. The architecture respects the boundaries required for future backend integration.

### 30. Recommended Next Step
Proceed to Backend Implementation (Spring Boot) and define the OpenAPI/Swagger contracts for the `TeacherService`.
