# OCR follow-up: reviewed training and 266-image draft recognition

Date: 2026-10-11. The owner explicitly authorized continued line recognition and training. Completed one bounded 30-epoch experiment and ran its frozen private candidate over all 266 images. **Production remains unchanged:** the candidate still fails the release gate, and automatic crop geometry remains a major limitation.

## Reviewed sources and split safeguards

Reviewed three full source pages and twice-rendered individual crops. Accepted **17 new references**: five TRAIN records from page 962, and 12 HOLDOUT records from pages 970 and 995. The new HOLDOUT comprises five mathematical expressions and seven prose records, including pencil writing. Four preliminary crops were excluded for clipped descenders or neighboring-row ink. Overwritten answers, long-division blocks, crossed-out text, diagrams and a truncated date were excluded rather than guessed. Preserve literal visible text; do not solve an equation to supply its transcript.

Reclassified the preceding phase's already scored 16 HOLDOUT records as TRAIN only in this new manifest, retaining their former split and exposure note. Previous manifests and evaluations remain immutable. Final cohort: **241 TRAIN / 48 DEV / 12 HOLDOUT**, 301 records. TRAIN includes 72 prose and 82 expression records, plus previously reviewed text and numeric fields. Teacher regularization uses only TRAIN prose. The previous exposed test records are not fresh validation.

Verified all 266 original byte hashes, representing 238 distinct hashes. The three newly reviewed source hashes have no collisions in 35 prior reviewed manifests. Page 968 is a byte alias of TRAIN page 962 and supplies no extra independent reference. Known source-group, source-hash, full-page pixel and crop-pixel cross-split guards pass. Writer independence, alternate captures and original base-model exposure remain unknown. These are correlated notebook/book styles and a small purposive sample. The new pages already had unverified production drafts; they had no prior reviewed score or fitting use.

## Bounded training and frozen selection

Start from the unchanged production checkpoint. Reuse the existing trainer: CPU, two threads, batch four, 30 epochs, learning rate 0.0001, seed 20261011, aspect-preserving resize at height 64 and width 64–1024. Adapt the final CNN block, BiLSTM and CTC head; the first three CNN blocks stay frozen. Reuse TRAIN-only warm multiplication initialization, prose replay three and prose KL anchor weight two. No contrast augmentation. There are 289 cached development originals and 385 sampled TRAIN views per epoch; replay is not additional independent data.

One predefined recipe was completed. Select **epoch 26** by DEV role regressions, critical edits, CER and exact lines, then freeze the paired checkpoint, vocabulary and reviewed manifest before new HOLDOUT inference. No HOLDOUT neural preprocessing, teacher targets, epoch scoring or checkpoint selection occurred during training. No fitting or selection followed the final HOLDOUT score.

| Same reused DEV: 48 lines / 702 characters | Previous private candidate | New private candidate |
|---|---:|---:|
| Literal CER | 4.27% | 3.99% |
| Exact lines | 32/48 | 34/48 |
| Critical digit/operator/punctuation edits | 9 | 8 |

The selected epoch has no role regressions against production under the trainer's checks. DEV is reused development evidence, not an estimate of general accuracy or an independent test of the previous candidate.

## New-source manual-crop evaluation

| HOLDOUT: 12 lines / 144 characters | Unchanged production | Frozen candidate |
|---|---:|---:|
| Literal CER | 34.03% | 9.03% |
| Exact lines | 0/12 | 5/12 |
| Critical edits, including selected prose punctuation | 13 | 2 |
| Expression CER, five lines | 49.02% | 1.96% |
| Exact expressions | 0/5 | 4/5 |
| Expression critical digit/operator edits | 10 | 0 |
| Prose CER, seven lines | 25.81% | 12.90% |
| Exact prose | 0/7 | 1/7 |

