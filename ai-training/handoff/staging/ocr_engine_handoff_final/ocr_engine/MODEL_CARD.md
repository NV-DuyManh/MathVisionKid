# Model Card: Vietnamese Handwriting OCR (CRNN + CTC) — Full Model

## 1. Model Overview

| Field | Detail |
|---|---|
| **Model Name** | Vietnamese-Handwriting-OCR-Full |
| **Model ID** | `ocr_handwriting_full` |
| **Model Version** | 1.0.0 |
| **Architecture** | CRNN (4-block Conv2D + GroupNorm(8, C) + BiLSTM(128) + CTC Loss) |
| **Parameter Count** | **5,962,560** (~5.96M parameters, verified at runtime) |
| **Task** | Vietnamese Handwritten Line-Level Text Recognition |
| **Supported Input Unit** | **Text line crop** (Height=64, Width=1024, RGB) |
| **Output Shape** | `[B, 128, 320]` (128 sequence timesteps, 320 token classes) |
| **Official Checkpoint** | `best_cer.pth` (PyTorch state_dict) |
| **Checkpoint SHA256** | `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` |
| **Checkpoint Size** | 23,856,925 bytes (~23.86 MB uncompressed, ~22.55 MB zipped) |
| **Status** | **Official Handoff Checkpoint / Integration Candidate** for `services/ai-service` |

> [!NOTE]
> **Terminology Notice**: This checkpoint is an **Official Handoff Checkpoint** and **Integration Candidate**. It has undergone independent code and weight verification. It is NOT yet designated as a production-accepted model until MathVision completes system-level validation.

---

## 2. Metric History & Training Run Reconciliation

Two distinct experiments exist in the project history. Their metrics must not be conflated:

### Old Experiment (`ocr_handwriting_15k`)
- **Dataset**: Initial subset of 15,000 samples.
- **Validation CER**: 0.1483 (~14.83%) at step 9,800.
- **Initial Smoke Test**: 0.1411 on 20 sample images.
- **Classification**: Deprecated experimental baseline.

### Current Official Handoff Candidate (`ocr_handwriting_full`)
- **Dataset**: Scaled up to 59,462 training samples.
- **Official Best Validation CER**: **0.1133876 (~11.34%)** across the 500-sample validation set.
- **Best Checkpoint Step**: Step 16,900.
- **Early Stopping Step**: Step 18,901 (training stopped via patience after 2,001 steps without validation improvement).
- **Official Checkpoint File**: `best_cer.pth` (saved at step 16,900).
- **Official Checkpoint SHA256**: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.
- **Classification**: **Official Handoff Candidate**.

---

## 3. Generalization Gap Reconciliation

Previous documentation reported:
- `final_train_cer = 0.1132741` (at step 18,901 from `final.pth`)
- `best_val_cer = 0.1133876` (at step 16,900 from `best_cer.pth`)
- Derived claim: "generalization gap = 0.00011 / virtually zero overfitting"

**Correction**:
This comparison was not methodologically sound because the two metrics came from different training steps:
1. `best_val_cer` was recorded at the peak validation checkpoint at step 16,900.
2. `final_train_cer` was evaluated on the final model at step 18,901, after 2,000 steps of plateau/degradation where validation had worsened and triggered early stopping.

### Rigorous Re-evaluation Using the Same Checkpoint (`best_cer.pth` @ step 16,900):
Evaluating both sets with `best_cer.pth` under identical inference conditions yields:
- **Validation Set Mean CER (500 samples)**: **0.1120 (11.20%)** | Exact Match: 44/500 (8.80%)
- **Train Subset Mean CER (1,600 samples)**: **0.0866 (8.66%)** | Exact Match: 223/1,600 (13.94%)
- **True Generalization Gap**: **0.0254 (2.54%)**

**Conclusion**: The model exhibits a healthy and expected generalization gap of ~2.54%. Claims of "virtually zero overfitting" have been removed.

