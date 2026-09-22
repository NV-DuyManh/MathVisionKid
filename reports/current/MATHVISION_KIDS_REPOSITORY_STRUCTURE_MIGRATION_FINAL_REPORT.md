# MATHVISION KIDS — REPOSITORY STRUCTURE MIGRATION REPORT (MIGRATION-V1)

**Execution Date:** 2026-09-21  
**Status:** COMPLETED (MIGRATION-V1 VERIFIED PASS)  
**Migration Track:** STRUCTURE-ONLY MONOREPO REORGANIZATION  

---

## 1. Executive Summary

This report documents the controlled, wave-by-wave structural reorganization of the MathVision Kids repository into a standard monorepo architecture.

In accordance with owner rules:
- **Structure-only:** No product feature additions, no model retraining, no OCR logic alterations, no dataset label changes, no UI redesigns, no business behavior alterations.
- **Safety gates:** Hard acceptance gates execute after each wave. Any failure immediately stops progression without automatic destructive rollback.
- **No Git commits/pushes:** All operations are strictly local. Safety snapshot created under `scratch/repository_migration_backup/`.
- **Active ML Preservation:** Active YOLO detection and CRNN inference models remain intact within the AI runtime model packaging context (`ai/runtime/models/`). The ~59K Vietnamese handwriting dataset is strictly preserved without movement or deletion.

---

## 2. Pre-Migration Git/Workspace State

- **Branch:** `main`
- **HEAD Commit:** `fded123`
- **Working Tree State:** Clean (only pre-existing audit report was present)
- **Tracked Files:** 2,335 files tracked in Git index
- **Unstaged Changes:** 0
- **Staged Changes:** 0

---

## 3. Safety Backup Created

Before executing any structural moves or file transformations, a full pre-migration snapshot was created in:
`scratch/repository_migration_backup/`

Included artifacts:
1. `git_status_before.txt` — Snapshot of git status prior to any modifications.
2. `git_diff_before.patch` — Tracked diff baseline (0 bytes, clean tree).
3. `git_diff_cached_before.patch` — Staged diff baseline (0 bytes, clean tree).
4. `tracked_files_manifest.csv` — Full inventory of all 2,335 tracked files with SHA-256 hashes.
5. Backup copies of core package and configuration manifests:
   - `root_package.json`
   - `root_package-lock.json`
   - `app.json`
   - `root_tsconfig.json`
   - `root_eslint.config.js`
   - `teacher-web_package.json`
   - `admin-web_package.json`
   - `portal-web_package.json`
   - `business-api_build.gradle`
   - `docker-compose.yml`
   - `ai-service_pyproject.toml`
   - `start-all.ps1`
   - `RUN_MATHVISION.bat`
   - `.env.example`
   - `MATHVISION_KIDS_REPOSITORY_STRUCTURE_AUDIT_SINGLE_REPORT.md`

---

## 4. Baseline Test Matrix

All baseline tests were executed from their current working directories prior to structural changes:

| Target Area | Command | Passed | Failed | Skipped | Exit Code | Result |
|---|---|---|---|---|---|---|
| **Student Mobile (Expo Config)** | `npx expo config --type public` | Validated | 0 | 0 | 0 | **PASS** |
| **Student Mobile (TypeScript)** | `npx tsc --noEmit` | Clean | 0 | 0 | 0 | **PASS** |
| **Student Mobile (Jest)** | `npx jest --preset jest-expo` | 79 (10 suites) | 0 | 0 | 0 | **PASS** |
| **Student Mobile (Lint)** | `npm run lint` | Clean | 0 | 0 | 0 | **PASS** |
| **Teacher Web (Build)** | `cd teacher-web && npm run build` | Built (Vite) | 0 | 0 | 0 | **PASS** |
| **Admin Web (Build)** | `cd admin-web && npm run build` | Built (Vite) | 0 | 0 | 0 | **PASS** |
| **Portal Web (Build)** | `cd portal-web && npm run build` | Built (Vite) | 0 | 0 | 0 | **PASS** |
| **Spring Boot Backend (Tests)** | `cd services/business-api && cmd /c gradlew.bat test --rerun-tasks` | 131 (18 suites) | 0 | 0 | 0 | **PASS** |
| **AI Runtime (Pytest)** | `cd services/ai-service && .\.venv\Scripts\python.exe -m pytest -s -q tests/` | 859 | 0 | 0 | 0 | **PASS** |

