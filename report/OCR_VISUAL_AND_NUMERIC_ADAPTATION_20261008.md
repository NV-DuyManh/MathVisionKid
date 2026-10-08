# Visual adaptation and source-reviewed numeric fields — 2026-10-08

The frozen 1,319-page queue now has **244 saved cloud reads and 1,075 pending**.
Saved reads include unreadable classifications and are not verified transcripts.
This phase adds real source review and bounded CPU training; no experimental
checkpoint is installed. Recognition of every image is **not complete**.

## Source review and data integrity

Original bytes are read through the existing Drive-backed reader and checked
against their frozen SHA-256. No full corpus copy or new pretrained weights are
downloaded. Source sheets and individual component crops are inspected before
their candidate predictions. References copy the student's writing, including
wrong arithmetic values; no equation is solved to supply an OCR label.

Across successive manifests, 137 additional reviewed line/component scopes were
retained: 37 general scopes, 24 numeric scopes, 57 further numeric scopes, and
19 scopes from another page. These are overlapping task cohorts, not 137 new
pages or independent writers. Eight further pages were sampled in fixed queue
order for source-only review; only clearly scoped numerals from three of those
pages enter these experiments. Thirty proposed expression components containing
neighboring operator fragments were excluded before candidate inference. Their
initial manifest and the explicit exclusion revision are retained.

One reference initially read as `35` was corrected to `3,5` after examining the
source at higher magnification. The first manifest and raw run are preserved;
the corrected evaluation is explicitly post hoc. That nine-field set is exposed,
and its later measurements are development confirmation, not an unseen test.

Previously examined HOLDOUTs are explicitly retired in newer manifests. Reuse
as TRAIN is recorded; no source, decoded page, crop pixel alias or page group may
cross splits in a run. Related captures are grouped where known. Writer identity
and V1 pretraining membership remain unknown.

## Bounded experiments

All runs use the existing CPU runtime, four threads, batch size four and seed
20261008. Experimental aspect-preserving input has height 64 and width 64–1024,
rounded to stride eight. Production preprocessing remains unchanged.

The visual option adapts the last CNN block, BiLSTM and CTC head. The first three
CNN blocks remain frozen. Per-crop GroupNorm precedes feature padding; packed
recurrent sequences exclude padding from backward context. A numeric-only option
creates a paired 14-class vocabulary, limited to unsigned numerals and separators.
It cannot read prose, operators or complete expressions.

| Run | TRAIN / DEV / HOLDOUT | Selection and measurement |
| --- | --- | --- |
| General visual adaptation | 87 / 19 / 16 | Epoch 10/24; HOLDOUT 7/16 exact, CER 36.67% |
| Numeric head + recurrent | 77 / 19 / 9 | Epoch 7/24; corrected, exposed HOLDOUT 7/9 exact, CER 13.33% |
| Numeric visual, DEV only | 77 / 19 / 9 | Epoch 21/24; DEV 14/19 exact; no HOLDOUT inference |
| Numeric visual + TRAIN contrast | 77 / 19 / 9 | Epoch 2/24; DEV 15/19 exact, CER 16.13%; no HOLDOUT inference during development |
| Frozen recipe, new scopes | 77 / 19 / 57 | New HOLDOUT 46/57 exact, CER 13.75%; 11 digit errors |
| Expanded numeric training | 134 / 19 / 19 | Epoch 23/24; DEV 15/19 exact, CER 12.90%; new HOLDOUT 17/19 exact, CER 5.26%; two digit errors |

The 57-field checkpoint was reproduced from the fixed selected two-epoch recipe.
Its checkpoint bytes, every tensor, vocabulary and DEV measurements exactly
match the preceding selected run, before new HOLDOUT inference. The final
expanded run explicitly reuses those now-exposed 57 fields as TRAIN and reserves
19 fields from a different source page. These HOLDOUTs differ; their scores are
not a direct before/after comparison. One or two pages cannot establish broad
writer/layout accuracy.

TRAIN contrast augmentation adds one grayscale/autocontrast view per crop.
It changes no source file or evaluation pixels. The final run has 134 original
TRAIN crops and 134 augmented views, not 268 independent examples. DEV alone
selects epochs; `--defer-holdout` prevents neural HOLDOUT inference during tuning.
The separate frozen evaluator fits nothing and selects no new checkpoint.

