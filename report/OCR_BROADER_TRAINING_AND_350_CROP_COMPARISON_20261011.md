# OCR: broader reviewed data, frozen training, and 350-image crop comparison

Date: 2026-10-11. Owner request: continue recognizing lines, train further, improve quality and include other images.

Completed a bounded offline experiment: 49 additional visually reviewed references, one 30-epoch training recipe, frozen-checkpoint evaluation on two reserved pages, and two recognition passes across 350 image entries. The candidate improves aggregate character error but fails the prose regression gate. **Keep the production model unchanged.** The margin helper is an offline experiment, not a change to live detection.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded OCR script changes and a small crop-context experiment; no UI/design work.
  - Applied to: one native Python helper, existing training/recognition runners, narrow provenance correction, and meaningful geometry/regression tests. No new dependency or production abstraction.

Workspace skill registry inspected before editing. Exact Expo v57 documentation read before writing code; no Expo, Student Mobile, web UI, auth, or deployment code changed.

## Data and review

Six source pages were visually inspected in full and in individual crops. Their hashes were absent from 37 known prior reviewed manifests. This does not establish writer independence, alternate-capture independence, or absence from original base-model training.

| Source | Split | New reviewed references | Contents |
|---|---|---:|---|
| 901.jpeg | TRAIN | 8 | Pencil phrases: qua nhà, vỉa hè, đá quý, cổ vũ |
| 904.jpeg | TRAIN | 12 | Repeated phrases and four prose lines |
| 905.jpeg | TRAIN | 2 | Visible literal “ngụ”; not corrected to “ngủ” by context |
| 910.jpeg | TRAIN | 19 | Multiplication/division expressions |
| 907.jpeg | HOLDOUT | 2 | ngõ nhỏ; nghé ngủ |
| 926.jpeg | HOLDOUT | 6 | Two prose lines and four unboxed expressions |

49 accepted references = 41 new TRAIN + 8 fresh HOLDOUT. Uncertain diacritics, clipped strokes, neighboring-row ink, crossed-out/marked expressions and boxed two-dimensional work were excluded. Crop coordinates on the perspective-distorted table were corrected before fitting. No answer was supplied by solving an expression; labels transcribe visible ink.

The new manifest has **350 reviewed records: 294 TRAIN / 48 DEV / 8 HOLDOUT**. These 350 reviewed records are different from the 350 image entries used for inference below. The preceding phase's 12 already-scored HOLDOUT references are explicitly reclassified as exposed TRAIN only in the new manifest. Older manifests and models remain byte-identical. DEV retains the same 48 references as the preceding candidate comparison. Source/hash/pixel/crop split guards passed.

## Training and freeze

One predefined recipe, using the unchanged existing trainer: 30 epochs, batch 4, two CPU threads, learning rate 0.0001, seed 20261012, aspect-preserving input at height 64 and stride 8, width 64–1024. Adapt the last visual block, BiLSTM and CTC head; keep the first three visual blocks frozen. Warm the multiplication glyph from TRAIN, replay prose three times and anchor TRAIN prose against the original model with weight 2. There are 294 original TRAIN records, 101 prose anchor records and 496 sampled views per epoch. HOLDOUT is deferred during fitting.

Epoch **20** wins the predefined DEV ordering: scope regressions, critical edits, character error rate, exact lines. All 30 epochs completed. Checkpoint/vocabulary/manifest hashes were frozen before scoring HOLDOUT. The crop-margin policy was also frozen before that scoring. No later fitting, recipe change or selection used HOLDOUT results.

| Evaluation | Previous private candidate | This candidate | Meaning |
|---|---:|---:|---|
| Same 48 DEV records: CER | 28/702 = 3.99% | 24/702 = 3.42% | Selection/development result |
| Same DEV: exact lines | 34/48 | 34/48 | No aggregate exact-line gain |
| Same DEV: critical edits | 8 | 7 | Still has number/operator/punctuation errors |

Critical characters include digits, operators and punctuation/decimal separators; diacritic errors remain part of ordinary CER. CER counts character edits over reference characters. It is not application accuracy or a calibrated confidence estimate.

| Fresh manual-crop HOLDOUT | Production baseline | Frozen candidate |
|---|---:|---:|
| All 8 references, 106 characters: CER | 37/106 = 34.91% | 4/106 = 3.77% |
| Exact references | 2/8 | 5/8 |
| Four expressions: exact | 0/4 | 4/4 |
| Four prose references: exact | 2/4 | 1/4 |
| Critical edits | 11 | 0 |

**Gate fails: `HOLDOUT/prose: exact-line regression`.** For example, the baseline correctly reads “chia cho thương.” but the candidate writes “chia cho thưởng.” The candidate also writes “ngó nhó” for “ngõ nhỏ” and “nghé ngi” for “nghé ngủ”. Improvement in math must not conceal deterioration in a prose subgroup.

These are eight selected phrases/expressions on two pages, not full-page or general handwriting accuracy. The small, correlated notebook sample does not support a production-quality percentage. These references are now exposed evaluation data for future work.

## Additional images and line recognition

Freshly segmented the 84 earlier image entries, numbered 648–731, through the existing detector: 84 tested, 84 with regions, zero execution failures, no region-limit truncation. Original bytes were read through the existing storage mapping, including archived sources. Combined these with the recent 266 entries numbered 732–997.

