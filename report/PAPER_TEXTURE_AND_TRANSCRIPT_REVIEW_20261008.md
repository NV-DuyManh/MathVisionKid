# Paper-texture recovery and source transcription review — 2026-10-08

The detector now recovers one additional faint pencil crop after the previous
raw/contrast recovery paths fail. This is a source-supported row candidate,
not a certified transcript. The existing 1,500 regression predictions and the
frozen reference scores remain unchanged.

A separate bounded cloud inspection resumed 100 pending pages, saved 85 reads,
and stopped with 15 pending when the provider became unavailable. Seven math
sources were visually checked against their original bytes: four have verified
transcriptions within an explicitly limited scope; three retain uncertain
corrections. No source image, historical cloud prediction or original reference
label was replaced, and no training was performed.

This follows [the initial repair](LINE_REPAIR_AND_SOURCE_TRIAGE_20261008.md) and
[the crop-context expansion](LINE_CONTEXT_EXPANSION_20261008.md). It uses the
frozen corpus; it is not a fresh census of newly uploaded Drive files.

## Runtime change

The existing context-retry helper can make one final attempt on eligible warm
paper using a 3×3 Gaussian smoothing pass. This reduces paper texture without
relaxing the existing ink-body, seed coverage, baseline, neighbouring-row or
fraction safeguards. Raw and contrast-enhanced passes still run first; established
nonempty predictions return unchanged. The helper has at most three additional
local model inferences, and the smoothing retry cannot repeat recursively.

Small landscape-crop limits, source-coordinate clipping and missing-model
behavior remain intact. Blank paper, straight ruling, shadows and speckles do
not independently establish a text row. New candidates retain
`needs_review=true` and `geometry_verified=false`.

The API detector version is `runtime18-paper-texture-recovery-20261008`; the
cache epoch is `text-regions-v13`. The pinned detector weights remain unchanged:
SHA-256 `03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587`.
The update applies at the next normal runtime start. This phase did not restart
the running app or test a physical phone.

## Local source results

All 171 previously empty byte sources were checked through the existing
Drive-backed reader. The original visual categories remain independent of the
new detector predictions.

| Reviewed category | Sources | Current result |
| --- | ---: | --- |
| No visible writing | 140 | All remain empty; no false positives in this reviewed group |
| Visible writing | 24 | Eleven now return candidates; thirteen still empty |
| Clipped writing fragments | 7 | Still unresolved |

Ten of the eleven writing recoveries were established in the preceding phases.
The new recovery is a 519×69 pencil crop with a candidate rectangle
`[0, 7, 519, 60]`. The principal row is visible, but cut-off neighbouring strokes
remain ambiguous. The new `empty_triage_texture_20261008.json` preserves the
previous manifest hash, source hash, candidate box and review evidence.
`transcription_verified=false` and `training_eligible=false` remain explicit.

An actual in-process HTTP API call on this original source returned HTTP 200 and
one row with the new detector version. The CRNN text still contains mistakes.
Configured Groq and Gemini post-correction each made one external request;
their suggestions were returned while final text remained raw CRNN. The API
call took approximately 14.9 seconds, including cloud work. The roughly 0.375
second detector sample is not an end-to-end response-time promise.

## Regression and tests

- **1,671 distinct images** in the final uncached local batch: 171 reviewed
  empty sources, 1,000 existing regression sources and 500 newly selected sources.
- The new 500 comprise 100 pages, 200 supplied crops and 200 Parquet crops,
  selected with seed `2026100803` and excluding earlier samples.
- **All 1,500 regression images retain identical boxes.** Only the additional
  pencil recovery changes the previously empty group.
- Runtime17 baseline evidence consists of 671 newly captured calls and 1,000
  imported frozen baseline results with saved code/source hashes. Final runtime18
  made 1,671 calls. Imported evidence is not counted as new baseline execution.
- **178 existing references** were rechecked: 176/178 exact row counts,
  146/148 matched geometry rows and 20/22 fully matched geometry images.
  Reference label bytes and these scores remain unchanged.
- Batch/reference overlap is removed from the combined total: **1,704 distinct
  source-byte images** were locally evaluated in this phase.
- **365 Python tests passed**, with four deprecation warnings. New tests cover
  the bounded third retry, unchanged input, merged-row rejection, blank/grid/
  shadow/speckle safeguards, missing weights and fractional tiers.

