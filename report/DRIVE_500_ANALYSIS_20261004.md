# Drive follow-up: deferred 21 cases and 500 additional image files

Date: 2026-10-04. Scope: continue analysing the unresolved cases, defer them if
unsafe, then evaluate 500 other files from the owner's Drive. No training or
Git publication was performed.

## Outcome

The 21 remaining difficult pages are deferred with their source identities and
hashes retained. Further private fraction, neutral-ink and pretrained text-detector
experiments were rejected: they produced false background rows, merged columns
or incomplete mathematical expressions. Producing any rectangle is not recovery.

The new fixed selection contains **100 full photographs and 400 supplied crops**,
not 500 new whole pages. This mixed selection was the stated working assumption
after an optional scope question received no answer. All 500 files were decoded
and evaluated locally; their pixel hashes differ from the 204 previously tested
files and from each other. One duplicate candidate was excluded. The ledger now
contains **704 tested source identities with distinct pixel hashes**. Nothing was
deleted or marked in Drive itself.

## Measurements and their limits

| Local detector | Full photos with boxes / tested | Crops with boxes / tested | Count matches on 10 reviewed references |
| --- | --- | --- | --- |
| Conservative coloured-handwriting rows | 59 / 100 | 220 / 400 | 5 / 10 |
| Generalized local segmentation path | 99 / 100 | 358 / 400 | 7 / 10 |

These are **nonempty-output counts, not recognition accuracy**. Visual inspection
of 24 full photos found missed handwriting, background/page-edge boxes, merged
columns and broken equations. Forty-eight supplied crops were reviewed separately;
some contain clipped text, several rows, fragments or background. Ten sources
have reviewed row counts only. The sample is small and selected for inspection;
it does not establish a population accuracy percentage.

The generalized evidence comprises 500 runs before the one-pixel bounds fix,
followed by eight affected reruns after it. Seven of those outputs were unchanged;
source index 363 changed coordinates, with no count change. Both run versions and
their code hashes are preserved rather than relabelled as a single fresh run.
The conservative detector completed all 500 after the fix, with zero execution
errors. Its measured p95 was 106.94 ms for local geometry only. The generalized
pre-fix run's p95 was 6768.44 ms for full photos and 186.49 ms for crops. These
computer measurements exclude uploads, transcription and tutoring requests.

No new cloud OCR calls, full student-flow evaluation or physical-device tests
were made. Reading all mathematical text correctly is not established.

## Two production fixes

1. Generalized rectangle padding now uses vertically adjacent regions with
   overlapping horizontal spans. A row in a neighbouring column no longer
   truncates an existing tall fraction region through a global midpoint.
   This preserves the candidate's ink; it does not solve column reading order.
2. The handwriting detector clamps inverse-resized coordinates to the original
   image bounds. Eight new crop cases had previously extended one pixel beyond
   the bottom edge because the resized height was rounded.

Regression tests reproduced both defects before the fixes. The original fixed
200-image batch was rerun: **all 200 rectangle arrays stayed identical**, with
179 nonempty outputs and 21 exact counts among 23 reviewed references.

## Annotation and training status

The new batch has **10 `count_verified`, 490 `needs_review`, zero verified
geometry and zero verified complete transcriptions**. The request for accurate
annotations on all images remains incomplete. Predictions were not promoted to
labels. Four hundred supplied CSV labels were imported as
`unverified_source_label`; 30 common-filler flags identify review candidates only.
They do not automatically prove an incorrect label or a blank source.

Archive crop identities combine the archive Drive ID with a hash of the entry
path. They are not individual Drive file IDs. Each record retains its archive
entry, parent-page name, raw hash and archive hash. Different crops can originate
from pages previously tested: file/pixel uniqueness is not an independent
page-family holdout. Training/evaluation splits must group those families.

No model weights were trained or updated. Unverified crops, labels and these
development measurements are unsuitable for claiming an improved trained model.

## Durable private evidence

All student images, labels and measurements remain in Git-ignored storage:

- `ai-training/datasets/drive_math/20261004_500/`: immutable selection, originals,
  imported labels, both detector results, summaries, visual reviews and review
  queue. The queue identifies 126 review priorities; it is not exhaustive or a
  verified-error list. `combined_geometry_manifest.csv` lists all 500 outcomes.
  `tools/` retains the acquisition/selection/measurement helper scripts.
- `ai-training/datasets/drive_math/archives/dataset_clean_full.zip`: original
  public Drive archive, SHA-256
  `8823cdcb70c9b82eab50bae863e5136b364fff5d013725f5348c532607466a54`.
  Archive CRC checks passed. It includes 3007 supplied crops; annotated debug
  pictures were not treated as original photographs.
- `ai-training/datasets/drive_math/20261004/retries/failed-layout-20261004/continued-analysis/`:
  deferred 21 identities, rejected experiments and baseline contract evidence.
- `ai-training/datasets/drive_math/20261004/retries/coordinate-bounds-20261004/`:
  original 200 before/after rectangle comparison.
- `ai-training/datasets/drive_math/ledger.sqlite3`: tested-source exclusion ledger.

## Verification

From `ai/runtime`:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_handwriting_rows.py tests/test_notebook_tutor.py tests/test_live_path_contracts.py tests/test_generalized_segmentation.py tests/test_row_grouper.py ../../scripts/data/test_drive_line_batch.py -q
```

Result: **90 passed**, four existing framework deprecation warnings.
A broader run including `test_segmentation_contracts.py` had three failing
contracts (SEG09, SEG10 and SEG14). The same failures were reproduced with the
repository HEAD pipeline before these changes; they remain unresolved, not
silently counted as passes. Evidence is in `contracts_baseline.json`.

Final artifact validation confirmed 500 tested ledger entries for this selection,
matching source and current detector hashes, 500 annotation files and all current
conservative rectangles inside source bounds. The complete ledger has 704 distinct
pixel hashes. `git diff --check` passed; sample originals/results/archive paths
were confirmed ignored by Git.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded detector fixes and resumable local evidence without
    additional application dependencies.
  - Applied to: coordinate bounds, padding neighbours, regression tests and
    preservation of the existing batch/ledger workflow.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.930.31730/skills/computer-use/SKILL.md`
  - Why selected: inspect the owner's public Drive folder when the connector was
    unavailable.
  - Applied to: browser-visible folder discovery and source identity capture;
    originals were fetched through public Drive download responses.
