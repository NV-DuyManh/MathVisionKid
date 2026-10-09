# Review, evaluate and adapt local OCR

The local CRNN recognizes text inside supplied line crops. The notebook reader
also uses the configured vision service to interpret problem/work pages and
two-dimensional math. A new CRNN checkpoint does not automatically change that
cloud reader. The `crnn_vi_handwriting_v2` configuration is not a trained V2 model.

## Start with source evidence

Read [the Drive storage guide](DRIVE_DATA_STORAGE.md). Original photos can remain
on the mounted private Drive; the shared reader verifies their saved SHA-256.
Keep the active ledger and small manifests locally. Restore archived selections
and mappings before using an old batch.

For each proposed training row, inspect both the original page and its actual
crop. Reject cut-off strokes, adjacent-row contamination, ambiguous overwrites,
unread markers and automatically generated transcripts. Copy what the student
wrote, including an incorrect quotient or result. Never calculate an answer and
use it as OCR ground truth.

Use a new private manifest under `ai-training/datasets/drive_math/`. Each record
has these fields; `source` is the actual frozen selection entry, with its verified
`drive_id` and `sha256`:

```json
{
  "schema_version": 1,
  "records": [
    {
      "id": "source-id:row-index",
      "source": {"drive_id": "source-id", "sha256": "verified-image-sha256"},
      "source_batch": "actual-existing-batch",
      "source_group": "page:original-page-id",
      "box": [10, 20, 300, 80],
      "text": "exact source-reviewed transcript",
      "review_status": "verified",
      "reviewer": "reviewer and date",
      "uncertain": false,
      "layout": "TEXT_LINE",
      "training_eligible": true,
      "split": "TRAIN"
    }
  ]
}
```

This is a schema example, not runnable training data. Supply all three splits:
`TRAIN`, `DEV`, `HOLDOUT`. Keep a page, its recrops, aliases and related sources
in one `source_group` and split. The tool checks page groups, source hashes,
decoded page pixels and crop pixels across splits. Group related captures of
the same page together yourself; different photos cannot always be detected as
aliases. Record writer identity when available and reserve separate writers for
a stronger benchmark. Unknown historical pretraining membership must be disclosed.

A stacked fraction or long division is a structured block. Keep its numerator,
denominator, dividend, divisor, quotient and intermediate rows associated with
their source coordinates. Do not flatten the whole block into a prose-line
training label. Scoped component recognition is not full-layout accuracy.

## Run a bounded candidate

The owner must explicitly authorize training. The existing runtime environment
contains the needed PyTorch, torchvision and Pillow packages; this tool adds no
dependency and downloads no weights. From the repository root:

```powershell
& .\ai\runtime\.venv\Scripts\python.exe -X utf8 .\scripts\data\finetune_line_ocr.py `
  --manifest 'ai-training/datasets/drive_math/your-reviewed-cohort/reviewed_manifest.json' `
  --output 'ai-training/datasets/drive_math/your-reviewed-cohort/new-run' `
  --epochs 12 --threads 4 --batch-size 4 --learning-rate 0.001