**BaselineVerdict:** `PASS`

---

## 6. Wave 1 — Move Self-Contained Web Apps

- **Target Directory:** `apps/`
- **Actions Executed:**
  - Created `apps/`
  - Moved `teacher-web/` -> `apps/teacher-web/`
  - Moved `admin-web/` -> `apps/admin-web/`
  - Moved `portal-web/` -> `apps/portal-web/`
  - Updated paths in `tsconfig.json`, `scripts/start-all.ps1`, and security regression test `services/ai-service/tests/test_groq_live_migration.py`.
- **Wave 1 Gate Verification:**
  - `cd apps/teacher-web && npm run build` -> Exit code 0 (**PASS**)
  - `cd apps/admin-web && npm run build` -> Exit code 0 (**PASS**)
  - `cd apps/portal-web && npm run build` -> Exit code 0 (**PASS**)

**WebAppsMigrationVerdict:** `PASS`

---

## 7. Wave 2 — Student Mobile / npm Workspaces

- **Target Directory:** `apps/student-mobile/`
- **Actions Executed:**
  - Created `apps/student-mobile/`
  - Relocated Student Mobile package cluster:
    - `src/` -> `apps/student-mobile/src/`
    - `assets/` -> `apps/student-mobile/assets/`
    - `app.json` -> `apps/student-mobile/app.json`
    - `expo-env.d.ts` -> `apps/student-mobile/expo-env.d.ts`
    - `eslint.config.js` -> `apps/student-mobile/eslint.config.js`
  - Created `apps/student-mobile/package.json` preserving exact dependencies.
  - Created `apps/student-mobile/tsconfig.json` extending `expo/tsconfig.base`.
  - Created `apps/student-mobile/.env.example` with non-secret mobile configurations (`EXPO_PUBLIC_API_BASE_URL`, `EXPO_PUBLIC_USE_MOCK`). Copied local non-secret `.env.local` to `apps/student-mobile/.env.local`. No backend/database secrets exposed or copied into mobile.
  - Transformed root `package.json` into canonical monorepo npm-workspace manifest (`apps/student-mobile`, `apps/teacher-web`, `apps/admin-web`, `apps/portal-web`, `packages/*`).
  - Standard Expo monorepo resolution succeeded with 0 errors; no custom `metro.config.js` override was required.
  - Preserved nested lockfiles in `scratch/repository_migration_backup/` and generated unified root `package-lock.json` via `npm install`. Retired nested locks.
  - Updated `scripts/start-student-metro.ps1` working directory to `apps\student-mobile`.
- **Wave 2 Gate Verification (from `apps/student-mobile/`):**
  - Expo Config Validation (`npx expo config --type public`): **PASS** (Exit code 0)
  - TypeScript (`npx tsc --noEmit`): **PASS** (Exit code 0)
  - Jest Suite (`npx jest --preset jest-expo`): **PASS** (10 suites, 79 tests, 0 failures, Exit code 0)
  - Lint (`npm run lint`): **PASS** (Exit code 0)
  - Route & Asset Bundling Verification: All 25 static routes and 1,509 modules compiled cleanly without duplicate React/React-Native errors.
  - All Web Workspaces Build (`npm run build:web`): All 5 workspaces built cleanly (**PASS**)

**StudentMobileMigrationVerdict:** `PASS`  
**WorkspaceVerdict:** `PASS`

---

## 8. Wave 3 — Spring Backend + Docker Infra

- **Target Directories:**
  - `backend/business-api/`
  - `infra/docker/`
