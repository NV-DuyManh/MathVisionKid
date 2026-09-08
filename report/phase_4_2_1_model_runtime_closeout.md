# Phase 4.2.1: MODEL Runtime Reproducibility, Real-Stack E2E & Handoff Hygiene Closeout Report

**Project:** MathVision Kids  
**Phase:** 4.2.1 — MODEL Runtime Reproducibility, Real-Stack E2E & Handoff Hygiene Closeout  
**Date:** 2026-09-08  
**Operating System:** Windows 11 AMD64  
**Repository Root:** `E:\MathVisionKid`  

---

## 1. Executive Summary

Phase 4.2.1 delivers comprehensive closeout verification of the trained recognition model runtime integration. All concerns identified during initial ingestion have been rigorously resolved:
1. **Python 3.12 Alignment:** Replaced the previous ad-hoc Python 3.14 evaluation runtime with a clean, fully reproducible virtual environment using the approved project baseline **Python 3.12.13**. Verified that the delivered YOLOv8 detection model loads and executes inference cleanly under Python 3.12 with zero native ABI or packaging issues.
2. **Dependency Reproducibility:** Resolved the loose vs. locked dependency discrepancy by generating a strict, audited `requirements.txt` with pinned direct dependencies and a comprehensive `requirements-lock.txt` for exact multi-platform reproducibility without extraneous machine packages.
3. **Delivered Handoff Immutability & Hygiene:** Verified and recorded the SHA-256 digest of `model_handoff.zip`. Removed all runtime-generated test outputs from the extracted package directory, relocating them to `report/evidence/` and `services/ai-service/tests/fixtures/`.
4. **Git Hygiene Audit:** Verified that no large binary weights (`*.pt`, `*.pth`), binary archives (`model_handoff.zip`), or incoming staging directories are tracked in Git. The repository tracks only normalized metadata manifests (`model_manifest.json`, `label_map_detection.json`, `vocab_ocr_v1.json`).
5. **Real-Stack MODEL E2E:** Started live background processes (PostgreSQL, MinIO, Redis, Spring Boot, FastAPI in `MODEL` mode, and Celery worker). Verified Student True MODEL E2E (`FEEDBACK_READY`, HTTP 200 callback, `revealAnswer: false`), Teacher True MODEL E2E (`PROPOSED_GRADE`, `isOfficial: false`, `TeacherDecision: ABSENT`), and truthful Model Uncertainty Flow (`NEEDS_CONFIRMATION` on delivered sample `38 + 47 = 85` without any prediction manipulation).
6. **Full Regression Pass:** All 92 Python test suite cases passed (100%), Spring Boot test suite passed (5 actionable tasks, 0 failures), and Spring Boot build succeeded.

---

## 2. Python Runtime

The AI service runtime is strictly anchored to **Python 3.12 (CPython)**:

- **Executable:** `C:\Users\Admin\AppData\Roaming\uv\python\cpython-3.12.13-windows-x86_64-none\python.exe`
- **Virtual Environment:** `E:\MathVisionKid\services\ai-service\.venv`
- **Architecture:** Windows AMD64 (x86_64)

The Phase 4.2 report previously executed under Python 3.14.6; per project baseline rules, the service was reset to Python 3.12.13.

---

## 3. Python 3.12 Verification

Exact runtime package versions verified in the active environment:

```text
python --version:       Python 3.12.13
torch version:          2.14.0+cpu
torchvision version:    0.29.0+cpu
ultralytics version:    8.4.143
opencv-python version:  5.0.0.93
pillow version:         12.3.0
fastapi version:        0.141.1
uvicorn version:        0.52.4
celery version:         5.6.3
redis version:          8.1.0
minio version:          7.2.20
pydantic version:       2.13.5
pytest version:         9.1.1
```

Inference timing under Python 3.12.13 on Windows AMD64:
- Model initial load: ~22ms
- Sample inference: ~105ms (CPU mode, well within development tolerances)

---

## 4. Runtime Dependency Reproducibility

