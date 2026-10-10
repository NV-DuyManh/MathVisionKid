# Photo-based math tutoring — exact work checks and teaching review

Date: 2026-10-10. Owner request: continue recognizing photographed problems and teaching pupils how to solve them, with explanations they can understand.

## Status

Follow-up: [dynamic tutoring deployment and verification](dynamic-tutoring-release-2026-10-10.md) records the later release work. The hold and test counts below describe this earlier phase.

The working-tree implementation has been improved and the focused checks pass. **The replacement dynamic planner is still not released to the website.** Final real-provider runs cannot yet establish reliable, acceptable teaching: requests encounter rate limits, timeouts, unavailable fallback credentials, or rejected lesson content. A refused/unreviewed draft does not open a pupil lesson.

No production rebuild/restart, deployment, commit, push, model training, new subscription, or physical-device test was performed in this phase. This report concerns the photo-tutoring path; it is not a measured accuracy improvement for the owner's trained OCR model.

## Corrected fraction-work grading

The old image-work check read only a decimal/integer on the right side of an equality. For example, a faithfully transcribed `1/3 + 2/5 = 11/15` could be interpreted as a result of `11` and incorrectly reported as wrong.

The check now uses the existing bounded exact-fraction arithmetic for complete numeric equality rows. It checks every term in a chain of equalities, including parenthesized fractions, and preserves numerical units separately. Thus a chain containing a wrong intermediate equality is not accepted simply because its last number is correct. A mathematically consistent row whose result differs from the current requested quantity receives different feedback.

Textual trailing unit labels may be removed for arithmetic checking; this does not certify the physical unit or sentence meaning. Malformed/unsupported rows are left ungraded rather than interpreting a partial numerator. This automatic feedback runs only after the pupil independently answers the current lesson step correctly. It does not alter any photographed digit or create replacement source data.

Six regression examples cover correct fractions, parenthesized equality chains, wrong intermediate/final fractions, a correct calculation for a different quantity, and malformed partial results. The initial regression run had six failures overall, including the false-refusal checks; those failures were corrected.

## Planning and teaching changes

- Correct a false rejection in the student-text filter: accent folding turned `lần` into the technical acronym `LAN`, and also rejected the pupil names `Lan`/`Lân` and `hoa lan`. Match the network acronym/context separately; keep blocking actual technical details and account addresses. Three previously failing Vietnamese-language regressions now pass, alongside technical-term rejection checks.
- Normalize a provider's blank-line-separated guidance string into a paragraph list without changing its words, dropping paragraphs, or weakening the answer/length checks. Live output exposed this purely structural failure before meaningful teaching checks could run.
- Generate a fresh JSON lesson from the confirmed original source, then validate it locally and independently review its mathematical meaning, requested results, units and teaching. Stop preferring the nullable strict-schema envelope during planning: live comparisons found unnecessary refusals on solvable sources. The reviewer retains its constrained response schema on supported models.
- Allow one bounded reconsideration of an explicit `lesson:null`, using the unchanged confirmed source. A truly insufficient problem can still be refused. Transport/quota failures still do not trigger a credential sweep or an unreviewed lesson fallback.
- Opt into bounded, hidden reasoning for lesson planning and semantic review on documented supported Groq models. Qwen's omitted effort setting defaults to non-thinking. The final implementation uses low effort to limit the reasoning/output budget. Faithful photo reading keeps its existing transport settings and its explicit instruction not to solve or correct visible work.
- Require substantive initial teaching before worked help: the quantity, why the operation/order is needed, and an actionable starting task. The prompt requests three initial paragraphs; local validation requires at least two totaling 180 characters, alongside the existing three-to-six total guidance paragraphs, 240-character total, two hints and proper classroom solution sentence. Paragraph counts alone do not establish teaching quality; the semantic reviewer must also check meaning.
- Explain fractions through equal parts and the quantities those parts represent. Merely quoting reciprocal/common-denominator rules is insufficient. Explicitly reject confusing fractions with percentages when the source gives no percentage.
- Report the particular inadequate step in private repair feedback. Remove duplicated guidance from the review request: all resolved paragraphs are sent exactly as initial teaching or private worked teaching. No teaching is omitted from the review.