```

By default this adapts only the linear CTC head; the CNN and BiLSTM stay frozen. It is an
initial experiment for at most 512 reviewed rows, not full-scale model training.
Only TRAIN can add vocabulary classes. Checkpoint selection uses DEV alone.
The selected candidate is then evaluated on HOLDOUT. Once examined, that holdout
must not guide later tuning while still being advertised as unseen.

The output directory must be new and outside production model storage. Results
contain `candidate.pth`, its paired `vocab.json`, and `evaluation.json` with raw
references/predictions, CER, exact rows, digit/operator errors and the quality
gate. CER includes transcription spacing after NFC/whitespace normalization;
review raw predictions and critical-symbol metrics together.

The experiment gate rejects character, critical-symbol and exact-row regressions,
HOLDOUT CER above 5%, remaining
digit/operator errors or no HOLDOUT improvement. These are conservative
experiment criteria, not a guarantee of all-photo accuracy. Even a passing
experiment never installs a checkpoint. Production replacement requires broader
writer/layout evaluation, review and the paired vocabulary/checkpoint.

The 08/10/2026 candidate failed that gate and is **not installed**. Its tiny
cohort does not establish independent V1 pretraining or writer-disjoint accuracy.
See [the phase report](../report/OCR_COMPLETION_AND_CANDIDATE_20261008.md).

### Experimental short numeric fields

`--preserve-aspect-ratio` is an experiment-only input policy: height 64, width
rounded to the CNN stride, bounded to 64–1024. Unlike the production fixed resize,
it avoids stretching a single digit across the entire line canvas. Variable
feature sequences are padded only for batching; CTC and decoding use their real
lengths. The production provider still uses its original fixed resize.

`--train-recurrent` additionally adapts the BiLSTM, while keeping the CNN frozen.
Packed feature sequences prevent batch padding from entering backward recurrent
context. Use these flags only with explicitly authorized, reviewed data and a
fresh experiment directory. Neither flag installs a model. The emitted paired
checkpoint, vocabulary and input policy must be evaluated together.

Each new run saves `trainer_snapshot.py` and its SHA-256. Once a HOLDOUT has been
examined, retire it before tuning again, explicitly record any reuse in TRAIN or
DEV, and freeze a new evaluation group. Avoid putting recrops or related captures
of the same source into separate splits.

`--train-last-visual-block` also adapts the last CNN block, the BiLSTM and the
head. The first three CNN blocks remain frozen. Per-crop GroupNorm is evaluated
before feature padding, so another sample's padding cannot change its visual
normalization. This is still a bounded experiment, not a full V2 trainer.

Future runs retain `manifest_snapshot.json`, reject a manifest changed during
training, and report errors separately by declared scope role. Read numerator,
denominator, quotient and intermediate-row results separately; correct prose
must not hide wrong mathematical symbols.

The follow-up field experiments improved limited component measurements but
still failed the gate. See [the follow-up report](../report/OCR_FIELDS_AND_DECODER_20261008.md).

`--numeric-fields-only` creates a separate 14-class vocabulary (blank, digits,
comma, period and space), initialized from the matching V1 classes. Every record
must declare `content_kind: UNSIGNED_NUMERIC_FIELD` and contain only unsigned
numerals with optional separators. This candidate cannot recognize prose,
operators or an entire expression. Never substitute it for the general provider.

Use `--defer-holdout` while developing. It excludes HOLDOUT from neural inference
and forces the experiment gate to remain false. `--augment-train-contrast` adds
one grayscale/autocontrast view of each TRAIN crop; DEV/HOLDOUT, original files
and reported original-source counts remain unchanged. These views do not create
new pages or independent writers.

After freezing settings and the checkpoint using DEV, evaluate the paired run
without fitting or selecting another checkpoint:

```powershell
& .\ai\runtime\.venv\Scripts\python.exe -X utf8 .\scripts\data\finetune_line_ocr.py `
  --manifest 'ai-training/datasets/drive_math/your-reviewed-cohort/reviewed_manifest.json' `
  --evaluate-candidate 'ai-training/datasets/drive_math/your-reviewed-cohort/new-run' `
  --output 'ai-training/datasets/drive_math/your-reviewed-cohort/frozen-evaluation' `
  --threads 4
```

The evaluator verifies both candidate checkpoint and vocabulary hashes, the
paired reviewed manifest and the original baseline hashes. Older runs lacking
vocabulary-hash evidence are rejected. Preserve them; do not retrofit evidence
to make the check pass. A previously examined HOLDOUT remains exposed even when
this evaluator is used. Reserve new source groups before final evaluation and
report selected component accuracy separately from automatic crop/layout accuracy.

The later visual/numeric phase reaches 46/57 exact fields on one new evaluation
cohort and 17/19 on a different subsequent cohort after expanding TRAIN. Both
still contain digit errors and fail the gate. Neither is installed. See the
[visual/numeric phase report](../report/OCR_VISUAL_AND_NUMERIC_ADAPTATION_20261008.md)
for reference corrections, exposed-HOLDOUT reuse and limits.

## Resume page reading safely

Cloud outputs are predictions; they do not become verified labels automatically.
For the current versioned queue, after restoring its current state if needed:

```powershell
& .\ai\runtime\.venv\Scripts\python.exe -X utf8 .\scripts\data\drive_line_batch.py cloud `
  --batch 'all_current_20261007/cloud_groupedsafe1001_20261009' `
  --limit 10
