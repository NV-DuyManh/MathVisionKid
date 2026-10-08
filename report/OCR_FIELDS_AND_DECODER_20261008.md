# Short numeric fields and decoder integrity — 2026-10-08

The follow-up fixes a numerical defect in CTC alternative scores and adds two
real, bounded OCR adaptation experiments. Neither candidate meets the quality
gate, so production weights and preprocessing remain unchanged. The frozen page
queue gained seven saved reads: **209/1,319 saved, 1,110 pending** at this phase's
last check. Saved predictions are not approved labels.

## Production code change

`ai/runtime/app/ocr/crnn_provider.py` now accumulates CTC prefix probabilities
in log space. Previously, multiplying many probabilities could underflow; the
final `1e-30` floor made distinct low-probability alternatives appear to share
the same likelihood. Nonzero blank probabilities below `1e-6` were also omitted,
losing valid repeated-character paths. The new decoder retains those paths and
reports finite log likelihoods for long sequences.

This changes alternative scores, not the greedy source transcript or its
character-level visual evidence. Identical real logits from **85 source crops**
were decoded before and after the change: all 85 raw texts, token evidence,
raw confidence, blank ratios and entropy values were unchanged. The measured
median decoding time was 11.53 ms before and 13.65 ms after on this local sample;
this is not an end-to-end or phone latency measurement. Scores remain
uncalibrated model scores, not probabilities of a correct whole transcript.

Three new tests compare short-path scores with exhaustive enumeration, exercise
400-step low-probability sequences, and preserve a repeated digit separated by
a tiny nonzero blank probability. Written wrong digits are never solved or
replaced in this decoder.

The running service was not restarted in this phase. The code change takes
effect on its next normal restart. No physical-device evidence is claimed.

## Reviewed sources and experiments

Original image bytes were read through the Drive-backed source reader and their
SHA-256 values checked. Source-only sheets were reviewed before native outputs.
Twenty-five new fraction fields from two captures and twelve division fields
from two further captures were then visually reviewed individually. Their labels
retain the student's writing, including `33/2` and dividend `8924`; no value was
inferred by solving an equation. Only complete selected component boxes are
approved. Adjacent clipped rows and full-page coverage are not certified.

The previous exposed HOLDOUT is explicitly retired. Two of its pages become
TRAIN and two DEV for the first new experiment. The first new fraction HOLDOUT,
once examined, is explicitly retired and becomes TRAIN for the second experiment.
No result from either new HOLDOUT selected that experiment's checkpoint: DEV
critical-symbol errors, then DEV CER, select the checkpoint. New related captures
are conservatively grouped together and remain in one split.

`finetune_line_ocr.py` adds experiment-only variable-width input and optional
BiLSTM adaptation. Production still uses its fixed 64×1024 resize. Experimental
height is 64; width is rounded to stride 8 and bounded to 64–1024. The recurrent
model receives packed feature sequences, so batching padding cannot enter its
backward context. Real sequence lengths also bound CTC and decoding. CNN weights
stay frozen. The baseline uses unchanged production preprocessing on the same
source crops, rather than using the experimental policy as its own baseline.

| Experiment | TRAIN / DEV / new HOLDOUT crops | Adapted parameters | Selected epoch |
| --- | --- | --- | ---: |
| `candidate_fields_20261008/run01_aspect` | 34 / 14 / 25 | CTC head | 2 of 24 |
| `candidate_recurrent_20261008/run01` | 59 / 14 / 12 | BiLSTM + CTC head | 24 of 24 |

Both ran on CPU with four threads, batch size four and seed 20261008. Learning
rates were 0.001 and 0.0003 respectively. No dependency, pretrained weight or
full photo corpus was downloaded for training.

| Measurement on each experiment's own new HOLDOUT | Production baseline | Candidate |
| --- | ---: | ---: |
| Fraction fields: exact complete crops | 0 / 25 | 12 / 25 |
| Fraction fields: character error rate | 103.13% | 43.75% |
| Fraction fields: digit errors / reference digits | 32 / 32 | 13 / 32 |
| Division fields: exact complete crops | 0 / 12 | 5 / 12 |
| Division fields: character error rate | 106.06% | 33.33% |
| Division fields: digit errors / reference digits | 29 / 32 | 7 / 32 |

CER can exceed 100% when insertions exceed the number of reference characters.
The two HOLDOUT sets differ: these rows are not a direct head-versus-recurrent
comparison. The recurrent experiment's TRAIN CER is 0.72%, DEV CER 15.59%, and
HOLDOUT CER 33.33%; the gap warns against treating the training fit as recognition
accuracy. This tiny cohort does not establish writer-disjointness or independence
from unknown V1 pretraining. Component OCR is not full 2-D layout accuracy.

Both candidates fail the 5% HOLDOUT CER and zero critical-error requirements.
Neither is installed. The gate now also rejects decreasing exact-row counts.
Original weight SHA-256 remains
`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`;
original vocabulary SHA-256 remains
`6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`.
Both candidate checkpoints load strictly with their 321-class vocabulary. CNN
tensors remain identical; the second candidate changes recurrent tensors as
intended. Future runs save a trainer source snapshot and its hash. These two
earlier runs predate that snapshot addition; their raw outputs are preserved.

## Queue and remaining work

Three resumptions after the preceding phase saved six, then one, then zero new
reads, stopping on provider availability/backoff. Historical outputs were
hash-checked unchanged. The new batch now contains 70 saved reads: three PROBLEM,
31 WORK, five MIXED, 24 MULTIPLE and seven UNREADABLE. With historical 139, that
is 209 saved reads. The CLI returns exit code 2 while the 1,110 remain pending.
No keys, provider response bodies or credentials appear in this report.

The 13 previously unresolved detector crops and seven clipped fragments remain
unresolved; this phase did not change the detector or certify their geometry.
Further work needs larger reviewed groups of complete short numeric fields,
separate writers and capture families, fresh layout-level evaluation, completion
of the provider-blocked queue, and the owner's actual phone tests. An already
cut-off source cannot supply missing strokes.

## Validation and evidence

- The targeted data, confidence, segmentation, tutoring and live-path suite:
  **268 passed**, with four existing deprecation warnings.
- Final trainer suite: **17 passed**, including one real backward pass on
  synthetic mixed-length inputs. That test checks padding, frozen CNN tensors,
  changed recurrent tensors, preserved input checkpoint and trainer snapshot;
  it does not measure recognition accuracy. Sixteen overlap the broader suite.
- Separate real-model microbatch check passed; no physical phone was connected.
- Source hash, split-leakage, strict checkpoint, unchanged production bytes and
  real-logit checks were performed. No commit or push was performed.

Private working evidence is under
`infra/local-runtime/logs/ocr-completion-20261008`; new frozen manifests and
candidate outputs are under `candidate_fields_20261008` and
`candidate_recurrent_20261008` in the ignored Drive dataset working area. Follow
the [review/training guide](../docs/OCR_REVIEW_AND_TRAINING.md) and
[Drive storage guide](../docs/DRIVE_DATA_STORAGE.md) for restore and review.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: focused OCR correctness and reuse of the existing bounded trainer.
  - Applied to: log-space decoder, reviewed-source checks, optional recurrent
    adaptation, minimal validation, preservation and reporting.