---

## 4. Sample Provenance & Smoke Test Classification

### Provenance Audit
The 5 bundled sample images (`sample_01.jpg`, `sample_03.jpg`, `sample_04.jpg`, `sample_08.jpg`, `sample_09.jpg`) in `samples/` have `original_rel_path` values pointing to `images/train/train_XXXXX.jpg`.

Audit confirms:
- **Upstream Source**: HuggingFace `Viet-Handwriting-OCR-v2` raw parquet extracts. The upstream archive placed all extracted training images in a directory named `images/train/`.
- **Authoritative Split**: When the 500-sample validation set was constructed (with `seed=42`), the first 500 records were assigned to `val_manifest.json`, keeping their original paths. The remaining samples were assigned to `train_manifest.json`.
- **Audit Verification**:
  - All 5 samples are **present in `val_manifest.json`**.
  - All 5 samples are **strictly absent from `train_manifest.json`**.
- **Role in Package**: These 5 samples serve solely as **`PACKAGE_SMOKE_TEST_SAMPLES`**.

### Smoke Test Metric Classification
- **Measured Mean CER on 5 bundled samples**: **0.0699 (6.99%)**
- **Classification**: **Mean CER on the 5 packaged smoke-test samples only**.
- It must **NOT** be represented as:
  - Official validation CER (which is 0.1134 on 500 images)
  - Independent test set CER
  - Production accuracy

---

## 5. Input Contract & Limitations

> [!IMPORTANT]
> **Line-Level Input Contract**:
> - **Expected Input Unit**: **Single text-line or arithmetic-line crop**.
> - **Resolution**: Fixed `Height=64, Width=1024` (direct bilinear resize).
> - **Color Mode**: RGB (3 channels).
> - **Limitation**: **This model is not intended to directly OCR an entire worksheet image without upstream layout/region segmentation.** Passing a full-page worksheet image will distort aspect ratios and cause severe recognition degradation.

### Upstream Pipeline Requirements:
```
Full Worksheet Image
      │
      ▼
Layout / Region Detection (YOLO / Object Detector)
      │
      ▼
Cropped Line / Answer Region [H, W]
      │
      ▼
Resize to [64, 1024, 3] & Normalize
      │
      ▼
OCR Engine (CRNN + CTC)
      │
      ▼
Recognized String Output
```

---

## 6. MathVision Integration Role

The CRNN model performs purely **character-level recognition on pre-cropped image lines**.

In MathVision Kids, its conceptual role is:
1. **Upstream Layout Stage**: Detects problem regions, student handwriting boxes, and line crops (handled by YOLO / bounding-box detector).
2. **OCR Stage (`ocr_engine`)**: Transcribes the visual image crop into raw UTF-8 string tokens.
3. **Downstream Arithmetic Parser**: Tokenizes mathematical expressions (e.g. `12 + 5 = 17`), identifies operators and operands.
4. **Deterministic Grading Rule Engine**: Verifies mathematical correctness algorithmically.

The CRNN model does **NOT**:
- Replace layout / bounding box detection.
- Interpret whole-page worksheet structure.
- Execute mathematical grading or verification logic.
- Override teacher authority.

---

## 7. Arithmetic-Specific Evaluation

MathVision Kids specifically requires handwriting OCR for elementary arithmetic. An audit was conducted on the existing dataset to evaluate arithmetic capability.

### Dataset Composition Audit:
- **Pure arithmetic lines in 500 validation samples**: **0 / 500** (`ONLY_DIGIT_MATH: none`)
- **Pure arithmetic lines in 59,462 training samples**: **1 / 59,462**
- **Evaluation Status**: **`ARITHMETIC_SPECIFIC_EVALUATION = BLOCKED_DATASET`** for standalone arithmetic worksheet lines. The dataset is general Vietnamese prose, literature, and notes—not an arithmetic worksheet corpus.

