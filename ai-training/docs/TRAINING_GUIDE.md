# MathVision Kids Line OCR Training & Fine-Tuning Guide

**Document Version**: 1.0.0  
**Pipeline**: Transfer Learning from `best_cer.pth` (CRNN + CTC)  
**Target Hardware**: Google Colab T4 GPU / CUDA 12+

---

## 1. Transfer Learning Architecture

Rather than training a model from scratch, the pipeline warms up from the official `best_cer.pth` checkpoint, which has already learned extensive Vietnamese cursive handwriting representations from 59,462 lines.

### 1.1 Checkpoint Adaptation (`scripts/adapt_checkpoint.py`)
When expanding the vocabulary from 320 to 326 tokens (incorporating `×`, `÷`, `±`, `Ẳ`, `Ẵ`, `Ỳ`):
- All CNN backbone and BiLSTM layers matching keys and shapes are copied directly without modification.
- The classifier layer `fc.weight` and `fc.bias` copies rows for existing class indices ($0 \dots 319$) and initializes new rows ($320 \dots 325$) matching the empirical variance ($\sigma \approx 0.2363$).
- Generates `artifacts/checkpoints/adapted_init.pth` loaded with `strict=True`.

---

## 2. Multi-Stage Fine-Tuning Strategy

Configured in `configs/train_finetune.yaml`:

### Stage 1: Backbone Freezing (Steps $0 \to 200$)
- CNN backbone weights (`cnn.*`) are frozen (`requires_grad=False`).
- Only the BiLSTM recurrent layer and adapted classifier head (`rnn.*`, `fc.*`) are optimized with learning rate $\eta_{\text{head}} = 10^{-4}$.
- Prevents destroying pretrained convolutional feature extractors while newly initialized output classes stabilize.

### Stage 2: Full Differential Fine-Tuning (Steps $200+$)
- All network parameters are unfrozen.
- Differential learning rate schedule:
  - CNN Backbone: $\eta_{\text{backbone}} = 10^{-5}$ (conservative updates)
  - BiLSTM & Head: $\eta_{\text{head}} = 10^{-4}$
- Cosine annealing scheduler decays learning rates to $10^{-6}$.

---

## 3. Regularization & Stability Mechanisms

1. **Automatic Mixed Precision (AMP)**:
   - Utilizes `torch.amp.autocast('cuda')` and `GradScaler` for memory efficiency and ~2x throughput on Colab T4.
2. **Gradient Clipping**:
   - Norm clipped to max $5.0$ to prevent exploding gradients in recurrent LSTM timesteps.
3. **Blank Collapse Monitoring**:
   - Tracks empty prediction rate (`empty_rate`). If empty rate exceeds $15\%$, logs `[CTC_BLANK_COLLAPSE_WARNING]`.
4. **Grace Period Early Stopping**:
   - `min_steps_before_early_stop: 150`: Inhibits early stopping during initial exploration steps so the model has sufficient opportunity to converge.
5. **Data Augmentation**:
   - Light affine rotation ($\pm 3^\circ$), subtle contrast/brightness jitter ($0.1$), and occasional Gaussian blur. No heavy geometric warping that could sever diacritic dots.

---

## 4. Checkpoint Resumption & Drive Backup

### 4.1 Resuming from Interrupted Training
Colab sessions may disconnect after inactivity. Training state is fully checkpointed in `latest_checkpoint.pth`:
- Model state dict
- Optimizer state dict
- Scaler state dict
- Epoch & global step
- Best recorded validation CER

Resume command:
```bash
python training/train_finetune.py --resume artifacts/checkpoints/latest_checkpoint.pth
```

### 4.2 Automated Google Drive Backup
When running in Colab with Drive mounted, every improvement in `best_cer` automatically backs up to:
```
/content/drive/MyDrive/MathVisionKid_AI/checkpoints/run_YYYYMMDD_HHMMSS/
```
preserving checkpoints, manifests, and configs across disconnections.

---

## 5. Multi-Domain Evaluation Protocol

Evaluation (`scripts/evaluate.py`) computes fine-grained metrics broken down across:
- **TEXT_ONLY**: Handwritten essay lines, words ("Bài giải", "Thời gian xe chạy là:")
- **MATH_ONLY**: Pure formulas and operations ("55 x 3 = 165", "12 + 5 = 17")
- **MIXED**: Problem statements containing numbers, operations, and units ("Thời gian xe chạy là: 45 x 3 = 135 (phút)", "Đáp số: 165 km")

Target Subsets:
- **Digit Accuracy**: Strict recognition rate for characters $0 \dots 9$.
- **Operator Accuracy**: Accuracy on mathematical symbols ($+, -, \times, x, *, /, :, =, \div$).
- **Vietnamese Character Accuracy**: Preservation rate of accented vowels and diacritics.