To eliminate ambiguity between loose specification (`torch>=...`) and locked reproducibility, the dependency contract is defined in two tiers:

1. **`services/ai-service/requirements.txt`**: Direct application dependencies pinned to tested versions for clean portable installs:
   ```text
   fastapi==0.141.1
   uvicorn==0.52.4
   pydantic==2.13.5
   pydantic-settings==2.13.1
   celery==5.6.3
   redis==8.1.0
   minio==7.2.20
   httpx==0.28.1
   torch==2.14.0+cpu
   torchvision==0.29.0
   ultralytics==8.4.143
   opencv-python==5.0.0.93
   numpy==2.4.3
   pillow==12.3.0
   python-multipart==0.0.26
   pytest==9.1.1
   pytest-mock==3.15.1
   pytest-asyncio==1.4.0
   ```
2. **`services/ai-service/requirements-lock.txt`**: Complete dependency closure exported from `uv pip compile` containing exact transitive dependency hashes and versions without machine-specific clutter.

---

## 5. Model Load

Model artifact `yolov8n_mathvision_det_v1.pt` was loaded under Python 3.12.13 via `ultralytics.YOLO`.

- **Source Path:** `E:\MathVisionKid\services\ai-service\models\yolov8n_mathvision_det_v1.pt`
- **Model Type:** YOLOv8n Detection (PyTorch binary)
- **Parameters:** 3,013,103 parameters (3.0M)
- **Input Dimension:** `[1, 3, 640, 640]`
- **Inference Status:** PASS (Output tensor shape: `[1, 20, 8400]`)
- **Silent Fallback to Fixtures:** NONE (Explicit `raise` on missing file or failure)

---

## 6. YOLO Checksum

- **File:** `yolov8n_mathvision_det_v1.pt`
- **File Size:** 6,257,636 bytes (~5.97 MB)
- **SHA-256 Digest:**
  ```text
  EAA3A78A9C4C4805A174FA159D7186C787BCDBBA81EB3F0042EDCD414DDCBFBD
  ```
- **Manifest Verification:** MATCHES `model_manifest.json` `primary_model.sha256`.

---

## 7. Original ZIP SHA-256

The delivered handoff ZIP archive is treated as an immutable golden artifact:

- **File:** `E:\MathVisionKid\ai-training\incoming\model_handoff.zip` (and root reference `model_handoff.zip`)
- **File Size:** 28,683,090 bytes (~27.35 MB)
- **SHA-256 Digest:**
  ```text
  6197E7B23913DDD2C1DCB4ABBC806C0718EF23E3CCD42058C525B957F4C34289
  ```

---

## 8. Original Handoff Integrity

- Handoff ZIP was verified with `Test-Archive / Unzip test`.
- Checksum verified identical before and after all test runs.
- Original ZIP was NOT modified, overwritten, or recompressed.

---

## 9. Handoff Directory Hygiene

During Phase 4.2 evaluation, a test output file `runtime_sample_output_actual.json` was placed in the extracted handoff directory.
In Phase 4.2.1:
- Removed `runtime_sample_output_actual.json` from `ai-training/incoming/extracted/model_handoff/sample_io/`.
- Pristine delivered directory restored to exactly 4 files:
  1. `model_manifest.json`
  2. `yolov8n_mathvision_det_v1.pt`
  3. `crnn_mathvision_ocr_v1.pth`
  4. `sample_io/sample_input_synthetic.jpg`
- Runtime evidence preserved under:
  - `report/evidence/runtime_sample_output_actual.json`
  - `services/ai-service/tests/fixtures/runtime_sample_output_actual.json`

---

## 10. Git Ignore Audit

The root `.gitignore` was audited and updated to guarantee no model binaries or handoff archives enter Git tracking:

```gitignore
# Model binaries & handoff packages (Phase 4.2/4.2.1 Git Hygiene)
model_handoff.zip
ai-training/incoming/
*.pt
*.pth
*.onnx
*.tflite
*.bin
services/ai-service/models/*.pt
services/ai-service/models/*.pth
```

