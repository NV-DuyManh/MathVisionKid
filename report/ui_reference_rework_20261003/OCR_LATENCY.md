# OCR interactive latency repair — 2026-10-03

The multiline review now returns segmentation and the unchanged CRNN result before waiting for cloud spelling advice. Saving a trial still runs the existing Groq/Gemini document advisors afterward. No model, weights, training, segmentation thresholds, privacy confirmation, ownership or RBAC rules were changed.

## Evidence and cause

The owner's saved 12-line request `req_fh5s4b5m_mur6xe59` spent 30.65 seconds overall, including 27.37 seconds waiting for line advisors. The backend previously waited for this advice during detection and then ran document advisors again after submission. External provider failover and latency therefore delayed the first useful screen.

The existing AI `X-Fast-Path` option already skips only the per-line post-advice stage. It retains CV segmentation, conditional Groq segmentation assistance, and batch CRNN recognition. The backend now enables it for interactive multiline detection. Advisor status and confidence stay null until actual results arrive.

## Measured timings

All measurements use identical 253,206-byte image input, SHA-256 `5586280c8865ca1cf52fb399984632f3ba157ec87f58278de7b3891c37f79fbe`. Every detection forces segmentation, returns 12 lines and reports `cacheHit=false`.

| Actual HTTP run | Seconds | Provider advice during detection |
| --- | ---: | --- |
| Ordinary, first CRNN request after runtime startup | 25.461 | 19.94 seconds of advisor waiting |
| Fast path, warmed CRNN | 5.754 | Deferred |
| Fast path, warmed CRNN repeat | 6.627 | Deferred |
| Ordinary, warmed CRNN and cached successful advice | 7.244 | 11 milliseconds; no new key attempts |
| Public backend detection after builds completed | 4.900 | Deferred |
| Public backend trial save | 1.320 | Deferred |

The first internal measurements overlapped backend builds/tests. These are observations, not a uniform device benchmark or a universal speed guarantee. Detection cache and advisor cache are separate: the warmed ordinary request reused successful cloud advice despite `cacheHit=false` for segmentation.

The public flow made the detected page and saved trial available in approximately 6.22 seconds. Background advice then settled 32.88 seconds after the first read: Groq succeeded for 9 lines and reported unavailable for 3; Gemini succeeded for all 12 after a timeout and fallback. That later work is not counted as finished when the initial result appears.

## Quality and feedback safety

For this image, the ordinary and fast paths returned exactly equal box coordinates, line order, raw CRNN text, measured confidence and confidence provenance. Their initial final text was also equal. The real public flow matched the same core fields.

The existing background arbitration applied six safe corrections to unverified lines and retained raw OCR. Of the six successful per-line suggestions from the ordinary run, four Groq suggestions and all six Gemini suggestions matched later document suggestions. This confirms that the later providers still contribute; it does not establish universal accuracy equivalence between provider prompts.

Background work now starts after successful transaction commit rather than guessing with a 500-millisecond sleep. Provider network requests run outside database transactions. A short transaction reloads lines under the same row lock used by feedback before writing advice, and automatic final-text changes require `UNVERIFIED`. This prevents delayed advice from merging stale student corrections.

A real HTTP correction was submitted while the providers were waiting. After advice completed, the exact human text including surrounding whitespace, normalized text, verdict, raw OCR and predicted text were preserved. The verification trial is test data and remains ineligible for training. Its stored image hash exactly matches the uploaded bytes.

If background HTTP or storage access fails, or the batch response is unusable, remaining pending providers now finish as `UNAVAILABLE`. A short locked reload updates only pending provider fields, retains successful advice, and preserves student text and feedback. This prevents permanently null provider status after an exception. Failure-state persistence errors are logged separately if the database itself cannot be reached.

## Validation

- Final full backend H2 test profile: 164 tests across 22 suites, zero failures, errors or skips.
- Final targeted backend phase: 30 tests passed, including commit/rollback scheduling, four feedback verdicts during provider waiting, and four terminal-failure scenarios.
- HTTP timeout, storage exception, bad HTTP response and invalid batch count regressions confirm that only pending provider fields become unavailable; settled successful advice and exact human feedback survive.
- Two AI contract tests passed: fast-path core OCR, optional Groq segmentation assist, and truthful pending advisor fields.
- Real public HTTP: detection 200, creation 201, feedback 200, subsequent read 200, then actual background provider updates.
- MathVision backend and AI runtime remain healthy, with verified project paths and database health. Docker volumes, stored records and applied migrations were preserved.

Evidence: [ocr-latency.json](ocr-latency.json), [backend-tests.json](backend-tests.json), [runtime.json](runtime.json), [terminal-failure-guard.json](terminal-failure-guard.json). Private input and full OCR bodies remain in ignored `scratch/ocr_latency_20261003/`; no tokens or API keys are included in these reports.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Backend/API latency repair and minimal reuse of existing pipeline behavior.
  - Applied to: Existing fast-path header, native transaction commit scheduling, shared feedback row locking and a pending-only terminal failure guard; no new dependency or model pipeline.

Versioned Expo documentation was read at <https://docs.expo.dev/versions/v57.0.0/> as required by project instructions; this component changes no mobile source.
