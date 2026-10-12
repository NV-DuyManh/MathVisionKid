# Full known OCR corpus and reviewed adaptation — 2026-10-11

## Status

**Completed the known 64,779-image snapshot:** 101,144 unverified region drafts,
zero final execution failures, three bounded adaptation experiments and final
integrity checks. **The selected candidate still fails release criteria and was
not installed.** No commit, push, deployment, paid service or external AI
inference occurred in this phase. Temporary caches have been removed.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Python OCR tooling, bounded data processing and simple reuse.
  - Applied to: existing source reader, SQLite recognition runner and tests.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.20/skills/google-drive/SKILL.md`
  - Why selected: authenticated access to source containers when the mounted
    Drive filesystem failed on large random reads.
  - Applied to: fetching and verifying the eight original Parquet containers.

## Scope and source integrity

The frozen **known inventory** contains 64,779 unique original-image SHA-256
values: 1,557 page images, 2,975 supplied ZIP crops and 60,247 supplied Parquet
crops. This merges the earlier recorded inventory with the 266 recent images;
28 recent aliases were deduplicated. It is not a fresh census of all Google Drive.

Supplied transcripts are excluded from inference inputs. They are not verified
labels. Source bytes are checked against the inventory before decoding, and page
boxes must match the current oriented image and detector provenance.

Drive's mounted Parquet reads failed on several large blocks. Eight exact
containers were fetched through authenticated Drive access, checked against the
recorded complete-container SHA-256 and used through a batch-local index. The
global source index is preserved. No access token or signed URL is stored in
public outputs. A connector request for the large ZIP exceeded its download size
limit; the mounted original was copied and its complete on-disk bytes checked
against the frozen SHA-256. Reading in 8 MiB blocks reduced the mounted ZIP's
read overhead. Only the batch-local mapping changed during materialization;
the verified image bytes and model inputs remained identical.

## Recognition

All 1,557 page images have completed execution: **37,922 regions**, of which
31,525 produced nonempty draft text. Two temporary read failures were retried
successfully. These counts describe processing, not correctness.

Page drafts flag 15,758 regions for conservative layout review and 2,185 for
width-limited resizing. These are heuristics, not verified errors. A manually
inspected nearly blank grid page demonstrates a real remaining defect: six
grid regions were detected, four were flagged, and one produced nonempty text;
the actual small red letter near the top was missed. Successful execution does
not certify detection or transcription quality.

The full-corpus inference checkpoint is the previously frozen paired candidate
`18d1501b130262f74ceaa22de2d460bcf7eec095c34ae5663f97a43ef5cb0ff7`
with vocabulary
`dc25d2de8fe00fb680b8a18c0abac8e4df0e4ec54aa71e5dcde1ec253814a9fd`.
It was frozen before this large run and remains separate from the subsequent
short-prose experiment. Do not attribute the latter's measurements to these drafts.

| Partition | Images completed | Regions executed | Nonempty drafts |
|---|---:|---:|---:|
| Pages | 1,557 | 37,922 | 31,525 |
| Supplied ZIP crops | 2,975 | 2,975 | 2,684 |
| Supplied Parquet crops | 60,247 | 60,247 | 60,246 |
| Total | **64,779** | **101,144** | **94,455** |

There are 6,689 empty drafts, 15,991 conservative layout flags and 8,741
width-limited resizes. The private review queue contains **25,156 regions** in
the union of these categories and the manually observed grid case. These counts
are not verified error rates. The six grid-only false detections also have a
separate manual negative-geometry record; no blank-page claim or training
eligibility was inferred from them.

The private runner buffers at most 128 lines plus one page of at most 200
regions. Equal-width microbatches avoid adding CNN padding that changes the
recognition output. SQLite transactions retain committed drafts; changed frozen
inputs reject resume. Output rows explicitly set `labels_verified`,
`reference_label`, `training_eligible`, and `score_is_accuracy` to false.

Three interrupted attempts on the mixed supplied-crop selection are
retained for traceability, not counted twice. Complete ZIP and Parquet partitions
supply the authoritative aggregate with the completed page partition.
The CPU thread comparison matched all 16 blind probe transcripts at four and
eight threads; this is a runtime check, not an accuracy benchmark.

## Reviewed data and training

The first new manifest has **403 references: 335 TRAIN / 54 DEV / 14 HOLDOUT**.
Its 53 new references were checked directly against visible ink. Uncertain,
neighbor-contaminated or mismatched supplied transcripts were excluded. The
previously scored eight-reference HOLDOUT was explicitly exposed and moved to
TRAIN; it was never counted as fresh evaluation again.

Two 30-epoch recipes used aspect-preserving inputs, the last CNN block,
BiLSTM/head adaptation, TRAIN-only multiplication-glyph initialization and
original-model prose anchoring. The earlier candidate remained the DEV-selected
winner because it retained fewer critical digit/operator errors.

| Candidate | DEV character errors / characters | Exact DEV lines / 54 | Critical errors |
|---|---:|---:|---:|
| Earlier frozen candidate | 55 / 1,009 (5.45%) | 35 | 11 |
| New prose replay, LR 0.0001 | 56 / 1,009 (5.55%) | 35 | 12 |
| Lower LR 0.00005 | 54 / 1,009 (5.35%) | 34 | 13 |

The frozen earlier winner was evaluated once on the reserved 14-reference
HOLDOUT: **32 / 265 character errors (12.08%), 3 exact lines and 3 critical
errors**. Its gate failed, including a prose digit/operator regression.

After that result, 75 additional literal crop drafts were reviewed: 65 were
accepted and ten rejected for neighbor-row ink or mixed printed fill-in dots.
The new manifest has **468 references: 392 TRAIN / 54 DEV / 22 HOLDOUT**. The
previous 14 HOLDOUT records are now exposed TRAIN data. Of the 65 additions,
43 handwriting-practice crops enter TRAIN; 16 printed prose labels and six
handwritten expressions from two different pages form the new HOLDOUT.

A third 30-epoch run used these references, single prose replay and the same
visual/recurrent adaptation and anchor. Selection used only the unchanged
54-reference DEV set, prioritizing scope regressions, then critical errors,
then CER and exact lines. The selected checkpoint has **57 / 1,009 DEV character
errors (5.65%), 34 exact lines and 10 critical errors**. It improved one critical
error while slightly worsening character and exact-line results against the
earlier candidate.

After selection was frozen, the new 22-reference HOLDOUT was evaluated once:
**15 / 151 character errors (9.93%), 13 exact lines and 2 critical errors**.
The gate failed because CER exceeds 5% and digit/operator errors remain. On its
six handwritten expressions alone it has 11 / 72 character errors and only one
fully exact transcript. This is insufficient evidence for replacing production.
The two critical mistakes include reading `8 × 3 = 24` as `8 × 5 = 24` and
replacing the equals sign with a minus sign in another expression. Spacing
differences account for some other character errors, but cannot excuse these
number/operator mistakes. Predictions were not corrected by solving the math.

A **DEV-only preprocessing ablation** uses the unchanged original weights with
the experimental aspect-preserving input: 213 / 1,009 character errors (21.11%)
and 59 critical errors, compared with 282 / 1,009 (27.95%) and 121 critical
errors using native fixed-width input. Thus part of the combined-system gain
comes from preprocessing. On the 16 DEV prose lines this original-aspect system
has 39 / 635 character errors and seven exact lines. The new candidate has
44 / 635 errors and six exact prose lines, a regression against this controlled
input policy even though its mathematical expressions improve substantially.
No new HOLDOUT inference or refitting followed this
diagnostic; it cannot support an independent release claim.

The two HOLDOUT percentages describe different small cohorts and must not be
treated as a before/after general-accuracy improvement. The latest HOLDOUT is
largely printed text; writer identity and original pretraining exposure are
unknown. Blind older-model corpus drafts were not consulted to select its
labels or splits. None of these experiments evaluates two-dimensional fractions,
full-page end-to-end correctness, or the quality of generated student solutions.

## Verification and artifacts

136 initial tests passed for the frozen implementation that ran the corpus.
After completion, safety fixes expanded the final suite to **158 passing tests**:

- Critical metrics retain Unicode division, minus, comparison and multiplication
  marks, plus parentheses/brackets so missing grouping cannot hide behind a low CER.
- A visibly reviewed literal question mark is accepted; uncertainty flags and
  the `[?]` unread marker still reject a training reference.
- A missing retained source copy can fall back to its verified source mapping;
  an existing copy with changed bytes still fails instead of silently falling back.
- Resume rejects reference/verified/training claims, changed pixel dimensions,
  malformed text/boxes, non-finite scores and incorrect record status. Runtime
  versions, CPU threads and microbatch size now participate in the fingerprint.

A real 16-crop smoke run and subsequent corrupted-reference recovery completed:
the repaired draft returned to `reference_label=false`. This is a pipeline guard
test, not an OCR accuracy claim. The measured environment was Python 3.12.13,
Torch 2.14.0+cpu, Torchvision 0.29.0+cpu and Pillow 12.3.0.

All three completed JSONLs reconcile with SQLite, their frozen fingerprints and
summaries. The source-ID/SHA union is exactly the 64,779-image snapshot; integer
boxes, finite scores and false verified/training flags passed. All 16 protected
production/historical artifact hashes match. Matching code snapshots retain the
implementation used by the completed corpus and fitting runs; later guard
changes did not retroactively rewrite them.

The expanded critical metric was checked **post hoc** against already exposed
frozen predictions, without new neural inference, fitting or checkpoint
selection. CER/exact-line scores are unchanged; critical-symbol denominators
include grouping now. HOLDOUT still has three critical errors for the first
cohort and two for the latest cohort. Historical evaluation files and the table
above retain their original metric/selection context.

Nine independently hash-checked temporary containers were removed, freeing
**2,844,629,192 bytes (about 2.84 GB)**. The batch-local index was restored to the
original mapping and its global counterpart remains unchanged. Forty small
original-byte review files, manifests, paired checkpoints, drafts and evidence
were retained. A future full rerun may need to materialize the containers again.

Private evidence root:
`ai-training/datasets/drive_math/all_recognition_20261011/`.
It contains source selections, reviewed manifests, review decisions, paired
checkpoints, frozen selections, evaluation JSON, per-partition SQLite/JSONL
drafts and verification logs. Raw images, literal transcripts, source identity
and candidate weights remain private. Public workflow:
[`docs/OCR_CORPUS_RUN.md`](../docs/OCR_CORPUS_RUN.md).

## Production decision and remaining deficiencies

**Do not promote any candidate from this phase.** The existing production
checkpoint, vocabulary, OCR provider, detector and tutoring code remain the
protected baseline. Their unchanged hashes were confirmed at completion.

Remaining work for a future release is concrete: resolve number/operator and
Vietnamese accent errors; obtain a larger independently reviewed, writer-aware
evaluation set; distinguish grid/blank regions from writing; and handle merged
columns and two-dimensional mathematical notation. More unverified predictions
or additional epochs alone cannot establish these capabilities.