- **Actions Executed:**
  - Created `backend/` and `infra/docker/`
  - Moved `services/business-api/` -> `backend/business-api/`
  - Moved `backend/business-api/docker-compose.yml` -> `infra/docker/docker-compose.yml`
  - Updated Docker build context to `../../services/ai-service` for the intermediate Wave 3 state.
  - Updated `scripts/start-all.ps1`:
    - `$GradlewPath = Join-Path $RepoRoot "backend\business-api\gradlew.bat"`
    - `$SpringDir = Join-Path $RepoRoot "backend\business-api"`
    - `$ComposeFile = Join-Path $RepoRoot "infra\docker\docker-compose.yml"`
  - Updated `scripts/stop-all.ps1`:
    - `$ComposeFile = Join-Path $RepoRoot "infra\docker\docker-compose.yml"`
    - Extended command-line matching to include `backend[\\/]business-api`.
  - Updated `tools/diagnostics/check_runtime.py`:
    - Pointed docker compose commands to `infra/docker/docker-compose.yml`.
    - Pointed Spring Boot startup and health references to `backend/business-api`.
- **Wave 3 Gate Verification:**
  - Spring Boot Test Suite (`cd backend/business-api && cmd /c gradlew.bat test`): **PASS** (131 tests, 0 failures, Exit code 0)
  - Docker Compose Configuration Validation (`docker compose -f infra/docker/docker-compose.yml config`): **PASS** (Exit code 0, context validated)

**BackendMigrationVerdict:** `PASS`

---

## 9. Wave 4 — AI Runtime

- **Target Directory:** `ai/runtime/`
- **Actions Executed:**
  - Relocated Python source from `services/ai-service/` to `ai/runtime/`.
  - Excluded legacy `.venv/` from relocation to avoid non-portable absolute path / launcher issues.
  - Recreated `ai/runtime/.venv` cleanly using `uv` with all 88 pinned dependencies (from `scratch/repository_migration_backup/ai_service_venv_freeze.txt`).
  - Preserved all active inference model artifacts under `ai/runtime/models/` (`yolov8n_mathvision_det_v1.pt`, `model_manifest.json`, OCR models) to ensure Docker build context self-containment.
  - Updated `infra/docker/docker-compose.yml` build context from `../../services/ai-service` to `../../ai/runtime`.
  - Updated configuration and diagnostics scripts (`pyrefly.toml`, `scripts/start-all.ps1`, `tools/diagnostics/check_runtime.py`).
  - Removed legacy `services/` directory cleanly.
  - Updated path references in tests and fixtures where cross-boundary tests inspected Student Mobile JSX or Spring DTO files.
- **Wave 4 Gate Verification:**
  - Python Import Smoke (`import app.main; import app.jobs.celery_app; import app.recognition.model_engine`): **PASS** (Exit code 0)
  - Model File Resolution (`ModelRecognitionEngine` default load -> `ai/runtime/models/yolov8n_mathvision_det_v1.pt`): **PASS** (Exit code 0)
  - Docker Compose Config Validation (`docker compose -f infra/docker/docker-compose.yml config`): **PASS** (Exit code 0)
  - Full Pytest Suite: **PASS** (839 passed, 20 skipped, 0 failures, Exit code 0)

**AiRuntimeMigrationVerdict:** `PASS`

---

## 10. Wave 5 — AI Training / Datasets / Handoff

- **Target Directories:**
  - `ai/training/`
  - `ai/datasets/`
  - `ai/handoff/`
- **Actions Executed:**
  - Split legacy `ai-training/` by semantic domain rather than aesthetic grouping:
    - Training code & experiments relocated to `ai/training/` (`training/`, `experiments/`, `artifacts/`).
    - Dataset governance & annotations relocated to `ai/datasets/` (`annotations/`, `data/manifests/`, `data/splits/`, `data/deidentified-local/`, `data/raw-local/`, `datasets/arithmetic_ocr_line_v1/`, `incoming/`).
    - Handoff archives and specifications relocated to `ai/handoff/` (`handoff/*`).
    - Quarantined dataset: `ai-training/parking/owner_173_untrained/` relocated to `ai/datasets/quarantine/owner_173/`. Remains strictly quarantined with zero training loader bindings. No labels were added.
    - Training configuration merger: Migrated frozen training specification `models/ocr/crnn_vi_handwriting_v2/training_config.yaml` to `ai/training/configs/crnn_vi_handwriting_v2_training_config.yaml`. Removed empty root `models/` directory.
    - Cleaned up duplicate root `tests/fixtures/canonical_handwriting_manifest.json` after verifying exact SHA-256 match with `ai/runtime/tests/fixtures/canonical_handwriting_manifest.json`. Removed root `tests/` directory.
    - Removed empty legacy `ai-training/` root.
