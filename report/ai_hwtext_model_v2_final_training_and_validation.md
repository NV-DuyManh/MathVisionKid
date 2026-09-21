# AI.HWTEXT.MODEL.V2-FINAL — Data Governance, Training Audit, Independent Holdout & Production Gate Report

**Phase:** `AI.HWTEXT.MODEL.V2-FINAL`  
**Engineer:** Senior AI/ML Handwriting Model Engineer  
**Date:** September 21, 2026  
**Status:** **BLOCKED: INDEPENDENT_HOLDOUT_REQUIRED & MISSING_TRAINING_CORPUS**  
**Companion Documents:**
- Benchmark Governance: `report/HANDWRITING_BENCHMARK_GOVERNANCE.md`
- Dataset Manifest: `report/HANDWRITING_MODEL_V2_DATASET_MANIFEST.json`
- Training Data Audit: `report/HANDWRITING_MODEL_V2_DATA_AUDIT.md`
- V2 Verification Results: `report/HANDWRITING_MODEL_V2_VERIFICATION_RESULTS.json`
- Independent Holdout Results: `report/HANDWRITING_MODEL_V2_INDEPENDENT_HOLDOUT_RESULTS.json`
- Model V2 Training Config: `models/ocr/crnn_vi_handwriting_v2/training_config.yaml`
- Model V2 Acceptance Gate: `report/HANDWRITING_MODEL_V2_ACCEPTANCE_GATE.md`

---

## Skills Applied

Skills matched: none

---

## 1. Executive Summary

Phase `AI.HWTEXT.MODEL.V2-FINAL` was executed to govern data splits, reclassify legacy evaluation benchmarks, freeze preprocessing standards, audit training data availability, and determine Model V2 readiness.

### Key Outcomes:
1. **Evaluation Governance Established:** Dataset roles have been formally partitioned into `TRAIN`, `DEV`, `REGRESSION_33`, and `INDEPENDENT_HOLDOUT_V2`. Anti-leakage rules and writer-disjoint requirements are encoded into `report/HANDWRITING_BENCHMARK_GOVERNANCE.md`.
2. **Truthful Reclassification of the 33-Line Benchmark:** The 33-line locked benchmark in `report/HANDWRITING_OCR_LOCKED_BENCHMARK_MANIFEST.json` has been formally reclassified as **`REGRESSION_33`** (an engineering regression set, not an independent holdout). Its holdout eligibility is set to `false`, and training exposure status is set to `UNKNOWN`.
3. **Official Preprocessing Frozen (`OCR_PREPROC_V2_1`):** Fixed tensor shape `[B, 3, 64, 1024]`, aspect-preserving resize with right padding, ImageNet normalization, and Unicode NFC canonical composition.
4. **Data Quality Audit & Honest Training Block:** An exhaustive audit revealed that the upstream 59,462 raw handwriting images from `Viet-Handwriting-OCR-v2` are absent from this machine. Quarantined owner data has 0 verified labels. PyTorch in `.venv` is CPU-only. In accordance with Section 9 and Section 3 of the prompt, gradient training was **halted honestly without fabricating synthetic checkpoints**.
5. **Release Gating:** Physical pipeline smoke testing remains **`READY`**, but final OCR release acceptance is strictly **`WAIT_FOR_MODEL_V2`** / **`NOT_READY_FOR_FINAL_OCR_ACCEPTANCE`**.

---

## 2. Dataset Governance

The governance manifest `report/HANDWRITING_MODEL_V2_DATASET_MANIFEST.json` catalogues all on-disk handwriting assets and defines strict operational boundaries:

### Split Roles & Rules:
- **`TRAIN`:** Gradient updates only. Currently **0 samples on disk** (upstream corpus missing).
- **`DEV`:** Checkpoint selection and early stopping only. Currently **5 verified samples** (`DEV_train_0010933`, `DEV_train_0054912`, `DEV_train_0030168`, `DEV_train_0000288`, `DEV_train_0000582`).
- **`REGRESSION_33`:** Continuous integration non-regression test fixture. 33 lines. Prohibited from checkpoint selection or generalization claims.
- **`INDEPENDENT_HOLDOUT_V2`:** Genuinely unseen multi-writer test set for release gating. Currently **0 samples on disk** (`INDEPENDENT_HOLDOUT_REQUIRED`).
- **`PARKED_UNTRAINED`:** 173 owner images (331 lines) quarantined in `ai-training/parking/owner_173_untrained/`. 0 verified annotations. Barred from training.

### Anti-Leakage Invariants:
1. Synthetic variants generated from `TRAIN` remain `TRAIN` permanently.
2. No writer or page overlap between `TRAIN`, `DEV`, and `INDEPENDENT_HOLDOUT_V2`.

---

## 3. Regression33 Reclassification

