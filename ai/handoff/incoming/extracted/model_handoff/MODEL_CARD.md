# MODEL CARD — MathVision Kids

**Version**: 1.0.0  
**Date**: 2026-09-08  
**Prepared by**: Nhóm 6  

---

## 1. Model Overview

MathVision Kids consists of **two trained models** plus a **deterministic parser engine**:

| Component | Architecture | Task | Format |
|-----------|-------------|------|--------|
| Detection | YOLOv8n (ultralytics) | Object detection of handwritten math tokens | `.pt` (ultralytics native) |
| OCR | CRNN (CNN + BiLSTM + CTC) | Line-level Vietnamese handwriting recognition | `.pth` (PyTorch state_dict) |
| Parser | Deterministic rule engine | Vertical add/subtract verification | `.py` (pure Python) |

---

## 2. Detection Model — YOLOv8n

### Architecture
- **Base**: YOLOv8n (nano) — pretrained on COCO, fine-tuned
- **Backbone**: CSPDarknet (YOLOv8n standard)
- **Head**: YOLOv8 detection head, 14 output classes
- **Parameters**: ~3.2M
- **Input**: 640×640 RGB, letterbox-resized by ultralytics

### Training Setup
- **Framework**: ultralytics >= 8.0, PyTorch 2.6.0+cu124
- **Optimizer**: SGD (auto by ultralytics), lr0=0.01, lrf=0.01
- **Batch size**: 24
- **Epochs**: 3 (fine-tune from COCO pretrained)
- **Augmentation**: mosaic=1.0, fliplr=0.5, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, translate=0.1, scale=0.5, erasing=0.4, randaugment
- **AMP**: enabled
- **Seed**: 42
- **GPU**: NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM)
- **Training time**: ~145 seconds (3 epochs)

### Dataset Version
- **Dataset**: `combined_dataset_fixed_v1.0` (cleaned from `combined_dataset`)
- **Data config**: `D:\nhom6\train_thu_clean\data.yaml`
- **Train images**: 1809
- **Val images**: 192
- **Total annotations**: 14,512
- **No train/val image overlap**: confirmed (0 overlap)

### Supported Labels (14 classes)
| ID | Label | Category |
|----|-------|----------|
| 0-9 | `0`–`9` | Digit |
| 10 | `+` | Operator |
| 11 | `-` | Operator |
| 12 | `=` | Separator |
| 13 | `c1` | Carry marker |

### Evaluation Results (D3 — val set, 192 images)

| Metric | Value |
|--------|-------|
| **mAP@50** | **0.9672** |
| **mAP@50-95** | **0.7222** |
| **Precision** | **0.9284** |
| **Recall** | **0.9450** |

#### Per-class mAP@50:
| Class | mAP@50 | Precision | Recall |
|-------|--------|-----------|--------|
| 0 | 0.984 | 0.957 | 0.985 |
| 1 | 0.915 | 0.993 | 0.916 |
| 2 | 0.923 | 0.958 | 0.926 |
| 3 | 0.895 | 0.922 | 0.907 |
| 4 | 0.964 | 0.800 | 0.982 |
| 5 | 0.924 | 0.945 | 0.931 |
| 6 | 0.975 | 0.950 | 0.979 |
| 7 | 0.984 | 0.983 | 0.983 |
| 8 | 0.994 | 0.964 | 1.000 |
| 9 | 0.982 | 0.934 | 0.983 |
| + | 0.903 | 0.952 | 0.909 |
| - | 0.845 | 0.920 | 0.860 |
| = | 0.748 | 0.757 | 0.898 |
| c1 | 0.965 | 0.964 | 0.973 |

#### Latency (val set):
| Metric | Value |
|--------|-------|
| Mean | 28.4 ms |
| Median | 16.4 ms |
| P95 | 76.7 ms |

### Limitations & Known Failure Cases

1. **`=` sign (equals/horizontal line)**: Lowest mAP@50 = 0.748, precision = 0.757. Often confused with horizontal lines in ruled paper.
2. **`-` sign (minus)**: mAP@50 = 0.845. Can be confused with horizontal lines, especially in scan artifacts.
3. **Only 3 epochs of fine-tuning**: Model converged fast from COCO pretrained weights but may underfit on harder examples.
4. **Synthetic-heavy dataset**: 85% synthetic data (1200 syn + 500 syn_batch2), only 15% real HME images (301). Real handwriting variation may not be fully covered.
5. **Bbox clipping artifacts**: 196 annotations have slight out-of-[0,1] coordinates from synthetic generation (clamped at inference).
6. **Multiplication/Division**: NOT supported. Only vertical addition and subtraction.
7. **Multi-problem pages**: May produce `needs_review` if page contains more than one math problem.
8. **Class imbalance**: digit `1` has 1508 instances vs `=` with only 468 (3.2:1 ratio).

