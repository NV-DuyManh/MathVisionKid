# Math OCR beam alternatives and component review — 2026-10-13

This phase completed a same-logit decoder comparison over **507 reviewed crops**, supplementary recognition over **273 automatically detected regions on nine math pages**, and source review/recognition of **37 new mathematical references**. Plain beam decoding improves aggregate DEV metrics slightly but regresses one role and can drop a repeated zero. It remains a review alternative; the installed model and default result were not changed.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the existing CTC beam decoder and bounded original-source reader rather than repeat a rejected fitting experiment.
  - Applied to: frozen decoding comparison, RAM-only reference checks, supplementary metadata and focused verification.

## Frozen decoder comparison

The previous 512-record manifest remains unchanged. Its **412 TRAIN and 95 DEV** records were evaluated; all five current HOLDOUT records and their source hashes were excluded before source reads. **68 original source pages** were read into RAM with full SHA verification, zero retries and no original-file persistence.

Greedy and beam consume identical logits from the unchanged private parent checkpoint/vocabulary `4903062b…` / `dc25d2de…`, on identical aspect-preserving crops. The existing decoder uses beam width 15, top-K five and selects the first candidate by sequence log probability. No vocabulary masking, language model, arithmetic solving or reference-based reranking was added.

Policy and input/model/code hashes were frozen before the first inference. A metadata comparison was corrected before launch to compare effective verified rotations rather than optional zero-degree metadata formatting; this did not depend on predictions. Acceptance retained the earlier limits: fewer than 30 critical errors, at most 107 character errors, at least 53 exact and 64 critical-exact lines, with no role regression on the same 95 DEV references.

| Same 95 DEV records | Greedy | Plain beam |
|---|---:|---:|
| Character errors / 1,097 characters | 107 | 105 |
| Character error rate | 9.75% | 9.57% |
| Critical digit/operator errors / 432 symbols | 30 | 29 |
| Exact transcripts | 53 | 54 |
| Critical-exact transcripts / 87 | 64 | 65 |

Aggregate metrics meet their limits, but comparison-expression character errors increase. **The frozen no-role-regression policy rejects beam as the default.** The observed gain is small development evidence, not independent accuracy or deployment readiness.

Examples of genuine tradeoffs:

- `65+8=73`: greedy emitted `65 +8 - 73`; beam emitted `65 +8 = 73`, correcting the equality sign while retaining different spacing.
- A reviewed denominator `7`: greedy was empty; beam emitted `7`.
- `300 cm² = 3 dm²`: greedy was correct; beam emitted `30 cm² = 3 dm²`, losing a zero.
- `16,7 > 16,07`: both decoders are wrong; beam adds another incorrect space.

These alternatives were not used to relabel the images. A valid arithmetic result was never substituted for what OCR saw. The beam approximates CTC sums because it prunes classes and prefixes; normalized scores and margins remain uncalibrated, not correctness percentages.

## Supplementary page recognition

All existing detected regions on nine source-matched, reviewed TRAIN math pages were processed: **453, 773, 926, 928, 960, 970, 962, 951 and 952.jpeg**, totaling **273 regions**. Regions include mathematical components and prose on those pages; this is not a count of 273 verified equations.

The plan freezes original SQLite payload/provenance fingerprints, source SHA, all rectangles and old text. Supplementary output preserves every original draft text/box and adds current greedy output plus up to five plain beam alternatives. Original databases, geometry, references and model files were not overwritten.

- **23** regions have different greedy/beam strings.
- **106** regions require review because of disagreement, empty greedy output, prior layout flag or prior width cap. These categories overlap.
- **18** greedy outputs are empty; one has a nonempty beam proposal (`n`), which is not verified mathematical recovery.
- Nine source reads completed with zero retries and no cloud calls.

Known TRAIN sources **956, 961 and 965.jpeg** had no matching selected-corpus record by exact ID/SHA in this plan. Their original bytes were read later for manual field recognition, but no matching automatic-region supplement is claimed. This phase did not generate new geometry or establish that the old geometry is correct.

