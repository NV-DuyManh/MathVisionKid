# Math OCR reference expansion and durable training — 2026-10-13

The phase added **19 visually reviewed mathematical references** and completed a 12-epoch head experiment plus a separate 4-epoch recurrent/head experiment. Both candidates regress mathematical transcription on the unchanged DEV set and were rejected. Production weights were not replaced.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the bounded OCR trainer with focused data additions, memory limits and durable state.
  - Applied to: reference/cohort checks, private experimental wrappers, prediction batching, atomic epoch checkpoints and focused validation.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.20/skills/google-drive/SKILL.md`
  - Why selected: inspect the original Drive container metadata when the mounted Drive reader stalled.
  - Applied to: connected metadata lookup only; no sharing changes or connector materialization of original files. The owner's Drive-only storage instruction was preserved by reading original bytes into RAM.

## References and splits

- Added six comparison expressions and one decimal field from already-TRAIN pages 637 and 158, plus six arithmetic expressions and six numeric components from already-TRAIN pages 224, 226 and 271.
- Source bytes and exact final crops were visually reviewed in RAM. Original G: source SHA values were checked. Recorded source orientation was applied before checking crop coordinates/pixels.
- Ambiguous dots, writing over a digit, neighbouring ink and overlapping crop proposals were excluded. One final equality-sign crop was extended six pixels downward to preserve its lower stroke; the original reference file remains intact.
- The revised cohort stays **494 records: 394 TRAIN / 95 DEV / 5 reserved HOLDOUT**. Nineteen redundant TRAIN prose entries were removed only when an equivalent transcript from the same source remained.
- All prior non-prose TRAIN entries, all source groups, and all DEV/HOLDOUT records—including their order and fields—were preserved. An independent metadata audit verified all 19 new crop rectangles are in bounds, do not overlap another same-source reference, and use exclusively existing TRAIN sources.
- No OCR prediction became a reference. Student-written mathematical mistakes remain literal transcription. Original images/crops/archives were not restored locally.

## Experiments and results

Both start from the same unchanged private parent checkpoint/vocabulary, use aspect-preserving input, full literal transcripts, math-role weight 2 and prose KL anchor weight 1. CNN layers remain frozen. DEV predictions use the same 95 references/1,097 characters/432 critical symbols.

| DEV metric | Unchanged parent, same input | Expanded-data head | Expanded-data recurrent/head |
|---|---:|---:|---:|
| Completed epochs | — | 12 | 4 |
| Learning rate | — | 0.00001 | 0.000005 |
| Selected epoch | — | 1 | 1 |
| Character errors | 107 | 107 | 111 |
| Character error rate | 9.75% | 9.75% | 10.12% |
| Critical digit/operator errors | 30 | 32 | 32 |
| Exact transcripts | 53/95 | 52/95 | 51/95 |
| Critical-exact transcripts | 64/87 | 62/87 | 63/87 |

**Neither passes the frozen DEV limits or the role-specific regression checks.** More arithmetic examples in this small existing-source cohort did not demonstrate an improvement. No overall application accuracy is inferred from these development measurements.

An initial recurrent run was stopped after four epochs to reduce evaluation memory. A subsequent bounded 12-epoch run was interrupted at epoch eight without a final candidate/evaluation artifact. Those logs are preserved and neither interrupted run is counted as a completed experiment.

Because all eight observed epochs regressed, the final restarted recurrent experiment was deliberately limited to four epochs and declared as a **new experiment**, with its own frozen policy, trainer and output. It is not described as resuming the lost eight-epoch state. Repeated DEV exposure informed this budget and remains a limitation.

## Memory and interruption recovery

- Neural prediction is divided into batches of at most 16 while preserving source order and valid sequence lengths. This avoids evaluating the entire recurrent cohort in one large allocation.
- A real packed-BiLSTM check on 37 unequal-length synthetic sequences verified valid logits and greedy predictions match bulk evaluation. The actual unchanged-parent DEV metrics also stayed 107 character/30 critical errors in the final run.
- Atomic private state is now saved after every completed epoch: current model, Adam optimizer, best model/selection, complete history, Python/Torch RNG and frozen input/settings fingerprints.
- Resume rejects changed inputs, inconsistent epoch/history order, an invalid best-state decision or promotion/HOLDOUT flags. RNG is restored after feature preparation.
- A focused real-Adam serialization test verified the next update after restoring model, optimizer and both RNGs is identical. This test verifies state continuation; it is not a claim that every real training failure mode was simulated.
- The final training job ran as a hidden background process with a status file. It reports completion only after verifying candidate/vocabulary/evaluation artifacts and all four epochs. A saved partial training state alone is never marked complete.
- Final receipts contain 73 hash-verified reads of 69 unique original page sources per experiment, zero retries, unchanged input fingerprints, no local source-image writes and no HOLDOUT neural inference.

## Recognition progress

The **2026-10-13 09:44:43 UTC** reconciliation verifies that all selected, non-reserved sources have completed recognition. Successful retries supersede prior execution failures without deleting the historical receipts:

| Group | Recognized draft sources | Unresolved executions | Reserved |
|---|---:|---:|---:|
| Original pages | 1,580/1,581 | 0 | 1 |
| Supplied ZIP crops | 2,975/2,975 | 0 | 0 |
| Screened Parquet candidates | 2,295/2,295 | 0 | 0 |

There are **42,679 draft lines**, including 3,795 empty predictions, 3,166 width-cap flags and 12,828 layout-review flags. Flags may overlap; they are not verified error counts. All drafts remain unverified and ineligible for training. Zero unresolved executions means source processing finished; it does not mean the transcriptions are correct.

The metadata inventory contains **64,803 sources** (1,581 pages, 2,975 ZIP crops and 60,247 Parquet lines). This phase processed all pages/ZIP crops and the union of **2,295 screened Parquet math candidates**: 6,850 recognized sources plus one reserved page. The unverified keyword/expression screening can miss mathematics in the remaining Parquet lines. This is not a claim that all 64,803 sources were recognized or that all mathematical content was found.

The remaining page and ZIP reads completed through bounded mounted-source retries. For the 1,234 stalled Parquet candidates, a focused private reader fetched six frozen original containers directly from Google Drive into RAM. Every full-container SHA and individual source-image SHA matched before inference. No original archive/image/crop was saved locally, no Drive sharing was changed, and no paid or cloud inference service was called.

The HTTP reader bounds each original container to 256 MiB and checks the Drive confirmation form, file ID, binary completeness and full SHA. This limit applies to archive bytes, not total process memory or decoded row groups. HTTP timeouts apply per connection/read, not to the total transfer duration; automatic redirects occur before the final destination-host check. These limits do not invalidate the current hash-verified outputs. Offline mocked tests verified identity, checksum, binary, destination-host and size rejection paths.

## Recovery of previously excluded controls

The separate RAM-only recovery completed **18/18 controls: 12 TRAIN and six DEV**, across eight frozen original Parquet containers. An independent read-only audit verified the exact planned IDs, archive/source/pixel hashes, crop bounds, reader/plan fingerprints, unchanged labels and zero failed results. Four controls retain historical `review_split: HOLDOUT` metadata after their previously exposed labels were moved into TRAIN; they are not independent holdout evidence. No source from the current five-field reserved set was accessed.

Recovery performed **no neural inference or training** and saved no original source files. It establishes that these sources and crop pixels can be read again. Both completed candidates still used the declared 494-record cohort, excluding these 18 controls. Their rejection metrics remain unchanged; no full-cohort reevaluation or model promotion is claimed. The earlier mounted-read receipt (1/18 recovered) remains historical evidence and is superseded for availability by the completed HTTP recovery receipt.

## Validation and remaining limits

- Reference hashes, cohort hashes, unchanged validation records, source-group/SHA split separation and rectangle checks passed.
- Weighted objective, bounded prediction equivalence and optimizer/RNG continuation checks passed.
- Final artifact decisions verified candidate/vocabulary hashes, frozen manifest/trainer policy, source-read receipts, unchanged-parent metrics and false promotion flags.
- Independent read-only audits verified the final recurrent candidate equals its recorded best state, the four-epoch history/selection and optimizer/RNG state are present, and all 1,234 direct-read candidate mappings and hashes match the frozen source plan.
- Recognition reconciliation verified every selection/provenance/code/model fingerprint, unverified-label flags, zero cloud inference calls, unchanged production hashes and continued absence of local original-image/archive files and the owner's deleted source folders.
- Production checkpoint/vocabulary remain `a807eaa7…` / `6af4062e…`. Draft recognition uses the earlier private parent pair `4903062b…` / `dc25d2de…`, never either rejected new candidate.
- Writer/pretraining independence remains unknown. New labels are from existing TRAIN sources, DEV has been repeatedly used, and the reserved set is five fields from one page. Manual crops do not establish automatic segmentation or 2-D fraction/long-division accuracy.
- No physical-device evidence, deployment, commit or push was generated in this phase.

## Evidence

Private root: `ai-training/datasets/drive_math/math_all_20261013/expanded_math_review/`.

- `comparison_references.json`, `arithmetic_references.json`, `arithmetic_parent_references.json`: frozen reviewed references and the preserved crop refinement.
- `parent_comparison_review.json`, `parent_arithmetic_review.json`, `cohort_receipt.json`, `reviewed_manifest.json`: parent review and exact cohort changes.
- `run_weighted/evaluation.json`, `run_recurrent_resilient/evaluation.json`, `comparison_decision.json`: completed candidates and rejection evidence.
- `train_recurrent_bulk_evaluation_interrupted.log`, `train_recurrent_bounded.log`, `restart_receipt.json`: preserved interrupted work, without completion claims.
- `trainer_math_resilient.py`, `acceptance_policy_resilient.json`, `run_recurrent_resilient_training_state.pth`, `resilient_job_status.json`: durable state, frozen policy and verified completion.
- `read_receipt_weighted.json`, `read_receipt_recurrent_resilient.json`: mounted-source reads and immutable input pins.
- `../recognition_progress.json`, `../recognition_failed_sources.json`: latest source coverage and explicit unresolved sources.
- `../drive_http_ram.py`, `../test_drive_http_ram.py`, `../http_archive_plan.json`, `../bounded_runs/parquet_http_retry/recognition/`: RAM-only original-container reader, offline checks, frozen identities and completed direct-read recognition evidence.
- `../http_control_recovery_plan.json`, `../recover_http_controls.py`, `../http_control_recovery_receipt.json`: frozen 18-control recovery plan and complete source/crop verification without inference.

Next quality work requires more diverse, source-reviewed mathematical examples and independent evaluation. These same epochs should not be extended merely to produce a new checkpoint. The new candidates remain rejected even when source availability is restored; their measured regressions are unchanged.