### Per-Symbol Accuracy in General Validation Text (500 Samples):
While pure arithmetic lines are absent, digits and operators appear within dates, bullet points, and notes:

| Category | Evaluated Count | Correct | Accuracy | Common Confusions |
|---|---|---|---|---|
| **Overall Digits (0–9)** | 246 | 206 | **83.74%** | See breakdown below |
| **Overall Operators (+, -, =)** | 69 | 61 | **88.41%** | Mostly hyphens (-) used as dashes |
| Digit '0' | 37 | 30 | 81.1% | Confused with 'o', 's', '.' |
| Digit '1' | 63 | 54 | 85.7% | Deleted, confused with 't', '0' |
| Digit '2' | 51 | 45 | 88.2% | Deleted, confused with '1', 'a' |
| Digit '3' | 17 | 16 | 94.1% | Confused with 'D' |
| Digit '4' | 17 | 14 | 82.4% | Confused with '+', 'C', '9' |
| Digit '5' | 13 | 13 | 100.0% | None observed |
| Digit '6' | 12 | 11 | 91.7% | Deleted |
| Digit '7' | 10 | 5 | 50.0% | Confused with 't', '2', 's' |
| Digit '8' | 20 | 14 | 70.0% | Deleted, confused with 'S', '0' |
| Digit '9' | 6 | 4 | 66.7% | Confused with '5', '2' |
| Operator '+' | 6 | 5 | 83.3% | 1 deletion |
| Operator '-' | 50 | 45 | 90.0% | 4 deletions, 1 '=' |
| Operator '=' | 13 | 11 | 84.6% | 1 deletion, 1 '∈' |

### Key Recommendation:
Because the full training run was dominated by general Vietnamese text, symbol recognition on digits (83.7%) and operators (88.4%) is moderate, but **standalone arithmetic expression OCR has not been trained on worksheet data**. MathVision Kids should plan a targeted fine-tuning phase with synthetic or collected elementary math worksheets.

---

## 8. Validation Independence & Data Integrity

- **Train Samples**: 59,462
- **Validation Samples**: 500
- **Split Method**: Shuffled random split with `seed=42`.
- **Image Overlap**: `0` duplicate filenames (`overlap = 0`).
- **Writer Independence**: **UNKNOWN**. Writer IDs are not annotated in the upstream dataset. Lines originating from the same document page may appear in both train and validation sets.

---

## 9. Inference API & Memory-Safe Micro-Batching

`predict_batch()` incorporates configurable micro-batching to prevent Out-Of-Memory (OOM) errors during teacher batch grading workflows (10–30+ images):

```python
from ocr_engine import predict_batch

# Processes images in memory-safe chunks of 4 (configurable)
results = predict_batch(image_paths, batch_size=4)
```

### Micro-Batch Smoke Test Results:
- **Batch 1 (1 image)**: PASS (0.58s first-call / 0.01s warmed)
- **Batch 5 (5 images)**: PASS (0.06s)
- **Batch 10 (10 images)**: PASS (0.11s)
- **Batch 30 (30 images)**: PASS (0.31s)
- **Order Preservation**: 100% verified.
- **Output Count**: Exactly 1 prediction per input.

---

## 10. Verified Runtime Environment

The package was verified in the following standalone environment:

| Component | Verified Version |
|---|---|
| **OS** | Windows 11 (AMD64) [`Windows-11-10.0.26200-SP0`] |
| **Python** | 3.13.9 |
| **PyTorch** | 2.6.0+cu124 (CPU fallback verified) |
| **torchvision** | 0.21.0+cu124 |
| **Pillow** | 12.2.0 |
| **NumPy** | 2.4.4 |
| **Hardware** | NVIDIA GeForce RTX 4050 Laptop GPU / Intel Core CPU |

> [!WARNING]
> **Environment Compatibility Warning**:
> Do not blindly upgrade an existing MathVision AI environment. Integration must verify package version compatibility with the existing `services/ai-service` environment before installing dependencies.
