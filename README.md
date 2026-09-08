# MathVision Kids

MathVision Kids is an AI-assisted handwritten arithmetic grading and tutoring platform for Vietnamese primary-school students (Grades 1–5).

## Run Locally (Unified Local Stack)

To run the complete MathVision Kids local development environment (PostgreSQL, MinIO, Redis, Spring Boot Business API, FastAPI AI Runtime, Celery Worker, and Teacher Web Portal):

```cmd
# 1. Start complete stack
scripts\start-all.bat

# 2. Check system health
scripts\health-check.bat

# 3. Stop stack
scripts\stop-all.bat
```

For comprehensive guides, see:
- [Developer Local Setup Guide](docs/LOCAL_SETUP.md) -- Prerequisites, installation, and environment configuration.
- [Local Demonstration Guide](docs/DEMO_GUIDE.md) -- Step-by-step teacher batch and student demo flows.
- [Local Troubleshooting Guide](docs/TROUBLESHOOTING.md) -- Actionable solutions for common issues.
- [Local Runtime Architecture](docs/ARCHITECTURE_LOCAL_RUNTIME.md) -- Architecture diagrams and async correlation.
- [Local Maintenance Guide](docs/MAINTENANCE_GUIDE.md) -- Configuration, log inspection, and model handoff.

---

## Student Mobile App (Expo / React Native)


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
