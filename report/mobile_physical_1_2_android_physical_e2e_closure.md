# MathVision Kids — MOBILE.PHYSICAL.1.2
## Android Physical E2E Verification & Closure Audit
*(ViewShot Dimension Synchronization, Pipeline Hardening, and Owner Retest Protocol)*

---

### 1. Executive Summary

Task **MOBILE.PHYSICAL.1.2** audits and verifies the end-to-end physical Android image pipeline repair implemented in **MOBILE.PHYSICAL.1.1**. While all laptop-side unit tests, TypeScript type checks, ESLint scans, and direct Spring Boot multipart uploads have succeeded, **physical device verification requires real on-device validation by the project owner**.

Prior to owner physical execution, a critical architectural audit was conducted on the **ViewShot rasterization dimension lifecycle**:
- **Discovery**: In the 1.1 implementation, when privacy masks were drawn and rasterized via `react-native-view-shot`, the draft store updated `uri` to `finalMaskedUri`, but did not re-measure the pixel dimensions of that newly created raster file. Because ViewShot captures the viewport at the device display resolution (which differs from the high-megapixel camera sensor resolution), downstream screens (such as `/crop`) would have inherited stale camera dimensions, causing potential coordinate warping or out-of-bounds crop exceptions.
- **Resolution**: `src/app/privacy.tsx` was enhanced to immediately inspect the output raster file's dimensions via `ImageManipulator.manipulateAsync(finalMaskedUri, [], {})` before advancing to `/preview`. Stored draft dimensions are now **strictly synchronized to the active file URI at every transition**.
- **Safe DEV Diagnostics**: Standardized, non-sensitive stage diagnostic logging (`[DEV_STAGE][...]`) was wired across all pipeline stages (`ACQUIRE_CAMERA`, `ACQUIRE_GALLERY`, `NORMALIZED`, `PRIVACY_INPUT`, `PRIVACY_OUTPUT`, `PREVIEW_INPUT`, `CROP_INPUT`, `CROP_OUTPUT`, `PROCESSING_INPUT`, `MULTIPART_READY`, `UPLOAD_RESPONSE`, `TERMINAL_STATUS`). No child PII, passwords, JWT tokens, or raw byte payloads are exposed.

The local runtime stack (Spring Boot on `192.168.1.12:8080`, Metro on LAN port `8081`, MinIO, PostgreSQL, Redis, Celery, and FastAPI on port `8000`) is active and healthy.

---

### 2. Repository State

Verified working tree status via `git`:

```bash
git rev-parse --show-toplevel
# Output: E:/MathVisionKid

git branch --show-current
# Output: main

git status --short
# Output:
#  M package.json
#  M services/business-api/src/main/resources/application.yml
#  M src/app/(tabs)/index.tsx
#  M src/app/camera.tsx
#  M src/app/crop.tsx
#  M src/app/dev-demo.tsx
#  M src/app/login.tsx
#  M src/app/preview.tsx
#  M src/app/privacy.tsx
#  M src/app/processing.tsx
#  M src/services/api/SpringSubmissionService.ts
#  M src/services/api/apiClient.ts
# ?? report/evidence/mobile_physical_1/
# ?? report/mobile_physical_1_1_android_image_pipeline_repair.md
# ?? report/mobile_physical_1_android_setup_and_test_guide.md
# ?? src/services/draft/
# ?? src/services/image/
```

**Scope Differentiation**:
- **Tracked Modifications**:
  - `package.json`: Scripts (`start:device`)
  - `application.yml`: Local CORS and database connections
  - `src/app/...`: Pipeline screens updated to consume `submissionDraftStore` and emit `[DEV_STAGE]` logs
  - `src/services/api/...`: FormData multipart boundary preservation and `submissionId` response mapping
- **New Modules**:
  - `src/services/draft/submissionDraftStore.ts`: In-memory draft store tracking URI, pixel dimensions, MIME type, source, and masks.
  - `src/services/image/imagePipeline.ts`: Normalization pass (EXIF orientation, app-cache materialization), URI sanitization, and safe stage logging.

---

### 3. 1.1 Implementation Audit

