# MathVision Kids — Handwriting OCR Benchmark Governance Policy

**Version:** `1.0.0-MODEL.V2-FINAL`  
**Scope:** Evaluation Dataset Classification, Integrity Governance, and Leakage Prevention  
**Date:** September 2026  
**Status:** ACTIVE GOVERNANCE POLICY  

---

## 1. Principles of Evaluation Integrity

To prevent data contamination, optimistic reporting, and false holdout claims, MathVision Kids enforces strict separation between **Engineering Regression Sets** and **Independent Holdouts**.

No model evaluation metric may be cited as evidence of real-world generalization unless the evaluation dataset fulfills the strict criteria of an `INDEPENDENT_HOLDOUT`.

---

## 2. Dataset Roles & Definitions

| Dataset Role | Primary Purpose | Allowable Operations | Prohibited Operations |
|---|---|---|---|
| **`TRAIN`** | Gradient parameter optimization | Gradient descent, loss calculation, backpropagation, data augmentation | Model selection, hyperparameter tuning, release gating |
| **`DEV` (Validation)** | Hyperparameter & checkpoint selection | Early stopping, learning rate scheduling, CTC blank threshold tuning, checkpoint selection (`best_cer.pth`) | Gradient updates, final generalization claims |
| **`REGRESSION_33`** | Engineering regression guarding | Non-regression checks, decoder comparison (greedy vs beam), arbitration unit tests, CI test gate | Checkpoint selection, generalization claims, claiming "unseen holdout" accuracy |
| **`INDEPENDENT_HOLDOUT_V2`** | Final release & generalization gating | Pre-release model acceptance gating, true unseen accuracy estimation | Gradient updates, augmentation tuning, prompt engineering, threshold tuning, iterative re-testing |

---

## 3. Reclassification of the 33-Line Benchmark (`REGRESSION_33`)

The authoritative 33-line benchmark documented in `report/HANDWRITING_OCR_LOCKED_BENCHMARK_MANIFEST.json` spans 6 fixtures (`OWNER_POEM_BLOCK_1`, `OWNER_POEM_BLOCK_1_VAR2`, `SYNTHETIC_POEM_BLOCK_2`, `SYNTHETIC_POEM_BLOCK_3`, `OWNER_POEM_8_LINES`, and `WIDE_NOTEBOOK_SAMPLE`).

### Formal Governance Classification:
- **Designation:** `REGRESSION_33` (Engineering Regression Benchmark).
- **Rationale:** These 33 lines have been exposed across multiple development iterations (PROD.2A through PROD.4B.2R5). Engineering decisions (such as line segmentation padding, prefix beam search margins, and phonotactic rules) have been inspected directly against these samples.
- **Holdout Eligibility:** **`eligibleForHoldoutClaims = false`**. Under rigorous ML governance, an asset exposed during development is an engineering test fixture, not a blind holdout.
- **Training Provenance:** **`seenDuringModelTraining = "UNKNOWN"`**. Because the raw 59,462 training images from the historical HuggingFace archive are missing from this machine, exact overlap between training splits and these lines cannot be cryptographically proven. Marking as `UNKNOWN` is the only truthful classification.

---

## 4. Requirements for `INDEPENDENT_HOLDOUT_V2`

To qualify as a genuine independent holdout for Model V2 acceptance, a candidate dataset must satisfy:

1. **Writer Disjointness:** Must contain handwriting samples from children/writers whose handwriting was never included in `TRAIN` or `DEV`.
2. **Page & Notebook Disjointness:** Must not share pages, physical notebooks, or scan sessions with training data.
3. **Synthetic Disjointness:** Must not contain synthetic variants, augmentations, or font-rendered permutations of training phrases.
4. **Phrastic Diversity:** Must not reuse the Owner poem ("Em yêu mùa hè...") or known training prompts. Must span diverse elementary Vietnamese vocabulary, punctuation, uppercase cursive initials, and diacritics.
5. **No Post-Inspection Retuning:** Once evaluated on `INDEPENDENT_HOLDOUT_V2`, the dataset is considered "burned" if any subsequent hyperparameter, threshold, or weight adjustment is performed. Any retrained model must be evaluated on a newly drawn holdout.

---

## 5. Governance Enforcement Rules

1. Any benchmark report claiming "Holdout Generalization" on `REGRESSION_33` is **rejected at code review**.
2. If `INDEPENDENT_HOLDOUT_V2` is not available on disk, model acceptance is automatically blocked with status:
   `INDEPENDENT_HOLDOUT_REQUIRED`.
3. Synthetic variants derived from a `TRAIN` sample remain `TRAIN` forever and must never be placed into `DEV` or `INDEPENDENT_HOLDOUT`.
