# ocr_engine — Vietnamese Handwriting OCR (CRNN + CTC)

Standalone inference and integration package for the **Vietnamese Handwriting OCR Model** (`ocr_handwriting_full`).

- **Model Status:** Official Handoff Checkpoint / Integration Candidate (NOT yet designated as production-accepted)
- **Official Checkpoint:** `best_cer.pth` (59K full training run @ step 16,900)
- **Official Checkpoint SHA256:** `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`
- **Official Validation CER:** **0.1134 (11.34%)** on the 500-sample validation set
- **Packaged Smoke-Test CER:** **0.0699 (6.99%)** on the 5 bundled sample images (smoke test only)
- **Architecture:** CRNN (4-block Conv2D + GroupNorm(8, C) + BiLSTM(128) + Linear(320))
- **Parameter Count:** **5,962,560** parameters
- **Vocabulary:** 320 continuous tokens (`vocab.json`, CTC blank ID = 0, full Vietnamese tonal diacritics, digits 0–9, math symbols)

---

## 1. Purpose & Integration Role

This package provides offline, self-contained inference for recognizing single lines of handwritten Vietnamese text.

### Role in MathVision Kids:
```
Worksheet Image
      │
      ▼
Layout Detection (YOLO / Bounding Box Detector)
      │
      ▼
Text Line Crop [H, W]  ──►  ocr_engine (CRNN + CTC)  ──►  Recognized String
                                                                  │
                                                                  ▼
                                                      Arithmetic Expression Parser
                                                                  │
                                                                  ▼
                                                      Deterministic Grading Rule Engine
```

> [!IMPORTANT]
> **What This Model Does NOT Do**:
> - It does NOT process full-page worksheet images directly.
> - It does NOT replace layout / problem bounding-box detection (e.g., YOLO).
> - It does NOT perform mathematical calculation or grading.
> - It does NOT override teacher authority.

---

## 2. Input Contract & Preprocessing

- **Input Unit:** **Single text-line or arithmetic-line image crop**.
- **Aspect Ratio & Resize:** Resized directly to **(Height=64, Width=1024)** using bilinear interpolation.
- **Color Mode:** **RGB (3 channels)**. Single-channel grayscale and 4-channel RGBA images are automatically converted to RGB.
- **Tensor Range:** `[0.0, 1.0]` via `torchvision.transforms.ToTensor()`.
- **Normalization:** ImageNet standardization:
  - `mean = [0.485, 0.456, 0.406]`
  - `std  = [0.229, 0.224, 0.225]`
- **Limitation Notice:** Passing full-page worksheets without cropping will distort the aspect ratio and cause severe recognition degradation.

---

## 3. CTC Decoding

- Timesteps: 128 sequence positions output by BiLSTM + Linear layer.
- Greedy decoding: `argmax` per timestep.
- Consecutive identical characters are collapsed (`(c, c) -> c`).
- CTC blank token (`ID = 0`) is removed.
- Remaining indices are mapped to characters via `vocab.json`.

---

## 4. Supported Python API

### Single-Image Inference
```python
from ocr_engine import predict_text
from PIL import Image

# From file path:
text = predict_text("samples/sample_01.jpg")
print("OCR Output:", text)

# From PIL Image instance:
img = Image.open("samples/sample_01.jpg")
text = predict_text(img)
print("OCR Output:", text)
```

### Batch Inference with Memory-Safe Micro-Batching
For practical teacher workflows with 10–30+ images, `predict_batch()` uses configurable micro-batching to prevent GPU/system Out-Of-Memory (OOM) errors:

```python
from ocr_engine import predict_batch

image_list = ["crop_01.jpg", "crop_02.jpg", "crop_03.jpg", ...]

# Processes images in chunks of 4 (default conservative batch size)
results = predict_batch(image_list, batch_size=4)

for img_path, res in zip(image_list, results):
    print(f"{img_path} -> {res}")
```

### Device Selection (CPU / CUDA)
By default, the engine automatically selects CUDA if available, or falls back to CPU. You can explicitly set the device:

```python
# Force CPU execution:
text_cpu = predict_text("samples/sample_01.jpg", device="cpu")

# Or configure globally via environment variable:
import os
os.environ["OCR_DEVICE"] = "cpu"
```

---

## 5. Quickstart Verification & Smoke Test