The existing full selected-corpus reconciliation still accounts for **1,580 recognized pages, 2,975 ZIP crops and 2,295 screened Parquet candidates**, with one reserved page and zero pending/execution-failed sources. Its **42,679 drafts** remain unverified. Supplements are kept separate, not added to that count as new corpus coverage. The complete metadata inventory is larger than this selected scope; no all-source/all-mathematics accuracy claim is made.

## New literal references

The new pool contains **35 numeric fields and two horizontal expressions**:

| Existing TRAIN page | New reviewed references |
|---|---:|
| 962.jpeg | 11 |
| 951.jpeg | 4 |
| 970.jpeg | 2 |
| 952.jpeg | 4 |
| 956.jpeg | 13 |
| 961.jpeg | 1 |
| 965.jpeg | 2 |
| **Total** | **37** |

Complete source pages and every exact final crop were visually inspected in RAM before new field predictions. Literal writing was preserved without correcting calculations. Ambiguous `3/8` shapes, overwritten cells, neighbouring ink and full slanted rows that could not be cropped cleanly were withheld. Two-dimensional calculations were represented only by clear individual fields, never flattened into a made-up text-line equation.

Source bytes, recorded orientation, decoded dimensions and raw-RGB source/crop fingerprints were verified. Rectangles overlap neither the current 512-record manifest nor any of the prior 31 reviewed pool references nor another new rectangle from the same source. Source groups remain existing TRAIN groups; writer/pretraining independence remains unknown.

One `85` crop had a tight left margin. A separate source-reviewed refinement expanded its left margin and tightened its top to exclude detached borrowing ink: `[379,925,469,995]` → `[368,932,469,995]`. The literal label stayed `85`, the new crop was inspected again, and the original agent reference file remains unchanged. Parent approval records the separate refinement and exact new pixel hash.

All 37 references remain in the separate reviewed pool with `training_eligible: false`. A later detached-glyph audit corrected one literal label in a separate revision, as described below. No fitting, cohort replacement or production installation occurred in this phase.

## Recognition of the new fields

The 37 approved crops were recognized from **seven hash-verified Drive originals**, using the same unchanged private parent and both decoders. They were not fitted in this phase. These existing TRAIN source pages may have earlier model exposure, so the results are not an independent test set.

| Initial frozen references, 37 fields/expressions | Greedy | Beam |
|---|---:|---:|
| Character errors / 90 reference characters | 7 | 8 |
| Exact literal transcripts | 30/37 | 30/37 |
| Critical digit/operator errors / 82 reference symbols | 1 | 1 |
| Critical-exact transcripts | 36/37 | 36/37 |

The initial critical mismatch was reference `60 : 6 = 10` versus both predictions `60 : 6 = 16`. That disagreement triggered a separate source-quality audit. An independent observer inspected only the detached final glyph in RAM, without reference labels, predictions, neighbouring equation or arithmetic context. The observer read **6** from an open upper hook, continuous left descent and closed lower bowl. Parent review of a wider detached crop confirmed the same glyph.

The source therefore literally reads **`60 : 6 = 16`**. The earlier reference `10` was a transcription mistake. It was corrected in **a separate reference revision**, preserving the student's incorrect arithmetic rather than replacing it with the calculated answer. The original agent references, approval, predictions and frozen 37-field metrics remain unchanged as historical evidence. The revision explicitly records that the audit happened after seeing a prediction/reference mismatch, and that the label value comes from detached visual evidence rather than model or arithmetic output.

Retrospective comparison of those same saved predictions against the corrected source labels gives **zero critical errors, 37 critical-exact fields and 31 exact transcripts**. Greedy retains six character errors and beam seven, mainly internal spaces such as `326` → `32 6`. No new inference, training or weight change produced this result. It is **a reference correction, not a model improvement or independent accuracy estimate**. Critical metrics ignore spaces; exact-transcript metrics retain the formatting discrepancies.

