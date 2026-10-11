# OCR mixed-data adaptation and frozen validation — 2026-10-11

The experimental model improves recognition on newly reviewed pages and preserves the selected DEV prose checks. It still confuses mathematical operators and some prose characters, so **production remains unchanged**. This phase finishes the comparison and frozen validation; it does not establish that OCR is complete.

## Reviewed data and exposure

Visually inspected original images and crop sheets before accepting labels. Accepted 37 new line records and excluded 20 drafts containing neighboring writing, clipped symbols, teacher corrections or ambiguous pencil spelling. Final frozen cohort: **204 TRAIN / 48 DEV / 16 HOLDOUT**, 268 references, covering 23 / 4 / 2 distinct source hashes. TRAIN includes 55 prose and 62 expression records; the rest are previously reviewed text/numeric fields. New HOLDOUT contains 11 expressions and 5 prose records, from two different physical pages. Writer independence remains unknown; books, handwriting styles and arithmetic exercises can be correlated.

The 41 previously evaluated HOLDOUT records are explicitly reclassified TRAIN in this new manifest, with their former split and exposure recorded. All prior manifests/evaluations remain immutable. Newly scored source hashes are absent from previous reviewed cohorts. The batch already had unverified detector/production OCR drafts from earlier work; these new references had no prior labelled score and were excluded from fitting/selection, but the pages are not described as never processed before. Alternate captures of the same physical pages are excluded. Repetition of TRAIN prose is sampling, not extra independent data.

The draft limitation text retained a planned third HOLDOUT page, whose four ambiguous rows were subsequently excluded before fitting. `metadata_corrections.json` records the actual two-page count without changing the frozen manifest or paired model hashes. An additional final crop check excluded a partial exercise marker before HOLDOUT inference; two incomplete runs were stopped and emitted no model. Completed experiments use the corrected frozen cohort.

## Implementation and controlled experiments

Reused the existing bounded trainer and role-specific DEV selection. Added two opt-in experimental features; defaults retain earlier behavior:

- `--warm-multiplication`: initialize a TRAIN-introduced `×` class from the existing `x` head row. Split its exponential mass equally by subtracting log(2) from both biases. This preserves the combined x/× softmax mass at initialization and leaves the original head untouched. Other new classes retain the cold initialization. No held-out transcript defines a class.
- `--prose-anchor-weight`: finite weight 0–2, default 0. Before fitting, capture the original head's detached softmax distributions for **reviewed TRAIN prose only**, with the same aspect/time alignment. Add a KL term to CTC loss for those rows, padding new-class teacher probabilities with zeros. Predictions are regularization targets, never reference labels. DEV/HOLDOUT never supply teacher targets; numeric-only experiments reject this prose option.

Three completed 30-epoch runs start from the unchanged production checkpoint. Shared settings: CPU, two threads, batch 4, seed 20261011, lr 0.0001, final CNN block + BiLSTM + head, aspect resize, no contrast augmentation, TRAIN prose replay 3. Each epoch samples 314 TRAIN views from 204 originals; replay does not alter evaluation counts. The final CNN block changes; earlier three CNN blocks remain frozen. The third recipe was added adaptively after early DEV results showed prose regression, **before any new HOLDOUT scoring**. It is a DEV development comparison, not a pre-registered independent accuracy trial.

| Recipe | Selected epoch | DEV CER | Exact DEV lines | Critical edits | DEV role regressions |
|---|---:|---:|---:|---:|---:|
| Cold glyph initialization | 4 | 9.69% | 9/48 | 39 | 0 |
| Warm multiplication | 17 | 4.56% | 29/48 | 9 | 1: exact prose |
| Warm multiplication + prose KL, weight 2 | 29 | 4.27% | 32/48 | 9 | 0 |

Selected solely by DEV role regressions, critical edits, literal CER and exact lines. In the winner, prose CER improves from 4.57% to 3.96%, exact prose from 3/10 to 5/10, and prose critical edits remain 1. The unadapted aspect teacher was also checked on reused DEV prose for diagnosis, not on HOLDOUT. TRAIN performance and reused DEV scores are not estimates of general OCR accuracy.