---

## 3. OCR Model — CRNN (EXPERIMENTAL)

### Architecture
- **CNN backbone**: 4-layer CNN with GroupNorm(8), channels: 3→64→128→256→512
- **RNN**: 1-layer bidirectional LSTM, hidden=128
- **FC head**: Linear(256, 237) — 237 output classes
- **Loss**: CTC loss (blank_idx=0)
- **Parameters**: ~8M

### Training Setup
- **Framework**: PyTorch 2.6.0+cu124
- **Optimizer**: AdamW, lr=1e-3 (peak), weight_decay=1e-5
- **Schedule**: Warmup 200 steps at 1e-5, cosine anneal to 1e-3 over 4800 steps, total 5000 steps
- **Gradient clipping**: max_norm=5.0
- **Batch size**: 16
- **AMP**: enabled (torch.amp.GradScaler)
- **Early stop**: CER < 0.3 on validation
- **Seed**: 42

### Dataset Version
- **Dataset**: `Viet-Handwriting-OCR-v2` (external/Viet-Handwriting-OCR-v2/extracted)
- **Train**: 1800 samples
- **Val**: 200 samples
- **Vocab**: 237 characters (Vietnamese + symbols, built from first 1000 train samples)

### Input Preprocessing (MUST match at runtime)
```python
transforms.Compose([
    transforms.Resize((64, 1024)),     # PIL resize
    transforms.ToTensor(),              # [0,1]
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],    # ImageNet mean
        std=[0.229, 0.224, 0.225]      # ImageNet std
    )
])
```

### Evaluation Results

> ⚠️ **EXPERIMENTAL STATUS**: Full CER/WER evaluation on held-out test set has NOT been completed. Model was trained with early stop target CER < 0.3 but final validation CER was not captured in a reproducible report.

### Limitations & Known Failure Cases

1. **No validated CER metric**: The training script logged CER during training but no final evaluation report was generated.
2. **Vocab coverage**: Built from first 1000 samples only — may miss rare Vietnamese characters.
3. **Timestep bottleneck**: Input width=1024, after 3 max-pools (÷8) → 128 timesteps. Maximum text length 116 chars but 1646/2000 samples exceed 32 timesteps — CTC may struggle with long texts.
4. **Validate_checkpoint.py has bugs**: Multiple redefinitions of CRNN class and functions; the validation script is unreliable as-is.
5. **Single font/style**: Trained on Viet-Handwriting-OCR-v2 only — not tested on children's handwriting specifically.
6. **No beam search**: Greedy CTC decode only. Beam search with language model would improve accuracy.

---

## 4. Parser Engine — Deterministic

### Capabilities
- Parses vertical addition/subtraction from YOLO detections
- Column-by-column verification with carry/borrow tracking
- Returns structured JSON with per-column correctness
- 14/14 unit tests passing

### Limitations
- Only supports single-problem images (addition OR subtraction)
- No support for multiplication, division, or horizontal layout
- Multiple operators on one page → `needs_review`
- Depends on detection quality — low-confidence detections → `needs_review`

---

## 5. Hardware & Runtime Used for Training/Evaluation

| Component | Specification |
|-----------|---------------|
| GPU | NVIDIA GeForce RTX 4050 Laptop GPU, 6 GB VRAM |
| CUDA | 12.4 |
| Driver | 555.97 |
| CPU | (laptop, Windows) |
| Python | 3.13.9 |
| PyTorch | 2.6.0+cu124 |
| torchvision | 0.21.0+cu124 |
| OS | Windows |
| Disk | D: drive, ~22.8 GB free at training time |

---

## 6. Ethical Considerations

- **No child PII in model weights**: Model weights do not contain personally identifiable information.
- **De-identified sample**: The sample inference input is a synthetic/AI-generated image, not from any real student.
- **Dataset sources**: HME-VAS (public academic dataset), synthetic generated data, Viet-Handwriting-OCR-v2.
- **Real collected images** (33 images in `external/real_collected/`) were used for annotation review only and are NOT distributed in this handoff package.
