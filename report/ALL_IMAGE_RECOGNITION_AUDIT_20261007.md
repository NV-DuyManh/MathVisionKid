# Whole-corpus line audit and numeric-reading safeguards

Date: 2026-10-07

**Recognition is not complete across all images.** The three division examples from the previous phase are a small development sample. Neither successful execution nor a nonempty prediction establishes correct recognition.

## Scope and provenance

The downloaded Drive inventories contain **83,733 source identities**, representing **64,541 distinct byte images** after deduplication. The current sweep includes 1,319 page/reference photos, 2,975 supplied line crops, and 60,247 parquet crops. Previously inventoried training-folder images alias the parquet material; they are not counted again as independent images.

This is the frozen local inventory through 2026-10-06, **not a newly completed census of every live Drive folder**. A read-only NEW2 browser check observed the latest numbered files through 731, but full live pagination was not completed. Additional or subsequently uploaded files cannot be certified as covered.

Each audit result retains source SHA-256, code/model hashes, source-coordinate boxes, execution status and diagnostics. Results resume only when both source and code hashes match. Original files and existing reviewed labels are preserved. Predictions remain drafts with `training_eligible=false`; they are never promoted to reference labels automatically.

Private reproducible evidence: `ai-training/datasets/drive_math/all_current_20261007/`. The directory, source images, predictions and model artifacts remain ignored by Git.

The first local sweep was interrupted when E: ran out of disk space. Removed **62,298 newly generated duplicate draft-label files**, after checking they had no reviewed transcription and a retained result file. No original image or verified label was deleted. The shared audit runner now supports `--no-drafts`; this batch disables duplicate drafts and overlays while retaining predictions and source hashes. The resumed run rechecks source bytes before reusing saved results.

## Local segmentation

The full current-code sweep **completed all 64,541 images** in four process shards. The resumed run rechecked source hashes and reused 62,298 previously saved matching results; the other 2,243 images completed after the disk-space interruption. Final evidence is in `local_summary.json` and per-image `local_regions` results.

| Execution coverage | Result |
| --- | --- |
| Images processed | 64,541 / 64,541 |
| Execution failures in completed sweep | 0 |
| Images with predicted regions | 64,370 |
| Images with no predicted region | 171 |
| Region-limit-exceeded diagnostics | 0 |

The 171 empty predictions remain a review queue, **not proof that those images contain no writing**. No source was deleted because of an empty prediction. This sweep tests segmentation execution and bounds; it does not measure transcription accuracy.

The completed manifests and individual results agree on the totals. `coverage.json` records the per-source breakdown and all 171 empty-image identities. The empty detections are 149 supplied line crops and 22 parquet crops. All 1,319 full-page/reference photos produced some proposed regions, including **698 downloaded NEW2 images** (514 legacy-group images plus 184 NEW2/IMG images); this still does not establish correct line boundaries or text.

The **178 existing development references were all re-compared against newly saved detections**:

| Check | Result |
| --- | --- |
| Exact reference line count | 175 / 178 images |
| Geometry at IoU >= 0.5, one-to-one matching | 146 / 148 labelled rows |
| Complete geometric match | 20 / 22 geometrically labelled images |

Three count failures remain: sparse black calligraphy, a poem page with additional printed/side content, and a tight black single-line crop. Two fraction-image reference rectangles remain unmatched geometrically. The reference files were not changed to make these scores pass.

These are development comparisons, not held-out OCR accuracy. Count-only labels do not establish box correctness, and neither count nor box agreement establishes correct letters, operators, numerators, denominators or division working.

## Actual page reading

The initial reader run produced 9 / 1,319 inspection outputs before provider failure. Its evidence is preserved separately. After the numeric safeguard below and a further resume after backoff, the current run produced **39 / 1,319 inspection outputs**, leaving **1,280 pending** when the provider failed again. All 14 identified math photos in the latest 84-image batch received an output: 4 worked pages and 10 multiple-exercise pages. The latter require selecting an individual exercise; an empty transcript for that classification is not successful full-page transcription.

The remaining 25 completed outputs were non-math/unreadable classifications. Inspection can reject a page locally before a provider call when it exceeds capacity; the output count is not a count of cloud OCR transcriptions. None of the 39 outputs was automatically certified as an accurate reference label. Three audit attempts stopped on provider unavailability, including primary rate limits and fallback server failures. API availability blocked continuation, but recognition mistakes also remain independently of that service failure.

Full-source visual checks found:

- 719: wrong numeric transcription in the top equation and overwritten working. A review flag does not repair those digits.
- 718 and 721: crossed-out text had initially been returned without uncertainty. In the new run, 7 and 12 rows respectively required review, compared with zero initially.
- 722: diagram labels, crossed-out working and a corrected answer still require careful review.

The 721 source ends with an unfinished explanation; no final calculation is present on that photo. No missing answer is reconstructed from arithmetic. The limited visual observations are recorded in `visual_findings.json`, separately from reference labels.

## Shared fix

`ai/runtime/app/tutoring/notebook.py` previously could skip independent numeric verification when physical and transcribed row counts agreed. It now also verifies every row containing written digits, using the existing bounded second reading.

Agreement must preserve the entire normalized visible mathematical text. A one-digit or operator disagreement cannot pass a prose-similarity threshold. The first transcription stays unchanged; disagreement, crossed-out uncertainty, unavailable verification or an exhausted request budget retains the review flag. Initial uncertainty cannot be cleared by a later confident answer. No arithmetic is used to fill missing symbols or replace a pupil's wrong answer.

This adds one bounded verification request for numeric pages that previously skipped it. It retains the existing total request budget. Repeated agreement from the same provider is **not proof of correctness**; independent visual references and student correction remain necessary. This change improves review safety, not model weights or measured corpus-wide transcription accuracy.

## Validation and remaining work

- **149 Python tests passed** across notebook tutoring, math layout, capacity and math tutoring. Added checks cover same-count digit/operator disagreement, crossed-out values, unavailable verification, initial uncertainty and the exhausted time budget.
- Existing Starlette/httpx and AnyIO deprecation warnings remain.
- Audit CLI compilation and `--no-drafts` help passed; the resumed corpus sweep exercises that storage option.
- Original image hashes, current detector hashes and unchanged reference-label bytes were checked by the audit/comparison scripts.
- `git diff --check` passed with the repository's Windows line-ending configuration.
- No physical-device test, model training, weight replacement, commit, push or production deployment occurred in this phase.

Still required: review the 171 empty detections, finish the pending actual-page reading, resolve the five reference failures, label/review the unverified corpus, and evaluate faithful transcription on an independent held-out set, including stacked fractions and division rows. There is no evidence supporting a promise that every image is recognized correctly.

Resume commands from the repository root, using the existing local runtime:

```powershell
& .\ai\runtime\.venv\Scripts\python.exe .\ai-training\datasets\drive_math\all_current_20261007\audit.py local
& .\ai\runtime\.venv\Scripts\python.exe .\ai-training\datasets\drive_math\all_current_20261007\compare.py
# Resume only after the configured provider is available again.
& .\ai\runtime\.venv\Scripts\python.exe .\ai-training\datasets\drive_math\all_current_20261007\recheck_numeric_guard.py
```

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: use the existing audit runner and bounded reader verification rather than build a new OCR subsystem.
  - Applied to: private standard-library audit orchestration, unchanged-label comparison, minimal shared numeric-verification guard and regression checks.

Expo v57 documentation was read before implementation: https://docs.expo.dev/versions/v57.0.0/.