One expression has an extra space inside its numeral; literal CER counts it even though the separate critical-character comparison ignores whitespace. Prose still confuses n/M, b/v, gh/ch, Vietnamese accents and punctuation. The two remaining critical edits on this HOLDOUT are an omitted comma and an inserted period in prose, rather than incorrect mathematical digits/operators. DEV still contains mathematical critical errors. The final gate fails because overall HOLDOUT CER exceeds 5% and critical edits remain. No model is installed. Twelve selected lines cannot establish a reliable overall recognition percentage. This HOLDOUT is now exposed and must not be called fresh in subsequent work.

## Complete batch draft recognition and crop diagnostic

Reused the original source-coordinate detector regions after validating current dependency provenance, image hashes, oriented dimensions and integer bounds. Created new private inference evidence without changing the original results or labels. The frozen candidate read **266/266 images, 6,164 regions, zero execution failures**: 5,248 nonempty drafts and 916 empty drafts. Regions can include headings, individual symbols and non-text marks; they are not necessarily complete clean lines. Nonempty draft counts do not measure accuracy.

Candidate inference uses its matching aspect policy and individual CNN/LSTM forwards without padded-image context. Raw scores are the mean peak probability at initial emitted nonblank CTC transitions; they are uncalibrated and differ from the production provider's score calculation. Do not compare those scores as correctness probabilities. Every draft remains explicitly unverified, not a reference label and ineligible for training. No equation correction, pseudo-label approval, cloud OCR call or production provider change occurs.

For a partial-reference geometry diagnostic, match the same 12 selected references one-to-one by descending IoU at threshold 0.5. **Six match**, three per page; unmatched references emit empty text and count as deletions. On these detected crops, production CER is 56.25% and candidate CER is **47.22%**, exact lines 1/12 → 2/12, critical edits 22 → 19. These are the same references as the manual comparison, not additional independent samples.

Visual review of the existing detector overlays confirms that page 970 groups the three top expressions into one broad band. Page 995 separates columns, but some tall pencil letters and descenders are clipped vertically. A failed IoU match does not mean the detector found no ink; a matched box also does not guarantee a clean crop. Partial annotations cannot measure whole-page precision/recall, and this diagnostic is not phone, camera, browser, API or tutoring-flow evidence. Geometry must improve alongside recognition.

## Verification and outcome

**51 tests passed** across the existing bounded trainer, resumable recognition and source-storage suites. They verify safeguards and synthetic forward/backward behavior, not recognition accuracy. Checked all 301 reviewed records through the real source/split/pixel validator, recomputed selection over all 30 epochs, verified candidate/vocabulary/trainer/manifest pairing, and confirmed replay/teacher targets and deferred HOLDOUT counts. Frozen DEV inference reproduces the selected DEV metrics exactly.

After full-batch inference, reverified all 266 original hashes; production checkpoint, vocabulary, provider, segmentation and protected earlier evidence remain unchanged. Verified all output model/source hashes, unverified eligibility flags and finite scores. Private models, photos, transcripts, crop sheets and helper scripts remain Git-ignored. Unrelated cloud/deployment work is preserved. No application/mobile code change, model promotion, paid resource, commit, push or deployment occurred in this phase.

Private evidence: `ai-training/datasets/drive_math/new2_20261011_266/training_followup/`. Candidate SHA-256: `4a4507024559b46fb76273b0ad21a730d36477d4f7ddffac4607648188549323`. Paired vocabulary SHA-256: `dc25d2de8fe00fb680b8a18c0abac8e4df0e4ec54aa71e5dcde1ec253814a9fd`. `decision.json` pins manifests, selection, final scores, batch summary, geometry diagnostic and test evidence. Drafts and CSV are under `candidate_drafts/`.

Remaining work: complete crop envelopes for pencil ascenders/descenders, separate adjacent mathematical fields without breaking fractions/tables, improve literal prose and critical symbols, and reserve a larger newly reviewed cohort with full-page annotations and documented writers before production promotion.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: continue the existing OCR review/training workflow using bounded changes and established validation.
  - Applied to: existing source loader, trainer, draft runner, scoped gates and tests; small private reproducibility helpers without new dependencies or a parallel production pipeline.