Run the included verification suite to confirm package integrity, parameter count, checkpoint SHA256, single-image inference, and micro-batch execution:

```bash
# Inside ocr_engine directory:
python test_predict.py

# Or from workspace root:
python -m ocr_engine.test_predict
```

Expected output:
```
=================================================================
   OCR ENGINE HANDOFF VERIFICATION & PACKAGE SMOKE TEST
=================================================================
[1/6] Verifying Imports & Architecture...    --> PASS
[2/6] Verifying Official Checkpoint...       --> PASS (SHA256 verified)
[3/6] Verifying Vocabulary Contract...       --> PASS (320 tokens, blank=0)
[4/6] Verifying Model Parameter Count...     --> PASS (5,962,560 params)
[5/6] Running Package Smoke Test...          --> Mean CER: 0.0699 (6.99%)
[6/6] Testing Micro-Batch Inference...       --> Batches 1, 5, 10, 30 PASS
=================================================================
```

---

## 6. Metric History & Performance Distinctions

| Metric | Value | Scope / Dataset | Purpose |
|---|---|---|---|
| **Official Validation CER** | **0.1134 (11.34%)** | 500 validation images | Official model validation metric from training run |
| **Package Smoke-Test CER** | **0.0699 (6.99%)** | 5 bundled sample images | Functional smoke test only (NOT a benchmark) |
| **Old 15K Baseline CER** | 0.1483 (14.83%) | 15,000 subset | Deprecated initial experiment |
| **True Generalization Gap** | **0.0254 (2.54%)** | Step 16,900 train vs val | Measured using `best_cer.pth` (Train CER: 8.66%, Val CER: 11.20%) |

> [!CAUTION]
> Do NOT cite the 5-sample smoke test CER (6.99%) as validation accuracy or production accuracy. The authoritative validation metric is **11.34%** on the 500-sample validation set.

---

## 7. Arithmetic Evaluation & Known Limitations

1. **Arithmetic Dataset Limitation (`BLOCKED_DATASET`)**:
   - The training set contains 59,462 lines of general Vietnamese handwriting (literature, essays, notes).
   - Standalone arithmetic worksheet lines are virtually absent (0 pure arithmetic lines in validation, 1 in train).
   - In general text occurrences:
     - **Digit Accuracy (0–9)**: **83.74%**
     - **Operator Accuracy (+, -, =)**: **88.41%**
   - **Recommendation**: Do NOT expect reliable recognition of complex arithmetic layouts without dedicated math fine-tuning.
2. **Line-Level Scope**: Requires upstream line detection (YOLO).
3. **Fixed Width (1024)**: Very short words are stretched and very long lines are compressed; preprocessing maintains fixed (64, 1024) dimensions.
4. **Validation Independence**: Images are disjoint from training, but writer independence is unverified (writer IDs were not labeled in the raw dataset).

---

## 8. Verified Runtime Environment

Verified on:
- **OS**: Windows 11 (AMD64)
- **Python**: 3.13.9
- **PyTorch**: 2.6.0+cu124 (CPU fallback verified)
- **torchvision**: 0.21.0+cu124
- **Pillow**: 12.2.0
- **NumPy**: 2.4.4

> [!WARNING]
> Do not blindly upgrade an existing MathVision AI environment. Integration must check version compatibility with the existing `services/ai-service` environment before installing dependencies. Exact versions are documented in `requirements-verified.txt`.

---

## 9. Package File Structure

```
ocr_engine/
├── __init__.py               # Package marker and exports
├── best_cer.pth              # Official checkpoint weights (SHA256: a807eaa...)
├── model.py                  # CRNN architecture definition
├── vocab.json                # 320-token vocabulary mapping
├── predict.py                # Inference module with micro-batching
├── test_predict.py           # Verification & smoke test suite
├── requirements.txt          # Minimal dependency requirements
├── requirements-verified.txt # Exact versions from verified environment
├── model_manifest.json       # Machine-readable handoff manifest
├── MODEL_CARD.md             # In-depth architectural & metric documentation
├── README.md                 # This documentation
└── samples/                  # Bundled smoke test samples
    ├── sample_01.jpg
    ├── sample_03.jpg
    ├── sample_04.jpg
    ├── sample_08.jpg
    ├── sample_09.jpg
    └── sample_manifest.json  # Provenance & split metadata
```