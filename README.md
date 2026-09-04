# MathVision Kids - Student Android MVP

MathVision Kids is an AI-assisted handwritten arithmetic grading and tutoring platform for Vietnamese primary-school students (Grades 1–5).

This repository contains the UI-first vertical slice of the Android mobile app, built with Expo and React Native.

## How to run the demo

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the Expo development server:
   ```bash
   npm start
   ```

3. Scan the QR code with the Expo Go app on your Android device or run it on an Android Emulator.

## Demo Flows (Mock API)

The current version uses a robust `MockSubmissionService` to simulate the AI and Backend processing.
On the **Home Screen**, scroll to the bottom to find the **"Demo Mocks (For Testing)"** section. Tapping any of these options will simulate selecting an image from the gallery and bypass the camera to trigger specific scenarios:

- **mock-correct**: Simulates a correct math exercise. (FLOW A)
- **mock-earliest-error**: Simulates an arithmetic mistake in the tens column and provides a hint without revealing the full answer. (FLOW B)
- **mock-confirm**: Simulates an ambiguous recognition where the system asks the student to confirm a token. (FLOW C)
- **mock-blur**: Simulates a bad photo quality and asks to retake. (FLOW D)
- **mock-out-of-scope**: Simulates capturing fractions/geometry. (FLOW E)
- **mock-review**: Simulates a case where AI confidence is too low. (FLOW F)

## Switching from Mock API to Spring Boot API

Currently, the app relies on `src/services/api/MockSubmissionService.ts`. 
To switch to the real Spring Boot API in the future:
1. Create a new service (e.g., `SpringSubmissionService.ts`) implementing the exact same method signatures as `MockSubmissionService`.
2. Implement network calls (e.g., via `axios` or `fetch`) to the corresponding endpoints:
   - `POST /api/v1/student/submissions` (multipart upload)
   - `GET /api/v1/student/submissions/:id` (polling)
   - `POST /api/v1/student/submissions/:id/confirm-token`
3. Update the imports in `app/processing.tsx` and `app/results/token-confirmation.tsx` to use the real service.
