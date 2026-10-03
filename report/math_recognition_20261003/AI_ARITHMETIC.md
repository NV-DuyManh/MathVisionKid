# Arithmetic runtime component — 2026-10-03

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal fixes to the existing recognition/parser/worker boundaries.
  - Applied to: AI callback contract, scope guards, real-model readiness, local launcher and focused regressions.

## Implemented

- The YOLO adapter preserves all detected digit rows. The parser rejects multiple operators or more than three digit rows, rather than silently grading the first exercise. `oneExerciseOnly=false` does not imply that multi-exercise grading exists; it returns `MULTIPLE_EXERCISES_UNSUPPORTED`.
- `allowedOperations` and operand `maxDigits` are enforced before validation. Supported limits are 1–6 digits per operand; addition may have one extra result digit. Invalid columns, subtraction below zero and unsupported limits abstain with a terminal reason. Original tokens are retained.
- Callbacks contain actual `recognizedTokens` plus `validation={isValid,diagnosisState,evidence}`. Ungraded results use `isValid=null`. Wrong-result evidence includes the original result token ID and normalized box when a token exists. Column zero is units, counted from the right.
- Validators scan the actual digit width, including an extra addition carry column. Student feedback continues to withhold the answer; teacher proposals remain advisory.
- A model is ready only after its checkpoint loads. The configured default artifact checksum is verified against the existing manifest. Image decoding uses EXIF orientation; decode/runtime failures are not presented as a successful out-of-scope inference. Private object filenames are no longer treated as fixture quality tags.
- `/ready` returns HTTP 503 unless Redis, the model and a responding `mathvision@...` worker are available. `/health` remains the API liveness endpoint. The launcher executes the worker probe from `ai/runtime`, verifies its project command before avoiding duplicate workers, and uses the Windows solo pool with concurrency one and a MathVision worker name. Diagnostics use the same worker identity.
- AI tests block live arithmetic task enqueue unless a test explicitly mocks it. Direct in-process task execution remains testable.

## Verification already completed

1. Parser/adapter/validators/fixture callbacks/real YOLO callbacks/model provenance/manifest/quality/OCR bridge group: **77 passed**, 7.36 seconds.
2. Job API/Celery/callback retry/private MinIO/resolver/row grouper/bridge/confidence/model preprocessing/readiness group: **77 passed**, 5.08 seconds. These sets overlap; their counts must not be added.
3. Final broker-isolation/API/boundary/readiness/callback-retry/Celery group: **23 passed**, 3.58 seconds.
4. PowerShell launcher parsed successfully with the native AST parser. Scoped `git diff --check` passed.

The existing private MinIO integration test uploaded its two known synthetic sample objects. API task enqueue and callbacks were mocked; no live arithmetic queue job was created by these tests. The root audit found six queued messages with no matching `ai_jobs` database row; their origin has not been established. No purge, reset, worker launch or runtime restart occurred in this component phase.

## Local real-weight inference probes

All inputs below are existing **synthetic test images**, using the real YOLO artifact whose manifest SHA begins `e78f8fa5`. They are not physical-device evidence or a general accuracy benchmark.

| Fixture under `ai/runtime/tests/fixtures/` | Actual result | Local pipeline time |
|---|---|---:|
| `synthetic_addition.jpg` | `45 + 27 = 72`, valid | 1507.60 ms, first inference in a fresh process |
| `synthetic_subtraction.jpg` | `52 - 18 = 34`, valid | 71.95 ms, warm |
| `synthetic_addition_incorrect.jpg` | uncertain recognition, no grade | 67.27 ms, warm |
| `synthetic_subtraction_incorrect.jpg` | `52 - 18 = 44`, invalid; tens column evidence | 71.00 ms, warm |
| `sample_input_synthetic.jpg` | uncertain recognition, no grade | 92.88 ms, warm |

The root subsequently loaded the updated backend/runtime and started the named worker. Live student API → worker → authenticated backend callback verification completed successfully; see `arithmetic-flow.json`. The six queued messages had no matching database jobs and were consumed normally; their callbacks returned 404 without retry. No queue purge or database reset was used. The browser also uploaded a cropped image through the public student flow and confirmed its uncertain token; see `browser-records.json` and `browser/arithmetic-confirmed-real.png`.

The final distinct 15-module arithmetic regression run passed **88 tests** in 7.22 seconds (`ai-current-tests.xml`). This supersedes the overlapping component groups as the reported count for this phase; it is not the entire AI repository suite.

## Boundaries

- The installed detection model recognizes digits, `+`, `-`, separator and carry-1 classes. The two differently named detection checkpoints have the same checksum; they are not two stronger models.
- This component supports one vertically arranged natural-number addition/subtraction. Multiplication, division, fractions, negative results and multi-exercise pages do not gain detector support from this change.
- The handwriting OCR bridge is diagnostic/shadow only. Its row text has no per-character detector boxes and has not been validated as a horizontal arithmetic detector; it remains disabled by the configured runtime. No silent CRNN replacement of YOLO tokens or training occurred.
- Worded solutions and `×`/`÷` calculations based on confirmed handwriting text belong to the separate word-solution evaluator contract, not to a claim that the YOLO model recognizes those operators.
- Recognition confidence derives from YOLO token scores; structure/diagnosis values retain existing policy heuristics. Diagnostics label that method; these values are not calibrated accuracy percentages.
