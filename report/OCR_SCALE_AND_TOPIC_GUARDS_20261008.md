# OCR scale stability, topic guards and continued reading — 2026-10-08

Status: bounded fixes verified; **all-photo recognition remains incomplete**.
The frozen 1,319-source queue now contains **256 saved predictions and 1,063
pending sources**. Six provider responses were added; saved predictions are not
automatically correct transcripts or training references.

## Changes

### Neutral fraction capture size

The neutral-ink path was disabled for crops taller than 320 pixels. Small blue
ruling fragments could also grow past its fixed eight-pixel colored-ink test
when a capture was enlarged. The fraction probe now checks colored components
relative to crop height and downsamples its neutral working image to a bounded
height before applying the existing local-contrast kernel. Original pixels are
not modified; division panels retain their existing ink path.

One previously reviewed real fraction crop now retains isolated-fraction support
at 1×, 2×, 4× and 8×, where the pushed baseline lost it at 4× and 8×. Another
fraction still loses support at larger sizes, and four other individual crops
remain unsupported. Both expression crops and the whole worksheet remain
unsupported by this guard. These are resized derivatives of manual crops, not
independent camera captures, automatic line recovery or symbol-recognition scores.

### A lesson title cannot supply the original question

A new actual cloud response for `172.jpeg` classified the heading
“Bài 18: Đề-xi-mét vuông, mét vuông, mi-li-mét vuông” as an original problem.
The source contains notes and completed unit conversions, without an original
task. The reader now explicitly distinguishes notes from questions in its prompt,
and a bounded guard clears topic-only numbered headings from `problemText` while
preserving the transcribed rows as `WORK` requiring a question.

The guard preserves explicit tasks and bare expressions, including subtraction,
fractions, multiplication, unit-conversion instructions and written questions.
An initial regression caught the hyphens in “đề-xi-mét”; that was corrected before
the final validation. This is a conservative heading guard, not a general semantic
classifier. One other newly read page of several activities is still incorrectly
classified as `PROBLEM` in its raw cached response and is not silently rewritten.

## Actual verification

- **452 Python tests passed**, with four existing framework deprecation warnings.
  This includes notebook contracts, source confirmation, fraction/division literal
  preservation, detector paths, CTC integrity and the new guard regressions.
- **140 existing reviewed no-writing sources** were checked through mounted
  storage with original-byte SHA-256 validation. None triggered the three math
  layout guards. These remain development negatives, not held-out OCR accuracy.
- The scale comparison uses the pushed `d5dcce8` layout implementation and the
  same verified source/crops. Two enlarged derivative probes changed from no
  support to isolated-fraction support; no multiple-fraction trigger appeared.
- A cached-response replay on the real `172.jpeg` source produces `WORK`, empty
  `problemText` and `needsProblem=true`, preserving all 17 transcribed rows.
  The actual provider response is hash-checked unchanged. This replay substitutes
  cached responses for provider calls; it verifies control flow, not a fresh AI read.
- All **256 successful historical prediction files** are matched to original
  source IDs/hashes and preserved byte for byte.
- One separately reviewed row in `170.jpg` reads “số mét khối”, whereas the provider
  writes “số nước”. Another row has an overwritten divisor and remains `[?]` in the
  separate review. The provider outputs are unchanged; scoped reviews remain
  `training_eligible=false` because full coverage and geometry are not certified.

Private reproducible evidence is under
`infra/local-runtime/logs/ocr-scale-stability-20261008/`: `scale-verification.json`,
`heading-replay.json`, `source-scope-review.json`, `guard-verification.json`,
`final-historical-preservation.json` and `phase-receipt.json`.

## Queue and service limits

The preceding neutral-fraction version again stopped without a new read. The
scale version saved six responses: three WORK, two PROBLEM and one MULTIPLE,
then stopped at provider unavailability. Raw provider classifications are retained
even when a later source review finds mistakes.

The final prompt/guard change requires another reader version. Its selection
contains only the **1,063 pending IDs**, excluding all 256 saved reads:

`all_current_20261007/cloud_heading1063_20261008`

The latest saved failure's backoff is inherited into that new queue. A direct CLI
resume therefore cannot discard the preceding deadline merely by changing batch
names. The final invocation made no new request while that backoff was active.
Current reader fingerprint:
`37837eb0ca97147be50113c444e6d142802861b2fc3929462d745835fc73f837`.

No training, model promotion, physical-device test, commit or push occurs in this
phase. The original V1 weights/vocabulary remain unchanged. The earlier numeric
candidate still fails its critical-digit gate; no new percentage is claimed for
local OCR or complete notebook accuracy. Thirteen missed writing crops and seven
clipped fragments from earlier triage remain unresolved.

The prior project-service restart was rejected by automatic approval review with
reason **“blocked by policy”**. No restart is executed or bypassed. These source
changes require the next normal project launch; this report does not claim the
existing service process has reloaded them.

## Evidence storage and continuation

Archive `ocr-scale-topic-20261008` supplements the preceding immutable archives on
mounted Drive G. It includes the six new predictions, pending queue, real-source
review previews, comparison baseline, tested code and receipts. Each ZIP entry
and a fresh selected restore are verified. Independent confirmation of completed
Google server upload is unavailable, so small working evidence remains local.

Resume the current queue after its saved deadline using
[the review guide](../docs/OCR_REVIEW_AND_TRAINING.md#resume-page-reading-safely).
Continue independent source review and evaluate automatic layout plus transcription
on new page/writer groups. Do not train from cached predictions or treat mocked
replay tests and resized crops as evidence of perfect recognition.

## Owner-authorized startup follow-up

After this implementation phase, the owner explicitly requested startup. The
verified project AI process was restarted through the normal launcher. All core
services, Student Metro and the LAN readiness checks passed. The earlier restart
restriction described above records the state at the end of implementation;
the new source is now loaded by the restarted AI service. No physical-device
verification or training is implied by runtime readiness.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal changes to the shared reader/ink path and reuse of existing tools.
  - Applied to: bounded scale normalization, topic guard, regression tests, immutable
    source-linked reviews and inherited queue backoff.
