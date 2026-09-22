# MathVision Kids — Vietnamese Handwriting OCR Model V2 Acceptance Gate Specification

**Document Version:** `1.0.0-PROD.4B.2R5`  
**Target Subsystem:** Vietnamese Handwriting OCR Engine (`services/ai-service`)  
**Target Recipient:** AI/ML Handwriting Model Engineering Team  
**Status:** ACTIVE GATE SPECIFICATION — MODEL UPGRADE REQUIRED (`AI_ML_HANDOFF_REQUIRED`)  
**Companion Documents:**
- Handoff Analysis: `report/AI_ML_HANDOFF_HANDWRITING_MODEL_GAPS.md`
- Locked Benchmark Manifest: `report/HANDWRITING_OCR_LOCKED_BENCHMARK_MANIFEST.json`
- Evidence Integrity Report: `report/ai_hwtext_prod_4b2r5_evidence_integrity_model_gate.md`

---

## 1. Objective & Gate Purpose

Phase `AI.HWTEXT.PROD.4B.2R5` conclusively determined that while the multi-line segmentation pipeline achieves $6/6$ canonical line detection (100% accuracy) and the prefix beam search CTC decoder cleanly resolves sequence candidate margins and token-level posterior distributions, **the production CRNN model weights (`best_cer.pth`) are an architectural acoustic/visual bottleneck**.

Under the current V1 model:
- Character Error Rate (CER): $\approx 5.99\%$ (or $3.75\%$ on padded baseline)
- Word Error Rate (WER): $\approx 15.15\% - 22.73\%$
- Exact Match Line Rate: $\approx 45.45\% - 54.55\%$
- Dominant failure modes: Cursive capital confusion ($E/S/T/C$), tone mark inversion/omission, and cursive ligature collapses ($r/l/h$).

**This gate specifies the non-negotiable architectural, cryptographic, tensor-contract, and metric requirements that any candidate Model V2 artifact must fulfill before it can be merged into production or released for physical mobile acceptance testing.**

---

## 2. Model V2 Artifact Delivery Structure

The Model V2 package must be delivered as a discrete, self-contained directory under:
```
models/ocr/crnn_vi_handwriting_v2/
├── best_cer.pth              # PyTorch model weights (state_dict)
├── vocab.json                # Character-to-index vocabulary dictionary
└── model_manifest.json       # Metadata, cryptographic hashes, and training provenance
```

### 2.1 File Path & Identity Contract
| Artifact | Relative Path | Format / Specification |
|---|---|---|
| **Model Weights** | `models/ocr/crnn_vi_handwriting_v2/best_cer.pth` | PyTorch serialized `state_dict` (torch.save). Must load cleanly with `weights_only=True`. |
| **Vocabulary** | `models/ocr/crnn_vi_handwriting_v2/vocab.json` | JSON mapping `{ "char": int_index }`. Index `0` must be reserved for CTC `<blank>`. |
| **Manifest** | `models/ocr/crnn_vi_handwriting_v2/model_manifest.json` | JSON manifest specifying architecture, hashes, training set stats, and validated metrics. |

---

## 3. Cryptographic Verification & Manifest Schema

Candidate artifacts must provide an authoritative `model_manifest.json` adhering to the following JSON schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "VietnameseHandwritingOcrModelManifest",
  "type": "object",
  "required": [
    "model_name",
    "version",
    "architecture",
    "checkpoint_sha256",
    "vocab_sha256",
    "tensor_contract",
    "target_metrics",
    "validated_metrics",
    "training_provenance"
  ],
  "properties": {
    "model_name": { "type": "string", "const": "Vietnamese-Handwriting-OCR-V2" },
    "version": { "type": "string", "pattern": "^2\\.[0-9]+\\.[0-9]+$" },
    "architecture": { "type": "string" },
    "checkpoint_sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "vocab_sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "tensor_contract": {
      "type": "object",
      "required": ["input_shape", "normalization", "output_shape", "blank_index"],
      "properties": {
        "input_shape": { "type": "array", "items": { "type": "integer" } },
        "normalization": { "type": "string" },
        "output_shape": { "type": "array", "items": { "type": "string" } },
        "blank_index": { "type": "integer", "const": 0 }
      }
    },
    "target_metrics": {
      "type": "object",
      "required": ["max_cer", "max_wer", "min_exact_match"],
      "properties": {
        "max_cer": { "type": "number", "maximum": 0.025 },
        "max_wer": { "type": "number", "maximum": 0.080 },
        "min_exact_match": { "type": "number", "minimum": 0.850 }
      }
    },
    "validated_metrics": {
      "type": "object",
      "required": ["locked_benchmark_cer", "locked_benchmark_wer", "locked_benchmark_exact_match"]
    },
    "training_provenance": {
      "type": "object",
      "required": ["training_dataset_version", "num_epochs", "optimizer", "date_trained"]
    }
  }
}
```

### Pre-Load Integrity Invariants:
1. `checkpoint_sha256` computed from `models/ocr/crnn_vi_handwriting_v2/best_cer.pth` must match manifest exactly.
2. `vocab_sha256` computed from `models/ocr/crnn_vi_handwriting_v2/vocab.json` must match manifest exactly.
3. If hashes do not match, `CrnnOcrProvider` must reject loading and raise `ValueError("MODEL_CORRUPTION_DETECTED")`.

---

## 4. Inference Tensor Contract

The runtime provider (`app.ocr.crnn_provider.CrnnOcrProvider`) enforces an immutable tensor input/output contract:

### 4.1 Input Tensor Contract
- **Shape:** `[B, 3, 64, 1024]` (Batch size $B \ge 1$, 3 color channels, height 64 px, width 1024 px).
- **Aspect Ratio Handling:** Line crop resized proportionally to height 64, padded on the right with white pixels (`255` before normalization) up to width 1024.
- **Normalization:** PyTorch standard ImageNet normalization:
  - $\mu = [0.485, 0.456, 0.406]$
  - $\sigma = [0.229, 0.224, 0.225]$
  - Input range: Normalized floating point tensor (`torch.float32`).

### 4.2 Output Logits Contract
- **Shape:** `[T, B, num_classes]` (or `[B, T, num_classes]` permutable with $T=256$ timesteps).
- **Vocab Alignment:** `num_classes = len(vocab)`.
- **CTC Blank Index:** Index `0` **strictly reserved** for CTC blank.
- **Emission:** Raw unnormalized logits or log-softmax probabilities suitable for standard PyTorch CTC Loss and Prefix Beam Search decoding.

---

## 5. Vocabulary & Phonotactic Requirements

The vocabulary file `vocab.json` must support complete standard Vietnamese orthography:
1. **Lower and Upper Case Latin:** `a-z`, `A-Z`.
2. **Vietnamese Extended Vowels with Diacritics:**
   - Acute ($sắc$): `á, ắ, ấ, é, ế, í, ó, ố, ớ, ú, ứ, ý` (and uppercase).
   - Grave ($huyền$): `à, ằ, ầ, è, ề, ì, ò, ồ, ờ, ù, ừ, ỳ` (and uppercase).
   - Hook above ($hỏi$): `ả, ẳ, ẩn, ẻ, ể, ỉ, ỏ, ổ, ở, ủ, ử, ỷ` (and uppercase).
   - Tilde ($ngã$): `ã, ẵ, ẫ, ẽ, ễ, ĩ, õ, ỗ, ỡ, ũ, ữ, ỹ` (and uppercase).
   - Dot below ($nặng$): `ạ, ặ, ậ, ẹ, ệ, ị, ọ, ộ, ợ, ụ, ự, ỵ` (and uppercase).
   - Horn/Breve modified bases: `ă, â, đ, ê, ô, ơ, ư` (and uppercase).
3. **Punctuation:** `.` `,` `!` `?` `:` `;` `-` `(` `)` `"` `'` `/`.
4. **Digits:** `0-9`.
5. **Whitespace:** Explicit space character `" "` mapped to an index $> 0$.
6. **Unicode Normalization:** All vocabulary entries must be NFC composed (`unicodedata.normalize('NFC', char)`).