`report/HANDWRITING_OCR_LOCKED_BENCHMARK_MANIFEST.json` has been updated and ratified under `report/HANDWRITING_BENCHMARK_GOVERNANCE.md`:

```json
{
  "benchmarkRole": "REGRESSION_33",
  "benchmarkScope": "Authoritative locked engineering regression benchmark (REGRESSION_33) spanning 6 fixtures and 33 ground-truth handwriting lines",
  "eligibleForHoldoutClaims": false,
  "seenDuringModelTraining": "UNKNOWN"
}
```

### Rationale:
The 33 lines have been inspected across repeated engineering cycles (PROD.2A through PROD.4B.2R5) to calibrate line bounding box padding, character posteriors, and CTC beam search margins. Under scientific ML governance, an asset exposed during development is an engineering regression fixture, not a blind holdout.

---

## 4. Independent Holdout Definition

To qualify as `INDEPENDENT_HOLDOUT_V2` for final release gating, a dataset must meet the following mandatory specifications:
1. **Minimum 10 distinct child writers** spanning elementary grades.
2. **Minimum 20 unique physical pages** and **200 line crops**.
3. **Diverse paper styles:** Grid-ruled (ô ly), horizontal ruled, and plain paper.
4. **Writing implements:** Blue fountain pen, blue ballpoint, black pencil, and gel pen.
5. **No phrase reuse:** Must not reuse the Owner poem ("Em yêu mùa hè...") or known training prompts.
6. **Current Status:** **`BLOCKED_DATASET_MISSING`** (`INDEPENDENT_HOLDOUT_REQUIRED`).

---

## 5. Data Audit

Full audit details are documented in `report/HANDWRITING_MODEL_V2_DATA_AUDIT.md`. Across all 38 active on-disk evaluation samples (745 characters, 146 spaces):

| Category | Character / Feature | Count on Disk | Status / Deficit |
|---|:---:|:---:|---|
| **Target Cursive Capitals** | **`E`** | 7 | Low (restricted to 2 poem phrases) |
| | **`S`** | **0** | **CRITICAL DEFICIT (Absent from disk)** |
| | **`T`** | 11 | Moderate (restricted to 4 phrases) |
| | **`C`** | 5 | Low (restricted to `"Có hoa sim tím"`) |
| **Cursive Ligatures** | **`r`** | 26 | Moderate |
| | **`l`** | 8 | Low |
| | **`h`** | 42 | Adequate (digraphs `nh`, `th`, `ch`) |
| **Vietnamese Base Bases** | **`ă`** | 3 | Low |
| | **`â`** | 6 | Low |
| | **`ê`** | 16 | Moderate |
| | **`ô`** | **0** | **CRITICAL DEFICIT (Absent)** |
| | **`ơ`** | 1 | Low |
| | **`ư`** | 13 | Moderate |
| | **`đ` / `Đ`** | 8 / **0** | Lowercase present; **Uppercase Đ absent** |
| **Tone Marks (NFD)** | **Acute (`sắc`)** | 41 | 39.8% |
| | **Grave (`huyền`)** | 30 | 29.1% |
| | **Hook (`hỏi`)** | 12 | 11.7% |
| | **Dot (`nặng`)** | 16 | 15.5% |
| | **Tilde (`ngã`)** | **4** | **3.9% (Severely deficient)** |

**Deficit Summary:** Without uppercase cursive $S$, uppercase $Đ$, base $ô$, and balanced tilde diacritics, any model trained on local data would fail to learn elementary Vietnamese orthography.

---

## 6. Architecture Decision

### Comparison of Candidate Paths:
1. **Candidate A: Enhanced CRNN + 2-Layer BiLSTM(256) + Focal CTC (SELECTED FOR V2)**
   - **Backbone:** 4-block CNN + GroupNorm(8, C) + 2-layer BiLSTM (hidden size 256) + Linear(320).
   - **Tensor Contract:** Exactly preserves `[B, 3, 64, 1024]` input and `[T, B, 320]` output.
   - **CPU Latency:** Measured $< 60\text{ ms}$ on local CPU (well under the 150 ms threshold).
   - **Advantage:** Doubling LSTM capacity and introducing Focal CTC directly addresses ligature collapses without breaking runtime integration.
2. **Candidate B: CRNN + Spatial Transformer Network (STN)**
   - **Evaluation:** Increases parameter footprint and introduces grid sampling overhead without addressing character-level class imbalance.
3. **Candidate C: Vision Transformer / TrOCR (REJECTED)**
   - **Evaluation:** High inference latency on mobile CPU ($> 450\text{ ms}$), requires massive pre-training data ($> 500\text{k}$ lines), and breaks the real-time synchronous OCR contract.

---

## 7. Training Configuration

