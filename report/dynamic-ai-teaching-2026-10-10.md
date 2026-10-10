# Dynamic AI lesson planning — implementation and release hold

Date: 2026-10-10. Owner request: new problems must receive a newly reasoned, detailed lesson, rather than a stored problem-family solution. Each classroom solution line needs an explanation of the quantity, the operation and the order, plus small calculation actions and a proper written solution sentence.

## Status

Later release work is recorded in [dynamic tutoring deployment and verification](dynamic-tutoring-release-2026-10-10.md). The status below is the original implementation-phase hold, not the current deployment record.

**The new planning path is implemented in the working tree. It is not released.** The current website still uses the previously deployed AI image. Real provider calls have not met the quality/availability requirement needed to replace that image.

Follow-up: [photo tutoring, exact fraction-work checks and teaching review](photo-tutoring-fraction-review-2026-10-10.md) records the later implementation and validation. Planning now uses JSON mode with full local validation, lesson calls explicitly opt into bounded reasoning, and review guidance is deduplicated. The strict planning-mode description below is historical. Release remains held.

The production source no longer selects `primary_plan`, `fraction_garden_plan` or `trapezoid_plan`. Every lesson start sends the confirmed source to the configured model, validates its new plan, and requests a separate semantic review before publishing a session. Provider failure, unclear input, invalid calculations or rejected teaching do not produce a canned lesson.

This change applies to planning and tutoring. It does not train or replace the owner's OCR model, change OCR transcription evidence, or treat an image identifier as an answer lookup.

## Implemented behavior

- Preserve the confirmed original problem and its actual requested goal. Distinguish given operands from additional mathematical constants. Pupil work remains untrusted supporting material; excerpts must match the supplied work exactly.
- Ask for primary-school explanations of **why this quantity**, **why this operation**, **why this order**, and **how to calculate**. Require substantive guidance, two hints, and a classroom solution sentence for every calculation. Algebraic manipulation and rewriting source numbers as artificial sums of constants are explicitly disallowed in teaching.
- Use a structured plan envelope and constrained JSON output on documented compatible Groq models. Other configured providers retain their existing JSON mode; local validation is still mandatory. Structured output guarantees structure, not mathematical or pedagogical truth.
- Evaluate only bounded basic arithmetic with exact fractions, using an AST allowlist. No `eval`, code, functions or powers are accepted. Literal inputs must come from the confirmed source or justified mathematical conventions. A prior calculated literal can be normalized to an exact prior-step dependency; new operands remain rejected.
- Independently request the actual results asked for, check their exact values and units against the plan, and verify the conclusion points to the requested quantity rather than a verification result. This is another model call, not a mathematical proof.
- Keep the current worked calculation private initially. First help stays at the starting action; a second explicit help request can open the current worked explanation. Completed steps retain their explanation and written solution. Future answers, unchecked references and computed values in the always-visible outline are blocked.
- A wrong pupil answer stays on the current step. Exact equivalent fractions are accepted; rounded decimals are not treated as exact fractions. Existing account ownership, revision checks, expiry and bounded session storage remain.
- Permit one bounded content rewrite after invalid/rejected output. Private repair feedback is sent as data, never inserted into trusted instructions. A failed rewrite publishes no session. The entire start operation has a deadline shorter than the existing backend/client deadlines.
- Disable and skip invalid credentials with a small bound. Quota, timeout and provider failures do not sweep credentials or initiate content repair. No model/provider setting or credential file has been changed by the experiments.
- Block developer/provider details and account emails in generated student-facing teaching. No frontend or backend authentication change was needed.

## Automated validation

From `ai/runtime`:

```text
.venv/Scripts/python.exe -m pytest tests/test_primary_lessons.py tests/test_guided_lesson.py tests/test_fraction_lesson_support.py tests/test_math_tutor.py -q --tb=short
```

**185 passed.** These checks cover unchanged confirmed source delivery for different lesson families and goals, exact fraction arithmetic, ownership/replay behavior, unsupported expressions, source grounding, failed semantic reviews, result/unit mismatch, bounded repair and deadlines, progressive disclosure, future-answer protection, structured output transport, and credential/quota behavior.

The test-only candidates in `tests/_lesson_test_data.py` are provider fixtures for contract/session tests. They are not imported by production, and these tests are **not an OCR accuracy percentage or a score for the model's teaching quality**.

A full runtime regression run also completed earlier in the iteration: **1480 passed, 21 skipped**. A later full run completed with **1481 passed, 22 skipped, 4 pre-existing FastAPI lifecycle deprecation warnings**. The final outline/detail guards were added after that full run and are covered by the latest 185-test focused run above. Scoped `git diff --check` passed; Windows line-ending notices were informational.

## Real-provider evidence and remaining failure

Live tests used manually confirmed, readable source text, not image lookup. Teacher-expected numerical results existed only in the ignored local evaluation harness. Examples included equal groups followed by subtraction, sharing then addition, a fraction word problem, appending a digit, and a changed sum/difference goal asking for the product.

- An intermediate configured-provider run completed the garden problem with exact `4/15` and `60`, using two solution lines with five teaching paragraphs each. This does not qualify the final implementation for release.
- Another intermediate test using a temporary process-only model override completed the groups problem numerically, but its review/repair exposed a misunderstanding of the source-number/constant distinction. That wording has been corrected; the run is not accepted as evidence of consistently good teaching.
- The five-case configured-provider batches were unreliable: quota responses, invalid credentials, provider failures, malformed responses, an unnecessary refusal on the solvable append-digit problem, and insufficient/unsuitable teaching prevented publication.
- A process-only test of a different Gemini model also failed through authentication/response availability. No production model configuration was changed.

Private traces are kept under ignored `infra/local-runtime/pc-preview/`. They contain draft answer material and are intentionally excluded from the repository. No credential values are in this report.

**Release remains held.** A successful model-generated plan plus an approving model review is necessary, but not sufficient evidence that unfamiliar problems will always be explained correctly. The final path still needs successful real-provider testing across varied requested goals and human inspection of the explanations, including the append-digit problem. The local guards cannot fully understand natural-language meanings or guarantee that spelled-out answers never leak; semantic review carries that remaining responsibility.

No new image build, runtime restart, Vercel deployment, commit, push, model training, purchase, or physical-device validation was performed in this phase. The prior deployed lesson remains available while this replacement is being evaluated.

## Documentation consulted

- [Expo SDK 57 documentation](https://docs.expo.dev/versions/v57.0.0/) — required versioned project reference, read before edits.
- [Groq structured outputs](https://console.groq.com/docs/structured-outputs) — supported strict-schema models and required object fields.
- [Gemini structured output documentation](https://ai.google.dev/gemini-api/docs/structured-output) — reviewed while investigating provider response structure; Gemini transport remains on its existing JSON mode in this change.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: replace a growing set of problem-specific branches with the existing model transport and a single validated lesson path.
  - Applied to: template deletion, exact-arithmetic/session reuse, bounded generation/review/repair, transport changes and focused regression checks. No dependency or parallel worker was introduced.