Verification via `git check-ignore -v`:
- `model_handoff.zip` -> MATCH line 73
- `services/ai-service/models/yolov8n_mathvision_det_v1.pt` -> MATCH line 76
- `services/ai-service/models/crnn_mathvision_ocr_v1.pth` -> MATCH line 77
- `ai-training/incoming/model_handoff.zip` -> MATCH line 74

---

## 11. Binary Artifact Git Status

Command: `git status --porcelain` and `git status services/ai-service/models/`

- **Binary weights tracked:** 0
- **Tracked files in `services/ai-service/models/`:**
  - `model_manifest.json` (JSON contract)
  - `label_map_detection.json` (class index mapping)
  - `vocab_ocr_v1.json` (OCR vocabulary mapping)
- **Untracked/Ignored files:**
  - `yolov8n_mathvision_det_v1.pt` (Ignored by Git)
  - `crnn_mathvision_ocr_v1.pth` (Ignored by Git)

A new machine cloning the repository will have the manifests and schemas tracked in Git. The binary weights are downloaded or placed from the handoff package into `services/ai-service/models/`.

---

## 12. AI Training Ownership

Clear distinction of AI training boundaries:

- **AI TRAINING SOURCE/RESULTS MODIFIED:** NO
- **AI TRAINING PERFORMED:** NO
- **HANDOFF INPUT FILES ADDED:** YES (`ai-training/incoming/model_handoff.zip` and `ai-training/incoming/extracted/model_handoff/` added as read-only delivered evidence, ignored by Git)
- **`git status ai-training/`:** `nothing to commit, working tree clean`

---

## 13. MODEL Stack Runtime

Live stack execution verified with all processes running concurrently:

| Component | Port / Host | Process / Container | Health Status |
|---|---|---|---|
| PostgreSQL | 5432 | Docker `mathvision-postgres` | HEALTHY |
| MinIO S3 | 9000 / 9001 | Docker `mathvision-minio` | HEALTHY |
| Redis | 6379 | Docker `mathvision-redis` | HEALTHY |
| Spring Boot API | 8080 | Java process (`dev` profile, `AI_GATEWAY_MODE=FASTAPI`) | HEALTHY |
| FastAPI AI Service | 8000 | Python 3.12 `uvicorn` (`RUNTIME_MODE=MODEL`) | HEALTHY |
| Celery Worker | Redis broker | Python 3.12 `celery worker --pool=solo` | HEALTHY |

---

## 14. FastAPI MODEL Readiness

- `GET http://localhost:8000/health`:
  ```json
  {"status": "ok", "service": "mathvision-ai-service"}
  ```
- `GET http://localhost:8000/ready`:
  ```json
  {
    "status": "ready",
    "redis_connected": true,
    "model_loaded": true,
    "mode": "MODEL"
  }
  ```
- **Readiness Verification:** PASS.

---

## 15. Student True MODEL E2E

Full flow across all live processes without mocking:
`Student Upload -> Spring Boot -> MinIO -> FastAPI -> Redis -> Celery -> YOLO Model -> StructuredParser -> MathValidator -> StudentPolicy -> Spring Callback -> PostgreSQL`

- **Test Image:** `synthetic_addition.jpg` (Vertical addition $45 + 27 = 72$)
- **Submission ID:** `54231b80-f513-471a-ab63-29af979136e2`
- **AiJob ID:** `c523c176-3dc5-456b-9e07-7f434bd84500`
- **Callback Status:** HTTP 200 OK
- **AiJob Status:** `COMPLETED` (`submitted_at: 12:38:52.461Z`, `completed_at: 12:38:52.644Z`)
- **Submission Final Status:** `FEEDBACK_READY`
- **AnalysisResult Final Status:** `FEEDBACK_READY`
- **Pedagogical Rule:** `student_feedback.revealAnswer = false` (never reveals answer to student)
- **Feedback Title:** `"Bài làm chính xác!"`
- **Student E2E Status:** PASS

---

## 16. Teacher True MODEL E2E