On the last 19-field set, the unchanged production baseline gets zero complete
fields exact. The candidate gets 17; its two errors are source `64` read as `04`
and source `40` read as `4`. Neither prediction is arithmetically repaired. The
remaining critical errors and CER above 5% fail the experiment gate. Even a
passing bounded gate would not automatically install this specialized model.

Selected numerator/denominator recognition is component OCR. It does not certify
automatic detection of those boxes, complete fractions, division working rows,
whole-page text or the app's end-to-end accuracy.

## Detector and queue work

The 13 unresolved writing crops were probed against the current detector guards.
Failures include missing learned seeds, tiny seed coverage, widely separated
fragments and crops whose contextual recovery would swallow an adjacent clipped
row. Joining seeds before the existing context guard produces a box in only one
case; visual inspection rejects it because it includes a clipped row. No such
box is promoted. Seven source-clipped fragments still need larger originals.

Six resumptions in this phase save 6, 5, 0, 6, 12 and 6 additional reads: 35 beyond
the preceding phase's total of 209. The active new batch has 105 reads, added to
139 preserved historical reads. All historical successful output bytes were
hash-checked unchanged. Provider failures/backoff prevent the remaining 1,075
pages from being completed; a timer does not prove provider recovery.

The actual automatic region detector was also run on three newly reviewed pages:
27 regions on the arithmetic page, 28 on the fraction page and 37 on the larger
notebook page. Each overlay was inspected. Numeral regions are inconsistently
separated on the arithmetic page; the neutral-ink fraction page has mixed merged
regions and missed small regions. Complete page-layout ground truth was not
annotated, so no precision/recall score is claimed. A private neutral-ink
fraction-mask probe does not reliably establish fraction support and is rejected;
neither it nor these diagnostics modifies production. This confirms that manual
component crops conceal remaining automatic segmentation work.

Successful cloud reads are now immutable even with `--force`. A reader signature
or actual source-byte mismatch requires a new comparison batch. Later cached
successes are counted even after an early provider stop, and pending originals
are not fetched while backoff applies. Cloud predictions never automatically
become training labels.

## Verification and runtime limits

- Final focused Python regression run: **284 passed, one skipped, four warnings**.
  Coverage includes real bounded backward passes, TRAIN-only augmentation,
  held-out exclusion, split/hash checks, paired frozen evaluation, immutable cloud
  results, decoder probability integrity, detector, math layout and tutoring.
  The skip is the Windows symlink-privilege check; warnings are existing
  framework deprecations. Earlier broader runs are retained separately.
- Final checkpoint loads strictly with its paired 14-class vocabulary. The first
  three CNN blocks are tensor-identical to V1; last CNN block and recurrent
  tensors change as intended. Candidate checkpoints and manifests are private.
- V1 weight SHA-256 remains
  `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`;
  V1 vocabulary SHA-256 remains
  `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`.
- Final candidate SHA-256:
  `5b7e5551ab3d7efb531752e6df846562ad13cba67fa4b45f4a69c7f6d5feb0ff`.
  Paired vocabulary SHA-256:
  `b70b2473a349996aaf56102f4c593e8b2e73532648af06cdd3ad4ad213146db5`.
- No physical-phone test or Git push occurs in this phase.

Restarting the identified project AI service to apply the preceding decoder
fix was rejected by automatic approval review with reason **“blocked by policy”**.
No stop/restart was executed or bypassed. That code change takes effect at the
next normal launch; this phase does not claim it is live in the existing process.

## Evidence and next work

Private final receipt: `infra/local-runtime/logs/ocr-visual-adaptation-20261008/final-phase-receipt.json`.
Raw predictions, source review previews, original and revised manifests,
trainer/manifest snapshots, checkpoint pairs, and tests are retained separately.
The first focused Drive archive captures 238 reads; an immutable supplemental
archive preserves the final 244-read queue and subsequent detector probes. The
storage guide records both archives and their restore procedures.

Next work is to resume only after saved provider backoff, review further diverse
writers and critical symbols, reserve new page/writer groups before evaluation,
and measure automatic crop/layout plus transcription together. The unresolved
numeric candidates and 13 writing crops must remain visible; do not relax the
gate or replace references with solved answers to declare completion.

See [review and training instructions](../docs/OCR_REVIEW_AND_TRAINING.md) and
[phone handoff](../docs/PHONE_TEST_HANDOFF.md).

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal, evidence-preserving OCR and data-tool changes.
  - Applied to: existing CRNN/reader reuse, bounded optional adaptation,
    standard-library hashes/manifests, regression tests and no new dependencies.
