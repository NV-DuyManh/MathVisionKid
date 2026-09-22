# DATASET CARD — MathVision Kids

**Version**: 1.0.0  
**Date**: 2026-09-08  
**Prepared by**: Nhóm 6  

---

## 1. Detection Dataset (`combined_dataset_fixed_v1.0`)

### Overview
Combined dataset for training YOLOv8n to detect handwritten math tokens (digits, operators, carry markers) in children's math worksheets.

### Dataset Size
| Split | Images | Annotations |
|-------|--------|-------------|
| Train | 1,809 | 13,016 |
| Val | 192 | 1,496 |
| **Total** | **2,001** | **14,512** |

### Source Distribution
| Source | Images | Description |
|--------|--------|-------------|
| HME-VAS | 301 | Academic handwritten math expression dataset |
| Synthetic (batch 1) | 1,200 | Programmatically generated vertical math problems |
| Synthetic (batch 2) | 500 | Additional synthetic with varied layouts |

**Synthetic-to-real ratio**: ~85% synthetic, ~15% real (HME-VAS)

### Class Distribution (Train + Val)
| Class | Count | % of total |
|-------|-------|-----------|
| 1 | 1,508 | 10.4% |
| 4 | 1,191 | 8.2% |
| 2 | 1,184 | 8.2% |
| 7 | 1,154 | 8.0% |
| 8 | 1,112 | 7.7% |
| 3 | 1,108 | 7.6% |
| 9 | 1,096 | 7.5% |
| 5 | 1,061 | 7.3% |
| 6 | 1,057 | 7.3% |
| - | 1,057 | 7.3% |
| + | 969 | 6.7% |
| c1 | 949 | 6.5% |
| 0 | 598 | 4.1% |
| = | 468 | 3.2% |

**Imbalance note**: Digit `1` (1,508) to `=` (468) ratio is 3.2:1. Class `0` and `=` are underrepresented.

### Train/Val/Test Split
- **Split method**: File-based split in `data.yaml`
- **Train/Val overlap**: **0** (confirmed by audit — no shared filenames)
- **Test set**: No separate held-out test set in this version
- **Seed**: 42 (deterministic)

### Writer/Student Separation
- **Writer-disjoint**: ⚠️ **NOT APPLICABLE** for synthetic data (no real writer identity)
- **HME-VAS subset**: Original HME-VAS has its own split protocol; our split does NOT guarantee writer-disjoint across HME-VAS images
- **Real collected images** (33 images, `external/real_collected/`): Used only for annotation review and NOT included in train/val

### Annotation Procedure
1. **Synthetic data**: Auto-generated YOLO annotations from the synthetic generator (bbox coordinates are deterministic from layout engine)
2. **HME-VAS data**: Pre-annotated in source dataset, converted to YOLO format
3. **Real collected data**: Pre-annotated by YOLO model (`pre_annotate_c1.py`), then manually reviewed via custom annotation tool (`tools/annotate.html` + `tools/annotate_server.py`)

### Double Annotation Statistics
- **Synthetic**: N/A (auto-generated, no double annotation)
- **HME-VAS**: N/A (single source annotation)
- **Real collected (33 images)**: Single annotator + AI pre-annotation review. No formal double annotation or inter-annotator agreement computed.

### Known Annotation Issues
- **196 bbox coordinates slightly out of [0,1] range**: All from synthetic sources (`syn_*` and `syn2_syn_*`), caused by slight clipping artifacts in the layout engine. These are minor (typically ±0.06 from boundary).
- **`c1` class semantics**: In some images, `c1` marks carry digits; in others, it marks ruled paper lines. Inconsistent usage.

### De-identification Status
- **Synthetic data**: No PII — fully generated
- **HME-VAS**: Public academic dataset, no PII
- **Real collected (33 images)**: ⚠️ **NOT included in this handoff**. These images are stored locally only at `D:\nhom6\train thử\external\real_collected\` and must NOT be committed to Git without de-identification review.

### Limitations
1. **No held-out test set**: Only train/val split available. Production evaluation requires a separate test set.
2. **Synthetic-heavy**: Model may overfit to synthetic rendering style and underperform on diverse real handwriting.
3. **Single task**: Only vertical addition/subtraction. No multiplication, division, or horizontal layouts.
4. **Vietnamese-specific**: HME-VAS contains Vietnamese context (e.g., "Bài giải", "Đáp số") but digit/operator detection is language-agnostic.
5. **No diversity metadata**: No demographics, age, or handedness information for HME-VAS writers.

---

## 2. OCR Dataset (`Viet-Handwriting-OCR-v2`)

### Overview
Vietnamese handwriting OCR dataset used for training the CRNN text recognition model.

### Dataset Size
| Metric | Value |
|--------|-------|
| Total samples | 2,000 |
| Train | 1,800 |
| Val | 200 |
| Vocab size | 237 characters |

### Text Length Statistics
| Metric | Value |
|--------|-------|
| Min | 7 characters |
| Max | 116 characters |
| Mean | 45.0 characters |
| Median | 44 characters |

### Annotation Format
- JSONL: one JSON object per line with `{"image": "path/to/img.png", "text": "ground truth text"}`

### Train/Val/Test Split
- **Method**: Random 90/10 split from 2,000 samples
- **Seed**: 42
- **Test set**: No separate test set

### Writer/Student Separation
- **Writer-disjoint**: ⚠️ **Unknown** — the Viet-Handwriting-OCR-v2 dataset documentation does not specify writer identity separation.

### Annotation Procedure
- Source dataset provides text transcriptions
- No modification to annotations during our pipeline

### Double Annotation Statistics
- Inherited from source dataset
- No additional annotation review performed by our team

### De-identification Status
- Source dataset assumed de-identified (public distribution)
- No PII audit performed by our team

### Limitations
1. **General Vietnamese handwriting, not math-specific**: Dataset contains general text, not specifically children's math worksheets
2. **Vocab subset**: Vocabulary built from first 1,000 samples — may miss rare characters
3. **Timestep constraint**: 82.3% of samples (1,646/2,000) have text longer than 32 characters, causing CTC alignment challenges with the model's 128-timestep output
4. **No age/grade metadata**: Unknown if writers include children

---

## 3. Annotation Schema Versions

| Schema | Version | Format | Used By |
|--------|---------|--------|---------|
| Detection annotations | `yolo-v1.0` | `class_id x_center y_center width height` (normalized [0,1]) | YOLOv8n detection model |
| OCR annotations | `jsonl-v1.0` | `{"image": "...", "text": "..."}` per line | CRNN OCR model |
| Label map (detection) | `mathvision_det_v1.0` | 14 classes: 0-9, +, -, =, c1 | YOLOv8n + Parser Engine |
| Vocab (OCR) | `ocr_vocab_v1.0` | 237 characters | CRNN OCR model |
