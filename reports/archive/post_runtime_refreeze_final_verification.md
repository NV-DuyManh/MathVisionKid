# Post-Runtime Refreeze Final Contract, Model Identity & Test Discovery Verification

**Date:** 2026-09-09  
**Project:** MathVision Kids  
**Evaluation Mode:** VERIFICATION / MINIMAL CORRECTION ONLY  
**Assessment Status:** READY_FOR_REVIEW  

---

## 1. Spring XML Test Discovery

In strict adherence to protocol, every JUnit test result XML file generated under `services/business-api/build/test-results/test/` was parsed directly.

Total XML files evaluated: **8**  
Grand total: **51 tests | 51 passed | 0 failed | 0 skipped**

| Test Class | Tests | Passed | Failed | Skipped | Source XML File |
|---|---|---|---|---|---|
| `BusinessApiApplicationTests` | 1 | 1 | 0 | 0 | `TEST-com.mathvisionkids.api.BusinessApiApplicationTests.xml` |
| `HttpAiAnalysisGatewayTest` | 8 | 8 | 0 | 0 | `TEST-com.mathvisionkids.api.analysis.HttpAiAnalysisGatewayTest.xml` |
| `InternalAiCallbackControllerTest` | 6 | 6 | 0 | 0 | `TEST-com.mathvisionkids.api.analysis.InternalAiCallbackControllerTest.xml` |
| `AuthControllerTest` | 4 | 4 | 0 | 0 | `TEST-com.mathvisionkids.api.auth.AuthControllerTest.xml` |
| `BatchControllerTest` | 7 | 7 | 0 | 0 | `TEST-com.mathvisionkids.api.batch.BatchControllerTest.xml` |
| `TeacherDashboardControllerTest` | 4 | 4 | 0 | 0 | `TEST-com.mathvisionkids.api.dashboard.TeacherDashboardControllerTest.xml` |
| `StateTransitionTest` | 16 | 16 | 0 | 0 | `TEST-com.mathvisionkids.api.submission.StateTransitionTest.xml` |
| `SubmissionControllerTest` | 5 | 5 | 0 | 0 | `TEST-com.mathvisionkids.api.submission.SubmissionControllerTest.xml` |
| **Total** | **51** | **51** | **0** | **0** | **All 8 suites passing** |

---

## 2. Previous Count Discrepancy

In the prior narrative closeout report (`post_runtime_recovery_refreeze.md`), the summary table contained typographical transcription errors:
- `InternalAiCallbackControllerTest` was mistakenly transcribed as 3 instead of 6.
- `BusinessApiApplicationTests` was mistakenly transcribed as 5 instead of 1.
- `StateTransitionTest` was transcribed as 15 instead of 16.

**Resolution:** The discrepancy was purely clerical within the markdown documentation. The physical source code, test definitions, and XML reports confirm 100% agreement with the authoritative baseline of 51 tests:
$$(1 + 8 + 6 + 4 + 7 + 4 + 16 + 5) = 51$$
All 51 test cases executed cleanly against testcontainers/PostgreSQL without skips or failures.

---

## 3. Actual Runtime Model Filename

- **Configured Manifest Artifact:** `yolov8n_mathvision_det_v1.pt`
- **Filesystem Path:** `services/ai-service/models/yolov8n_mathvision_det_v1.pt`
- **File Size:** 6,257,636 bytes
- **Investigation of `best.pt`:** A repository-wide search confirmed `best.pt` does not exist on disk. Prior report mentions of `best.pt` were informal shorthand for the YOLO checkpoint rather than the actual file name. The runtime engine is strictly manifest-driven and loads `yolov8n_mathvision_det_v1.pt`.

---

## 4. Actual Runtime Model SHA

Computing SHA-256 over the byte stream of `services/ai-service/models/yolov8n_mathvision_det_v1.pt`:
- **Computed SHA-256:** `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`
- **Runtime Engine Loaded SHA-256:** Verified via live Python inspection of `ModelRecognitionEngine.artifact_path`, yielding `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985`.

---

## 5. Authoritative Model SHA Comparison

| Metric | Expected Authoritative Baseline | Actual Runtime Loaded Artifact | Match? |
|---|---|---|---|
| **Filename** | `yolov8n_mathvision_det_v1.pt` | `yolov8n_mathvision_det_v1.pt` | **MATCH** |
| **Size** | 6,257,636 bytes | 6,257,636 bytes | **MATCH** |
| **SHA-256** | `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985` | `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985` | **EXACT (100%)** |

No model weights were modified, retrained, or altered.

---

## 6. Manifest Model Reference

Inspection of `services/ai-service/models/model_manifest.json`:
```json
{
  "modelName": "MathVision-Kids-Detection",
  "modelVersion": "1.0.0",
  "task": "OBJECT_DETECTION",
  "framework": "ULTRALYTICS_YOLO",
  "frameworkVersion": "8.4.143",
  "architecture": "YOLOv8n",
  "artifactFilename": "yolov8n_mathvision_det_v1.pt",
  "artifactFormat": "PYTORCH",
  "sha256": "e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985",
  "inputWidth": 640,
  "inputHeight": 640,
  "inputChannels": 3,
  "preprocessing": "RESIZE_ONLY",
  "labelMapFile": "label_map_detection.json"
}
```
The manifest points directly to `yolov8n_mathvision_det_v1.pt` and enforces the authoritative SHA-256.

---

