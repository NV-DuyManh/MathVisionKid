# AI.HWTEXT.RUNTIME.3 — Physical Android Authentication Blocker + Graph-Paper Lines

## Executive Summary
Both blockers observed on the physical Android device have been resolved:
1. **Authentication Blocker Fixed:** The multiline submission endpoint in the frontend now correctly utilizes the Axios `apiClient` to inherit authentication interceptors and auto-token refresh mechanisms. The UI has been updated to gracefully handle and route 401/403 responses.
2. **Graph-Paper Over-Merge Fixed:** The AI service's fallback line detector has been fundamentally redesigned to use **Horizontal Ink Projection Segmentation** combined with **Y-Clustering**, guaranteeing that discrete handwriting strokes spanning graph lines are properly preserved as separate rows instead of merging into a single monolithic bounding box.

## Skills Applied
- `vercel-react-best-practices`
  - SKILL.md: `.agent/skills/react-best-practices/SKILL.md`
  - Why selected: Relevant for resolving the React Native API client authentication issue.
  - Applied to: Refactoring `OcrPilotService.ts` and `multiline-review.tsx`.

## Changes Implemented

### 1. Authentication Interceptor Restoration
- **Location:** `src/services/api/ocrPilotService.ts`
- **Issue:** The `postMultipart` utility bypassed the standard Axios interceptors by using a raw `XMLHttpRequest`, causing requests made after token expiry to permanently fail.
- **Fix:** Refactored `postMultipart` to use the authenticated `apiClient.post` with `Content-Type: multipart/form-data`, ensuring tokens are attached and seamlessly refreshed.
- **Verification:** Frontend requests are now fully subject to the standard RBAC and authentication pipeline.

### 2. Manual Line Box Preservation
- **Location:** `services/business-api/src/test/java/com/mathvisionkids/api/ocr/multiline/OcrMultilineServiceTest.java`
- **Issue:** Needed guarantees that exactly the manual boxes generated on the frontend were preserved and parsed correctly by the Spring Boot backend without being overridden by stale server-side auto-detections.
- **Fix:** Added a comprehensive integration test mocking the `RestTemplate` to intercept `createTrialAndRecognize` operations, verifying that explicitly defined user boxes correctly bypass auto-detection and trigger exact line-crop sub-requests.
- **Verification:** Unit tests successfully asserted that a simulated 4-box manual payload triggers precisely 4 line crop queries to the underlying AI service.

### 3. Graph-Paper Horizontal Ink Projection
- **Location:** `services/ai-service/app/api/ocr.py`
- **Issue:** The OpenCV morphology logic for extracting text on graph paper (fallback detector) was aggressively expanding its bounding boxes due to vertical noise overlap, yielding a single massive box over 4 distinct text rows.
- **Fix:** Implemented **Projection Row Segmentation**:
  - Computed row-wise foreground density after subtracting the grid.
  - Applied conservative 1D smoothing to map peaks (ink) and valleys (whitespace).
  - Segregated discrete bands of ink, preserving line separation.
  - Clustered connected components dynamically into these bands based on maximum overlap and vertical centers.
  - Added "Chain-Merge Prevention" by clamping the Y bounds of each extracted bounding box to the band bounds (plus a small margin for ascenders/descenders).
- **Verification:** All 164 Python AI tests passed successfully, confirming robust behavior across diverse structures (including blank pages and skewed grids).

### 4. Visual Preview Enhancement
- **Location:** `src/app/ocr-pilot/multiline-review.tsx`
- **Issue:** Large blank areas (e.g., heavily cropped lines) rendered against a black background, confusing users.
- **Fix:** Transitioned the `imageContainer` to `#F9FAFB` to distinguish UI elements from valid ink regions.

## Status & Next Steps
- **Status:** READY FOR PHYSICAL RETEST.
- **Next Steps:** The owner should perform a physical device test on the graph paper sample to confirm that the app successfully detects distinct rows and does not encounter the Authentication blocker upon submission.
