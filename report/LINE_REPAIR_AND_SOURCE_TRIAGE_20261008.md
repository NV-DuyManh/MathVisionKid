# Line detection repair and source triage — 2026-10-08

One previously missed black-ink strip now produces a reviewable line box.
All 500 images in the regression sample retain identical boxes. Recognition
is still incomplete: 23 reviewed crops with visible writing remain empty,
and seven additional crops contain cut-off writing fragments.

This phase reviews the previously frozen corpus, not a fresh census of Drive.
It measures line geometry, not transcription accuracy. No training, weight
replacement, cloud OCR request, device test, runtime restart, commit or push occurred.

## Source review

All 171 previously empty sources were read through the Drive-backed reader,
checked against their frozen SHA-256 and inspected on five contact sheets.
Ambiguous writing and failed geometry references were inspected separately.

| Category | Images | Outcome |
| --- | ---: | --- |
| No visible writing: cloth, desk, paper edges or blank ruling | 140 | Marked for exclusion from text training; zero new false-positive boxes |
| Visible writing needing review | 24 | One recovered; 23 remain unresolved |
| Cut-off writing fragments | 7 | Kept as clipped sources; no missing strokes reconstructed |

Private `all_current_20261007/empty_triage_20261008.json` binds decisions to
source hashes and contact-sheet positions. Exclusions are sidecar metadata;
original ZIP members and Parquet rows remain intact. These decisions do not
certify transcriptions or automatically alter training imports. Future curation
should consult this manifest.

## Runtime repair

`detect_crop_regions` now tries neutral-ink recovery after existing learned,
coloured-ink and chalk paths return no regions. It considers light-paper strips
8–128 pixels tall, at least four times wider than tall and at most 4,096 pixels wide.
Multiple substantial glyph bodies must support one baseline and non-straight
stroke shapes. Grids, partial parallel rulings, dense shadows, speckles and
ambiguous two-row/fraction support are rejected.

Existing nonempty results and unavailable-model signals remain intact. Bounds
come from visible components, without full-image guesses, calculated answers
or per-image lookups in production code. The recovered digit-1 practice crop
returns one box instead of zero, with `needs_review=true`,
`geometry_verified=false` and potentially clipped source text.

The cache epoch was incremented. API detector version:
`runtime16-neutral-strip-recovery-20261008`. Changes apply on the next normal
runtime start; there was no running listener to restart during this phase.

## Unchanged-reference comparison

All 178 original label files retained their exact byte hashes.

| Measurement | Before | After |
| --- | ---: | ---: |
| Exact count, all development references | 175 / 178 | 176 / 178 |
| Exact count, references with writing | 36 / 39 | 37 / 39 |
| Correctly empty negative references | 139 / 139 | 139 / 139 |
| Geometry matches, frozen row rectangles | 146 / 148 | 146 / 148 |
| Complete geometry match, reference photos | 20 / 22 | 20 / 22 |

Two count discrepancies remain: sparse black calligraphy misses isolated
letter rows; the poem page returns 18 text regions against a count of 12
handwriting rows. Source review finds all 12 poem rows plus six printed/side
regions. Printed text must remain available for printed math problems; it was
not globally suppressed to force the handwriting count.

Two legacy “là:” rectangles exclude visible letter, accent or colon strokes.
Separate source-based revisions in `geometry_review_20261008` match 15/15 rows
on those two photos. Original labels and historical scores remain unchanged.
This is **label repair**, not detector improvement or held-out accuracy.
Revisions remain `training_eligible=false`; other transcriptions were not
re-certified. These photos show percentage and cube-area work; the earlier
report's description of them as fraction fixtures was corrected.

## Regression and tests

The actual production detector ran twice per image, with only the new fallback
disabled and then enabled. Caches were cleared between calls. Source hashes,
source-coordinate bounds and current code hashes were checked.

- **171** previously empty sources rechecked: one recovered; 140 unwritten
  sources still empty.
- **500/500** additional sources retain identical boxes. Seed `20261008`:
  50 page photos, 225 supplied crops and 225 Parquet crops. All feature-off
  predictions in this sample were nonempty.
- **178** frozen references rechecked separately. The cohorts overlap:
  **708 distinct source-byte images**, not 849 independent images.
- **341 Python tests passed**, including fractions, long-division rows,
  leading zeros, wrong handwritten quotients, uncertainty, segmentation,
  detached marks, tiny crops, tutoring and API serialization.
- Existing FastAPI/Starlette/httpx/AnyIO deprecation warnings remain.
- `git diff --check` passed; no physical-device evidence is claimed.

From `ai/runtime`:

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m pytest `
  tests/test_text_detector.py tests/test_handwriting_rows.py `
  tests/test_short_row_recovery.py tests/test_short_row_marks.py `
  tests/test_tiny_row_ends.py tests/test_generalized_segmentation.py `
  tests/test_segmentation_contracts.py tests/test_notebook_math_layout.py `
  tests/test_notebook_tutor.py tests/test_notebook_capacity.py `
  tests/test_math_tutor.py tests/test_live_path_contracts.py -q
```

## Evidence on Drive

Private previews, hash-bearing results, comparison helpers, triage and geometry
revisions are in archive `line-repair-20261008`, listed in
[the catalog](../docs/drive-archives.json). All 1,768 entries were read back and
hash-checked. A fresh selected restore reproduced the three geometry-review
files byte for byte. Drive's background upload completion was not independently
checked; small working evidence remains local until synchronization is confirmed.
Original corpus images remain on Drive.

The catalog's garbled Unicode root was repaired to
`My Drive/Dự án/MathVisionKid/Lưu trữ`, matching the actual mounted folder.

Restore only the required part from the repository root:

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id line-repair-20261008 `
  --prefix 'infra/local-runtime/logs/line-repair-20261008'
py -3 .\scripts\data\restore_drive_archive.py --id line-repair-20261008 `
  --prefix 'ai-training/datasets/drive_math/geometry_review_20261008'
py -3 .\scripts\data\restore_drive_archive.py --id line-repair-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/empty_triage_20261008.json'
```

Private comparisons require the existing runtime, reviewed labels, frozen
selections and source mapping. Verify saved code hashes before attempting to
reproduce historical numbers with a later checkout. No new model is downloaded.

## Remaining work

The 23 still-empty writing crops, seven clipped sources and sparse black
calligraphy need further work. Previous pending page transcriptions remain
pending; provider availability was not retested here. An independent held-out
transcription set for fractions and division working is still required.
Successful execution, line counts and tests do not establish perfect OCR.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimally extend the existing detector and reuse source and
    restoration helpers.
  - Applied to: bounded recovery, cache/version updates, regression tests,
    source triage, unchanged-label comparison and Drive evidence.

Expo v57 documentation was read before implementation:
https://docs.expo.dev/versions/v57.0.0/. Student Mobile UI was not changed.
