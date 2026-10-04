# Drive math audit — 2026-10-04

This report records the **initial 200-image pass**. A later failed-layout retry
changed local coverage from 178 to 179 images; see
[the retry report](DRIVE_FAILED_RETRY_20261004.md). The tables and cloud-reading
measurements below are historical. Current `summary.json`, `manifest.csv` and
`results/` contain the rerun; its summary is also frozen in the private retry
evidence directory.

## Outcome

Downloaded, preserved and tested 200 distinct source photographs: 99 grade-5,
85 grade-4 and 16 collection images. All 200 completed the local detector and the
configured application's vision-reading path. This is completion of the test
batch, **not verification of 200 transcriptions or completion of all annotations**.

Original Drive files were not renamed, moved or deleted. Original bytes are kept
privately under `ai-training/datasets/drive_math/20261004/images/`. Source metadata,
raw and oriented-pixel SHA-256 hashes bind results and labels to each image.
The SQLite ledger has 204 tested IDs: today's 200 plus four verified existing
test inputs from October 3. Selecting today's IDs again returns no unseen IDs.
Marking is local exclusion from subsequent batches, not deletion from Drive.

## Implemented changes

- Reuse notebook-rule evidence to deskew wide crops before locating handwriting;
  map each rectangle back to the original coordinate system.
- Support one/two-row crops and short writing rows without relaxing the established
  full-page detector. Keep Vietnamese accents with their writing row.
- Prevent answer-bearing work without a visible question from becoming an invented
  original problem in the notebook-reading response.
- Add a resumable SQLite/JSON/CSV audit workflow, source/version-aware caches and
  separate API predictions. Never automatically promote predictions to labels.
- Preserve partial results on provider failure and honor backoff before resuming.

No model weights were trained. Detector code and notebook-reading rules changed;
there was no model-training claim, commit or push.

## Measured evidence

| Measurement | Before | After |
|---|---:|---:|
| Images with local row rectangles | 173/200 | 178/200 |
| Exact row count on 23 source-counted pages | 11/23 | 21/23 |
| Mean absolute row-count error on those pages | 0.783 | 0.087 |

The detector-only p95 is 76.975 ms on this computer, excluding loading, networking
and model inference. This is not phone latency. Matching counts do not prove
correct rectangles or text; tilted axis-aligned envelopes can overlap.

All 200 configured API calls produced persisted application outcomes:
7 `PROBLEM`, 121 `WORK`, 15 `MIXED`, 56 `MULTIPLE`, 1 `UNREADABLE`.
`MULTIPLE`/`UNREADABLE` are application outcomes, not successful transcription.
Temporary provider errors occurred and the audit resumed from the saved position.

The separately source-verified text subset contains **14 pages / 99 lines**.
Seven complete page transcripts exactly match after documented normalization;
aggregate normalized character error rate is **1.084%** on this subset only.
Normalization is Unicode NFC, whitespace removal and multiplication `x` → `×`;
it does not repair numbers. The batch was used for development, so these figures
are **not a held-out score, global OCR accuracy or accuracy on all 200 images**.

## Annotation status and remaining work

| Reference stage | Images | Meaning |
|---|---:|---|
| `verified` | 14 | Source-checked geometry and unambiguous text, 99 lines |
| `geometry_verified` | 8 | Boxes checked; overwritten/unclear symbols remain flagged |
| `count_verified` | 1 | Only row count independently confirmed |
| `needs_review` | 177 | Layout reviewed; full line/text annotation still required |

The original request for precise labels on all unlabeled images is **not complete**.
The remaining 177 must not be treated as accurate training labels. Eight further
pages also require symbol/transcription review. Preserve pupil mistakes instead
of replacing a visible operation with a mathematically convenient one. Examples
found include missed fraction denominators, wrong units, unclear overwritten digits
and a division sign that must not be changed to subtraction.

Each of the 22 no-rectangle sources was viewed individually and categorized in
private `failure_review.json`. Problems include black/pencil/red ink, two-page
spreads, columns, tables, vertical arithmetic, fractions, diagrams, large blank
gaps and hand occlusion. The local detector still targets coloured handwriting;
full-page region detection and faithful transcription of these layouts remain
work, not a claimed fix. Further development should first annotate exercise/column
regions, and evaluate separate unseen pages before considering training.

More aggressive row-floor/anchor prototypes were rejected after they produced
false rows. The detector evaluated in this initial pass has SHA-256
`5677c336cc7ad9a85e262846bd9f33b3f8f5098cdc11b7ca26c2d182a9c7c699`.

## Artifacts and verification

- Private batch: `ai-training/datasets/drive_math/20261004/`.
- Index: `manifest.csv`; detector evidence: `summary.json`, `results/`.
- Immutable selection: `source_selection.json`; labels: `labels/`.
- API evidence: `cloud_results/`, `cloud_summary.json`.
- Independent review: `comparison.json`, `transcription_audit.json`,
  `failure_review.json`.
- Persistent exclusion: `ai-training/datasets/drive_math/ledger.sqlite3`.
- Reusable instructions: `docs/DRIVE_BATCH_REVIEW.md`.
- Regression command from `ai/runtime`:
  `.venv/Scripts/python.exe -m pytest tests/test_handwriting_rows.py tests/test_notebook_tutor.py tests/test_live_path_contracts.py tests/test_generalized_segmentation.py tests/test_row_grouper.py ../../scripts/data/test_drive_line_batch.py -q`.
- Result: **83 passed**, four existing framework deprecation warnings.
- No physical-device validation was performed for these changes.
- Student photographs, labels, raw responses and runtime credentials remain ignored
  by Git. Public code/report contains no raw keys or signed download links.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal resumable workflow and bounded detector improvements.
  - Applied to: SQLite/JSON/CSV reuse, source caches, regression checks and existing
    OpenCV/Pillow implementation; no new dependencies.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: access the owner's supplied Drive photographs.
  - Applied to: discovery, metadata provenance, binary retrieval and preservation
    of original files and sharing settings.