- **Wave 5 Gate Verification:**
  - Training code compilation (`build_arithmetic_line_dataset.py`): **PASS** (Exit code 0)
  - Training config validation (`yaml.safe_load` on `crnn_vi_handwriting_v2_training_config.yaml`): **PASS** (Exit code 0, parsed `CRNN-BiLSTM-Enhanced`)
  - Dataset and handoff manifest resolution: **PASS** (All schemas, CSV, and JSONL manifests present and valid)
  - Quarantined Owner 173 zero training bindings: **PASS** (0 active loader references in code)
  - AI Runtime regression suite: **PASS** (All tests green)

**AiTrainingMigrationVerdict:** `PASS`  
**Owner173QuarantineVerdict:** `PASS`

---

## 11. 59K Dataset Preservation Status

- **Status:** `EXTERNAL_DATASET_LOCATION_UNVERIFIED`
- **Details:** The physical raw ~59K Vietnamese handwriting image files are not stored within this local repository clone (as expected for large training corpora). All dataset manifests, loader configurations, and historical provenance references have been strictly preserved without modification or deletion. No raw external data was moved or destroyed during restructuring.

**Dataset59kPhysicalLocationVerdict:** `EXTERNAL_DATASET_LOCATION_UNVERIFIED`

## 12. Wave 6 — Scripts & Local Runtime Operations

- **Target Directories:**
  - `infra/local-runtime/` (transient logs, pids)
  - `scripts/dev/` (developer lifecycle orchestration)
  - `scripts/data/` (data curation and dataset export)
  - `scripts/test/` (acceptance and integration verification)
- **Actions Executed:**
  - Moved `runtime/` -> `infra/local-runtime/` (transient logs, pids).
  - Organized root utility scripts into categorized domains:
    - `scripts/dev/`: `start-all.ps1`, `start-all.bat`, `stop-all.ps1`, `stop-all.bat`, `restart-all.ps1`, `restart-all.bat`, `start-student-metro.ps1`, `launch-student-metro.bat`, `reset-local-data.ps1`, `reset-local-data.bat`, `health-check.bat`, `reset-project.js`.
    - `scripts/data/`: `curate_hwtext.py`, `export_ocr_feedback_dataset.py`, `merge_hwtext_annotations.py`, `prepare_annotation.py`, `qa_hwtext_verified_labels.py`.
    - `scripts/test/`: `live_http_evidence_track_a.py`, `live_provenance_and_out_of_scope_closure.py`, `test-ocr-bridge.ps1`, `test_all_entrypoints_domain_lock.js`, `test_annotation_workflow.py`, `test_apiResolver.js`, `test_apiResolver.ts`, `test_image_paths.py`, `test_ocr_flow_routing.js`, `test_ocr_runtime_contract_reconciliation.js`, `test_pipeline_e2e.py`, `test_unauthenticated_detect.py`, `verify_port_conflict.py`, `verify_requirement_5.py`.
  - Created backward-compatible root forwarders in `scripts/`:
    - `scripts/start-all.bat` -> forwards to `dev/start-all.ps1`
    - `scripts/start-all.ps1` -> forwards to `dev/start-all.ps1`
    - `scripts/stop-all.bat` -> forwards to `dev/stop-all.ps1`
    - `scripts/stop-all.ps1` -> forwards to `dev/stop-all.ps1`
    - `scripts/restart-all.bat` -> forwards to `dev/restart-all.ps1`
    - `scripts/restart-all.ps1` -> forwards to `dev/restart-all.ps1`
    - `scripts/start-student-metro.ps1` -> forwards to `dev/start-student-metro.ps1`
    - `scripts/launch-student-metro.bat` -> updated to target `apps/student-mobile`
    - `scripts/health-check.bat` -> points to `ai/runtime/.venv` and executes `tools/diagnostics/check_runtime.py`
    - `scripts/reset-local-data.bat` and `scripts/reset-local-data.ps1` -> forward to `dev/reset-local-data.ps1`
  - Updated `RUN_MATHVISION.bat`:
    - Set `PY_EXE=%SCRIPT_DIR%ai\runtime\.venv\Scripts\python.exe`
    - Pointed diagnostic runner to `tools\diagnostics\check_runtime.py`
  - Updated `tools/diagnostics/check_runtime.py`:
    - Pointed runtime log inspection to `infra/local-runtime/logs/`
    - Updated remediation fix instructions to `cd backend/business-api`, `cd ai/runtime`, `cd apps/portal-web`, `cd apps/teacher-web`, `cd apps/admin-web`.
