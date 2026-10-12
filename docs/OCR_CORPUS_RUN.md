# Offline OCR corpus runs

This workflow reads the private image inventory, trains only visually reviewed
references, and writes unverified OCR drafts. It does not install a production
model. A processed image is not necessarily correctly recognized.

## Prepare sources

Keep `source_selection.json` under `ai-training/datasets/drive_math/<batch>`.
Every entry needs its stable `drive_id`, `name`, and SHA-256 of the original image
bytes. The existing `source_storage.py` reads the mounted Drive file, ZIP member,
or Parquet image mapping. Keep photos, transcripts, weights and outputs private.

If Drive's virtual filesystem fails to read a large Parquet block, read the
authenticated original into bounded RAM and verify its complete SHA-256 against
the frozen inventory. Do not recreate a local archive or photo cache. Preserve
the original global mapping and keep tokens or signed URLs out of the repository.

Supplied line crops use the original whole crop, with unverified geometry.
Other images need current, source-coordinate page regions:

```powershell
& ai/runtime/.venv/Scripts/python.exe scripts/data/audit_text_regions.py `
  --batch <batch> --max-regions 200 --no-overlays --no-drafts
```

Investigate failed sources and empty/capped detections separately. Do not turn
missing detection into an invented transcript.

### Reviewed sideways pages

Do not choose image direction from a longer transcript or a higher OCR score.
Visually review the original page first. In a **new** private selection, add
`reviewed_orientation` with `clockwise_degrees` (0/90/180/270), `sha256` equal
to the original source hash, `status: "verified"`, and a named `reviewer`.
This verifies direction only; boxes and transcripts remain unverified.

The shared `source_orientation.py` applies EXIF once, then the reviewed rotation
in RAM. Detection, draft recognition and reviewed-label loading use the same
coordinate frame. Boxes refer to the resulting oriented image, whose dimensions
are recorded in the region JSON; they must not be reused on unrotated pixels.
Changed direction/review invalidates cached geometry and text, including 90 and
270 degrees, which have equal dimensions. Use a fresh batch/output to preserve
earlier evidence. Original Drive files are never rotated or overwritten.

## Train and evaluate

Use `finetune_line_ocr.py` with a reviewed manifest. TRAIN defines new vocabulary;
DEV selects a checkpoint; fresh HOLDOUT is deferred until selection is frozen.
Previously scored HOLDOUT is exposed development data, never a fresh test again.
The existing trainer validates source hashes, crop bounds and split leakage and
limits each experiment to a reviewed cohort of at most 512 records.
A literal `?` may be included when visible and verified; unread spans must carry
the uncertainty flag or `[?]` marker. Metrics keep Unicode operators and grouping
marks, because removing parentheses can change a calculation without changing
its digits.

Do not feed predicted text back as verified reference labels. Supplied archive
transcripts also require review; they can contain wrong words, missing accents
and captions that do not match the image. Compare character error, exact lines
and digit/operator errors in separate prose and mathematical scopes.

If a candidate changes both weights and preprocessing, also evaluate the
unchanged weights with that input policy on DEV. A combined gain does not
identify how much came from fitting. A small same-page or largely printed
HOLDOUT cannot establish general handwriting accuracy. Do not compare CER
percentages from different HOLDOUT cohorts as a before/after result.

The trainer records `preprocessing_control` and its per-role metrics using the
original weights with the candidate input policy. DEV checkpoint selection
compares against this control. Frozen evaluation checks both the original
production input and the same-input control; a resize benefit cannot conceal
worse prose, digits or operators caused by fitting.

Do not identify a retained source by its filename alone: `xyz/image-001.jpeg`
may later contain another photo. If a reviewed source disappears or changes,
locate its exact original bytes on Drive using its observed ID, verify the frozen
SHA-256, and bind a **new** manifest to that Drive source. Keep old manifests
and previous measurements immutable. Never train an old label on a new photo
that happens to reuse its filename.

## Recognize and resume

Use the frozen candidate directory containing `candidate.pth`, `vocab.json` and
its `evaluation.json`. Keep the paired files together.

```powershell
& ai/runtime/.venv/Scripts/python.exe scripts/data/recognize_corpus.py `
  --batch ai-training/datasets/drive_math/<batch> `
  --candidate ai-training/datasets/drive_math/<experiment>/run `
  --output ai-training/datasets/drive_math/<batch>/recognition `
  --regions ai-training/datasets/drive_math/<batch>/local_regions `
  --threads 8 --batch-size 4
```

Omit `--regions` for a supplied-crop-only inventory. `--margins` enables the
existing offline bounded-margin experiment for page boxes; it cannot recover a
missing line, split a merged column, or parse stacked fractions.

The runner buffers at most 128 lines plus the current page (at most 200 regions)
and batches only equal-width tensors. SQLite transactions preserve completed
drafts. Rerun the same command to resume; changed model/code/inventory/geometry
requires a fresh output directory. Source bytes and boxes are rechecked before
reusing a record, and failed sources are retried.
Runtime versions, CPU threads and batch size also participate in the fingerprint.
Approved-looking, malformed or non-finite cached drafts are recomputed instead
of being adopted as references.

Outputs: `predictions.sqlite`, UTF-8 `predictions.jsonl`, `provenance.json`, and
`summary.json`. The summary distinguishes successful drafts, no detected regions
and execution failures. Scores are raw model scores, not accuracy. None of these
outputs grants training eligibility or certifies a production release.

The owner's current policy requires originals to stay on Drive. Read observed
mounted Drive files directly, or authenticated references into bounded RAM;
never recreate local photographs, ZIP/Parquet archives or image contact sheets.
Retain metadata, outputs and source/code hashes. A historic `raw/` or container
path is not permission to download a source again. If Drive renames a file,
accept its new binding only after the original SHA-256 matches; keep the old
manifest and global index immutable for historical measurements.

## Complete a large inventory

Partition pages, supplied ZIP crops and supplied Parquet crops into separate
private selections when their storage access patterns differ. Verify that the
union has exactly the original source IDs and original-byte SHA-256 values,
without omissions or duplicate counting. Keep interrupted exploratory outputs
separate from the final partitions; do not silently copy records into a database
with a different frozen fingerprint.

At completion, reconcile JSONL with SQLite and each partition summary. Check
source membership/hashes, finite scores, in-bounds integer boxes, the frozen
model/vocabulary pair and false verified-label/training flags. Retain a matching
code snapshot when changing the runner after an experiment, so historic outputs
remain traceable to the implementation that actually produced them.

A private review queue may prioritize empty transcripts, conservative layout
flags and width-limited resizing. These signals are not reference labels or
proof of errors; narrow correct letters can also trigger a layout flag. Missing
detection still requires inspection of the whole source page. Never automatically
approve or train on the queue or on high-score predictions.

## Inspect split glyphs before retrying text

A line can return empty text because its box contains only a thin part of a
digit. Inspect the source pixels and the parent detector region. The runtime's
stroke guard uses faint ink to veto a cut through a complete stroke or extend
its supported row. It never creates a new row from faint ink. Ambiguous wide
regions retain the established geometry; fraction tiers remain one expression.
Notebook rulings are removed only from the guard mask, never from OCR pixels.

This is a geometry repair, not a transcription approval. Check preserved column
separation as well: arithmetic and prose in adjoining pages can have different
baselines. A repair must not reintroduce a crop spanning both pages. Targeted
reference metrics cannot establish overall accuracy, and fewer boxes do not
mean fewer true lines. Keep unresolved crops and wrong digits in the review queue.