These are development regression and geometry checks. They do not establish
held-out transcription accuracy or perfect recognition. Sparse black calligraphy
and the reference whose scope excludes printed footer text remain unresolved.

Run from `ai/runtime`:

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m pytest `
  tests/test_text_detector.py tests/test_handwriting_rows.py `
  tests/test_short_row_recovery.py tests/test_short_row_marks.py `
  tests/test_tiny_row_ends.py tests/test_generalized_segmentation.py `
  tests/test_segmentation_contracts.py tests/test_notebook_math_layout.py `
  tests/test_notebook_tutor.py tests/test_notebook_capacity.py `
  tests/test_math_tutor.py tests/test_live_path_contracts.py -q
```

## Cloud inspection and source labels

The bounded cohort excludes the 39 previously completed page reads, whose output
hashes were checked unchanged. Resume reuses completed results with matching
source hashes and reader signatures. Three attempts made progress to 51, 57 and
then 85 reads; they stopped on provider availability errors instead of fabricating
responses or exhausting keys. The last pending failure records a rate limit and
retry deadline. The remaining 15 retain their queue entries.

The 85 saved reads contain 23 `WORK`, nine `MULTIPLE` and 53 `UNREADABLE`
classifications. `UNREADABLE` is the math reader's classification, not proof that
the source has no handwriting. Visually checked examples include legible
calligraphy and a non-math project slide. These classifications were not promoted
into training labels or used to delete source files.

Together with the historic 39, the original 1,319-page queue has **124 saved
reads and 1,195 pending**. A completed provider response is not automatically
a correct transcript.

The private `source_review_texture_20261008` contains seven separate reviews:

- Four scoped clear transcriptions: the cow ratio solution, a decimal division
  with speed units, division rules/examples, and a distance/unit-conversion solution.
- Three partial corrections retaining uncertainty: algebra with fraction
  cancellation, an overwritten time calculation, and an age-solution fragment
  with inserted side text.

The algebra source clearly writes `2x`, while the provider reads `3x` and reports
`uncertain=false`. The time source visibly writes `95` minutes; it must not be
replaced by a more plausible `45`. The age fragment contains an inserted side
calculation and crossed-out text that the provider merges into a spurious `310`.
Reviews preserve the visible writing and uncertainty, without substituting a
calculated answer. Fraction cancellation and parallel diagram labels are recorded
as such; these inline division examples do not independently validate long division.

Each review binds the original source and raw provider prediction by SHA-256.
Whitespace and multiplication glyphs are normalized explicitly. Full-image
coverage and geometry remain unverified; all seven reviews are ineligible for
automatic training. The four clear records certify only their declared scopes,
not the provider output or the entire image.

## Drive evidence and reproduction

Archive `sparse-ink-20261008` is registered in
[the archive catalog](../docs/drive-archives.json). It contains selections,
baseline/final results, code/test snapshots, source previews, versioned triage,
HTTP/test receipts, bounded cloud outputs and separate source reviews.

All **3,676 archived files** were read back and checked against their SHA-256.
A fresh selected restore reproduced the triage manifest byte for byte. The ZIP
is 8,789,248 bytes; SHA-256:
`6be835de867ccd4a562db9e82a5d441fa944356f0d566816cbf5684bbf218af4`.

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id sparse-ink-20261008 `
  --prefix 'infra/local-runtime/logs/sparse-ink-20261008'
py -3 .\scripts\data\restore_drive_archive.py --id sparse-ink-20261008 `
  --prefix 'ai-training/datasets/drive_math/source_review_texture_20261008'
py -3 .\scripts\data\restore_drive_archive.py --id sparse-ink-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_resume_20261008_100'
```

Historical reruns require the existing private source mapping and source
containers. Consult [the storage guide](../docs/DRIVE_DATA_STORAGE.md) and check
saved code hashes. Preserve historical outputs; do not mix an old baseline with
current code or treat an uncertain candidate as approved ground truth.

Original datasets remain on Drive; a full image batch was not copied into E.
Drive streaming can still cache opened containers locally. Archive read-back
and selected restore are verified; background upload completion is not
independently verified, so working evidence is retained locally. No model
training, weight replacement, commit or push occurred in this phase.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the pinned detector and existing source, review and
    archive tools with a small bounded fallback and no new dependencies.
  - Applied to: paper-texture retry, source safeguards, cache/version updates,
    regression checks, separate transcription reviews and evidence preservation.

Expo v57 documentation was read before implementation:
https://docs.expo.dev/versions/v57.0.0/.