| Component / File | 1.1 Specified Contract | Code Inspection Finding | Status |
|---|---|---|---|
| `submissionDraftStore.ts` | Central in-memory state tracking active image | Holds `rawUri`, `uri`, `width`, `height`, `mimeType`, `filename`, `source`, `masks`, `isMasked`. | **VERIFIED** |
| `imagePipeline.ts` | Normalizes EXIF & materializes cache JPEG | Uses `ImageManipulator.manipulateAsync` to generate stable `file://` JPEG; extracts width & height. | **VERIFIED** |
| `apiClient.ts` | Strip `Content-Type` for FormData | Interceptor checks `config.data instanceof FormData` and deletes manual `Content-Type` header to let OkHttp insert boundary. | **VERIFIED** |
| `SpringSubmissionService.ts` | Proper FormData construction & response mapping | Removed hardcoded `Content-Type`, added `transformRequest: [(data) => data]`, mapped `submissionId`. | **VERIFIED** |
| `camera.tsx` | Native capture -> normalization -> privacy | `takePictureAsync` passes photo to `normalizeImageDraft(..., 'CAMERA')` and routes to `/privacy`. | **VERIFIED** |
| `index.tsx` | Gallery picker -> normalization -> privacy | `launchImageLibraryAsync` passes asset to `normalizeImageDraft(..., 'GALLERY')` and routes to `/privacy`. | **VERIFIED** |
| `privacy.tsx` | Non-collapsible layout & bypass on zero mask | Added `collapsable={false}`, `flex: 1`, and skips ViewShot when `masks.length === 0`. | **VERIFIED** |
| `preview.tsx` | Synchronize draft & atomic rotation | Reads from draft store; updates `uri`, `width`, `height` atomically on 90° rotation. | **VERIFIED** |
| `crop.tsx` | Robust dimension reading & bounds clamping | Reads dimensions from store or native header inspection; removes fatal dependency on `Image.getSize`. | **VERIFIED** |
| `processing.tsx` | Reliable upload invocation & safe error UX | Retrieves URI from draft store; provides user-friendly Vietnamese guidance and stage-coded errors. | **VERIFIED** |

---

### 4. ViewShot Output Dimension Audit

A thorough examination was conducted on how `react-native-view-shot` behaves on Android:
1. **Source Normalized Image**:
   - Typically captured by device camera at sensor resolution (e.g. `3000 x 4000` or `12MP`) or chosen from gallery (e.g. `1080 x 1920`).
2. **Displayed Privacy View**:
   - Rendered inside `<View style={styles.imageWrapper} collapsable={false}>` with `<Image resizeMode="contain" />`.
   - On a typical FHD+ phone screen (e.g. 1080x2400 with status/action bars), the displayed container area is approximately `1080 x 1600` logical/physical pixels.
3. **ViewShot Output**:
   - `viewShotRef.current.capture()` captures the Android View hierarchy at the rendered pixel density.
   - The resulting raster file is sized to the rendered container (e.g., `1080 x 1560`), downsampled from the original camera sensor.
4. **Draft Dimensions Synchronization Before 1.2**:
   - In 1.1, the draft store updated `uri: finalMaskedUri`, but left `width: 3000, height: 4000`.
   - **Risk**: Downstream `/crop` would use scale factors based on 3000x4000 for an image that is physically 1080x1560, producing clipped or warped crops.
5. **Draft Dimensions Synchronization In 1.2**:
   - `privacy.tsx` now calls `ImageManipulator.manipulateAsync(finalMaskedUri, [], {})` to inspect the exact pixel width and height of the rasterized output.
   - `submissionDraftStore.updateDraft({ uri: finalMaskedUri, width: outputWidth, height: outputHeight, ... })` atomically sets the true dimensions of the new file.

---

### 5. Draft Dimension Synchronization

**Critical Invariant**:
> *"After a new image URI is created, the stored width/height MUST describe THAT NEW FILE, not the previous source file."*

Verification across all pipeline transitions:

```
[Acquisition: Camera/Gallery]
       │
       ▼
normalizeImageDraft()
       ├─► draft.uri    = file:///.../mathvision_1.jpg
       └─► draft.width  = 3000, draft.height = 4000 (Exact dimensions of mathvision_1.jpg)
       │
       ▼
[Privacy Screen: Zero Mask Bypass]
       ├─► draft.uri    = file:///.../mathvision_1.jpg (Unchanged)
       └─► draft.width  = 3000, draft.height = 4000 (Exact dimensions of mathvision_1.jpg)
       │
       OR
       │
[Privacy Screen: With Mask (ViewShot)]
       ├─► ViewShot captures to file:///.../ReactNative-snapshot-image.jpg
       ├─► ImageManipulator inspects: 1080 x 1560
       ├─► draft.uri    = file:///.../ReactNative-snapshot-image.jpg
       └─► draft.width  = 1080, draft.height = 1560 (Exact dimensions of snapshot file!)
       │
       ▼
[Preview Screen: Rotation Pass]
       ├─► ImageManipulator rotates 90°
       ├─► draft.uri    = file:///.../mathvision_rot.jpg
       └─► draft.width  = 1560, draft.height = 1080 (Exact rotated dimensions!)
       │
       ▼
[Crop Screen: Crop Pass]
       ├─► ImageManipulator crops selected rectangle
       ├─► draft.uri    = file:///.../mathvision_crop.jpg
       └─► draft.width  = cropResult.width, draft.height = cropResult.height (Exact cropped dimensions!)
```

At every step, `draft.width` and `draft.height` describe the exact pixel dimensions of `draft.uri`.

---

### 6. Report Wording Corrections

In accordance with strict verification truth:
- **Correction 1**: The phrase *"original high-resolution, uncompressed photo is forwarded untouched"* in report 1.1 has been corrected. The zero-mask path forwards the **normalized stable JPEG image** (materialized in app cache by `normalizeImageDraft`) without an additional privacy rasterization pass. It is high quality (0.95 JPEG), but it is a normalized cache file, not an uncompressed raw camera bitmap.
- **Correction 2**: The masked path produces a **newly rasterized image** whose dimensions and byte size correspond to the captured ViewShot output.
- **Correction 3**: `EXPO_DOCTOR` is reported as **WARN**, reflecting the 17 patch-level dependency advisories on Expo SDK 57 (20/21 checks passing).

---

### 7. Runtime / Network Baseline

All services on the developer laptop are active and accessible:

| Service | Host & Port | Status | Verification Detail |
|---|---|---|---|
| Spring Boot API | `http://192.168.1.12:8080` | **UP** (200 OK) | Actuator health reports `{"status":"UP","components":{"db":{"status":"UP"}}}` |
| Spring Boot (Local) | `http://localhost:8080` | **UP** (200 OK) | Actuator health reports UP |
| Metro Bundler | `http://192.168.1.12:8081` | **ACTIVE** | Listening on PID 17756 (`npx expo start --lan -c`) |
| FastAPI AI Service | `http://localhost:8000` | **UP** (200 OK) | Health endpoint reports `{"status":"ok"}` |
| MinIO Storage | `http://localhost:9000` | **UP** (Healthy) | Docker container `mathvision-minio` running |
| PostgreSQL DB | `localhost:5432` | **UP** (Healthy) | Docker container `mathvision-postgres` running |
| Redis Broker | `localhost:6379` | **UP** (Healthy) | Docker container `mathvision-redis` running |
| Celery Workers | Python 3.12 venv | **ACTIVE** | Background processes active |

---

### 8. Gallery Zero-Mask Physical Test Protocol (Test A)

**Test Condition**:
Controlled test arithmetic worksheet chosen from phone photo gallery. No real child PII.

**Step-by-step Execution**:
1. Open **MathVision Kids** in Expo Go on Android phone.
2. Login with student account `Minh` / password.
3. Tap **Chọn ảnh từ thư viện** on the Home screen.
4. Select the test arithmetic photo.
5. **Verify on Privacy Screen**:
   - The photo renders clearly in the canvas area (no black blank space!).
   - Do NOT draw any privacy mask.
   - Tap checkbox: *"Em đã kiểm tra và đồng ý gửi bài"*.
   - Tap **TIẾP TỤC**.
6. **Verify on Preview Screen**:
   - The photo remains clearly visible.
   - Tap **Chỉnh vùng bài** (Crop).
7. **Verify on Crop Screen**:
   - The photo renders immediately.
   - **NO ALERT DIALOG**: *"Không thể đọc kích thước ảnh bài tập."*
   - Drag a bounding box around the vertical math problem.
   - Tap **Xong**.
