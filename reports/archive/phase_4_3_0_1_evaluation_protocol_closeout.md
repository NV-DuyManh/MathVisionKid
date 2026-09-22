# Phase 4.3.0.1 Report: Final Evaluation Protocol Sanity Check Closeout

**Project**: MathVision Kids  
**Phase**: 4.3.0.1 — Final Evaluation Protocol Sanity Check  
**Mode**: Targeted Evaluation-Contract Correction Only (No Training, No Benchmark Runs, No Threshold Tuning)  
**Date**: 2026-09-08  
**Status**: **READY_FOR_REVIEW**  

---

## 1. Executive Summary

Phase 4.3.0.1 was conducted as a targeted evaluation-contract sanity check and governance hardening step for MathVision Kids prior to receiving the independent gold dataset from the AI/ML team. 

All primary objectives of the protocol correction were achieved:
1. **Manifest Checksum Semantics Disambiguation**: Resolved conflation where the YOLO artifact SHA was previously recorded as "Manifest Checksum". All 4 critical hashes (`modelArtifactSha256`, `normalizedManifestSha256`, `labelMapSha256`, `evaluationConfigSha256`) and the declared manifest hash (`artifactChecksumDeclaredByManifest`) are now independently computed, recorded, and documented.
2. **Freeze Provenance**: Recorded explicit environment and threshold values across configs and evaluation outputs (Python 3.12.13, PyTorch 2.14.0+cpu, Ultralytics 8.4.143, conf=0.25, NMS=0.50, ambiguity=0.50, high-conf=0.85).
3. **TOKEN_BENCHMARK_SUBSET Contract**: Formalized mandatory token-level ground truth requirement (`image_id`, `token_class`, `token_bbox`, normalized coordinates `[0.0, 1.0]`, `annotation_provenance`) for images used in the Critical-Token Recognition benchmark (>= 90%).
4. **Gold Image Coverage Disclosure**: Mandated that non-token gold images are disclosed with coverage percentages (`total_gold_images`, `token_annotated_images`, `token_benchmark_coverage_percentage`), and prohibited calculating token metrics on images lacking token labels.
5. **Train/Val Leakage Verification Contract**: Replaced filename-only checks with a formal requirement for credible provenance mechanisms (train/val image SHA-256 exclusion manifest, original split manifest with stable hashes, or equivalent documented provenance).
6. **Leakage Reporting Wording**: Standardized reporting to `NO_KNOWN_OVERLAP_DETECTED` when checks pass, strictly forbidding `DATASET_INDEPENDENCE_VERIFIED` until full train/val provenance is provided.
7. **Evaluation Harness Pre-Execution Gate Tests**: Implemented 5 dedicated gate tests covering missing manifest, empty dataset, invalid schema, known leakage detection, and positive smoke. All 5 tests pass.
8. **Regression Stability**: Full Python regression passed with 97 passed / 0 failed / 0 skipped (baseline was 92). Spring Boot remains untouched and stable at 51 passed.
9. **Phase 4.3 Evaluation Status**: Strictly maintained at **BLOCKED_DATASET** with 0 gold images and zero formal Proposal metrics computed.

---

## 2. Model Artifact SHA

- **Field**: `modelArtifactSha256`
- **File**: `services/ai-service/models/yolov8n_mathvision_det_v1.pt`
- **File Size**: 6,257,636 bytes
- **SHA-256 Hash**: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- **Integrity Status**: **PASS** (Matches authoritative delivered handoff artifact exactly; zero tampering).

---

## 3. Runtime Manifest SHA

- **Field**: `normalizedManifestSha256`
- **File**: `services/ai-service/models/model_manifest.json`
- **File Size**: 1,155 bytes
- **SHA-256 Hash**: `3C1BDE47E72EE01C9DCBD8AD3E8589C6ACC78E7E1B361C3FE78C559027BBC743`
- **Semantic Disambiguation**: This is the file checksum of the JSON manifest itself, distinct from the model binary checksum.
- **Integrity Status**: **PASS**

---

## 4. Label Map SHA

- **Field**: `labelMapSha256`
- **File**: `services/ai-service/models/label_map_detection.json`
- **File Size**: 1,998 bytes
- **SHA-256 Hash**: `1A820BC5E35E2E2A0B5752CCA152C6EFA82DD3DBEC195ACCAF1839270451B972`
- **Classes**: 14 classes (`0`-`9`, `+`, `-`, `=`, `c1`)
- **Integrity Status**: **PASS**

