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
  --batch 'all_current_20261007/cloud_neutral_fraction1069_20261008'
```

Matching successful reads are skipped. A saved provider backoff survives restarts
and also applies to `--force`. Exit code 2 means there are still pending pages;
consult `cloud_summary.json` and the saved retry deadline. Do not use `--force`
to bypass limits or repeat a completed cohort. If reader code/source hashes
change, preserve the old outputs and create a separately versioned comparison.

Successful reads are immutable even with `--force`. A reader-version or source
byte mismatch stops with an explicit error and requires a new batch. During
backoff, later valid cached successes are still counted, and pending originals
are not fetched. No new provider request is made until the saved deadline passes.

The neutral-fraction follow-up preserves 250 successful historical source IDs
and selects only the 1,069 remaining sources into the batch above. The earlier
1180-source batch uses another reader fingerprint and remains historical evidence;
do not resume it with changed code or copy old predictions into the new batch.
The first new attempt stopped before saving a read; a later invocation honored
its persisted backoff. No cloud result is automatically a training reference.
See [the guard and queue report](../report/NEUTRAL_FRACTION_EVIDENCE_20261008.md).

Run dataset safety checks without cloud credentials:

```powershell
$env:PYTHONPATH = "$PWD/ai/runtime;$PWD/scripts/data"
& .\ai\runtime\.venv\Scripts\python.exe -X utf8 -m pytest `
  scripts/data/test_finetune_line_ocr.py scripts/data/test_source_storage.py `
  scripts/data/test_drive_line_batch.py -q
```
