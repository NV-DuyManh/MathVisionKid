# AI/Data Team Feedback Package: Phase 4.3 Independent Gold Benchmark Requirements

**Project**: MathVision Kids  
**Target Recipient**: AI/ML Teammate (Nhóm 6 / Model & Data Engineering)  
**Author**: Antigravity (Engineering Pair Programmer)  
**Date**: 2026-09-08  
**Phase Gating Status**: **BLOCKED_DATASET**  

---

## 1. Context & Blocker Summary

During Phase 4.3, the software engineering stack verified that the YOLOv8n runtime model (`v1.0.0`, SHA-256 `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`) is successfully loaded and integrated, achieving:
- Local inference smoke timing: **0.0854 seconds** warm CPU inference (N=10 on single synthetic sample; formal Proposal p95 latency remains **NOT_EVALUATED** pending the full gold workload).
- Reliable E2E pipeline integration (FastAPI -> Celery -> Redis -> Spring Boot -> PostgreSQL).

However, **formal quality gate verification against the Project Proposal is currently BLOCKED** because no independent, held-out gold test dataset exists in the workspace.

Per `DATASET_CARD.md` Section 1.3:
> *"Test set: No separate held-out test set in this version"*
> *"Real collected (33 images): NOT included in this handoff"*

Per governance guidelines, engineering must not:
1. Re-use validation images used for checkpoint selection (to prevent leakage).
2. Fabricate synthetic benchmarks or human hint quality ratings.
3. Label or adjudicate datasets.

---

## 2. Proposal Target Metrics Requiring Gold Gating

The following metrics are defined in the Project Proposal and must be evaluated on the independent gold dataset:

| Target Metric | Proposal Requirement | Benchmark Status in Phase 4.3 |
|---|---|---|
| **Critical-Token Recognition** | >= 90% across digits (0-9) & operators (+, -, =) | **NOT_EVALUATED (Blocked)** |
| **First-Error Precision** | >= 85% on high-confidence subset | **NOT_EVALUATED (Blocked)** |
| **First-Error Recall & Coverage** | Explicitly reported | **NOT_EVALUATED (Blocked)** |
| **Over-Correction Rate** | <= 5% (valid work marked erroneous) | **NOT_EVALUATED (Blocked)** |
| **p95 AI Latency** | <= 12.0 seconds across full evaluation workload | **NOT_EVALUATED (Blocked)** |
| **Hint Quality** | >= 4.0 / 5.0 (human rating) | **REQUIRES_HUMAN_EVALUATION** |
| **Supervised Usability** | >= 80% capture-confirm-retry | **NOT_EVALUATED (Pilot required)** |

---

## 3. Required Gold Evaluation Package Specification

To unblock Phase 4.3 evaluation, the AI/Data team must deliver an independent gold package matching the following criteria:

### A. Dataset Quantity, Provenance & Composition
- **Quantity Target**:
  - **W5 Target**: >= 100 verified pilot images.
  - **W11 Target**: >= 500 de-identified gold images (target: 700 images, >= 20% double annotation).
- **Split Separation & Leakage Verification Requirements**:
  - File-name or file-path checks alone do **not** prove dataset independence.
  - To enable credible leakage verification and prove independence, the delivery must include one of the following provenance mechanisms:
    1. **Train/Validation Image SHA-256 Exclusion Manifest**: A cryptographically verifiable list containing SHA-256 hashes of all 1,809 training images and 192 validation images used for `yolov8n_mathvision_det_v1.pt`.
    2. **Original Split Manifest**: Containing stable image IDs and image hashes defining train, validation, and test partitions.
    3. **Equivalent Documented Provenance**: Credible documentation sufficient to verify that gold test images were never exposed during model training or checkpoint selection.
  - **Writer-Disjoint Metadata**: Include writer identifiers (e.g., anonymized `writer_id: "writer_042"`) where writer identity can be represented safely, ensuring no student handwriting styles from the training split appear in the test set.
  - **Leakage Reporting Rule**: Automated harnesses will report `NO_KNOWN_OVERLAP_DETECTED` based on available data, and will strictly refuse to declare `DATASET_INDEPENDENCE_VERIFIED` until one of the credible provenance mechanisms above is supplied.
- **Real vs. Synthetic Proportion**:
  - Must contain real handwritten student worksheets (preferably diverse primary school student handwriting).
- **Canonical Supported Scope (1–6 Digits)**:
  - **Do NOT restrict scope to only 2-digit arithmetic**.
  - Canonical MVP evaluation domain:
    - One vertical exercise per image.
    - Vertical addition (`+`) and vertical subtraction (`-`).
    - Two operands, natural numbers.
    - **1 to 6 digits per operand/result**.
    - Carry operations (addition with carry and without carry).
    - Borrow operations (subtraction with borrow and without borrow).
    - Both correct and incorrect student calculations (for first-error localization and over-correction gating).
  - **Digit-Length Distribution**: The dataset manifest must report digit-length stratification (e.g., counts for 1-digit, 2-digit, 3-digit, 4-digit, 5-digit, 6-digit subsets) to disclose domain coverage.