---

## 5. Evaluation Config SHA

- **Field**: `evaluationConfigSha256`
- **File**: `services/ai-service/evaluation/evaluation_config_v1.json`
- **File Size**: 2,697 bytes
- **SHA-256 Hash**: `C805B02E2BFACB5FA0DE5302BC517FD92AE4F8F73FFFD83C6EEA58AEB1D0C7DC`
- **Integrity Status**: **PASS**

---

## 6. Checksum Semantic Correction

### Defect Identified:
In prior reporting iterations, the YOLO artifact binary SHA (`e78f8fa5...`) was inadvertently labeled as "Manifest Checksum". This conflated the model binary checksum with the JSON manifest file checksum.

### Remediation:
1. **Explicit Field Separation**:
   - `modelArtifactSha256`: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985` (binary hash of `yolov8n_mathvision_det_v1.pt`)
   - `artifactChecksumDeclaredByManifest`: `e78f8fa5a2fc8be581b8624fa510cd2c429c40cdbd0930dbb2f1c2d870338985` (value declared under key `"sha256"` in `model_manifest.json`)
   - `normalizedManifestSha256`: `3C1BDE47E72EE01C9DCBD8AD3E8589C6ACC78E7E1B361C3FE78C559027BBC743` (file hash of `model_manifest.json`)
   - `labelMapSha256`: `1A820BC5E35E2E2A0B5752CCA152C6EFA82DD3DBEC195ACCAF1839270451B972` (file hash of `label_map_detection.json`)
   - `evaluationConfigSha256`: `C805B02E2BFACB5FA0DE5302BC517FD92AE4F8F73FFFD83C6EEA58AEB1D0C7DC` (file hash of `evaluation_config_v1.json`)
2. **Configuration & Harness Synchronization**:
   - `services/ai-service/evaluation/evaluation_config_v1.json` was updated with `provenance_checksums` and `checksum_semantics_documentation`.
   - `services/ai-service/evaluation/run_evaluation.py` was updated to dynamically compute all file hashes at runtime.
   - `report/phase_4_3_gold_model_evaluation.md` was updated in Section 14 to present all 5 checksums explicitly.

---

## 7. Token Benchmark Contract

Updated in `report/phase_4_3_ai_team_feedback.md`:
- Token-level ground truth is **strictly mandatory** for images used to evaluate Proposal Metric **Critical-Token Recognition >= 90%**. It can no longer be left merely "where available".
- This subset is formalized as: **`TOKEN_BENCHMARK_SUBSET`**.
- Mandatory schema requirements for every token entry:
  1. `image_id`: Unique string referencing manifest image.
  2. `token_class`: Token class label or ID (0–13: '0'–'9', '+', '-', '=', 'c1').
  3. `token_bbox`: Bounding box `[x_center, y_center, width, height]`.
  4. `coordinate_convention`: Strictly normalized floating point coordinates `[0.0, 1.0]` relative to image dimensions.
  5. `annotation_provenance`: Human annotator ID, annotation tool, and review timestamp.

---

## 8. Token Benchmark Coverage Rule

- It is permissible for a portion of gold images intended strictly for whole-expression or error-localization evaluation (e.g., first-error column detection, over-correction rate) to lack token bounding boxes.
- Mandatory disclosure metrics in evaluation reports:
  - `total_gold_images`: Total gold images in test set.
  - `token_annotated_images`: Count of images with complete token-level annotations.
  - `token_benchmark_coverage_percentage`: `(token_annotated_images / total_gold_images) * 100%`.
- **Enforcement Rule**: Token recognition accuracy will **never** be calculated against images lacking verified token ground truth.

---

## 9. Dataset Provenance Requirement

Updated in `report/phase_4_3_ai_team_feedback.md`:
- File-name and file-path checks alone do **not** prove dataset independence.
- The AI/Data handoff package must supply at least one of the following credible provenance mechanisms:
  1. **Train/Validation Image SHA-256 Exclusion Manifest**: A list of cryptographic SHA-256 hashes of all 1,809 training images and 192 validation images used for `yolov8n_mathvision_det_v1.pt`.
  2. **Original Split Manifest**: Containing stable image IDs and hashes defining training, validation, and test splits.
  3. **Equivalent Documented Provenance**: Rigorous documentation verifying that gold test images were never used during model training or checkpoint selection.
- **Writer-Disjoint Metadata**: Safe anonymized identifiers (e.g., `writer_id: "writer_042"`) must be included to verify that student handwriting in the test split does not overlap with training writers.

---

## 10. Leakage Verification Rule

- The automated evaluation harness compares incoming gold candidate images against known training/val hashes and filenames.
- **Reporting Contract**:
  - When no overlaps are found, the harness reports:  
    `"leakage_guard_status": "NO_KNOWN_OVERLAP_DETECTED"`
  - The harness and evaluation reports strictly **refuse** to report:  
    `"DATASET_INDEPENDENCE_VERIFIED"`  
    until the AI team supplies the complete train/validation exclusion manifest or equivalent cryptographic provenance.
  - Currently recorded status: `dataset_independence = "NOT_VERIFIED"`.

---

## 11. Missing Manifest Test

- **Test Name**: `test_harness_missing_manifest_blocked`
- **Location**: `services/ai-service/tests/test_evaluation_harness.py`
- **Scenario Tested**:
  1. Harness initialized with `manifest_path=None`.
  2. Harness initialized with non-existent file path (`tmp_path / "does_not_exist.json"`).
- **Result**:
  - `validate_manifest()` returns `False` with `"MANIFEST_NOT_SPECIFIED"` / `"MANIFEST_NOT_FOUND"`.
  - `harness.run()` produces `status = "BLOCKED_DATASET"`, `gold_image_count = 0`.
- **Gate Status**: **PASS**

---

## 12. Empty Dataset Test

- **Test Name**: `test_harness_empty_dataset_blocked`
- **Location**: `services/ai-service/tests/test_evaluation_harness.py`
- **Scenario Tested**: Harness provided with JSON manifest containing `{"images": []}`.
- **Result**:
  - `validate_manifest()` returns `False` with `"EMPTY_DATASET"`.
  - `harness.run()` produces `status = "BLOCKED_DATASET"`, `gate_validation = "EMPTY_DATASET"`.
- **Gate Status**: **PASS**

---

## 13. Invalid Schema Test

- **Test Name**: `test_harness_invalid_schema_blocked`
- **Location**: `services/ai-service/tests/test_evaluation_harness.py`
- **Scenario Tested**: Manifest containing image entries missing mandatory schema fields (`operation`, `is_supported`, `ground_truth_expression`, `is_mathematically_correct`).
- **Result**:
  - `validate_manifest()` returns `False` with `"MISSING_SCHEMA_FIELDS_AT_INDEX_0"`.
  - `harness.run()` produces `status = "BLOCKED_DATASET"`.
- **Gate Status**: **PASS**

---

## 14. Known Leakage Test

- **Test Name**: `test_harness_known_leakage_sample_blocked`
- **Location**: `services/ai-service/tests/test_evaluation_harness.py`
- **Scenario Tested**: Manifest containing an image entry with filename `sample_input_synthetic.jpg` (known integration/training fixture).
- **Result**:
  - `validate_manifest()` returns `False` with `"DATA_LEAKAGE_DETECTED: sample_input_synthetic.jpg was used in integration or training/val."`.
  - `harness.run()` produces `status = "BLOCKED_DATASET"`, `leakage_guard_status = "BLOCKED"`.
- **Gate Status**: **PASS**

---

## 15. Positive Harness Smoke Test

- **Test Name**: `test_harness_positive_smoke_gate`
- **Location**: `services/ai-service/tests/test_evaluation_harness.py`
- **Fixture Used**: `services/ai-service/tests/fixtures/test_manifest_smoke.json` (explicitly documented as synthetic test fixture, NOT gold benchmark evidence).
- **Scenario Tested**: Structurally valid synthetic manifest passing pre-execution schema gate.
- **Result**:
  - `validate_manifest()` returns `True`, `"VALID_MANIFEST"`.
  - `harness.run()` produces:
    - `status = "READY_FOR_BENCHMARK"`
    - `gate_validation = "VALID_MANIFEST"`
    - `leakage_guard_status = "NO_KNOWN_OVERLAP_DETECTED"`
    - `dataset_independence = "NOT_VERIFIED"`
    - `gold_image_count = 1`
  - **Proposal Metrics Zero-Publishing Guarantee**:
    - `critical_token_recognition`: `"NOT_EVALUATED"`
    - `first_error_precision`: `"NOT_EVALUATED"`
    - `over_correction_rate`: `"NOT_EVALUATED"`
    - `p95_ai_latency`: `"NOT_EVALUATED"`
    *(Proposal metrics are never calculated or published from smoke test fixtures).*
- **Gate Status**: **PASS**

---

## 16. Python Regression

- **Environment**: Python 3.12.13 (Windows x86_64), `services/ai-service/.venv`
- **Command Executed**: `python -m pytest tests/`
- **Test Summary**:
  - **Total Tests**: **97**
  - **Passed**: **97**
  - **Failed**: **0**
  - **Skipped**: **0**
  - **Warnings**: 2 (Starlette `httpx` and `anyio` deprecation warnings in test client)
  - **Execution Time**: 12.67s
- **Baseline Comparison**: Expected baseline was 92 tests. With 5 new harness tests added, total is exactly 97.
- **Regression Status**: **PASS**

---

## 17. Files Modified

| File | Type | Description |
|---|---|---|
| `services/ai-service/evaluation/evaluation_config_v1.json` | Modified | Added `provenance_checksums` and `checksum_semantics_documentation` to eliminate SHA conflation. |
| `services/ai-service/evaluation/run_evaluation.py` | Modified | Dynamically computes 4 artifact SHA-256 hashes, records declared manifest SHA, sets `NO_KNOWN_OVERLAP_DETECTED`, enforces zero Proposal metric computation on smoke. |
| `services/ai-service/tests/test_evaluation_harness.py` | **NEW** | Added 5 unit tests for evaluation harness pre-execution gates. |
| `services/ai-service/tests/fixtures/test_manifest_smoke.json` | **NEW** | Tiny synthetic test-only manifest fixture for schema smoke testing. |
| `report/phase_4_3_ai_team_feedback.md` | Modified | Updated with `TOKEN_BENCHMARK_SUBSET`, coverage disclosure rule, and train/val exclusion manifest requirement. |
| `report/phase_4_3_gold_model_evaluation.md` | Modified | Updated Section 14 to independently record all 5 checksums and align status conventions. |
| `report/phase_4_3_0_1_evaluation_protocol_closeout.md` | **NEW** | This closeout report. |

---

## 18. Student Modified

- **Modified**: **NO**
- Zero changes made to `apps/student-mobile/`.

---

## 19. Teacher Modified

- **Modified**: **NO**
- Zero changes made to `apps/teacher-web/`.

---

## 20. AI Training Performed

- **Training / Fine-Tuning**: **NO**
- Model weights (`yolov8n_mathvision_det_v1.pt`) remain bit-for-bit identical to authoritative delivered handoff (`E78F8FA5...`). Zero weights retraining or fine-tuning performed.

---

## 21. Phase 4.3 Status

- **Phase 4.3 Status**: **BLOCKED_DATASET**
- **Gold Images**: **0**
- **Dataset Independence**: **NOT_VERIFIED**
- **Critical-Token Recognition**: **NOT_EVALUATED**
- **First-Error Precision**: **NOT_EVALUATED**
- **Over-Correction Rate**: **NOT_EVALUATED**
- **Formal p95 AI Latency**: **NOT_EVALUATED**
- **Local Inference Smoke Timing**: **RECORDED** (0.0854s warm on CPU, N=10 on single synthetic sample)

---

## 22. Recommended Next Step

Await delivery from the AI/ML training team (Nhóm 6) containing:
1. Held-out gold test dataset manifest (`ai-training/data/manifests/gold_eval_manifest_v1.0.json`) with >= 500 de-identified student worksheet images.
2. `TOKEN_BENCHMARK_SUBSET` bounding boxes and annotations for Critical-Token Recognition benchmarking.
3. Cryptographic train/validation SHA-256 exclusion manifest to verify dataset independence.

Once delivered, execute:
```bash
cd services/ai-service
.\.venv\Scripts\python.exe evaluation/run_evaluation.py --manifest ai-training/data/manifests/gold_eval_manifest_v1.0.json
```
to formally execute and close out Phase 4.3.