## Frozen new-source evaluation

Saved the selected checkpoint/vocabulary hashes before scoring one candidate. No other recipe was scored on new HOLDOUT; no fitting or checkpoint selection follows these results. NFC and repeated-whitespace normalization only; do not solve equations, silently fix digits, or strip troublesome prose/numerals.

| Measurement: manual reviewed crops | Production baseline | Frozen candidate |
|---|---:|---:|
| HOLDOUT CER, 16 lines / 183 characters | 44.26% | 7.65% |
| Exact lines | 1/16 | 10/16 |
| Critical edits: digits/operators/selected punctuation | 31 | 6 |
| Expression CER, 11 lines | 56.76% | 6.31% |
| Exact expressions | 0/11 | 9/11 |
| Prose CER, 5 lines | 25.00% | 9.72% |
| Exact prose | 1/5 | 1/5 |

No role regresses on this small HOLDOUT. Nevertheless, the release gate fails: **CER exceeds 5% and six critical edits remain**, including mathematical operator/numeral errors. Two pages and five prose samples cannot establish generalization or a reliable accuracy percentage. We retain the improved candidate privately, rather than install it.

## Detector-to-recognizer diagnostic

Used the same frozen candidate on previously cached production detector boxes, after validating original image bytes and exact detector code hashes. Match selected annotations one-to-one in descending IoU at threshold 0.5; a missing match emits empty text and counts as deletion. All **16 selected reference lines** matched. This does not measure detector precision or complete page recall because the pages are only partially annotated.

On these detected crops, baseline CER is 50.27%, candidate CER **9.29%**; exact lines 0/16 → 7/16, critical edits 47 → 4. Some detected rectangles include exercise-marker ink or neighboring marks, and some lose punctuation. A match above the geometric threshold is not proof of a clean OCR crop. Manual-crop and detected-crop measurements share the same 16 references and are not additional independent evidence. This diagnostic covers detector/recognizer components; it is not a claim of browser, phone, API, camera or student-flow validation.

## Verification and outcome

**42 tests passed** across the existing trainer, batch-recognition and source-storage suites. New tests check x/× probability-mass preservation and immutable original head, unchanged cold initialization, rejection of invalid anchor weights, and an actual backward pass with TRAIN-only prose teacher targets and deferred HOLDOUT pixels. Existing checks enforce reviewed eligibility, source/pixel split separation, literal wrong-arithmetic preservation, role-aware selection and frozen checkpoint/vocabulary/manifest pairing. Synthetic tests verify behavior, not recognition quality. Focused Git whitespace checks pass.

Verified all 266 original file SHA-256 hashes and protected production checkpoint, vocabulary, provider and earlier expanded evidence. Recomputed selected epochs and recipe ordering from saved DEV history; checked trainer/manifest snapshots and paired candidate hashes. Private images, transcripts, drafts and weights remain Git-ignored. Unrelated cloud/deployment changes are preserved. No production install, UI change, paid resource, cloud deployment, physical-device evidence, commit or push occurred.

Private evidence: `ai-training/datasets/drive_math/new2_20261011_266/training_mixed/` (preflight, reviewed decisions, immutable paired runs, frozen selection, final evaluation, detected-region evaluation, error review and final decision). Selected checkpoint SHA-256: `c903700319799628c62d322045382b464dc0df83a052e1f04c045635848b40f4`. Its aspect preprocessing differs from production; copying the weights alone would be invalid even after passing a release gate.

Remaining work is explicit: resolve multiplication/division/numeral confusion, preserve text/punctuation under detector crops, and validate on a larger newly reviewed cohort with documented writers and full-page geometry. These are remaining OCR limitations, not completed work.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: add targeted OCR adaptation controls while reusing existing data, training and validation machinery.
  - Applied to: small head initialization, bounded TRAIN-only prose regularization, existing role gates, focused tests and private component diagnostics; no new dependencies.