## Validation and outcome

- Existing probability-integrity tests passed: three checks cover exhaustive CTC paths with repeated digits, tiny nonzero blank paths and long-sequence underflow.
- An independent read-only audit reproduced all 507 comparison metrics/scopes, verified same-logit selection and policy/code/model pins, and confirmed beam's rejection.
- Supplement audit matched all nine original SQLite records/provenance hashes and verified preservation of all 273 texts/boxes and the reported counts.
- New-reference metadata checks confirm current TRAIN source/split identity, unique IDs, valid bounds, raw-RGB fingerprints and zero overlap. Final source and crop reads verify the approved refinement.
- The final independent detached-glyph audit and parent wider crop verified the literal `6` correction. Its separate revision retains all 37 IDs, source identities, boxes, crops and splits, with only the one label/provenance change. The diagnostic queue from the initial references remains historical; six spacing discrepancies remain after the correction.
- The final field audit recomputed all 37 literal metrics/scopes and verified seven TRAIN-only source hashes and the approved crop fingerprints. It caught later audit notes appended to the refinement receipt after approval. Those notes are now preserved separately, and the original frozen receipt was restored byte-for-byte against its recorded SHA (including Windows CRLF). Approved text, rectangle/pixels and the existing field evaluation were unchanged. `refinement_metadata_reconciliation.json` records the exact restoration and both receipt hashes.
- All recognition scores remain marked as uncalibrated; predictions never become reference labels. Original photos/crops/ZIP/Parquet files remain on Drive. No current HOLDOUT source was read in these jobs.
- Installed checkpoint/vocabulary stay `a807eaa7…` / `6af4062e…`. No student UI/runtime behavior, deployment, Git commit or push was changed.

Next improvements must address actual segmentation and difficult glyphs with broader source-reviewed data and independent evaluation. The beam tradeoff does not justify another automatic default or extending the same rejected training loops. Manual crops do not demonstrate automatic page or 2-D recognition.

## Evidence

Private root: `ai-training/datasets/drive_math/math_all_20261013/math_decode_review_20261013/`.

- `decode_policy.json`, `prepare_decode.py`, `evaluate_decode.py`, `decode_evaluation.json`, `decode_read_receipt.json`: frozen same-logit comparison and complete receipts.
- `supplement_plan.json`, `supplement_policy.json`, `supplement_predictions.json`: preserved original drafts and review-only alternatives for nine pages.
- `labels_a/references.json`, `labels_b/references.json`, `labels_b/parent_crop_refinement.json`, `parent_fields_review.json`: 37 literal references and approved separate crop refinement.
- `evaluate_fields.py`, `field_evaluation.json`: complete field predictions, source/crop hashes and literal metrics.
- `literal_digit_reference_correction.json`, `corrected_field_references.json`, `corrected_reference_comparison.json`: independent detached-glyph audit, preserved original reference history and retrospective comparison without new inference.
- `field_error_review_queue.json`, `corrected_field_error_queue.json`: preserved initial diagnostic queue and six remaining spacing items after the literal reference correction; not automatic repairs or general confidence signals.
- `../recognition_progress.json`: selected-corpus reconciliation, separate from this supplement.

New reference SHA256 values:

- Pool A: `1b6f136952785161199dc69f44407fe9485ddc65015fdb2f3342208f0f12e120`.
- Pool B: `d4013e0ebb798ae5630b454bccf3d96cbe81bdce7fef20cf429e9bb1193f5c78`.
- Frozen approved refinement: `2b76655eb13ad69ba2ac4e4e5a41531b1718986e77992a7e3c70694ec24f7a73`.
- Additional review notes, kept separately: `d7427cf2d4b6148646bbf9df2ab15a931f8575638a2c27896f58a05cf1bc4dc9`.