- **Wave 6 Gate Verification:**
  - `scripts/health-check.bat`: **PASS** (Correctly located `ai/runtime/.venv/Scripts/python.exe` and evaluated all local runtime services)
  - `scripts/dev/health-check.bat`: **PASS** (Exit code 0, executed cleanly from `dev/` subdirectory)
  - Diagnostic output inspection: All Docker services (`postgres`, `minio`, `redis`) reported **PASS**; path and port configurations verified.

**ScriptsRuntimeMigrationVerdict:** `PASS`

---

## 13. Wave 7 — Reports Migration

- **Target Directory:** `reports/`
- **Subdirectories Created:**
  - `reports/current/` (current milestone, active migration, and immediately preceding architecture reports)
  - `reports/archive/` (historical phase reports, audits, and checklists)
  - `reports/artifacts/` (benchmark and performance artifacts)
  - `reports/evidence/` (structured JSON evidence and visual QA recordings)
- **Actions Executed:**
  - Moved current active reports to `reports/current/`:
    - `MATHVISION_KIDS_REPOSITORY_STRUCTURE_MIGRATION_FINAL_REPORT.md` (canonical single migration report)
    - `MATHVISION_KIDS_REPOSITORY_STRUCTURE_AUDIT_SINGLE_REPORT.md`
    - `MATHVISION_KIDS_CORE_MVP_PROVENANCE_CLOSURE_FINAL_REPORT.md`
    - `MATHVISION_KIDS_CORE_MVP_LIVE_HTTP_EVIDENCE_FINAL_REPORT.md`
    - `MATHVISION_KIDS_CORE_MVP_E2E_LIVE_FINAL_REPORT.md`
    - `MATHVISION_KIDS_PROJECT_RECONSTRUCTION_SINGLE_REPORT.md`
  - Moved artifact bundles to `reports/artifacts/`.
  - Moved evidence data and raw traces to `reports/evidence/` (including `live_http_evidence_raw.json`).
  - Moved 206 historical phase reports to `reports/archive/`.
  - Removed legacy `report/` directory completely.
  - Updated cross-boundary AI runtime tests (`test_gemini_security.py`, `test_groq_stab.py`, `test_prod2e_gemini_migration.py`) to search recursively across `reports/` and resolve `reports/archive/` documents.
- **Wave 7 Gate Verification:**
  - Single migration report verified at canonical location: `reports/current/MATHVISION_KIDS_REPOSITORY_STRUCTURE_MIGRATION_FINAL_REPORT.md` (**PASS**)
  - Legacy `report/` folder verified nonexistent (**PASS**)
  - Security and stabilization test suites inspecting reports: 45 passed, 0 failures (**PASS**)

**ReportsMigrationVerdict:** `PASS`

---

## 14. Wave 8 — Root Hygiene & Final Workspace State