The configuration specification has been created at `models/ocr/crnn_vi_handwriting_v2/training_config.yaml`:
- **Optimizer:** AdamW ($lr = 0.0003$, $weight\_decay = 0.0001$).
- **Scheduler:** CosineAnnealingWarmRestarts ($T_0 = 10$, $T_{mult} = 2$).
- **Batch Size:** 32 ($input = [3, 64, 1024]$).
- **Loss:** CTCLoss with Focal Weighting ($0.25$) to penalize premature blank emissions.
- **Early Stopping:** Patience 15 epochs monitored strictly on `DEV` split CER.
- **Checkpoint Selection:** Prohibited from using `REGRESSION_33` or `INDEPENDENT_HOLDOUT_V2`.

---

## 8. Training Results

**Status:** **`HALTED_PRE_EXECUTION`**

### Reasons for Training Halt:
1. **Missing Training Dataset:** The 59,462 raw images from the upstream repository are not present on disk.
2. **Zero Verified Local Annotations:** The parked owner dataset has 0 verified lines (`"verified": 0, "status": "pending"`).
3. **Hardware / Runtime Compatibility:** Python environment `.venv` is CPU-only (`torch.cuda.is_available() == False`).
4. **Anti-Fabrication Policy:** Per Section 9 of the prompt, training was stopped honestly rather than generating fake or unvalidated weights.

---

## 9. Artifact Integrity

| Artifact | Location | SHA256 Hash | Status |
|---|---|---|:---:|
| **Model V1 Weights** | `services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth` | `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` | **VALID (Active)** |
| **Model V1 Vocab** | `services/ai-service/models/ocr/crnn_vi_handwriting_v1/vocab.json` | `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d` | **VALID (Active)** |
| **Model V2 Weights** | `models/ocr/crnn_vi_handwriting_v2/best_cer.pth` | — | **NOT_PRODUCED** |
| **Model V2 Config** | `models/ocr/crnn_vi_handwriting_v2/training_config.yaml` | `1115bbfd2d27e02eef51f506e30b80f8f3073d839352e071db116aa475eb0183` | **VALID (Spec Frozen)** |

---

## 10. V1 vs V2 Regression33

Evaluated under `OCR_PREPROC_V2_1` across `REGRESSION_33` (`report/HANDWRITING_MODEL_V2_VERIFICATION_RESULTS.json`):

| Model Candidate | CER (%) | WER (%) | Exact Match | P95 Latency (CPU) | Capital Confusions | Cursive Drops | Diacritic Errors | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Model V1 (Production)** | **3.75%** | **15.15%** | **18 / 33 (54.55%)** | **54.2 ms** | 7 | 8 | 6 | **BASELINE** |
| **Model V2 (Candidate)** | — | — | — | — | — | — | — | **BLOCKED** |
| **Target Gate Threshold** | **$\le 2.50\%$** | **$\le 8.00\%$** | **$\ge 85.00\%$ ($\ge 28/33$)** | **$\le 150.0\text{ ms}$** | **$\le 1$** | **$\le 1$** | **$\le 2$** | **GATE** |

---

## 11. V1 vs V2 Independent Holdout

Detailed in `report/HANDWRITING_MODEL_V2_INDEPENDENT_HOLDOUT_RESULTS.json`:
- **Model V1 Evaluation:** `NOT_EVALUATED_NO_HOLDOUT_DATASET`
- **Model V2 Evaluation:** `NOT_EVALUATED_NO_HOLDOUT_DATASET`
- **Holdout Status:** **`BLOCKED: INDEPENDENT_HOLDOUT_REQUIRED`**

---

## 12. Error Analysis (Current V1 Production Baseline)

1. **Cursive Capital Confusion ($E/S/T/C$):** 7 errors. Onset cursive loops in $E$ and $C$ compete with $S$ and $T$ ($P(C)=0.3599$ vs $P(T)=0.3571$).
2. **Cursive Ligature Drops ($r/l/h$):** 8 errors. Continuous strokes in $trên \to tên$, $lưng \to ng$, $rinh \to ring$ are absorbed by CTC blank collapse.
3. **Diacritic Inversions:** 6 errors. Horizontal drift in handwriting flourishes confuses grave ($huyền$) with circumflex roof ($è \to ề$).

---

## 13. Latency Audit

Benchmarked on local CPU across the 33 lines of `REGRESSION_33`:
- **Mean Single-Line Latency:** **38.6 ms**
- **P95 Single-Line Latency:** **54.2 ms**
- **Batch-4 Latency:** **78.4 ms**
- **Latency Gate ($\le 150\text{ ms}$):** **PASS**

---

## 14. Acceptance Gate Results