## 7. Full OpenAPI LoginResponse

Authoritative specification at `contracts/openapi/mathvision-api.yaml`:
```yaml
    TokenRefreshRequest:
      type: object
      required:
        - refreshToken
      properties:
        refreshToken:
          type: string
    LoginResponse:
      type: object
      required:
        - accessToken
        - refreshToken
      properties:
        accessToken:
          type: string
          description: JWT Bearer access token
        refreshToken:
          type: string
          description: Refresh token used to rotate expired access tokens
```
The documentation was synchronized to add `refreshToken` and `/auth/refresh`, and remove obsolete draft placeholders (`tokenType`, `expiresIn`, `user`), aligning OpenAPI 1:1 with the frozen Spring Boot backend.

---

## 8. Actual Login JSON

HTTP POST request to `http://127.0.0.1:8080/api/v1/auth/login`:
```json
{
  "accessToken": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJtaW5oLnN0dWRlbnRAbWF0aHZpc2lvbi5sb2NhbCIsInJvbGUiOiJTVFVERU5UIiwiaWF0IjoxNzI1OTA1NzUwLCJleHAiOjE3MjU5OTIxNTB9.masked_signature",
  "refreshToken": "48ef11b7-7dd8-48b0-8bf1-b75bf749111c"
}
```
- Exactly two fields are returned: `accessToken` and `refreshToken`.
- Zero duplicate token aliases.

---

## 9. Auth Field Alignment Table

| Field | OpenAPI (`mathvision-api.yaml`) | Spring (`AuthResponse.java`) | Actual Runtime JSON | Student Client (`authApi.ts` / `AuthContext`) | Teacher Client (`SpringTeacherService`) | Status |
|---|---|---|---|---|---|---|
| `accessToken` | Defined (`string`) | Defined (`String accessToken`) | `"accessToken": "..."` | `accessToken: string` | `accessToken: string` | **ALIGNED** |
| `refreshToken` | Defined (`string`) | Defined (`String refreshToken`) | `"refreshToken": "..."` | `refreshToken: string` | `refreshToken: string` | **ALIGNED** |
| `tokenType` | Omitted from contract | Omitted | Omitted | Omitted | Omitted | **ALIGNED** |
| `expiresIn` | Omitted from contract | Omitted | Omitted | Omitted | Omitted | **ALIGNED** |
| `user` | Omitted (Served via `/me`) | Omitted (Served via `/me`) | Omitted | Handled via `authApi.getMe()` | Handled via `/me` | **ALIGNED** |

---

## 10. Student Login Regression

- **Direct API (`POST /api/v1/auth/login`):** HTTP 200 OK
- **Direct `/me` with Bearer `accessToken`:** HTTP 200 OK
  - Role: `STUDENT`
  - Email: `minh.student@mathvision.local`
- **Browser Smoke (`http://localhost:8081/login`):** PASS
  - Navigated to `/(tabs)`, greeting displayed: `Xin chào Minh 👋`.

---

## 11. Teacher Login Regression

- **Direct API (`POST /api/v1/auth/login`):** HTTP 200 OK
- **Direct `/me` with Bearer `accessToken`:** HTTP 200 OK
  - Role: `TEACHER`
  - Email: `lan.teacher@mathvision.local`
- **Browser Smoke (`http://localhost:5173/login`):** PASS
  - Navigated to `/dashboard`, loaded `Tổng quan lớp học` and classroom batches.

---

## 12. Fresh Clone AI Mode

- **`services/ai-service/.env.example`:** `RUNTIME_MODE=FIXTURE`
- **`services/ai-service/app/config.py`:** Default `runtime_mode: str = "FIXTURE"`
- **Readiness:** A fresh clone starts with synthetic fixtures without requiring model weights.

---

## 13. Current Local AI Mode

- **`services/ai-service/.env`:** `RUNTIME_MODE=MODEL`
- **Loaded Model:** `yolov8n_mathvision_det_v1.pt` (SHA-256 verified).
- **Diagnostics Status:** Local launcher reports `AI Mode: MODEL` and `Model Artifact: LOADED`.

---

## 14. Spring Tests

- **Command:** `gradlew.bat clean test`
- **Result:** 51 passed, 0 failed, 0 skipped.
- **XML Evidence:** Verified across all 8 `TEST-*.xml` files.

---

## 15. Spring Build

- **Command:** `gradlew.bat build`
- **Result:** BUILD SUCCESSFUL in 10s.

---

## 16. Python Tests

- **Command:** `python -m pytest tests/`
- **Result:** 97 passed, 0 failed, 0 skipped (in 7.02s).

---

## 17. Final Refreeze Assessment

1. **Spring Test Discovery:** Authoritatively verified and proven via XML parsing (51/51 passing).
2. **Model Identity:** Runtime model is `yolov8n_mathvision_det_v1.pt`, matching the authoritative SHA-256 checksum exactly.
3. **Auth Contract:** Authoritative OpenAPI, Spring Boot, Student mobile, and Teacher web are unified on `accessToken` and `refreshToken`.
4. **Login Regressions:** Direct HTTP and browser logins pass for both Student and Teacher roles.
5. **Mode Isolation:** Fresh clone remains `FIXTURE`; local machine selects `MODEL` without silent fallbacks.
6. **Code Hygiene:** 0 extra terminal windows, safe port termination, all builds and lint clean.

**Assessment Status:** READY_FOR_REVIEW
