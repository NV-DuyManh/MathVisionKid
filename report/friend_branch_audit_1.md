# Friend Branch Audit Report (1)

## 1. Executive Summary
This report provides a forensic audit of the `Namm` branch. The branch aims to fix and finalize OCR features for the MathVision Kids project, primarily touching AI segmentation models, Business API transport tracking, and the mobile multiline review screen. The branch appears largely complete and successful, focusing on hardening the OCR transport and reducing oversegmentation in the AI service.

## 2. Repository Truth
- **Repository Root:** E:/MathVisionKid
- **Current Branch:** Namm
- **Upstream/Tracking Branch:** origin/Namm
- **HEAD Commit:** `aa51f43 fix ocr`
- **Working Tree:** Clean
- **Clone Type:** Full clone

## 3. Current Branch & Baseline
- **Baseline:** `da67f51` (origin/main)
- **Reason:** The `Namm` branch branches off from `da67f51`, which is the latest commit on `main`. 
- **Merge-base:** `da67f51`

## 4. Unique Commit History
There are exactly 2 unique commits by the friend:
1. `43384c4 fix ocr`
2. `aa51f43 fix ocr`
**Subject/Scope:** Both commits are titled "fix ocr" and collectively introduce the transport tracking (SHA256 logging) in the backend, stale request handling in the mobile UI, and segmentation pipeline enhancements in the AI service, along with 3 documentation reports.

## 5. Changed File Inventory
Total Changed Files: 20

**A. Student Mobile**
- `src/app/crop.tsx` (Modified)
- `src/app/ocr-pilot/multiline-review.tsx` (Modified) - Stale detection response guarding, fixed fallback behavior.
- `src/services/api/OcrPilotService.ts` (Modified) - Added transport logging, throws errors instead of silent mock fallbacks.
- `expo_qr_code.png` (Added) - Unrelated asset.

**E. Spring Boot Business API**
- `services/business-api/build.gradle` (Modified)
- `services/business-api/gradle.properties` (Added)
- `services/business-api/src/main/java/com/mathvisionkids/api/ocr/multiline/MultilineDetectResponse.java` (Modified)
- `services/business-api/src/main/java/com/mathvisionkids/api/ocr/multiline/OcrMultilineService.java` (Modified) - Added SHA256 logging for received and forwarded OCR image bytes.
- `services/business-api/src/main/resources/application.yml` (Modified) - Added `ai.service.base-url` config.
- `services/business-api/src/test/java/com/mathvisionkids/api/ocr/multiline/OcrMultilineServiceTest.java` (Modified) - Added SHA256 preservation test.

**F. FastAPI AI Service**
- `services/ai-service/app/api/ocr.py` (Modified)
- `services/ai-service/app/recognition/quality.py` (Modified)
- `services/ai-service/app/schemas/ocr_pilot.py` (Modified)
- `services/ai-service/tests/test_live_path_contracts.py` (Added)
- `services/ai-service/tests/test_physical_regression.py` (Modified)
- `services/ai-service/tests/test_segmentation_contracts.py` (Added) - 19 comprehensive segmentation tests.

**L. Documentation / reports**
- `report/ai_hwtext_runtime_6_live_runtime_transport_forensics.md` (Added)
- `report/ai_hwtext_runtime_7_diacritic_oversegmentation_fix.md` (Added)
- `report/ai_hwtext_runtime_8_general_satellite_filtering_fix.md` (Added)

**M. Configuration**
- `tsconfig.json` (Modified) - Fixed Typescript/Jest conflict.

## 6. Feature Matrix
- **Mobile Stale Request Guarding:** PASS - Implemented with `useRef` correctly.
- **Mobile Offline Fake Fallback Removal:** PASS - Replaced with strict error throwing.
- **Backend OCR Image SHA256 Tracking:** PASS - Logging correctly records `RECEIVED` and `FORWARDED` SHA256.
- **AI Service Oversegmentation Fix (Diacritics):** PASS - Documented and tested in `test_segmentation_contracts.py`.

## 7. Mobile Changes
Removed the hardcoded offline fallback box generation (which faked a single box on network failure). Implemented proper request deduplication/stale-guarding using `useRef` to avoid double fetches and UI glitches.

## 8. Business API Changes
Added cryptographic (SHA256) tracking of image binaries being forwarded to the AI service to detect any loss or corruption in transit. Properly tests this new logging and forwarding logic.

## 9. AI Service Changes
The segmentation contracts now cover 19 test cases for overlapping bounding boxes, diacritic marks (dots, accents, circumflexes), fragments, and isolated satellites. The code correctly handles merging/isolating these fragments.

## 10. Web/Admin/Teacher Changes
None.

## 11. Database Changes
None.

## 12. Dependency Changes
None introduced explicitly in package files.

## 13. Model/Data Artifact Audit
No new model weights added.

## 14. Mock/Placeholder Audit
- The branch explicitly **REMOVES** a mock placeholder (offline fake box generation) from `OcrPilotService.ts`.
- No new mock placeholders were detected.

## 15. Security/Configuration Audit
- Added `ai.service.base-url` to application config.
- No hardcoded secrets were committed.
- Logging of SHA256 is secure (does not log image bytes).

## 16. Reports vs Reality
The reports (`ai_hwtext_runtime_6`, `7`, `8`) claim fixes to live transport and diacritic oversegmentation. The implementation matches these claims perfectly (test coverage added for exactly these scenarios).

## 17. Test/Build Results
- **AI Service:** Partial pass (1 collection error due to `test_ocr_bridge.py` path duplication, remaining tests pass).
- **Business API:** Passed all tests (`./gradlew test`).
- **Mobile:** Passed `npm run lint`, `npx tsc --noEmit`, and `npx jest`.

## 18. Integration Compatibility
COMPATIBLE. The changes adhere to the repository rules. 

## 19. Risk Matrix
- **HIGH/CRITICAL:** None. 

## 20. Completed vs Partial vs Missing
- **COMPLETED:** All targeted features in the commits are completed and tested.
- **PARTIAL:** None.
- **MISSING:** None.

## 21. Keep / Fix / Reject Recommendation
**KEEP_WITH_FIXES**: The changes are solid and desirable. The only required fix is resolving the duplicated test file `test_ocr_bridge.py` in the AI service that causes pytest collection failure, and ignoring/removing the irrelevant `expo_qr_code.png`.

## 22. Files Reviewed
20 files reviewed.

## 23. Skills Applied
None — no installed skill matched the task.

## 24. Final Verdict
The branch successfully hardens the OCR pipeline against network/transit bugs and AI oversegmentation. It is safe and highly recommended to integrate once the pytest collection issue is patched.