```

Matching successful reads are skipped. A saved provider backoff survives restarts
and also applies to `--force`. Exit code 2 means there are still pending pages;
consult `cloud_summary.json` and the saved retry deadline. Do not use `--force`
to bypass limits or repeat a completed cohort. If reader code/source hashes
change, preserve the old outputs and create a separately versioned comparison.

`--limit` now bounds **new successful reads in this invocation** (default 200).
For example, use 10 for a small continuation or 100 for a larger one. Existing
immutable results are counted and hash-checked but do not consume the new-read
budget. `batch_limit` means this bounded invocation stopped with work remaining,
not that the provider failed. Resume the same batch to continue. It never bypasses
the saved provider deadline. `new_reads` and `max_new_reads` are recorded in the
summary; classification responses without transcribed rows are still predictions,
not fully recognized pages or approved training labels.

Successful reads are immutable even with `--force`. A reader-version or source
byte mismatch stops with an explicit error and requires a new batch. During
backoff, later valid cached successes are still counted, and pending originals
are not fetched. No new provider request is made until the saved deadline passes.

The historical neutral-fraction follow-up preserves 250 successful source IDs
and selects the then-remaining 1,069 sources into its own versioned batch. The earlier
1180-source batch uses another reader fingerprint and remains historical evidence;
do not resume it with changed code or copy old predictions into the new batch.
The first new attempt stopped before saving a read; a later invocation honored
its persisted backoff. No cloud result is automatically a training reference.
See [the guard and queue report](../report/NEUTRAL_FRACTION_EVIDENCE_20261008.md).

The subsequent scale/topic phase adds six reads: **256 saved, 1,063 pending**.
That phase selected only those pending IDs under its reader version.
Earlier neutral and scale batches remain immutable historical evidence. The new
queue inherits the prior provider-failure deadline, so a batch-name change does
not bypass backoff. The topic guard was checked using a cached-response replay;
that is control-flow verification, not an independent provider accuracy result.
See [the follow-up report](../report/OCR_SCALE_AND_TOPIC_GUARDS_20261008.md).

The 2026-10-09 continuation saves 28 further provider responses: **284/1,319
saved responses, 1,035 pending sources**. Of these new responses, 16 classify
multiple exercises and three classify unreadable pages without transcribed
rows. Saved responses are therefore not a count of fully recognized pages.
Four source-linked visual spot reviews remain separate from raw predictions;
none is automatically approved for training. The queue fingerprint is unchanged
and its historical queue resumed the remaining IDs after persisted backoff.
See [the continuation report](../report/CONTINUED_OCR_AND_LESSON_FIXES_20261009.md).

The bounded 2026-10-09 follow-up saves another **10 responses**, bringing the
immutable total to **294/1,319**, with **1,025 pending**. Six new responses classify
multiple exercises and one is unreadable without rows; only three contain
transcribed content. A source-linked review found one worked solution incorrectly
classified as a question. The shared guard now retains the original transcribed
lines as WORK and requests the missing problem, without correcting numbers.

That guard changed the reader fingerprint. It created the planned
`cloud_workguard1025_20261009` queue containing only the remaining 1,025 IDs.
Its `queue_plan.json` records provenance and signature. The parent
`cloud_heading1063_20261008` results remain unchanged; do not resume that parent
with changed reader code. A cached-response comparison verifies guard behavior
only, not an independent OCR reading or a fully approved reference.

The subsequent physical-row/task-review phase saves **20 new source responses**:
**314/1,319 unique sources have responses; 1,005 remain pending**. Eight new
responses are MULTIPLE and ten UNREADABLE without rows; two contain 17 predicted
rows. Two independent repeat readings of historical sources are comparison
evidence and are excluded from coverage. These counts measure saved predictions,
not correctness or approved training references.

That phase used `cloud_rowreview1025_20261009`, whose fingerprint covers
the task guard, tall-glyph row detector and conservative row-boundary handling.
Its first 20 responses are immutable and will be skipped on resume. The prior
`cloud_workguard1025_20261009` plan was never invoked; preserve it as provenance
rather than running it with changed code. Source spot checks still show merged
prose and a misread operator in a table page. No weights or reference labels were
changed. See [the physical-row follow-up](../report/OCR_PHYSICAL_ROW_REVIEW_20261009.md).

The candidate-band follow-up saves **15 new responses**: **329/1,319 unique source
IDs have saved responses; 990 remain pending**. Ten are MULTIPLE, three UNREADABLE,
and two contain 24 predicted rows. Four additional readings repeat historical
sources for comparison and are excluded from coverage. No reference labels or
production weights were changed.

The current command uses `cloud_groupedsafe1001_20261009`. Four new readings were
saved under the preceding flat-band version and eleven under the final grouped
version. The failed provider record and its deadline were carried into the new
queue unchanged. The final run stopped on provider unavailability before reaching
its bounded budget; honor `retry_not_before` before resuming. Earlier completed
responses remain immutable. `cloud_grouped1001_20261009` and its comparison are
uninvoked historical plans, not the current queues.

Candidate bands include the full source, retain original pixels and never count
as approved crops. Internal grouped replies may contain zero or several actual
rows per candidate. Only identical ordered content/roles can reconcile breaks;
non-singleton grouping cannot supply displayed geometry. The actual comparison
split wrapped prose but duplicated another row, so the guard rejected adoption.
This is progress in review and safety, not proof of improved whole-corpus accuracy.
See [the candidate-band report](../report/OCR_CANDIDATE_BANDS_20261009.md).

Run dataset safety checks without cloud credentials:

```powershell
$env:PYTHONPATH = "$PWD/ai/runtime;$PWD/scripts/data"
& .\ai\runtime\.venv\Scripts\python.exe -X utf8 -m pytest `
  scripts/data/test_finetune_line_ocr.py scripts/data/test_source_storage.py `
  scripts/data/test_drive_line_batch.py -q
```