### B. Directory Structure
Deliver to `ai-training/` using the established schema:
```text
ai-training/
├── data/
│   ├── deidentified-local/
│   │   ├── gold_0001.jpg
│   │   └── ...
│   ├── manifests/
│   │   ├── gold_eval_manifest_v1.0.json
│   │   └── train_val_exclusion_manifest.json (or split_manifest.json)
│   └── splits/
│       └── test/
│           └── (image links / file manifests)
└── annotations/
    ├── primary/
    ├── secondary/
    └── adjudicated/
        └── gold_annotations_v1.0.json
```

### C. Annotation Schema & Token Benchmark Contract

The gold evaluation manifest (`gold_eval_manifest_v1.0.json`) must provide for each image:
1. `image_id`: Unique de-identified string (e.g., `gold_eval_001`).
2. `filepath`: Relative path to image.
3. `operation`: `VERTICAL_ADDITION` or `VERTICAL_SUBTRACTION`.
4. `is_supported`: Boolean (true for 1–6 digit vertical arithmetic).
5. `ground_truth_expression`:
   - `operand1`: String representation (e.g. `"45"`).
   - `operand2`: String representation (e.g. `"27"`).
   - `operator`: `"+"` or `"-"`.
   - `student_result`: String representation of student answer (e.g. `"72"`).
6. `is_mathematically_correct`: Boolean.
7. `earliest_error` (when applicable):
   - `has_error`: Boolean.
   - `column_index`: Column index (0-indexed from right: units=0, tens=1, hundreds=2, etc.).
   - `error_type`: `COMPUTATION_ERROR`, `CARRY_BORROW_ERROR`, or `PLACE_VALUE_ALIGNMENT_ERROR`.
8. `tokens` (**TOKEN_BENCHMARK_SUBSET Requirements**):
   - For the subset of images used to calculate **Critical-Token Recognition >= 90%**, token-level ground truth is strictly **MANDATORY** (it must NOT be left merely "where available").
   - This subset is designated as `TOKEN_BENCHMARK_SUBSET`.
   - Mandatory attributes per token:
     - `image_id`: De-identified image identifier.
     - `token_class`: Token class name / ID (0-13: '0'-'9', '+', '-', '=', 'c1').
     - `token_bbox`: Bounding box `[x_center, y_center, width, height]`.
     - `coordinate_convention`: Strictly normalized float coordinates `[0.0, 1.0]` relative to image width and height.
     - `annotation_provenance`: Origin, annotator ID, and review date.
   - **Other Gold Images (Expression / Error Level Only)**:
     - It is acceptable for some gold images intended only for expression/error-level evaluation (such as end-to-end first-error localization or over-correction rate) to lack detailed token bounding boxes.
     - However, the evaluation harness and reports will explicitly calculate and disclose:
       * `total_gold_images`
       * `token_annotated_images`
       * `token_benchmark_coverage_percentage`
     - Token recognition accuracy will **never** be calculated against images without verified token ground truth.
9. `annotation_provenance`: Source metadata (origin dataset / collection site, date).
10. `writer_metadata`: Anonymized writer identifier (e.g., `writer_042`) or school/cohort code where safely representable.
11. `double_annotated`: Boolean (to verify >= 20% double-annotation requirement).
12. **Adjudication Metadata** (for double-annotated / disputed samples):
    - `primary_annotation`: Annotator 1 reading.
    - `secondary_annotation`: Annotator 2 reading.
    - `adjudicated_result`: Reconciled reading.
    - `adjudicator_id`: Identifier/version of senior adjudicator.
    *(Do NOT fabricate fake adjudication records for samples that were never disputed).*

---

## 4. How Engineering Will Execute Once Delivered

Once the package is placed in `ai-training/`:
1. Engineering will execute the frozen evaluation harness:
   ```bash
   python evaluation/run_evaluation.py --manifest ai-training/data/manifests/gold_eval_manifest_v1.0.json
   ```
2. The harness will automatically compute:
   - Token detection & classification accuracy, precision, and recall.
   - Full-expression exact match rate.
   - First-error localization precision, recall, and coverage.
   - Over-correction rate.
   - Subgroup metrics (addition vs. subtraction, carry vs. borrow, 1–6 digit breakdown).
   - Formal p95 end-to-end AI latency across the gold workload.
3. Machine-readable outputs will be written to `report/evidence/phase_4_3/`.
4. Phase 4.3 closeout will be finalized.