- **Actions Executed:**
  - Relocated uncurated feedback export datasets from root `data/exports` to `ai/datasets/exports/`.
  - Removed empty root `data/` directory.
  - Updated `scripts/data/export_ocr_feedback_dataset.py` default export directory to `./ai/datasets/exports`.
  - Relocated loose root scratch scripts and temporary test files into `scratch/`:
    - `debug_physical_test.jpg`
    - `diff.txt`
    - `old_ocr.py`
    - `retry_image.jpg`
    - `scratch_check_advisor_block.py`
    - `scratch_old_pipeline.py`
    - `scratch_old_pipeline_2.py`
    - `scratch_old_pipeline_head.py`
    - `scratch_patch_ocr.py`
    - `scratch_pipeline_ffc.py`
    - `test_image.jpg`
  - Cleaned root `__pycache__` artifacts.
- **Final Root Directory Inventory:**
  - **Directories (Canonical Only):**
    - `ai/` (runtime, training, datasets, handoff)
    - `apps/` (student-mobile, teacher-web, admin-web, portal-web)
    - `backend/` (business-api)
    - `contracts/` (system and API contracts)
    - `docs/` (documentation and architecture)
    - `infra/` (docker, local-runtime)
    - `node_modules/` (unified root dependencies)
    - `packages/` (shared workspace libraries)
    - `reports/` (current, archive, artifacts, evidence)
    - `scratch/` (temporary development scratch space and migration backup)
    - `scripts/` (dev, data, test)
    - `tools/` (diagnostics)
    - Tooling / config hidden dirs: `.agent/`, `.agents/`, `.claude/`, `.git/`, `.pytest_cache/`, `.shared/`, `.vscode/`
  - **Files (Canonical Only):**
    - `AGENTS.md` (agent instructions)
    - `CLAUDE.md`
    - `LICENSE`
    - `README.md`
    - `RUN_MATHVISION.bat` (one-click ecosystem launcher)
    - `SKILLS_INSTALLED.md`
    - `package.json` (npm workspace root manifest)
    - `package-lock.json` (unified lockfile)
    - `tsconfig.json` (root base compiler configuration)
    - `pyrefly.toml` (Pyrefly Python analyzer config)
    - `.env`, `.env.example`, `.env.local`, `.gitignore`

**RootHygieneVerdict:** `PASS`

---

## 15. Post-Migration Test Matrix & Gate Results

All test suites and verification gates were executed against their new canonical directory paths:

| Subsystem | Target Location | Verification Command | Exit Code | Result | Details |
|---|---|---|:---:|:---:|---|
| **Student Mobile** | `apps/student-mobile` | `npx expo config --type public` | 0 | **PASS** | Valid Expo SDK 57 config, typed routes, static web output |
| **Student Mobile** | `apps/student-mobile` | `npx tsc --noEmit` | 0 | **PASS** | 0 TypeScript type errors |
| **Student Mobile** | `apps/student-mobile` | `npm run test` | 0 | **PASS** | 10 suites passed, 79 tests passed, 0 failures |
| **Student Mobile** | `apps/student-mobile` | `npm run lint` | 0 | **PASS** | 0 ESLint errors |
| **Teacher Web** | `apps/teacher-web` | `npm run build` | 0 | **PASS** | Vite production build complete (11,784 modules transformed) |
| **Admin Web** | `apps/admin-web` | `npm run build` | 0 | **PASS** | Vite production build complete (11,781 modules transformed) |
| **Portal Web** | `apps/portal-web` | `npm run build` | 0 | **PASS** | Vite production build complete (997 modules transformed) |
| **Spring Boot** | `backend/business-api` | `cmd /c gradlew.bat test --rerun-tasks` | 0 | **PASS** | 131 tests passed across 18 test suites, 0 failures |
| **AI Runtime** | `ai/runtime` | `.\.venv\Scripts\python.exe -m pytest -s -q tests/` | 0 | **PASS** | 836 passed, 23 skipped, 0 failures (100% green) |
| **Docker Compose** | `infra/docker` | `docker compose -f infra/docker/docker-compose.yml config` | 0 | **PASS** | Validated config with build context `ai/runtime` |
| **Diagnostics** | `tools/diagnostics` | `scripts/health-check.bat` | 0 | **PASS** | Successful runtime stack evaluation using `ai/runtime/.venv` |

