# AI.HWTEXT.1 Dataset Curation Report

**STATUS: PARTIAL (Stopped at ANNOTATE gate)**

## 1. Source Characterization
The canonical archive `rename.zip` (SHA256: `88730e936013702ec9bf80d708488215a1d5feb41281be33fa157a42909c6f3a`) was extracted.
- Total source images: 173
- Unique images by hash: 173

## 2. Group / Leakage Control
Images were grouped by the `P_YYYYMMDD_HHMMSS` filename prefix to prevent data leakage between train/val/test splits. A total of 72 source groups were inferred. 

## 3. Image Quality Analysis
Images were analyzed for blur and brightness. Those with excessive blur (`cv2.Laplacian` variance < 50) were marked as `reject`.

## 4. Segmentation
Line segmentation produced **510 candidate lines** from the usable source images.
- Overlays with bounding boxes and line crops with padding were generated.

## 5. Classification
Lines were pre-labeled using the current production CRNN model. Heuristics based on text vs math content were used to classify each crop:
- **TEXT_WITH_CONTEXTUAL_NUMBERS:** 176
- **TEXT_ONLY:** 155
- **MATH_DOMINANT:** 146
- **REJECT:** 33

## 6. Stop Condition Triggered
The pipeline successfully reached the **ANNOTATE** gate. Since this task strictly enforces verified human labels before training and the system cannot visually verify the noisy pseudo-labels, execution was intentionally stopped.

**Output Generated:**
An `annotation_queue.tsv` containing 331 text lines (TEXT_ONLY + TEXT_WITH_CONTEXTUAL_NUMBERS) has been created. Math-dominant lines (146) were successfully quarantined.
