# Drive failed-layout retry — 2026-10-04

## Outcome

Retried all **22 sources with no local row rectangles** in today's fixed
200-image selection. One source now returns useful row geometry; **21 remain
unresolved**. This is a small improvement, not a complete recovery of difficult
handwriting or a claim of accurate OCR on all 200 images.

| Local measurement | Before retry | After retry |
|---|---:|---:|
| Images with row rectangles | 178/200 | 179/200 |
| Empty results in the original failed group | 22/22 | 21/22 |
| Exact row count on the same 23 source-counted pages | 21/23 | 21/23 |
| Mean absolute count error on those 23 pages | 0.087 | 0.087 |

Comparing all 200 rectangle arrays against the frozen pre-retry detector found
only source **181, `Trang_12.jpg`**, changed. All original 178 nonempty results
are exactly unchanged. The new result has **16 physical row boxes**: 14 writing
regions and two standalone exercise markers. Source/overlay review found the
meaningful writing, both calculations and both answers contained. Some boxes
include curved notebook-margin/grid noise; crossed-out symbols remain uncertain.
This is qualitative coverage review, not verified pixel-accurate ground truth.

The current detector-only p95 is **93.409 ms** on this computer. Loading,
networking, model inference and physical-phone performance are excluded.
The batch's `failed: 0` field means no execution errors; it does not mean that
all pages yielded lines.

## Implemented change

The existing detector can reject a whole page when its sections have large blank
gaps or an exercise marker is shorter than ordinary writing. A bounded second
pass now permits those cases only with sufficiently saturated coloured ink.
It rejects faint ink and component patterns suggesting a stacked fraction, since
splitting a numerator from its denominator would be an invalid mathematical row.

The retry runs at most once and retains the existing image-size, line-count and
ink-coverage limits. Coordinates still refer to the original image. No new
dependencies or model weights were introduced. The fraction check is a
conservative guard, not a general fraction/layout recognition system.

- Runtime version: `runtime8-strong-sparse-rows-20261004`.
- Row detector SHA-256:
  `6fc3577c8ef50b8cb625466285c348281a35b16363c9f54d2411259ae61eec6f`.
- Frozen pre-retry row detector SHA-256:
  `5677c336cc7ad9a85e262846bd9f33b3f8f5098cdc11b7ca26c2d182a9c7c699`.

## Rejected experiments and remaining layouts

All 22 failed sources were re-examined. More permissive generic segmentation,
projection/component grouping, neutral-ink masks and fraction-anchor experiments
were tried privately. They produced boxes on more pages but included false grid
rows, person/background regions, merged columns, clipped prose or missing
fraction denominators. They were not connected to the application's fallback.
One fraction experiment matched a page's count of ten yet missed part of an
equation, showing why count alone is not acceptance evidence.

The remaining 21 sources contain faint/black/pencil handwriting, stacked
fractions, vertical arithmetic, tables, diagrams, columns or two-page spreads.
They need reliable exercise/column/expression regions before more permissive row
splitting. Private approximate region references for 12 grade-4 pages describe
that structure; they are explicitly not verified training labels.

## Application and annotation limits

This retry evaluated **local geometry**, with no new cloud reading calls. The
previous cached notebook response for source 181 is `MULTIPLE`. The notebook
reader returns that outcome before matching transcript lines to local boxes.
Consequently the newly recovered geometry does **not** establish that the app
now accepts that entire multi-exercise page or reads all its text correctly.

The current 200-image label status remains 14 `verified`, 8 `geometry_verified`,
1 `count_verified`, and 177 `needs_review`. No predictions or approximate region
references were promoted to accurate labels. The original precise-label request
remains incomplete. No training, new Drive download, commit or push occurred.
The local ledger still excludes the 204 already-tested source IDs from future
unseen-image batches.

## Evidence and verification

- Private durable retry evidence:
  `ai-training/datasets/drive_math/20261004/retries/failed-layout-20261004/`.
- `retry_results.json` identifies all 22 cases and the before/after rectangles;
  `review.json` marks the recovered case as geometry-only and the remaining 21
  unresolved. `full_batch_summary.json` freezes this rerun's measurements.
- `before_rows.py` preserves the exact comparator; `overlays/` contains the
  current failed-group overlays. Approximate references and rejected experiment
  reviews are kept separately from `labels/`.
- Current batch results: `ai-training/datasets/drive_math/20261004/results/`.
- From `ai/runtime`, regression command:
  `.venv/Scripts/python.exe -m pytest tests/test_handwriting_rows.py tests/test_notebook_tutor.py tests/test_live_path_contracts.py tests/test_generalized_segmentation.py tests/test_row_grouper.py ../../scripts/data/test_drive_line_batch.py -q`.
- Result: **86 passed**, four existing framework deprecation warnings.
- Full fixed-selection local rerun:
  `ai/runtime/.venv/Scripts/python.exe -X utf8 scripts/data/drive_line_batch.py run --force`.
- `git diff --check` passed. Photographs, private results and labels remain ignored
  by Git. No physical-device validation or live server restart was performed.

Follow-up: the remaining 21 cases were analysed further, then deferred. A separate
500-file mixed batch and two additional geometry fixes are documented in
[DRIVE_500_ANALYSIS_20261004.md](DRIVE_500_ANALYSIS_20261004.md). Measurements above
describe this earlier retry and are retained as historical evidence.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: a bounded improvement to the existing detector with measurable
    regression protection and no additional dependencies.
  - Applied to: the saturated-ink retry, fraction rejection guard, reuse of the
    fixed local batch, targeted tests and explicit limits on experimental code.