| Acceptance Criterion | Target Threshold | Current Result | Gate Outcome |
|---|:---:|:---:|:---:|
| **Artifact Hashes Verified** | Valid SHA256 in manifest | V1 valid; V2 unproduced | **BLOCKED** |
| **Runtime Contract Compatibility** | `[B, 3, 64, 1024]` | Preserved by CrnnOcrProvider | **PASS** |
| **Regression CER** | $\le 2.50\%$ | V1: $3.75\%$ (V2 unproduced) | **BLOCKED** |
| **Regression WER** | $\le 8.00\%$ | V1: $15.15\%$ (V2 unproduced) | **BLOCKED** |
| **Regression Exact Match** | $\ge 85.00\%$ | V1: $54.55\%$ (V2 unproduced) | **BLOCKED** |
| **Independent Holdout Validation** | Certified on unseen holdout | Holdout dataset missing | **BLOCKED** |
| **P95 CPU Latency** | $\le 150\text{ ms}$ | V1: $54.2\text{ ms}$ | **PASS** |

---

## 15. Production Integration

### Safe Deployment Architecture:
1. **Active Model Selection:** Model V1 (`services/ai-service/models/ocr/crnn_vi_handwriting_v1`) remains the active production OCR engine.
2. **V2 Fallback Architecture:** `CrnnOcrProvider` validates cryptographic checksums against `model_manifest.json` on startup. If a candidate V2 directory is configured but corrupt or missing, the provider automatically falls back to V1 with an explicit diagnostic log.
3. **Zero Product Regressions:** All mobile and backend flows remain verified:
   - System picker launches directly from Home (never routes to `/gallery`).
   - Crop session reset verified.
   - Privacy masking bounds clamp cleanly.
   - Mounted async advisor updates operate without mutating user draft.
   - User edits (`MANUAL_EDIT`) and chip selections (`SUGGESTION_1/2`) strictly take precedence.

---

## 16. Full Test Accounting

| Test Suite | Pass | Fail | Skip | Command | Exit Code | Status |
|---|:---:|:---:|:---:|---|:---:|:---:|
| **Canonical Identity Forensics** | 3 | 0 | 0 | `pytest tests/test_canonical_manifest_identity.py` | 0 | **PASS** |
| **True Canonical Segmentation (6/6)** | 6 | 0 | 0 | `python tests/eval_6_sample_segmentation.py` | 0 | **PASS** |
| **Locked Benchmark Validator** | 1 | 0 | 0 | `python evaluation/validate_benchmark_manifest.py` | 0 | **PASS** |
| **Product No-Regression Pytest** | 33 | 0 | 6 | `pytest tests/test_owner_physical_line2_regression.py tests/test_true_redetect_quality_safety.py tests/test_groq_production_route.py tests/test_gemini_availability.py` | 0 | **PASS** |
| **Mobile React Native Jest** | 71 | 0 | 0 | `npx jest --preset jest-expo` | 0 | **PASS** |
| **Mobile TypeScript Strict Check** | 1 | 0 | 0 | `npx tsc --noEmit` | 0 | **PASS** |
| **Mobile ESLint Check** | 1 | 0 | 0 | `npm run lint` | 0 | **PASS** |
| **Spring Boot OcrMultiline Suite** | 5 | 0 | 0 | `.\gradlew.bat test --tests "*OcrMultiline*"` | 0 | **PASS** |

---

## 17. Remaining Limitations

1. **Acoustic/Visual Model Bottleneck:** Model V1 remains at CER $\approx 3.75\% - 5.99\%$ and WER $\approx 15.15\% - 22.73\%$.
2. **Missing External Datasets:** Retraining requires ingestion of the 59k training corpus or a new curated elementary dataset from the AI/ML team.
3. **GPU Training Requirement:** Training must be conducted in an environment equipped with CUDA-enabled PyTorch.

---

## 18. Physical OCR Acceptance Readiness

### Operational Separation:
1. **Physical Pipeline Smoke Test:** **`READY`**
   - The end-to-end mobile app (camera/gallery direct acquisition, image cropping, 6/6 line segmentation, background Groq/Gemini suggestion montage, and UI review chips) is stable, safe, and ready for smoke verification.
2. **Physical OCR Acceptance Test:** **`WAIT_FOR_MODEL_V2`**
   - Formal acceptance of handwriting text accuracy must wait until a retrained Model V2 meets the target acceptance gate.

---

## 19. Final Verdict

```
Regression33Verdict: MODEL_BOTTLENECK
IndependentHoldoutVerdict: BLOCKED_DATASET_MISSING
LatencyVerdict: PASS
ArtifactIntegrityVerdict: BLOCKED_NO_V2_ARTIFACT
ModelV2Verdict: BLOCKED
PhysicalPipelineSmokeTestVerdict: READY
PhysicalOcrAcceptanceVerdict: WAIT_FOR_MODEL_V2
ReleaseVerdict: NOT_READY_FOR_FINAL_OCR_ACCEPTANCE
```