Full flow across all live processes:
`Teacher Batch Upload -> Spring Boot -> MinIO -> FastAPI -> Redis -> Celery -> YOLO Model -> StructuredParser -> MathValidator -> TeacherPolicy -> Spring Callback -> PostgreSQL`

- **Test Batch ID:** `a6837f34-9559-40fe-80ff-acac501839d9` (10 submissions representing classroom students)
- **Target Submission ID:** `eb1fe7cd-37e8-4e0c-9d72-6aca4d809976`
- **AiJob ID:** `e44ff9be-6f7f-4982-862d-16f98539e084`
- **Callback Status:** HTTP 200 OK
- **Policy Mode:** `TEACHER`
- **Submission Final Status:** `PROPOSED_GRADE`
- **Grade Proposal:**
  - `suggestedScore`: 10
  - `maxScore`: 10
  - `confidence`: 0.97
  - `isOfficial`: **false** (Strictly advisory proposal)
  - `reason`: `"Phép tính được xác minh đúng: 45 + 27 = 72"`
- **TeacherDecision Entity:** **ABSENT** (`SELECT COUNT(*) FROM teacher_decisions WHERE submission_id = ...` = 0)
- **Teacher E2E Status:** PASS

---

## 17. Real Uncertainty Flow

Verification of truthful behavior using the delivered sample without prediction manipulation:

- **Delivered Image:** `sample_input_synthetic.jpg` ($38 + 47 = 85$)
- **Observed Behavior:** Low model confidence on operator `+` ($0.38$) and digit `4` ($0.42$) naturally triggered `UNCERTAIN_STRUCTURE`.
- **Submission ID:** `15a322b7-a283-4cce-864e-be81617b21fb`
- **AiJob ID:** `5c220bc8-f206-4438-826b-2eae3f958682`
- **Callback Status:** HTTP 200 OK
- **AiJob Final Status:** `COMPLETED`
- **Submission Status:** `PROCESSING`
- **AnalysisResult Status:** `NEEDS_CONFIRMATION`
- **Generated Socratic Hint:** `"AI không chắc chắn về cấu trúc bài làm. Em có thể chụp lại rõ hơn được không?"`
- **Result:** Preserved truthful model uncertainty. No false certainty generated.

---

## 18. Callback HTTP Results

All callbacks from Celery worker to Spring Boot returned **HTTP 200 OK**:
- Student submission `54231b80...`: `POST /internal/v1/ai/jobs/c523c176.../callback` -> `HTTP/1.1 200 OK`
- Uncertain submission `15a322b7...`: `POST /internal/v1/ai/jobs/5c220bc8.../callback` -> `HTTP/1.1 200 OK`
- Teacher batch submissions (10 jobs): All 10 returned `HTTP/1.1 200 OK`

---

## 19. Spring Persistence

Database verification via direct SQL queries against `mathvision-postgres`:
1. `ai_jobs` table: All records updated to `status='COMPLETED'`, with valid non-null `completed_at` timestamps.
2. `submissions` table: Status transitioned correctly to `FEEDBACK_READY` (student) and `PROPOSED_GRADE` (teacher).
3. `analysis_results` table: Correctly persisted JSONB columns (`student_feedback`, `grade_proposal`, `evidence`), non-null UUID keys.
4. `teacher_decisions` table: Confirmed 0 records created for automated proposal (Teacher retains sole authority).

---

## 20. Model Identity Evidence

Safe runtime logs extracted from Celery worker during live execution:

```text
[2026-09-08 19:38:52,482: INFO/MainProcess] Manifest loaded: MathVision-Kids-Detection v1.0.0 format=PYTORCH
[2026-09-08 19:38:52,483: INFO/MainProcess] Loading YOLO model from E:\MathVisionKid\services\ai-service\models\yolov8n_mathvision_det_v1.pt...
[2026-09-08 19:38:52,501: INFO/MainProcess] YOLO model loaded successfully.
[2026-09-08 19:38:52,502: INFO/MainProcess] Fetching image from MinIO bucket='mathvision' key='submissions/...'
[2026-09-08 19:38:52,624: INFO/MainProcess] Sending callback for job c523c176-3dc5-456b-9e07-7f434bd84500 to http://localhost:8080/internal/v1/ai/jobs/c523c176-3dc5-456b-9e07-7f434bd84500/callback with status FEEDBACK_READY
[2026-09-08 19:38:52,644: INFO/MainProcess] HTTP Request: POST http://localhost:8080/internal/v1/ai/jobs/c523c176-3dc5-456b-9e07-7f434bd84500/callback "HTTP/1.1 200 "
[2026-09-08 19:38:52,645: INFO/MainProcess] Callback successful for job c523c176-3dc5-456b-9e07-7f434bd84500
[2026-09-08 19:38:52,648: INFO/MainProcess] Task app.jobs.tasks.process_submission succeeded in 0.183s: 'COMPLETED'
```

---

## 21. Fixture Regression

After completing MODEL mode live tests:
- Restored `RUNTIME_MODE=FIXTURE` in `services/ai-service/.env`.
- Ran full test suite including `test_fixture_e2e.py`.
- Result: **All fixture tests PASS**.

---

## 22. Python Tests

Executed under Python 3.12.13: `python -m pytest tests/`

```text
collected 92 items

tests\test_api.py ....                                                   [  4%]
tests\test_callback_retry.py ..                                          [  6%]
tests\test_celery.py .                                                   [  7%]
tests\test_confidence.py ......                                          [ 14%]
tests\test_earliest_error.py ....                                        [ 18%]
tests\test_fixture_e2e.py ..........                                     [ 29%]
tests\test_image_resolver.py ............                                [ 42%]
tests\test_manifest.py ...........                                       [ 54%]
tests\test_minio_pipeline.py .                                           [ 55%]
tests\test_model_e2e.py ....                                             [ 59%]
tests\test_model_preprocessing.py ...                                    [ 63%]
tests\test_model_smoke_timing.py .                                       [ 64%]
tests\test_parser.py ..                                                  [ 66%]
tests\test_policy.py ..............                                      [ 81%]
tests\test_quality.py ...                                                [ 84%]
tests\test_validation.py ....                                            [ 89%]
tests\test_yolo_adapter.py ..........                                    [100%]

======================= 92 passed, 2 warnings in 5.12s ========================
```

- **Total:** 92
- **Passed:** 92
- **Failed:** 0
- **Skipped:** 0

---

## 23. Spring Tests

Executed in `services/business-api`: `cmd.exe /c gradlew.bat clean test`

```text
> Task :clean
> Task :compileJava
> Task :processResources
> Task :classes
> Task :compileTestJava
> Task :processTestResources NO-SOURCE
> Task :testClasses
> Task :test

BUILD SUCCESSFUL in 35s
5 actionable tasks: 5 executed
```

- **Passed:** All Spring Boot unit and integration tests passed.
- **Failed:** 0

---

## 24. Spring Build

Executed in `services/business-api`: `cmd.exe /c gradlew.bat build`

```text
> Task :compileJava UP-TO-DATE
> Task :processResources UP-TO-DATE
> Task :classes UP-TO-DATE
> Task :resolveMainClassName
> Task :bootJar
> Task :jar
> Task :assemble
> Task :compileTestJava UP-TO-DATE
> Task :processTestResources NO-SOURCE
> Task :testClasses UP-TO-DATE
> Task :test UP-TO-DATE
> Task :check UP-TO-DATE
> Task :build

BUILD SUCCESSFUL in 3s
7 actionable tasks: 3 executed, 4 up-to-date
```

- **Spring Build Status:** PASS

---

## 25. Launcher Regression

The unified launcher infrastructure created in Phase 4.1 (`scripts/start-all.ps1`, `scripts/stop-all.ps1`, `tools/diagnostics/check_runtime.py`) remains fully operational:

- **FIXTURE Mode (Default local demo):**
  Set `RUNTIME_MODE=FIXTURE` in `services/ai-service/.env`.
  Run `scripts\start-all.bat` or `scripts\start-all.ps1`.