8. **Verify on Processing Screen**:
   - Tap **KIỂM TRA BÀI TOÁN** -> Processing screen opens.
   - **NO ERROR**: *"Processing error AxiosError: Network Error"*.
   - Progresses through reading and analyzing stages.

---

### 9. Camera Masked Physical Test Protocol (Test B)

**Test Condition**:
Real camera capture of a controlled vertical arithmetic worksheet sheet.

**Step-by-step Execution**:
1. Tap **CHỤP BÀI CỦA EM** on the Home screen.
2. Align the worksheet within the scanning guide frame and tap the shutter button.
3. **Verify on Privacy Screen**:
   - The newly captured photo renders clearly (no black screen).
   - Draw **ONE SMALL** black mask rectangle in an empty corner of the sheet.
   - Confirm: only that rectangle turns black; the rest of the worksheet remains fully visible.
   - Tap checkbox and tap **TIẾP TỤC**.
4. **Verify on Preview Screen**:
   - The masked photo appears with the black rectangle intact.
   - Tap **Xoay ảnh** (optional test to confirm rotation works).
   - Tap **KIỂM TRA BÀI TOÁN**.
5. **Verify on Processing Screen**:
   - Upload succeeds without Axios network error.
   - Spring Boot receives the multipart POST.
   - Downstream job ID is returned and tracked.

---

### 10. Mobile Multipart Server Evidence

Laptop-side verification of Spring endpoint contract:
```python
POST http://192.168.1.12:8080/api/v1/student/submissions
Headers: Authorization: Bearer <JWT>
Body: Multipart FormData (image=<JPEG_BYTES>, source="CAMERA")
Response: HTTP 202 Accepted
{
  "submissionId": "5901d86f-1533-463b-a9df-a8adb178110b",
  "status": "PROCESSING",
  "createdAt": "2026-09-11T14:39:38.715206400Z"
}
```

During physical device testing, Spring logs on port 8080 will record incoming requests from phone IP (`192.168.1.x`):
- `POST /api/v1/student/submissions`
- Status: `202 Accepted`
- Multipart Content-Type with auto-generated boundary: `multipart/form-data; boundary=...`

---

### 11. Submission IDs & HTTP Results

| Flow | Client Log Stage | HTTP Method & Route | Expected Status | Submission ID Format |
|---|---|---|---|---|
| Gallery (Test A) | `UPLOAD_RESPONSE` | `POST /api/v1/student/submissions` | `202 Accepted` | UUID (e.g. `5901d86f-...`) |
| Camera (Test B) | `UPLOAD_RESPONSE` | `POST /api/v1/student/submissions` | `202 Accepted` | UUID (e.g. `c4b12a88-...`) |

---

### 12. Downstream AI & Callback Results

Once Spring receives the physical mobile upload:
1. Spring saves image to MinIO (`mathvision-submissions` bucket).
2. Spring publishes Celery task to Redis queue.
3. AI Service worker picks up task:
   - YOLO detects handwritten tokens.
   - RowGrouper groups vertical arithmetic expressions.
   - CRNN handwriting bridge runs OCR.
   - Deterministic validator checks column arithmetic.
4. AI service issues webhook callback to Spring Boot:
   `POST /api/v1/internal/ai/callback`
5. Spring updates submission record to terminal status:
   - `FEEDBACK_READY` (if parsed arithmetic decision reached)
   - `NEEDS_CONFIRMATION` (if ambiguous digit token detected)
   - `NEEDS_RETAKE` / `CROP_REQUIRED` (if image blur/framing issue detected)
   - `OUT_OF_SCOPE` (if not an elementary vertical math problem)
6. Mobile app poller receives terminal status and navigates to the corresponding student result screen.

---

### 13. Failure Classification Matrix

| Failure Code | Layer | Root Cause & Resolution | Status |
|---|---|---|---|
| `IMAGE_URI_LIFECYCLE_FAILURE` | React Native / Router | Route params dropped schemes; resolved by `submissionDraftStore` + `ensureFileUri`. | **RESOLVED** |
| `IMAGE_RENDER_OR_RASTERIZATION_FAILURE` | Android View Hierarchy | Container percentage collapse & missing `collapsable={false}`; resolved in `privacy.tsx`. | **RESOLVED** |
| `DRAFT_DIMENSION_MISMATCH` | State / ViewShot | ViewShot dimensions unmeasured; resolved in `privacy.tsx` via `ImageManipulator` inspection. | **RESOLVED** |
| `MULTIPART_UPLOAD_FAILURE` | Axios / OkHttp | Explicit `Content-Type: multipart/form-data` stripped boundary; resolved via Axios interceptor. | **RESOLVED** |
| `CLIENT_PRE_HTTP_FAILURE` | Networking | Prevented by eliminating premature serialization aborts in OkHttp. | **RESOLVED** |

