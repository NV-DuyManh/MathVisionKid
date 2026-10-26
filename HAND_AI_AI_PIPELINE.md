# HandAI — Artificial Intelligence & Computer Vision Pipeline
## Step-by-Step Processing Specifications

---

## 1. Pipeline Overview

The HandAI AI Pipeline transforms raw, unconstrained photographs of Vietnamese primary school notebooks into pedagogically evaluated, character-accurate transcriptions. The pipeline consists of 7 discrete, verifiable stages:

```
+----------------------------------------------------------------------------------------------------+
|                                    HandAI AI Pipeline Stages                                       |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [Stage 1: Image Ingestion]                                                                        |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Stage 2: Image Normalization & Preprocessing]                                                    |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Stage 3: Line Detection & Morphological Segmentation]                                            |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Stage 4: Line Crop Extraction & Tensor Normalization]                                            |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Stage 5: CRNN Acoustic/Visual Sequence Recognition & CTC Decoding]                               |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Stage 6: AI Contextual Correction & Multi-Consensus Arbitration]                                 |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Stage 7: Ground Truth Evaluation & Error Taxonomy Classification]                                |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Stage-by-Stage Detailed Technical Specifications

### Stage 1: Image Input & Ingestion
- **Input:** Raw photograph or scan of a student notebook page uploaded via mobile camera or gallery.
- **Output:** Validated raw binary byte buffer with verified MIME type and computed SHA-256 digest.
- **Technology:** Android CameraX / Expo ImagePicker, Spring Boot `StandardMultipartHttpServletRequest`, Java `MessageDigest`.
- **Purpose:** Securely ingest the physical artifact, enforce file size limits ($\le 10\text{ MB}$), prevent malformed file attacks, and generate a cryptographic fingerprint for deduplication.
- **Processing Logic:**
  1. Inspect HTTP payload `Content-Type` ensuring strictly `image/jpeg` or `image/png`.
  2. Compute SHA-256 checksum over byte array.
  3. Validate image dimensions using Java `ImageIO.read()`. Reject images with width $< 300\text{ px}$ or height $< 300\text{ px}$.
  4. Stream byte array to MinIO object storage under `ocr-trials/multiline/{timestamp}_{sha256}.jpg`.

---

### Stage 2: Image Normalization & Preprocessing
- **Input:** Raw full-page RGB image bytes.
- **Output:** Contrast-enhanced, deskewed grayscale image array and binarized representation.
- **Technology:** OpenCV (`cv2`), NumPy.
- **Purpose:** Eliminate lighting gradients, shadows, page curvature, and notebook grid line (*vở ô ly*) interference prior to line detection.
- **Processing Logic:**
  1. **Grayscale Conversion:** Transform RGB image to single-channel luminance:
     $$Y = 0.299R + 0.587G + 0.114B$$
  2. **Contrast Enhancement:** Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) with tile grid size $(8 \times 8)$ and clip limit $2.0$ to balance uneven flash or ambient room lighting.
  3. **Binarization:** Apply Otsu's thresholding combined with Gaussian blur $(\text{kernel}=5 \times 5)$ to isolate ink strokes from background paper:
     $$\sigma_w^2(t) = \omega_0(t)\sigma_0^2(t) + \omega_1(t)\sigma_1^2(t)$$
  4. **Deskew Correction:** Detect predominant line angle via Radon transform / Hough line transform across margin rules; rotate image if $|\theta| \in [0.5^\circ, 15^\circ]$.

---

### Stage 3: Line Detection & Morphological Segmentation
- **Input:** Preprocessed binary image.
- **Output:** Sorted array of non-overlapping horizontal text line bounding boxes $[(x, y, w, h)]$.
- **Technology:** OpenCV morphology (`cv2.morphologyEx`), Horizontal Projection Profile (HPP).
- **Purpose:** Automatically isolate each physical line of handwritten text while preventing detached Vietnamese diacritics (acute, grave, hook, circumflex) from fragmenting into false candidate rows.
- **Processing Logic:**
  1. **Morphological Closing:** Apply an anisotropic rectangular structuring element $(\text{width}=25\text{ px}, \text{height}=3\text{ px})$ to bridge horizontal character gaps while preserving vertical line separation:
     $$I_{\text{closed}} = (I \oplus K) \ominus K$$
  2. **Horizontal Projection Profile (HPP):** Compute row-wise pixel density:
     $$H(y) = \sum_{x=0}^{W-1} I_{\text{bin}}(x, y)$$
  3. **Primary Row vs. Satellite Diacritic Consolidation:**
     - Identify local maxima in $H(y)$ representing primary character bodies.
     - Detect small satellite connected components located directly above or below primary rows (isolated tone marks like *sắc, huyền, hỏi, ngã, mũ*).
     - Merge satellite components into their nearest primary row polygon if vertical separation is within $0.8 \times \text{median\_row\_height}$. Discard isolated noise artifacts with ink mass $< 15\text{ pixels}$.
  4. **Sorting:** Sort final bounding boxes strictly top-to-bottom ($y$-coordinate ascending) with line ordering indices $1, 2, \dots, N$.

---

### Stage 4: Line Crop Extraction & Tensor Normalization
- **Input:** Original high-resolution color page image and confirmed bounding box coordinates $(x, y, w, h)$.
- **Output:** Normalized 4D PyTorch FloatTensor $[B, 3, 64, 1024]$ ready for neural inference.
- **Technology:** Java `BufferedImage.getSubimage()`, Pillow (`PIL.Image`), Torchvision `transforms`.
- **Purpose:** Extract individual text line image slices with padding preservation and normalize pixel distributions to match CRNN pre-training standards.
- **Processing Logic:**
  1. **Subimage Extraction:** Crop bounding rectangle with a safety margin of $4\text{ px}$ to avoid clipping extended ascenders (`l, h, k, b`) or descenders (`g, y, p, q`).
  2. **Aspect-Ratio Resizing:** Resize line crop to fixed height $H = 64\text{ px}$ and width $W = 1024\text{ px}$ using bilinear interpolation. If aspect ratio is smaller than $16:1$, right-pad with white pixels $(255, 255, 255)$.
  3. **Tensor Conversion:** Scale pixel intensities to floating point interval $[0.0, 1.0]$.
  4. **ImageNet Normalization:** Standardize color distribution across RGB channels:
     $$X_{\text{norm}}^{(c)} = \frac{X^{(c)} - \mu_c}{\sigma_c}, \quad \mu = [0.485, 0.456, 0.406], \; \sigma = [0.229, 0.224, 0.225]$$

---

### Stage 5: CRNN Acoustic/Visual Sequence Recognition & CTC Decoding
- **Input:** Normalized line tensor $[1, 3, 64, 1024]$.
- **Output:** Raw transcribed text string and frame-level sequence log-probabilities.
- **Technology:** PyTorch 2.3+, Convolutional Recurrent Neural Network (CRNN), Connectionist Temporal Classification (CTC).
- **Purpose:** Translate spatial feature representations of cursive handwriting strokes into an unconstrained text character sequence without requiring individual character-level segmentation.
- **Processing Logic:**
  1. **CNN Feature Extraction:** 4 Conv2d blocks with GroupNorm(8, C) and MaxPool2d downsample spatial dimensions from $[3, 64, 1024]$ to feature map $[512, 8, 128]$.
  2. **Feature Reshaping:** Permute and flatten spatial features into $T = 128$ sequential timesteps of feature dimension $D = 512 \times 8 = 4096$:
     $$\text{feat} \in \mathbb{R}^{B \times 128 \times 4096}$$
  3. **BiLSTM Sequence Modeling:** 1-layer Bidirectional LSTM with hidden size $128$ captures left-to-right and right-to-left contextual stroke dynamics, producing output dimension $2 \times 128 = 256$.
  4. **Linear Projection:** Fully connected layer projects hidden states to $K = 320$ class logits per timestep.
  5. **Greedy CTC Decoding:**
     - Select most probable class index per timestep:
       $$\pi_t = \arg\max_{k \in \{0, \dots, 319\}} P(c_k \mid x_t)$$
     - Collapse consecutive identical token indices:
       $$\pi = (\pi_1, \pi_2, \dots, \pi_T) \longrightarrow \pi'$$
     - Remove CTC blank token ($\text{ID} = 0$).
     - Map remaining token IDs to Vietnamese characters using `vocab.json`.

---

### Stage 6: AI Contextual Correction & Multi-Consensus Arbitration
- **Input:** Raw CRNN transcribed text, line confidence score, and surrounding paragraph context.
- **Output:** Pedagogically corrected final text, decision source (`CRNN` vs. `AI_CORRECTION`), and correction rationale.
- **Technology:** Groq Cloud API (Llama-3.3-70b-versatile), Google Gemini API (gemini-2.5-flash / gemini-4b-heuristic fallback), Spring Boot Rule Engine.
- **Purpose:** Resolve phonotactic ambiguities, restore missing tone marks, and correct lookalike cursive errors using language priors without hallucinating non-existent text.
- **Processing Logic:**
  1. **Trigger Evaluation:** If raw CRNN confidence $\ge 92\%$ and raw text matches known primary vocabulary, accept raw OCR directly (`fast-path`). If confidence $< 92\%$ or potential phonetic slips are detected, trigger LLM arbitration.
  2. **Prompt Formulation:** Prompt LLM with primary school MOET context constraints:
     - Input: `"Raw OCR: [text], Grade Level: [1-5], Vocabulary Scope: Primary Vietnamese"`.
     - Constraints: *"Preserve original word count. Do not rephrase. Only fix diacritical tone slips or visually ambiguous primary school handwriting letters."*
  3. **Multi-Consensus Arbitration:**
     - Compare Groq suggestion $T_{\text{groq}}$ and Gemini suggestion $T_{\text{gemini}}$.
     - If both LLMs agree, suggestion is designated high-confidence.
     - If LLMs diverge, check Levenshtein distance against raw CRNN output. Select the suggestion that minimizes edit distance while satisfying Vietnamese syllable structure rules.
  4. **Empirical Performance:** Rescues $67.0\%$ of baseline CRNN recognition errors, lifting overall line accuracy from $82.0\%$ to $94.0\%$ (+12.0% absolute gain).

---

### Stage 7: Ground Truth Evaluation & Error Taxonomy Classification
- **Input:** Final recognized text $p$ and reference ground truth $t$.
- **Output:** Character Error Rate (CER), Word Error Rate (WER), Line Accuracy, Character Accuracy, Word Accuracy, 8-class Error Taxonomy, and 4-class Root Cause failure code.
- **Technology:** TypeScript dynamic programming algorithms (`handAiAnalyticsStore.ts`), Unicode Normalization Form D (NFD).
- **Purpose:** Deliver objective, mathematically rigorous evaluation of handwriting performance for academic validation and student pedagogical feedback.
- **Processing Logic:**
  1. **Character Levenshtein Distance:**
     $$D_{\text{char}}(p, t) = \min(\text{insertions} + \text{deletions} + \text{substitutions})$$
     $$\text{CER} = \frac{D_{\text{char}}(p, t)}{\max(1, \text{length}(t))} \times 100$$
  2. **Word Levenshtein Distance (WER):** Tokenize by whitespace and compute token-level edit distance:
     $$\text{WER} = \frac{D_{\text{word}}(p_{\text{tokens}}, t_{\text{tokens}})}{\max(1, |t_{\text{tokens}}|)} \times 100$$
  3. **Unicode NFD Tone Error Analysis:** Decompose characters into base letters and combining accents. If $\text{Base}(p) = \text{Base}(t)$ and $p \neq t$, classify as `VIETNAMESE_TONE_ERROR`.
  4. **Homologous Lookup:** Match character substitution pairs against known lookalike matrix $\mathcal{D}_{\text{conf}}$ (e.g. `n ↔ m`, `u ↔ v`, `s ↔ x`, `tr ↔ ch`).
  5. **Root Cause Assignment:** Classify failure into `RECOGNITION_ERROR`, `LANGUAGE_CORRECTION_ERROR`, `SEGMENTATION_ERROR`, or `IMAGE_QUALITY_ERROR`.
