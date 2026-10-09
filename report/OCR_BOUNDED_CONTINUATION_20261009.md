# Bounded OCR continuation and worked-material guard — 2026-10-09

## Outcome

Continued the existing owner-authorized Drive reading queue for **10 new successful responses**. Added an actual cloud-invocation limit, corrected misleading model capability diagnostics, and repaired a source-observed case where a worked solution was treated as an original question. No OCR weights were changed, no labels promoted and no training performed.

## Changes

- `drive_line_batch.py cloud --limit N` now bounds new successful reads for this invocation. Existing immutable successes are counted/hash-checked but do not consume that budget. Later pending sources are not fetched after the limit. The summary records `new_reads`, `max_new_reads` and `batch_limit`. Existing provider backoff still wins; failures stop immediately. Exit 2 correctly means the overall queue remains incomplete.
- Groq catalog membership no longer sets `vision_capable=true`; capability remains unknown (`null`). A text ping is identified as `probeKind=text` and does not establish image support. Untrusted error codes are allowlisted before returning/logging them, preventing a provider error field from echoing credentials. Catalog HTTP status and actual text-probe metadata are recorded distinctly.
- Notebook reading now rejects completed numeric work and “Bài giải” as an original question when no task is visible. It retains all transcribed lines and numbers and asks for the original problem. Descriptive phrases “phép tính”, “cách tính”, “muốn tìm” do not count as a request. Actual questions, variable equations and blank-box tasks are retained.

## Actual reading evidence

| Measure | Count |
|---|---:|
| Source inventory | 1,319 |
| Earlier immutable responses outside parent queue | 256 |
| Parent queue saved before this phase | 28 |
| New responses | 10 |
| Total saved responses | 294 |
| Remaining sources | 1,025 |
| New responses with transcribed content | 3 |
| New MULTIPLE / UNREADABLE responses without rows | 6 / 1 |
| Approved new training references | 0 |

The parent queue ended with `batch_limit`, not a provider outage. Ten saved responses are not ten completely recognized images. Three content-bearing responses contain 24 predicted rows total; these rows are not independently verified references.

Two originals were viewed directly at their verified mounted G paths, without bulk downloading original images. In Lớp 5/IMG/20.jpg, only worked solution material is present; the saved provider response wrongly labels it PROBLEM and merges the final prose across physical rows. A separate replay of that exact saved response through the repaired guard changes interpretation to WORK, leaves line text unchanged, and keeps the original response file byte-for-byte. This is a control-flow comparison, not another provider inference or OCR accuracy measurement. In NEW2/IMG/20.jpg, the first blue operand needs numeral review and explanatory prose spans physical rows; its prediction is not approved for training.

The guard changed the reader fingerprint. A new selection `all_current_20261007/cloud_workguard1025_20261009` contains only the 1,025 pending IDs, with a provenance plan; the old queue and successful responses remain immutable. New reader signature: `d82d569e84ea0989b59cf00b1e1efe5030101d9d1a11eb00df19ad2fa5a6abd0`. Resume instructions were updated in `docs/OCR_REVIEW_AND_TRAINING.md`.

## Validation and runtime

- **185 tests passed** across notebook reading/layout/capacity, guided lessons, validator failures, source storage, cloud queue and training-gate safety. Two existing framework deprecation warnings remain.
- Coverage includes unknown vision capability from catalog/text evidence; sanitizing arbitrary/string/object error codes; bounded resumption without re-requesting successful sources; missing-source fetch avoidance after the limit; preserved wrong written arithmetic; actual questions retained; and rejected invalid batch limits.
- `git diff --check` passed, with normal repository LF/CRLF notices.
- Restarted only the listener whose executable/command confirmed this project’s AI runtime, retaining its existing loopback binding. Other services and mobile bundler were preserved. Runtime verification receipt is stored separately in ignored local evidence.

Local evidence: `infra/local-runtime/logs/ocr-continuation-bounded-20261009/cloud-run.txt`, `regression.txt`, `work-guard-comparison.json`. Original images stay in the mounted Drive source mapping. Accuracy percentage, full physical-row correctness, training promotion, physical phone checks and completion of all pending pages are **not** claimed. No commit or push in this phase.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded backend/queue fixes using the existing workflow.
  - Applied to: one shared notebook guard, existing resumable cloud loop, small diagnostic correction and focused regression checks; no new dependencies or training abstractions.

Google Drive file guidance was read for preserving existing source organization; mounted source paths and content hashes remain authoritative. This phase did not change Drive ownership or sharing.