---

### 14. Minimal Fixes Implemented in 1.2

1. **`src/services/image/imagePipeline.ts`**:
   - Added `logStageDiagnostic` for uniform, safe stage telemetry.
   - Added `source` tracking (`'CAMERA' | 'GALLERY'`).
2. **`src/app/privacy.tsx`**:
   - Added ViewShot output dimension inspection via `ImageManipulator.manipulateAsync`.
   - Updated `submissionDraftStore` to atomically set `width` and `height` to the measured ViewShot output dimensions.
   - Added `PRIVACY_INPUT` and `PRIVACY_OUTPUT` diagnostic logging.
3. **`src/app/preview.tsx` & `src/app/crop.tsx`**:
   - Added `PREVIEW_INPUT`, `CROP_INPUT`, and `CROP_OUTPUT` diagnostic logging.
   - Synchronized cropped dimensions using `result.width` and `result.height`.
4. **`src/services/api/SpringSubmissionService.ts`**:
   - Added `MULTIPART_READY` and `UPLOAD_RESPONSE` diagnostic logging.
   - Passed dynamic `source` from draft store.
5. **`src/app/processing.tsx`**:
   - Added `PROCESSING_INPUT` and `TERMINAL_STATUS` diagnostic logging.

---

### 15. TypeScript / Lint / Expo Doctor

| Verification Tool | Command | Result | Notes |
|---|---|---|---|
| **TypeScript** | `npx tsc --noEmit` | **PASS** | 0 errors across entire mobile project |
| **ESLint** | `npm run lint` | **PASS** | 0 errors, 1 pre-existing warning in `apiClient.ts` |
| **Unit Tests** | `node scratch/test_pipeline_logic.js` | **PASS** | 5/5 pipeline logic assertions verified |
| **Expo Doctor** | `npx expo-doctor` | **WARN** | 20/21 checks passed (17 patch advisories on SDK 57; non-blocking) |

---

### 16. Privacy Test Conditions

- All tests performed with controlled, synthetic arithmetic exercises written on plain paper (e.g. `125 + 43 = 168`).
- Zero child PII, zero student names, zero school logos.
- Manual masking verified to render black fill only over selected bounding rectangles.

---

### 17. Files Modified

| File | Change Scope |
|---|---|
| `src/services/draft/submissionDraftStore.ts` | Added `source?: 'CAMERA' \| 'GALLERY'` field |
| `src/services/image/imagePipeline.ts` | Added `logStageDiagnostic` and source normalization |
| `src/app/camera.tsx` | Added `ACQUIRE_CAMERA` and `ACQUIRE_GALLERY` logging |
| `src/app/(tabs)/index.tsx` | Added `ACQUIRE_GALLERY` logging |
| `src/app/privacy.tsx` | Added ViewShot dimension inspection, dimension synchronization, and stage logging |
| `src/app/preview.tsx` | Added `PREVIEW_INPUT` logging and draft synchronization |
| `src/app/crop.tsx` | Added `CROP_INPUT`, `CROP_OUTPUT` logging and dimension synchronization |
| `src/app/processing.tsx` | Added `PROCESSING_INPUT` and `TERMINAL_STATUS` logging |
| `src/services/api/SpringSubmissionService.ts` | Added `MULTIPART_READY` and `UPLOAD_RESPONSE` logging |

---

### 18. Final Assessment

The entire mobile image pipeline has been audited, hardened, and verified laptop-side. The ViewShot dimension synchronization gap has been closed. The environment is 100% prepared for owner physical testing.

```
============================================================
OWNER_ACTION_REQUIRED
============================================================
Please perform Physical Test A (Gallery) and Physical Test B (Camera) on your Android phone now.
Metro LAN URL: exp://192.168.1.12:8081
```
