# Empty-crop recovery and expanded regression — 2026-10-08

Nine more previously empty writing crops now return source-supported candidate
rows. The previous digit-practice recovery remains intact. This improves the
geometry available for review; it does **not** certify their transcriptions or
establish complete line coverage on these often clipped, multi-row sources.

This phase follows [the earlier triage](LINE_REPAIR_AND_SOURCE_TRIAGE_20261008.md).
It reuses the frozen Drive corpus rather than claiming a fresh census of files
added since that audit. No model training, cloud OCR call, weight replacement,
physical-device test, runtime restart, commit or push was performed.

## Runtime change

After the existing model, coloured, chalk and neutral-strip paths return no
regions, a bounded crop-context retry can consider small landscape images:
12–320 pixels tall, at least twice as wide as tall, and at most 4,096 pixels wide.
It supports neutral paper, aged yellow paper and suitable dark chalk boards.

- Reuse the pinned local detector, with source grayscale and, if needed, bounded
  contrast enhancement. At most two additional inferences use a working size
  bounded to 1,280 pixels plus white context; no weights are downloaded.
- Require several actual curved ink bodies, sufficient horizontal support and
  one supported baseline. Straight ruling, shadows and speckles cannot establish
  a row. Word gaps use component edges so connected cursive words are handled.
- Map each axis using its actual resize ratio and clip all boxes to source pixels.
  Nearby visible ink can extend a learned seed; no full-source substitute box,
  predicted answer or source-ID lookup is used.
- Reject seeds swallowing two supported baselines. Protect fraction tiers,
  including larger gaps between the numerator, divider and denominator.
- Preserve every established nonempty detection and missing-model behavior.
  Candidate boxes retain `needs_review=true` and `geometry_verified=false`.

The cache epoch is `text-regions-v12`; the API version is
`runtime17-crop-context-recovery-20261008`. The update applies at the next normal
runtime start. Student Mobile UI and tutoring answers were not changed.

## Source results and limits

All 171 previously empty original byte sources were read through the existing
Drive-backed reader and checked against frozen SHA-256 values. Previously reviewed
categories remain separate from detector predictions.

| Previously reviewed category | Sources | Final outcome |
| --- | ---: | --- |
| No visible writing | 140 | Still empty; zero false positives in this reviewed group |
| Visible writing requiring review | 24 | Ten now nonempty: one from the earlier repair, nine added here; fourteen still empty |
| Clipped writing fragments | 7 | Still unresolved; missing source strokes were not reconstructed |

The nine changed sources were individually inspected on source overlays. They
include small black cursive rows, chalk rows, yellowed-paper writing and faint
pencil. The faint pencil crop has visible stroke evidence but remains uncertain
to transcribe. Several sources also contain cut-off neighbouring rows; returning
the principal candidate is **partial recovery**, not proof that every row is found.

The new private `empty_triage_expansion_20261008.json` preserves the preceding
manifest hash, source hashes, candidate boxes, review evidence and exclusions.
No original image or label was edited. `training_eligible=false` and
`transcription_verified=false` remain explicit. Do not feed these predictions
into training as approved text labels.

## Regression and tests

A genuine runtime16 baseline was captured before edits, including source-code
snapshots. Final runtime17 predictions use the same sources, uncached production
calls, bounded source coordinates and saved code hashes.

- **1,000 additional regression images**: 100 page photos, 450 supplied crops
  and 450 Parquet crops, seed `2026100802`. Source identities exclude the previous
  500-image regression sample. All 1,000 retain identical boxes.
- The batch also includes the 171 reviewed empty sources. The sparse black
  handwriting reference was already among the 100 selected pages, and was
  called once more for review: **1,172 calls on 1,171 distinct sources** per
  baseline/final run. This repeated call is excluded from distinct-source totals.
- **178 frozen references** rechecked independently with original label-byte
  hashes preserved: 176/178 exact counts, 146/148 geometry rows and 20/22 complete
  geometry images. These reference scores are unchanged from runtime16.
- The batch and references overlap: **1,205 distinct source-byte images** were
  evaluated in this phase. Duplicate calls and shared references are not counted
  as extra independent images.
- **357 Python tests passed**, including 16 new context-retry cases, neighbouring
  rows, fractional tiers, resizing, aged paper, chalk, blank/ruling safeguards,
  long division, leading zeros, wrong quotients, uncertainty and API contracts.
- Existing FastAPI/Starlette/httpx/AnyIO deprecation warnings remain.
- No held-out transcription accuracy or perfect-recognition claim is made.

The original count discrepancies remain: sparse black calligraphy misses isolated
letter rows, and a poem reference counts student handwriting while the generic
detector also retains printed side/footer text. Neither was forced to match by
changing the original labels or suppressing printed math globally.

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

## Reproduction and private evidence

Private baseline/final results, source selection, code snapshots, inspected
overlays and triage are saved in `line-expansion-20261008`, listed in
[the archive catalog](../docs/drive-archives.json). Originals remain on Drive;
the phase does not restore a full image batch onto E. Google Drive may still
cache source containers while they are read.

All **2,547 archived files** were read back and SHA-256 checked. A fresh selected
restore reproduced the new triage manifest byte for byte. The ZIP is 3,319,061
bytes; its catalog SHA-256 is
`1f53706c4c7a221383f4dde582d2c655a677b8ebadde7c994a6f3e78088eade6`.

Restore only the required evidence:

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id line-expansion-20261008 `
  --prefix 'infra/local-runtime/logs/line-expansion-20261008'
py -3 .\scripts\data\restore_drive_archive.py --id line-expansion-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/empty_triage_expansion_20261008.json'
```

Historical reproduction also requires the existing runtime, private source
mapping, shard selections and frozen references described in the storage guide.
Check saved code hashes before comparing runs. The restored helper's `final`
results are the final-code evidence; intermediate experiment folders are not
accuracy baselines. Use a new phase directory rather than overwriting history.

Drive background upload completion is not independently verified; small working
evidence stays local until synchronization is confirmed. Previous archives are
preserved. Archive read-back and fresh selected-restore receipts accompany this
phase's private evidence.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: extend the existing pinned detector and reuse current source,
    regression and restoration tools without new dependencies.
  - Applied to: empty-only context retry, fraction/baseline safeguards,
    cache/version updates, tests, source triage and evidence preservation.

Expo v57 documentation was read before implementation:
https://docs.expo.dev/versions/v57.0.0/.
