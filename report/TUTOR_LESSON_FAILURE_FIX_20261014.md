# Tutor lesson failure fix — 2026-10-14

The garden problem was recognized correctly, but lesson creation returned 503.
Reproduction found content validation failures and reviewer confusion between
the intermediate share and the requested total. Provider availability is a
separate failure: subsequent live checks also returned Groq 429 and Gemini 503.

## Changes

- The generated draft separates initial teaching from private worked help;
  both are still checked before publishing a session. No prerecorded solution
  lookup was added.
- Prior fractions can supply their checked numerator/denominator in later
  formulas. Arbitrary/new operands and forward references remain rejected.
- Independent review receives resolved arithmetic and the claimed final step;
  its output schema limits a single-result problem to that step. It must still
  independently verify the original source, target, arithmetic, units and teaching.
- Repair feedback retains all bounded reviewer reasons. Internal logs record
  validation failures; API keys and source images are not logged by the new code.
- The initial action for a composite expression covers all its terms without
  publishing converted fractions or the computed answer.

## Validation

- 231 tests passed: guided lessons, primary lessons, fraction support and tutor
  transport/security checks.
- Fresh model planning and independent review succeeded for the garden problem:
  share `4/15`, final answer `60 cây`; the interaction reached `COMPLETE`.
- Restarted the owned local AI runtime and rebuilt/recreated the preview AI
  container behind the web. The container is healthy.
- A subsequent HTTP smoke request returned 503 because the primary provider
  returned 429 and the fallback returned 503. This is recorded separately from
  the successful generated-and-reviewed session; no quota key sweep was added.
- Final HTTP verification against the restarted runtime succeeded: lesson 200,
  both answer turns 200, status `COMPLETE`, conclusion `Đáp số: 60 cây.`. One
  invalid first draft was repaired and independently reviewed before publishing.
- Normalized SHA-256 of the lesson source matches between local and the running
  preview container: `1ede113322e22e93ffb2122a6a9fadca842507cc133c6367a070b6a7bfd45ac9`.
- No physical-device test, frontend redeployment, training, commit or push.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: fix shared backend behavior with existing validation and stdlib.
  - Applied to: lesson draft, exact dependencies, review schema and regression tests.
