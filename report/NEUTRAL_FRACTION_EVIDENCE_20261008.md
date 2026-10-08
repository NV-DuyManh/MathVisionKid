# Neutral fraction evidence and preserved pending queue — 2026-10-08

Status: improved bounded layout support; **the all-photo OCR task is incomplete**.
The fixed 1,319-source queue has **250 saved cloud reads and 1,069 pending**.
A saved read is a prediction, including MULTIPLE/UNREADABLE results; it is not
a verified transcription or an approved training label.

## Change and reason

`ai/runtime/app/tutoring/math_layout.py` previously relied on saturated colored
ink for fraction evidence. It now permits a local contrast mask on short,
light-background crops without substantial colored ink. The source pixels are
unchanged. Faint blue notebook rulings are excluded from the neutral mask;
crop-edge components cannot establish a complete fraction bar.

Several horizontal fragments associated with the same glyph components could
previously count as several fractions. Fraction-expression support now requires
independent numerator/denominator component groups. This prevents a real single
fraction with notebook rulings from being mistaken for several fractions.

These guards only support the existing bounded reread path when a result is
unreadable, multiple or incomplete. They do not identify digits, derive operands,
compute correct results, or supply student line boxes. The neutral division path
remains unchanged. Unsupported sources keep the ordinary reader path.

## What was actually verified

- **435 Python tests passed**, with four existing framework deprecation warnings.
  Coverage includes fraction/division preservation, notebook contracts, row
  recovery, detector paths, critical CTC probabilities and guided tutoring.
- **140 previously reviewed images without visible writing** were read through
  their mounted storage mappings, checked against their original SHA-256, and
  tested with all three layout guards. None triggered fraction/division support.
  These are existing development negatives, not a new independent accuracy set.
- One real mixed worksheet, `22.jpg`, was checked against its mounted original
  (`8e0c7e89672eefd94ad5b097641fbdb76b024780679527b986560069fae1d506`).
  The local review PNG is pixel-identical to that original after EXIF handling.
  Two manual crops now establish isolated neutral fraction evidence. Four other
  individual fraction crops and both expression crops still fail that guard;
  the whole page does not trigger it. The previously false multi-fraction trigger
  on a single fraction is removed.
- No symbol transcription or reference label was produced from that shape probe.
  Its manual coordinates are private verification fixtures, not application
  routing rules. This does **not** measure automatic segmentation or all-page OCR.
- All **250 historical successful output files** were hash-checked unchanged.
  Their source IDs and recorded hashes match the frozen 1,319-source selection.

Private receipts and reproducible scripts are under
`infra/local-runtime/logs/ocr-neutral-fraction-20261008/`:
`guard-verification.json`, `real-source-verification.json`,
`historical-preservation.json`, and `phase-receipt.json`.

## Cloud continuation

The reader version changed, so the earlier 1180-source batch cannot be resumed
with this version while preserving successful evidence. A new immutable selection
contains only the 1,069 pending IDs:

`all_current_20261007/cloud_neutral_fraction1069_20261008`

The first new attempt stopped at provider unavailability before saving another
read. A subsequent invocation honored the persisted backoff and made no new
request. Provider predictions are never automatically promoted to labels.
The reader fingerprint is
`a8e813032bdf7a28fb827c6c6b8ea7529f6c1d8b0f1948293a405a90b878730f`.
Use the current queue instructions in
[the review guide](../docs/OCR_REVIEW_AND_TRAINING.md#resume-page-reading-safely).

## Model and runtime limits

No training or production checkpoint replacement occurs in this phase. The
preceding numeric candidates still fail their critical-digit quality gates;
their best later component cohort is 17/19 exact, with two digit errors. See
[that phase's report](OCR_VISUAL_AND_NUMERIC_ADAPTATION_20261008.md).

The original model weight hash remains
`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`;
its vocabulary hash remains
`6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`.
Thirteen unresolved writing crops and seven source-clipped fragments remain
from earlier development triage. No fabricated boxes or computed answers are
used to turn these failures into passes.

The prior attempt to restart the project's AI service was rejected by automatic
approval review with reason **“blocked by policy”**. It was not stopped/restarted
or bypassed. These source fixes require the next normal project launch; the
existing service process is not claimed to use them. No phone test, commit or
push is performed in this phase.

## Storage and next work

Archive `ocr-neutral-fraction-20261008` supplements the earlier immutable ZIPs.
It preserves the current pending selection, the preceding 250-read state, guard
code/tests, source probes and receipts. Each mounted ZIP entry and a fresh
selected restore are verified before catalog registration. Google server upload
completion is not independently verified; small working evidence remains local.

Next work: resume after provider backoff, review literal symbols and layout on
more sources, and evaluate automatic crop/layout plus transcription together on
new page/writer groups. Keep missed fractions and critical digit errors visible;
neither a saved cloud result nor a passed shape test establishes perfect OCR.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: a minimal shared OCR guard and reuse of the existing queue/storage tools.
  - Applied to: bounded neutral mask, duplicate-evidence rejection, regression tests,
    standard-library hashes/receipts, and immutable pending selection.