Current worked calculations remain private until deeper help or completion. Future answers, fabricated work excerpts, unsupported expressions, unchecked references, wrong units/results and owner/revision mismatches remain guarded. No production problem-family answer lookup was introduced.

## Automated validation

From `ai/runtime`:

```text
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_primary_lessons.py tests/test_guided_lesson.py tests/test_fraction_lesson_support.py tests/test_math_tutor.py tests/test_notebook_tutor.py tests/test_notebook_row_panels.py -q --tb=short
```

**304 passed** on the final focused implementation. These include exact work comparisons, refusal/repair limits, unchanged source delivery, current/future answer separation, owner/replay behavior, result/unit checks, explicit reasoning opt-in, photo-reading isolation, fallback compatibility, Vietnamese names/vocabulary and paragraph normalization without losing answer guards.

The final complete `tests/` run passed **1524 tests, with 7 skipped and 4 dependency/lifecycle deprecation warnings**, in 220.29 seconds. This includes all final code changes above. Scoped `git diff --check` passed. Intermediate complete runs passed 1513 and 1516 tests. Calling pytest without a `tests/` path also discovered unrelated local scripts and failed during stdout-capture cleanup before tests ran; that command is not counted as a successful regression run.

Test-only provider fixtures verify contracts and guards. They do not measure OCR accuracy or prove the model's explanations are always correct.

## Real-provider and photo evidence

Private live traces are in the ignored local evaluation directory. Expected numerical answers belong only to the evaluation harness; production receives no teacher answer or image-answer mapping.

- The configured non-thinking provider initially completed the equal-groups/subtraction source, but refused the sharing, garden, append-digit and changed-target sources in the strict planning mode.
- In an intermediate JSON-mode comparison, sharing completed with `21` and garden completed with `60`. Human inspection found that the garden's teaching still relied too much on rules and used misleading percentage wording. The final teaching checks were strengthened afterwards; these intermediate passes are not final release evidence.
- Explicit low reasoning produced new candidate plans for append-digit and sum/difference-to-product sources. They were not published: the subsequent required stage encountered quota/fallback failures. A medium-effort trial also encountered a provider bad request; a small separate compatibility probe successfully returned ordinary JSON with hidden reasoning. No provider/model credential file was changed.
- A temporary process-only GPT-OSS model trial produced unsuitable algebra, invalid expressions/fields or repeated bad content. Local validation rejected those drafts. It was not adopted as the configured model.
- The supplied whiteboard screenshot was read as a single original question, retaining the visible digit `6` and difference `537`. Returned rows remained uncertain when independent verification did not complete. The supplied garden photo's probe failed through provider availability; it is not counted as a successful reading or an end-to-end lesson.
- A final reread of the garden photo also ended with provider unavailability (fallback server error). No transcript or lesson was fabricated for that failure.
- Configured append-digit trials encountered rate limit/timeout/fallback-auth failures, including one that ended at the existing overall deadline. A later available-provider run produced two drafts but still did not publish a lesson: paragraph shape, premature example answers, insufficient initial guidance and the inappropriate use of 'hạ' for subtraction were exposed. The paragraph-format compatibility and Vietnamese filter fixes followed this inspection; they do not certify that these draft explanations are good. Repeated credential attempts or repeated unattended provider polling were not used to bypass the limit.

**Remaining release work:** complete a varied, successful real-provider batch on the final implementation and inspect the actual initial/deep-help explanations, including fraction meaning, division actions and changed requested goals. These calls need an available configured provider. The website has not received this replacement and must not be described as already using it.

## References

- [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) — required project reference, read before implementation.
- [Groq API reference](https://console.groq.com/docs/api-reference) and [Qwen model documentation](https://console.groq.com/docs/model/qwen/qwen3.8-27b) — supported effort settings, non-thinking default and JSON-compatible hidden reasoning.
- [Groq reasoning documentation](https://console.groq.com/docs/reasoning) — bounded reasoning settings and response format.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: correct the existing arithmetic/lesson path with small changes rather than adding lesson-family templates, dependencies or another solver.
  - Applied to: reuse of exact Fraction/AST calculation, bounded refusal reconsideration, provider transport options, review payload deduplication and regression tests.
