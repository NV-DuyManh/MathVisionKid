# OCR queue follow-up and local candidate — 2026-10-08

The frozen page queue now has **202 saved reads out of 1,319**, with **1,117
pending** after another provider rate-limit stop. This phase added 63 reads,
preserved the preceding 139 outputs byte for byte, reviewed real source crops,
and trained a bounded local CRNN candidate. The candidate failed the quality
gate and **was not installed**. Recognition is not complete or perfect.

The owner has deferred physical-device testing and will test later. No phone
evidence is claimed. No commit or push was performed in this phase.

## Page queue and labels

The new frozen batch `all_current_20261007/cloud_remaining1180_20261008` excludes
the 139 historical reads. Its three resumptions saved 15, then 24, then 24 new
reads: 63 total. Sources were read through the Drive-backed reader with actual
image-byte hashes; historical output hashes were rechecked after each run.

| Saved predictions in this new batch | Count |
| --- | ---: |
| PROBLEM | 3 |
| WORK | 28 |
| MIXED | 5 |
| MULTIPLE | 20 |
| UNREADABLE | 7 |
| Total saved | 63 |

“Saved read” means an actual provider result was persisted, including unreadable
classifications. It does not mean a verified transcript. Predictions were not
automatically promoted to labels. This is the frozen 07/10 corpus, not a fresh
census of every file subsequently added to Drive.

`drive_line_batch.py` now respects a saved provider backoff across process
restarts and `--force`. The CLI exits with code 2 when pages remain pending.
This prevents an unavailable audit from appearing complete. The batch retains
the stopped source, error class and retry deadline, without credential values.

## Source review and the difficult crops

- The 13 unresolved writing crops and seven clipped fragments were reread and
  checked against their original hashes; their images were visually inspected.
- Five clearly readable **scoped** transcripts were recorded separately.
  Neighbouring cut-off rows, rectangle completeness and full-image coverage
  remain unverified. All five stay `training_eligible=false`; the detector still
  misses these sources. A manual transcript is not a detector recovery.
- Actual matching parent photos were found for clipped indices 49, 50 and 136.
  Their larger context helps review, but the affected rows are already cut off
  at the original photo boundary. No missing stroke was reconstructed and no
  full training crop was approved. The other four fragments still lack a
  confirmed larger original.
- Three principal stacked-fraction chains in source photos 125–127 match the
  cached cloud text exactly after whitespace removal. The cloud reader keeps
  `uncertain=true`. The comparison excludes cancellation/stray marks and does
  not certify all photo content or layout. This small development comparison
  is separate from the local CRNN experiment below.

New evidence lives in `manual_scope_review_20261008`; old labels, detector
weights, source photos and historical measurements were preserved. The prior
1,500-image unchanged-geometry regression is historical evidence from the
preceding phase, not a new test count for this one.

## Actual local training experiment

`scripts/data/finetune_line_ocr.py` reuses the existing CRNN architecture and
image transform. It verifies source bytes and reviewed boxes, rejects uncertain
or unapproved labels and 2-D blocks posed as prose lines, and checks source
groups, image hashes, decoded page pixels and crop pixels across splits.

The private frozen manifest contains **48 source-reviewed row/field crops**:

| Split | Crops | Source pages | Purpose |
| --- | ---: | ---: | --- |
| TRAIN | 22 | 5 | Clear selected arithmetic rows and one title from existing reviewed labels |
| DEV | 6 | 2 | Numeric rows; checkpoint selection only |
| HOLDOUT | 20 | 4 | 18 individual fraction components and two prose rows, excluded from this adaptation |

All actual proposed crop previews were inspected. Ambiguous overwrites and
remaining clipped fragments were excluded. Labels preserve the student's
written values rather than calculating replacement answers. Crossed
multiplication glyphs use the declared `×` transcription convention.

The experiment ran 12 epochs on CPU, batch size 4, four threads, learning rate
0.001, seed 20261008. Only the linear CTC head was adapted; CNN/BiLSTM parameters
were frozen. `×` was absent from V1's 320-entry vocabulary and was appended as
class 321 from TRAIN alone. The best checkpoint was selected on DEV critical
errors, then CER; selected epoch **11**. HOLDOUT was not used for selection.

