# OCR continuation: reviewed fitting and page recognition — 2026-10-13

The owner authorized further recognition and training. Two bounded continuation
experiments completed, and 246 pages from the latest orientation/stroke audit
were recognized again. The selected experimental pair remains **unpromoted**:
new fitting did not establish a general DEV improvement and still makes critical
digit/operator mistakes on the final small HOLDOUT.

## Source review and frozen cohort

- Original pages and exact proposed crops were inspected directly from mounted
  Drive bytes in RAM. SHA-256 and reviewed orientation identify the coordinate
  frame. No photographs, image contact sheets, ZIP or Parquet archives were
  created in this phase's local directory.
- Added **19 source-reviewed references**: five TRAIN, six DEV and eight HOLDOUT.
  Four TRAIN references were already exposed targeted geometry-development
  examples. They are explicitly training data here, never independent tests.
- Five HOLDOUT references scored on 12 October are now **DEV only** in the new
  manifest. All previous manifests and evidence remain unchanged.
- Total: **512 references — 432 TRAIN, 72 DEV, 8 HOLDOUT**. The existing loader
  verified hashes, crop bounds, source/page/pixel split separation and eligibility.
- Removed or recropped proposals containing adjacent-row strokes, ambiguous
  crossed writing, clipped unit suffixes and teacher annotations. The skewed
  pencil examples were reduced to complete numeric fields rather than labeling
  incomplete expression crops. References copy visible source content, not
  calculated answers or OCR predictions.
- The new HOLDOUT contains eight short numeric/arithmetic references on two
  pages. It has no prose, unknown writer independence and unknown original
  pretraining membership. Page sources had previously been processed as
  unverified corpus drafts. This is a targeted adaptation test, not a
  representative full-photo benchmark.

Manifest SHA-256:
`6ecb28ea1abe5e7b5ba0d9ce1949988d87f2b5d55fa6860fd2bd37c48439626f`.

## Actual training and selection

Both runs start from the frozen previous experimental pair `95577af0…` /
`dc25d2de…`, copied to private warm-start storage. They do not start from or
overwrite production files. Both keep the CNN frozen, preserve input aspect
ratio and use batch size 4, two CPU threads, TRAIN prose anchoring weight 2 and
deferred HOLDOUT inference.

1. BiLSTM/head continuation: **10 epochs**, learning rate 0.00003, seed 20261013.
   Selected epoch 3 regresses on DEV expression and prose scopes; rejected.
2. Head-only continuation: **10 epochs**, learning rate 0.00001, seed 20261014.
   Selected epoch 1 has no DEV scope regression but ties the unchanged parent.
   It is frozen for offline comparative drafts, not declared a production winner.

On the same 72 DEV references / 1,236 characters:

| Pair/input | Character errors | CER | Exact references | Critical edits |
|---|---:|---:|---:|---:|
| Production weights, production fixed resize | 365 | 29.53% | 4 | 152 |
| Production weights, experimental aspect resize | 262 | 21.20% | 10 | 73 |
| Unchanged experimental parent, aspect resize | 83 | 6.72% | 42 | 16 |
| Recurrent continuation, selected epoch 3 | 88 | 7.12% | 41 | 17 |
| Head continuation, selected epoch 1 | 83 | 6.72% | 42 | 16 |

Selected checkpoint:
`4903062bda8c543f221da2e970d0b281fc88ee312392f93822256a98fa77e838`.
The vocabulary remains the paired `dc25d2de…` file. Selection was recorded before
new HOLDOUT inference; no fitting or reselection followed that evaluation.

## Final HOLDOUT and release decision

Same eight references / 59 characters, after candidate selection:

| Pair/input | Character errors | Exact references | Critical edits |
|---|---:|---:|---:|
| Production weights, production fixed resize | 45 | 0 | 44 |
| Production weights, experimental aspect resize | 13 | 2 | 11 |
| Unchanged experimental parent, aspect resize | 32 | 1 | 6 |
| Frozen head continuation, aspect resize | 31 | 1 | 5 |

The head candidate reduces one character/critical edit versus its parent on this
small cohort, yet still reads `40` as `20`, confuses `=` with `-`, and reads a
leading `4` as `1`. The two comparisons against original production weights also
show a tradeoff: the aspect-resized production control has fewer character
errors but more critical errors than the experimental head. No overall winner
is established by eight targeted references.

CER includes transcription spacing after NFC/whitespace normalization. Compact
expression references and inserted spaces contribute to the 31 errors; the
separate five critical edits remain consequential regardless of spacing.
The frozen evaluator fails the 5% CER/zero-critical-error experiment criteria.
Production weights and preprocessing are retained. These HOLDOUT labels are now
explicitly marked **exposed** and must not be advertised as unseen in later work.

## Recognition and empty-region retries

- Recognized **246 images / 4,904 regions**, with **zero execution failures**.
  This is the latest orientation/stroke cohort, not a fresh rescan of all
  64,803 known source images.
- Initial results: **4,611 nonempty drafts, 293 empty drafts**. Source membership,
  hashes, coordinate frame, geometry and SQLite/JSONL payloads were reconciled.
- Retried **all 293 empty regions** on 94 images with two source-pixel views:
  RGB autocontrast and grayscale autocontrast, both with the frozen experimental
  pair and bounded aspect resize. **586 forward passes**, zero execution errors.
- **47 regions** have a nonempty hypothesis in at least one retry view;
  **246 remain empty in both**. None was promoted or used as a training label.
  Initial drafts remain unchanged.
- Eight nonempty retry hypotheses were inspected against raw crops. Examples
  include teacher marks, a correction cross, clipped descenders and ruling
  fragments. Several agreeing predictions are visibly unsupported; agreement
  does not establish correctness. The other 39 hypotheses remain unreviewed.
- Review queue: **2,447 regions**, including 293 empty drafts, 1,629 possible
  non-line layouts and 786 width-cap flags (categories overlap). Flags prioritize
  inspection; they are not proof of an OCR error or reference labels.

## Verification and retained state

- **101 relevant data/training/orientation/recognition regression tests passed**.
- Both real 10-epoch runs and frozen evaluation completed. Saved state comparison
  confirms head-only fitting changed just `fc.weight` / `fc.bias`; recurrent
  fitting changed RNN/head tensors. Both CNNs are unchanged.
- Trainer snapshots, manifest snapshots, model/vocabulary hashes and final code
  snapshots match their completed runs.
- Ten protected files, including both production model locations, earlier model
  evidence, the prior manifest and global source index, are byte-identical.
- No original-image/archive files written; deleted source-cache directories
  remain absent. No cloud inference calls, paid resources, application code
  changes, deployment, commit/push or physical-device claims in this phase.

Private evidence: `ai-training/datasets/drive_math/continuation_20261013/`, including
versioned crop proposals, accepted source review, frozen manifest/plans,
both experiments, selection, final/production comparisons, recognition database,
review queue, all empty retries, visual notes, integrity receipts and code snapshot.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the existing bounded trainer, source reader, orientation
    checks and resumable recognition runner instead of introducing another stack.
  - Applied to: private continuation experiments, minimal RAM-only review
    helpers, source integrity, existing regression checks and reproducible reports.