The combined inference selection contains **350 entries / 322 distinct source hashes**, including 28 aliases. Each pass reads **9,269 regions**. Two passes use the same frozen candidate and input policy:

| Pass | Images completed | Regions | Nonempty transcripts | Execution failures |
|---|---:|---:|---:|---:|
| Original detector boxes | 350 | 9,269 | 7,873 | 0 |
| Bounded margin boxes | 350 | 9,269 | 7,918 | 0 |

Completion and nonempty output measure execution, not correctness. Every output remains `labels_verified=false`, `reference_label=false`, `training_eligible=false`, `score_is_accuracy=false`. The greedy CTC score is uncalibrated and uses a declared experimental score definition. No automatically predicted transcript is accepted as a training reference.

## Crop-context experiment

`scripts/data/line_crop_margin.py` adds bounded horizontal/vertical context, clamps to image bounds and row/column neighbor midpoints, and leaves tall, overlapping or unsafe diagonal regions unchanged. It preserves box count/order and never reads transcripts. **3,599 of 9,269 boxes expand.** This cannot split merged columns, invent absent detections, distinguish fractions from prose, or recover ink missing from the source.

Compare 48 of the new references using one-to-one greedy IoU matching with a fixed 0.5 threshold. Exclude the “nghé ngủ” partial-row phrase: scoring it against a complete detected sentence would create a misleading text error. Missing matches count as empty predictions, including their deleted characters. TRAIN and HOLDOUT are reported separately.

| Diagnostic subset | Original boxes | Margin boxes |
|---|---:|---:|
| Geometry matches over 48 selected references | 29/48 | 40/48 |
| 41 TRAIN references: CER | 158/368 = 42.93% | 80/368 = 21.74% |
| 41 TRAIN references: exact | 11/41 | 23/41 |
| 7 HOLDOUT references: CER | 21/98 = 21.43% | 2/98 = 2.04% |
| 7 HOLDOUT references: exact | 2/7 | 5/7 |
| 7 HOLDOUT references: critical edits | 8 | 1 |

Across this diagnostic there are 11 newly matched references, no lost matches, 15 gains to exact transcript and no losses from an exact transcript. Larger boxes can cross the IoU threshold; therefore these gains combine geometric matching and recognition, and are **not whole-page detector recall/precision**. Forty-one references were used in fitting. The seven HOLDOUT references are a small subset of the same two reserved pages, not a second independent test.

Visual comparison of six expanded crops on pages 904 and 910 confirms additional context around pencil text and arithmetic strokes in those examples. Remaining concrete failures: the margin output drops the final period in “chia cho thương.” and reads “ngó nhỏ” instead of “ngõ nhỏ”. No margin policy is chosen for production based on these HOLDOUT results.

## Code, verification and safeguards

- Added the standalone offline margin helper and six geometry cases covering neighbor separation, diagonal/overlapping blocks, image bounds, tall math regions and malformed inputs.
- Fixed the batch runner to preserve an explicitly declared experimental provider on failure as well as success; its production provider default is unchanged. Extended the existing failure/provenance test.
- **131 tests passed in 16.88 seconds** across margin geometry, fine-tuning guards, recognition batch provenance, storage and text detector regression tests. These tests do not establish OCR accuracy.
- Final verification re-read and SHA-checked all 350 source entries, validated reviewed splits and frozen selection, matched both passes to the candidate/vocabulary, checked finite scores and draft flags, recomputed all margin boxes and counts, and rechecked protected production/prior experiment hashes. Passed.
- `git diff --check` passed. Private images, reviewed labels, model weights and inference outputs remain ignored. No commit, push or deployment was performed in this phase.

Production checkpoint, vocabulary, runtime provider, detector and tutoring rows are unchanged. Student Mobile and web behavior are unchanged. This phase used zero cloud inference calls and registered no paid resources.

## Reproducible evidence

Private artifacts under `ai-training/datasets/drive_math/new2_20261011_266/training_broader/`:

- `reviewed_manifest.json`, `preflight.json`, `run_warm_anchor/evaluation.json`, `train.log`
- `frozen_selection.json`, `final_evaluation/evaluation.json`, `evaluate.log`
- `geometry_policy.json`, `inference_preflight.json`, `geometry_comparison.json`
- `combined350_raw/`, `combined350_margin/`, `recognition.log`, `margin_visual_review.jpg`
- `tests_final.log`, `verify_finish.py`, `decision.json`

Frozen SHA-256:

- Candidate: `18d1501b130262f74ceaa22de2d460bcf7eec095c34ae5663f97a43ef5cb0ff7`
- Vocabulary: `dc25d2de8fe00fb680b8a18c0abac8e4df0e4ec54aa71e5dcde1ec253814a9fd`
- Reviewed manifest: `aded92f15b583e3df2ebc53ff4ea3ce450459ab20a1f9446223c331dfe3ea375`
- Margin policy code: `8159a1aad350cd6b342d8ec0e070299aed7880d398a4f8933c4e27887a7f0b53`

## Decision and remaining work

Retain production. Further useful work needs more independently reviewed prose/diacritics, wider page/writer coverage, and row/column geometry checks for the remaining misses and merges. Future selection must use DEV and a newly reserved evaluation set rather than treating these now-exposed pages as fresh HOLDOUT. Fraction/vertical-layout understanding and general full-image accuracy were not established by this line-recognizer experiment.