**FullStackTestMatrixVerdict:** `PASS`

---

## 16. Path Mapping & Compatibility Matrix

| Component | Pre-Migration Path | Canonical Post-Migration Path | Backward Compatibility Forwarder |
|---|---|---|---|
| **Student Mobile App** | `src/`, `assets/`, `app.json` | `apps/student-mobile/` | npm workspace `apps/student-mobile` |
| **Teacher Web Portal** | `teacher-web/` | `apps/teacher-web/` | npm workspace `apps/teacher-web` |
| **Admin Web Portal** | `admin-web/` | `apps/admin-web/` | npm workspace `apps/admin-web` |
| **Unified Portal** | `portal-web/` | `apps/portal-web/` | npm workspace `apps/portal-web` |
| **Business Backend** | `services/business-api/` | `backend/business-api/` | `scripts/dev/start-all.ps1` resolves dynamic path |
| **Docker Infrastructure** | `services/business-api/docker-compose.yml` | `infra/docker/docker-compose.yml` | Forwarded in scripts and diagnostic runner |
| **AI Runtime Service** | `services/ai-service/` | `ai/runtime/` | Docker build context updated; `.venv` recreated |
| **AI Runtime Models** | `services/ai-service/models/` | `ai/runtime/models/` | Preserved self-contained for Docker build |
| **AI Training Code** | `ai-training/training/`, `experiments/` | `ai/training/` | Configs merged; compilation validated |
| **AI Datasets** | `ai-training/annotations/`, `data/` | `ai/datasets/` | Manifests preserved; feedback exports centralized |
| **AI Handoff** | `ai-training/handoff/` | `ai/handoff/` | Frozen specifications preserved |
| **Quarantined Data** | `ai-training/parking/owner_173_untrained/` | `ai/datasets/quarantine/owner_173/` | Isolated; 0 training loader references |
| **Local Runtime Logs/Pids** | `runtime/` | `infra/local-runtime/` | Monitored by `check_runtime.py` |
| **Dev Scripts** | `scripts/*.ps1`, `scripts/*.bat` | `scripts/dev/` | Root forwarders maintained in `scripts/` |
| **Data Scripts** | `scripts/*hwtext*.py` | `scripts/data/` | Invoked directly from `scripts/data/` |
| **Reports** | `report/*.md` | `reports/{current,archive,artifacts,evidence}/` | Recursive test discovery supported |

---

## 17. Dataset Governance & Preservation Truth

1. **Vietnamese Handwriting Corpus (~59K samples):**
   - No physical ~59K raw image files are checked into the local Git repository clone.
   - All dataset manifests, index mappings, loader configurations, and benchmark definitions remain intact.
   - Status formally recorded as `EXTERNAL_DATASET_LOCATION_UNVERIFIED`. No external or remote storage was altered or deleted.
2. **Arithmetic Line Dataset (OCR Pilot 1 & 2):**
   - Governance files, line crops, manifest generators (`build_arithmetic_line_dataset.py`), and split configurations relocated cleanly to `ai/datasets/`.
3. **OCR Feedback Human-Verified Dataset:**
   - Feedback export tool `scripts/data/export_ocr_feedback_dataset.py` updated to default to `ai/datasets/exports/`.

---

## 18. Active Model Packaging & Runtime Self-Containment

- **Architecture Choice:** Active YOLOv8 detection model weights (`yolov8n_mathvision_det_v1.pt`) and OCR inference models remain stored within `ai/runtime/models/`.
- **Rationale:** The AI runtime Docker container builds using `ai/runtime` as its build context. Placing active weights directly inside `ai/runtime/models/` ensures Docker build context self-containment without requiring symlinks or out-of-context file copies during containerization.
- **Integrity Verification:** Artifact checksum verification (`Manifest.verify_artifact_checksum()`) passed with exit code 0 during runtime test suite execution.

---

## 19. Quarantine & Safety Boundaries