| Measurement | Original head baseline | Candidate |
| --- | ---: | ---: |
| TRAIN character error rate | 40.21% | 23.71% |
| DEV character error rate | 34.75% | 26.27% |
| DEV digit/operator edit errors | 14 / 73 reference symbols | 11 / 73 |
| HOLDOUT character error rate | 45.19% | 43.27% |
| HOLDOUT digit/operator edit errors | 32 / 49 reference symbols | 32 / 49 |
| HOLDOUT exact complete crops | 1 / 20 | 0 / 20 |

The candidate is **rejected**: HOLDOUT CER exceeds 5% and digit/operator errors
remain. Lower aggregate CER alone did not justify replacement. The 18 short
fraction components are particularly difficult for this fixed-width line model;
these measurements are not end-to-end notebook/cloud-reader accuracy.

This is a tiny page-disjoint adaptation experiment, not a new full-scale V2
model. Writer independence and original V1 pretraining membership are unknown.
The photos have prior development use in the reader/detector work. Do not call
this a certified unseen or writer-disjoint benchmark, and do not tune subsequent
runs against this now-examined holdout while retaining that claim.

The candidate and paired vocabulary remain private. Strict model loading
passed; 24 CNN/LSTM state tensors are unchanged, the classifier parameters
changed, and the original deployed model/vocabulary hashes remain unchanged.
The existing cloud notebook reader and student app were not replaced.

## Verification and device handoff

| Check in this phase | Result |
| --- | --- |
| Dataset review, source storage, batch resume and archive safety tests | 50 passed; one Windows symlink-privilege test skipped |
| Actual 48-crop train/evaluation execution | Completed; quality gate failed as reported |
| Candidate strict checkpoint/vocabulary load | Passed |
| Historical 139 cloud outputs | Byte hashes preserved |
| AI health, business API health, mobile web page | HTTP 200 |
| Physical phone | Not tested; owner deferred |

The running application code was not changed in this phase; the previous
428 Python / 53 mobile / 80 Java / 13 HTTP checks remain separately documented
in [the previous phase report](MATH_SOURCE_CONFIRMATION_AND_REMAINDER_20261008.md).
They are not newly executed or counted here.

Use [the phone checklist](../docs/PHONE_TEST_HANDOFF.md) for crop/rotation,
back navigation, small-preview regression, draft preservation, correction and
confirmation, fraction tiers, long-division rows, wrong answers and outages.
Every real-device result is currently marked “Chưa test”.

## Reproduce, restore and resume

Read [the OCR review/training guide](../docs/OCR_REVIEW_AND_TRAINING.md) and
[the storage guide](../docs/DRIVE_DATA_STORAGE.md). Archive
`ocr-completion-20261008` holds the new queue outputs, reviewed manifest, rejected
checkpoint/vocabulary, raw evaluation, previews, source-parent review, test
receipt and code snapshots under the existing private Drive archive root.
Its hash and verified restore receipt are registered in
[the catalog](../docs/drive-archives.json).

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id ocr-completion-20261008 `
  --prefix 'ai-training/datasets/drive_math/candidate_line_20261008'
py -3 .\scripts\data\restore_drive_archive.py --id ocr-completion-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_remaining1180_20261008'
```

Restore the existing source-storage mapping and dataset sources as described
in the storage guide before reading crops. Resume only after the saved retry
deadline. Source/signature-matching successful results are skipped; the old
historical outputs live in their separate versioned batches.

Archive bytes and every entry were read back from the mounted G drive. A fresh
selected restore was checked separately. This verifies the mounted copy;
background upload completion to Google's servers is not independently verified.
Small active evidence is retained locally, and original photos stay on Drive.

Outstanding work remains explicit: **1,117 pending page reads, 13 unresolved
writing crops, seven incomplete fragments, a stronger reviewed/writer-separated
training cohort and local model, and the deferred physical-device test**.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the existing Drive reader, CRNN, transforms and batch
    runner without new dependencies or production-model replacement.
  - Applied to: source/split guards, bounded head adaptation, persisted provider
    backoff, evaluation, private evidence and device handoff.

The exact [Expo v57 documentation](https://docs.expo.dev/versions/v57.0.0/) was
read before code edits; no Expo or React Native application code changed here.