---

## 6. Minimum Acceptance Criteria & Gating Thresholds

No candidate Model V2 checkpoint will be accepted for production release unless it satisfies the following thresholds evaluated against the locked 33-line benchmark (`report/HANDWRITING_OCR_LOCKED_BENCHMARK_MANIFEST.json`):

| Metric | V1 Baseline (Current) | Model V2 Target Threshold | Gating Policy |
|---|:---:|:---:|---|
| **Character Error Rate (CER)** | $5.99\%$ (padded: $3.75\%$) | **$\le 2.50\%$** | **HARD GATE**: Failure to achieve $\le 2.50\%$ blocks release. |
| **Word Error Rate (WER)** | $22.73\%$ (padded: $15.15\%$) | **$\le 8.00\%$** | **HARD GATE**: Failure to achieve $\le 8.00\%$ blocks release. |
| **Exact Match Line Rate** | $45.45\%$ (15/33 lines) | **$\ge 85.00\%$** ($\ge 28/33$ lines) | **HARD GATE**: At least 28 lines must match ground truth 100%. |
| **Capital Confusion ($E/S/T/C$)** | 7 instances | **$\le 1$ instance** | Capital flourishes must be discriminated reliably. |
| **Cursive Ligature Drops ($r/l/h$)** | 8 instances | **$\le 1$ instance** | Continuous strokes must not drop consonants. |
| **P95 Line Inference Latency** | $< 120\text{ ms}$ (CPU) | **$\le 150\text{ ms}$ (CPU)** | Must maintain real-time mobile/CPU performance. |

*Note: These are TARGET acceptance thresholds, not current results.*

---

## 7. Deterministic Benchmark Verification Command

To evaluate candidate Model V2 against this acceptance gate, execute the following command within the repository root:

```bash
# Set candidate model path and run locked benchmark evaluator
python services/ai-service/evaluation/eval_locked_benchmark.py \
  --manifest report/HANDWRITING_OCR_LOCKED_BENCHMARK_MANIFEST.json \
  --model-weights models/ocr/crnn_vi_handwriting_v2/best_cer.pth \
  --vocab models/ocr/crnn_vi_handwriting_v2/vocab.json \
  --output report/HANDWRITING_MODEL_V2_VERIFICATION_RESULTS.json
```

**Verification Gate Execution Rules:**
1. Evaluator must exit with code `0` if all target thresholds are met.
2. If any threshold fails, evaluator must exit with code `1` and output `GATE_REJECTED: <failure_reason>`.
3. The benchmark manifest must not be modified during verification.

---

## 8. Current Handoff Status

- **Model V2 Artifact Status:** `AI_ML_HANDOFF_REQUIRED` (No validated candidate weights currently submitted).
- **Interim Release Decision:**
  - `PhysicalPipelineSmokeTestVerdict: READY` (End-to-end image picking, segmentation, and arbitration pipeline is verified and stable).
  - `PhysicalOcrAcceptanceVerdict: WAIT_FOR_MODEL_V2` (Formal physical OCR acceptance requires V2 model meeting target metrics).
  - `ReleaseVerdict: NOT_READY_FOR_FINAL_OCR_ACCEPTANCE`.