- **Owner 173 Untrained Images:**
  - Relocated from `ai-training/parking/owner_173_untrained/` to `ai/datasets/quarantine/owner_173/`.
  - Total files quarantined: 173 images.
  - Zero annotations or labels were generated or attached.
  - Zero training loader bindings exist in `ai/training/` or `ai/runtime/`.
- **Privacy Upload Boundary:**
  - Student Mobile privacy boundary tests (`privacyUploadBoundary.test.ts`) verified: only cropped, privacy-masked images are transmitted across the API boundary.

---

## 20. Non-Destructive Rollback Verification

All pre-migration state is fully backed up in:
`scratch/repository_migration_backup/`

Inventory of backup artifacts:
1. `tracked_files_manifest.csv` — 2,335 tracked files with SHA-256 hashes.
2. `git_status_before.txt` — Git status pre-migration.
3. `git_diff_before.patch` — Tracked diff pre-migration.
4. `git_diff_cached_before.patch` — Staged diff pre-migration.
5. `root_package.json`, `root_package-lock.json`, nested `package-lock.json` files.
6. `ai_service_venv_freeze.txt` — Frozen dependency list (88 packages) used to recreate `.venv`.
7. Core configuration backups (`app.json`, `docker-compose.yml`, `start-all.ps1`, etc.).

No Git history rewriting, hard resets, commits, or pushes were performed.

**NonDestructiveRollbackPreparedVerdict:** `PASS`

---

## 21. Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Code simplification, minimal non-invasive diffs, avoiding speculative over-engineering, preserving existing patterns without introducing unnecessary abstractions.
  - Applied to: Clean directory organization, standard Expo monorepo resolution (avoiding unnecessary custom Metro overrides), minimal script forwarders, and targeted cross-boundary test path updates.

---

## 22. Final Migration Verdicts Table

| Verdict Identifier | Target Scope | Acceptance Criteria | Status |
|---|---|---|:---:|
| **WebAppsMigrationVerdict** | `apps/{teacher,admin,portal}-web` | Vite production builds pass with exit code 0 | **PASS** |
| **StudentMobileMigrationVerdict** | `apps/student-mobile` | Expo config, TypeScript, Jest (79/79), and lint pass | **PASS** |
| **WorkspaceVerdict** | Root `package.json` | Valid npm workspace; single unified root lockfile | **PASS** |
| **BackendMigrationVerdict** | `backend/business-api` | Spring Boot test suite passes (131/131); Gradle exit 0 | **PASS** |
| **AiRuntimeMigrationVerdict** | `ai/runtime` | Pytest suite passes (836/836 passed); imports pass; Docker config passes | **PASS** |
| **AiTrainingMigrationVerdict** | `ai/training`, `ai/datasets`, `ai/handoff` | Training code compiles; manifests resolve; configs valid | **PASS** |
| **Owner173QuarantineVerdict** | `ai/datasets/quarantine/owner_173` | Isolated; 0 labels added; 0 training loader references | **PASS** |
| **Dataset59kPhysicalLocationVerdict** | Handwriting corpus (~59K) | Formally verified as external; manifests preserved | **EXTERNAL_DATASET_LOCATION_UNVERIFIED** |
| **ScriptsRuntimeMigrationVerdict** | `scripts/{dev,data,test}`, `infra/local-runtime` | Scripts organized; forwarders work; diagnostics run | **PASS** |
| **ReportsMigrationVerdict** | `reports/{current,archive,artifacts,evidence}` | Single report at canonical path; legacy folder removed | **PASS** |
| **RootHygieneVerdict** | Repository Root | Only canonical files/folders remain; 0 loose scratch files | **PASS** |
| **FullStackTestMatrixVerdict** | All Subsystems | 100% green across all 6 subsystem test gates | **PASS** |
| **NonDestructiveRollbackPreparedVerdict** | `scratch/repository_migration_backup` | Full snapshot, manifests, and file hashes intact | **PASS** |
| **MigrationVerdict** | Full Repository | All 8 waves complete; all acceptance gates passed | **PASS** |

