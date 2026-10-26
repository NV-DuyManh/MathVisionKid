# MathVision Kids Line OCR Model Version History

---

## Version 1.2.0 — MathVision Kids Vietnamese & Math Line OCR (Production Candidate)
- **Release Date**: 2026-09-21
- **Artifact Location**: `artifacts/export/ocr_vi_math_line_v1/`
- **Architecture**: CRNN (4-block Conv2d + GroupNorm + BiLSTM + Linear(326))
- **Vocabulary**: 326 tokens (`configs/unified_vocab.json`)
- **Key Enhancements**:
  - Full support for elementary math operators: $+$, $-$, $\times$ (U+00D7), $x$ (ASCII), $*$, $/$, $:$, $=$, $\div$ (U+00F7)
  - Decimal separators: `,`, `.`
  - Units: $m, cm, km, kg, g, giờ, phút, giây, \dots$
  - Exponents and specials: $\%$, $^\circ$, $^2$, $^3$
  - Multi-stage fine-tuning with backbone freezing and cosine annealing
- **Export Package**:
  - `best_cer.pth`
  - `model.py`
  - `vocab.json`
  - `predict.py`
  - `config.yaml`
  - `model_manifest.json`
  - `evaluation_report.json`

---

## Version 1.1.0 — Unified Vocabulary Checkpoint Adaptation
- **Release Date**: 2026-09-21
- **Artifact Location**: `artifacts/checkpoints/adapted_init.pth`
- **Vocabulary Expansion**: 320 $\to$ 326 tokens (appended $\pm, \times, \div, \text{Ẳ}, \text{Ẵ}, \text{Ỳ}$)
- **Preserved Weights**: 100% of CNN backbone and BiLSTM recurrent weights copied from baseline
- **Classifier**: Initialized 6 new class rows matching empirical weight variance ($\sigma = 0.2363$)

---

## Version 1.0.0 — Upstream Vietnamese Handwriting Base (Baseline A)
- **Release Date**: Pretrained Base
- **Artifact Location**: `handoff/staging/ocr_engine_handoff_final/ocr_engine/best_cer.pth`
- **Upstream Dataset**: `Viet-Handwriting-OCR-v2` (59,462 training lines, 500 validation lines)
- **Vocabulary**: 320 tokens (`handoff/staging/ocr_engine_handoff_final/ocr_engine/vocab.json`)
- **Validation CER**: 11.34%
- **SHA-256**: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`
- **Role**: Warm-start foundation for MathVision transfer learning