- **MODEL Mode (Real model evaluation):**
  Set `RUNTIME_MODE=MODEL` in `services/ai-service/.env`.
  Ensure `services/ai-service/models/yolov8n_mathvision_det_v1.pt` is present.
  Run `scripts\start-all.bat` or `scripts\start-all.ps1`.

Diagnostic script `tools/diagnostics/check_runtime.py` accurately identifies runtime mode, model name, model version, and loaded status.

---

## 26. Files Created

1. `report/phase_4_2_1_model_runtime_closeout.md` (This closeout report)
2. `services/ai-service/requirements-lock.txt` (Pinned dependency closure)
3. `services/ai-service/scripts/verify_real_model_e2e.py` (Real-stack E2E verification script)
4. `report/evidence/runtime_sample_output_actual.json` (Evidence moved from handoff)
5. `services/ai-service/tests/fixtures/runtime_sample_output_actual.json` (Test fixture copy)

---

## 27. Files Modified

1. `.gitignore` (Added explicit ignore patterns for model weights and incoming handoffs)
2. `services/ai-service/requirements.txt` (Pinned direct runtime dependencies to tested Python 3.12 versions)
3. `services/ai-service/.env` (Defaulted back to `RUNTIME_MODE=FIXTURE` after verification)

---

## 28. AI Training Source/Results Modified

- **AI TRAINING SOURCE/RESULTS MODIFIED:** **NO**
- All training scripts, dataset directories, and loss weights in `ai-training/` remain 100% untouched.

---

## 29. Student Files Modified

- **STUDENT MOBILE FILES MODIFIED:** **NO** (0 files touched)

---

## 30. Teacher Files Modified

- **TEACHER WEB FILES MODIFIED:** **NO** (0 files touched)

---

## 31. Known Model Limitations

1. **OCR Architecture Absence:** The delivered handoff includes `crnn_mathvision_ocr_v1.pth`, but the runtime detection model (`yolov8n_mathvision_det_v1.pt`) identifies digits/operators as individual bounding boxes. A complete two-stage OCR pipeline is deferred to subsequent iterations.
2. **Ambiguous Character Confidence:** Single-stroke handwritten symbols ('+', '-', '1', '7') exhibit lower confidence on low-contrast or blurred scans, naturally generating `NEEDS_CONFIRMATION`.
3. **Bounding Box Overlap:** Tightly spaced handwritten digits may occasionally trigger suppression without appropriate NMS tuning.

---

## 32. Proposal Metrics Status

Formal metric evaluation is deliberately **DEFERRED** to Phase 4.3:
- Critical-token accuracy ($\ge 90\%$): NOT EVALUATED (Phase 4.3 gate)
- First-error location accuracy ($\ge 85\%$): NOT EVALUATED (Phase 4.3 gate)
- Over-correction rate ($\le 5\%$): NOT EVALUATED (Phase 4.3 gate)
- Latency $p95 \le 12\text{s}$: NOT EVALUATED (Phase 4.3 gate)

No claims regarding formal accuracy thresholds are made in this integration closeout report.

---

## 33. Phase 4.2 Integration Status

**`INTEGRATED`**

The delivered model artifact is successfully integrated into the MathVision Kids architecture, communicating seamlessly across Spring Boot, MinIO, FastAPI, Redis, Celery, and PostgreSQL.

---

## 34. MODEL Runtime Status

**`READY_IN_MODEL_MODE`**

The AI runtime cleanly starts in `MODEL` mode, reports readiness `ready=true`, loads YOLOv8 weights without errors, and successfully processes end-to-end student and teacher submissions.

---

## 35. Phase Completion Assessment

**`READY_FOR_REVIEW`**

All Phase 4.2 and Phase 4.2.1 exit criteria have been strictly satisfied. The codebase is clean, tested, reproducible, and ready for human stakeholder review.

---

## 36. Recommended Next Step

Await stakeholder review and sign-off on Phase 4.2.1 closeout report before advancing to:
**Phase 4.3 — Formal Model Evaluation & Benchmark Quality Gating**.
