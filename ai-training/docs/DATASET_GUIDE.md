# MathVision Kids OCR Dataset Engineering Guide

**Version**: 1.0.0  
**Target Domain**: Elementary Vietnamese Handwriting & Math Line OCR  
**Storage Architecture**: Hybrid (Local Fixture / Google Drive Real Data)

---

## 1. Storage & Provenance Model

To prevent heavy repository bloats and avoid forcing users to download multi-gigabyte raw image archives to local development machines, the dataset architecture is split into two operating environments:

1. **Local Environment (FIXTURE MODE)**:
   - Contains only lightweight synthetic/curated samples (`data/fixtures/`, `artifacts/samples/`).
   - Used for verifying architecture loading, crop quality gates, manifest schemas, training loops, and smoke tests.
   - Status: `LOCAL_PIPELINE_READY`.
2. **Google Colab Environment (REAL DATA MODE)**:
   - Mounts Google Drive directly at `/content/drive/MyDrive/C1SE.01`.
   - Accesses full primary student handwriting datasets without downloading to Windows or committing raw image files to Git.
   - Status: Transitions from `WAITING_FOR_DRIVE_MOUNT` to `DISCOVERED` upon mounting.

---

## 2. Google Drive Dataset Discovery

The pipeline discovers images dynamically under `/content/drive/MyDrive/C1SE.01` across the following candidate paths:

- `C1SE.01/Chữ Viết Tay Về Toán/Lớp 4`: Grade 4 math exercises and solutions
- `C1SE.01/Chữ Viết Tay Về Toán/Lớp 5`: Grade 5 multi-step word problems (toán có lời văn)
- `C1SE.01/Chữ Viết Tay Về Toán/NEW/IMG`: Newly acquired worksheet scans
- `C1SE.01/Chữ Viết Tay Về Toán/Sưu tập Tùm Lum`: Miscellaneous handwriting samples
- `C1SE.01/Ảnh`: Raw mobile camera captures

The discovery script `scripts/discover_drive_dataset.py` gracefully handles any missing subdirectories and produces an inventory report at `artifacts/reports/drive_inventory.json`.

---

## 3. Line Segmentation & Quality Gate

Worksheets undergo line-level extraction using `scripts/segment_lines.py` according to parameters in `configs/crop.yaml`:

### 3.1 Preprocessing Pipeline
1. **Deskewing**: Hough transform / minAreaRect angle compensation (up to 15°).
2. **Otsu Binarization**: Inverted foreground extraction where ink strokes are foreground.
3. **Grid Line Subtraction**: Morphological horizontal/vertical kernel filters remove graph notebook rulings (vở ô ly) without severing pen strokes.
4. **Accent Preservation**: Adds safety vertical padding (`accent_padding_top: 8`, `accent_padding_bottom: 8`) so Vietnamese diacritics (sắc, huyền, hỏi, ngã, nặng, dấu mũ) and descenders are preserved inside the crop.

### 3.2 Quality Gate Acceptance Thresholds
Evaluated via `scripts/validate_crops.py`:
- Width: $\ge 40$ px
- Height: between $16$ and $250$ px
- Foreground Ink: $\ge 80$ px and ink ratio $\in [0.004, 0.70]$
- Blank line threshold: white ratio $< 0.995$
- Pure grid line rejection: flags and drops crops that contain only horizontal rulings

---

## 4. Transcription & Prelabeling: Qwen 3 VL Plus

Line crops are prelabeled using **Qwen 3 VL Plus** (`qwen-vl-plus` via DashScope API):

### 4.1 Strict Prompt Contract
Qwen is strictly configured as a verbatim transcriber, **NOT a solver**:
- Must preserve exact Vietnamese text with full diacritics.
- Must preserve math operations (+, -, ×, x, :, /, =), decimals (commas and periods), fractions, and units.
- Must NEVER calculate answers or correct spelling mistakes.
- Must NEVER output conversational chatter ("Đây là ảnh...", "Không thể đọc...").

### 4.2 Prelabel Validation Gate
`scripts/validate_prelabels.py` validates prelabels against:
- Empty strings $\to$ `REJECTED`
- Conversational / description phrases $\to$ `NEEDS_REVIEW`
- Excessive length or abnormal character repetitions $\to$ `NEEDS_REVIEW`
- Characters outside `configs/unified_vocab.json` $\to$ `NEEDS_REVIEW`
- Compliant transcriptions $\to$ `READY_FOR_REVIEW`

---

## 5. Human Review Workflow

The tool `tools/review_labels.py` provides an interactive terminal interface:
- `[A]ccept`: Confirms transcription as `VERIFIED`.
- `[E]dit & Accept`: Prompts for human correction and saves as `VERIFIED`.
- `[R]eject`: Marks low-quality/noise crops as `REJECTED`.
- `[S]kip`: Leaves as `NEEDS_REVIEW`.
- `--auto_accept`: Flag for automated headless execution in CI or Colab.

**Rule**: ONLY records with `status="VERIFIED"` are eligible for training.

---

## 6. Zero-Leakage Dataset Splitting

Dataset partitioning is executed by `scripts/split_dataset.py`:
1. **Grouping Key**: `source_image_id`. All line crops derived from the same parent worksheet remain strictly within the same split (Train, Val, or Test).
2. **Leakage Audit**: Verifies zero intersection between splits across source image IDs and image SHA256 hashes. If leakage $> 0$, the pipeline fails immediately.
3. **Outputs**:
   - `data/manifests/train.jsonl`
   - `data/manifests/val.jsonl`
   - `data/manifests/test.jsonl`
   - `artifacts/reports/split_report.json`
