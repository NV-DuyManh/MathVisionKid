# Progressive hints for repairing written division — 2026-10-09

## Outcome

Pupils can request two increasingly concrete hints at the first incorrect quotient digit or compact calculation row. The first hint explains the operation; the second explains how to choose the digit or bring down the next original dividend digit. Hints use the submitted operands and confirmed written quotient, and never replace the pupil's transcription or fill an answer.

Editing any field clears old feedback and revealed hints, cancels an outstanding check, and requires confirmation before checking again. The two hints are supplied in the existing check response; opening them makes no additional network request. Small screens wrap operand fields and row controls.

## Validation

- Full Spring test suite: **261 tests, zero failures/errors/skips** across 27 suites.
- Full Student Mobile Jest suite: **43 suites, 467 tests passed**.
- TypeScript: `npx tsc --noEmit` passed.
- `git diff --check` passed; Git emitted existing LF/CRLF conversion notices.
- Backend tests cover differing operand widths, an internal zero in the quotient, incorrect quotient digits, intermediate rows and final remainders. They also verify that unread/unsupported layouts receive review rather than calculation hints, and that the original written values remain unchanged.
- Controller tests exercise the real checker through the authenticated endpoint, retain anonymous/teacher restrictions, and verify the serialized hints and the repaired response.
- Client tests reject malformed hints and hints attached to a successful or unreadable result. UI tests verify progressive disclosure, no answer substitution or extra request, and reset after editing.

## Running application verification

Only the verified project API listener was restarted after the tests. The updated service started successfully on 8080; existing image service and mobile bundler were preserved.

The browser opened a **manually entered test**, not an OCR result: `87 : 4`, written quotient `21`, rows `08`, `3`.

1. Checking remained disabled until source confirmation.
2. The live API identified row 1 and returned two hints: multiply `2 × 4` and subtract from `8`; then bring down `7`, represented as `(8 − 2 × 4) × 10 + 7`.
3. Opening both hints left the entered row `08` unchanged.
4. Manually changing the row to `07` cleared both hints and confirmation.
5. Confirming and checking again returned the success message with final remainder `3`.
6. Browser viewports 375 × 812 and 812 × 375 had document width equal to viewport width, with visible controls and wrapped hint text. The temporary viewport override was reset.

Private evidence is under `infra/local-runtime/logs/division-hints-20261009/`; full Java and mobile test logs are sibling files named `division-hints-20261009-*-full.txt`. Screenshots include `division-hints-portrait.png`, `division-hints-landscape.png` and `division-repaired-portrait.png`.

## Limits

This checker handles compact primary-school division rows (brought-down numbers followed by the final remainder). Separate product/subtraction layouts still require review. This phase does not change OCR weights, train a model, call cloud OCR, or establish an OCR accuracy percentage. Browser verification is not physical-device evidence; native keyboard and screen-reader behavior still need a phone check. No commit or push was performed in this phase.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded backend and client implementation without new dependencies.
  - Applied to: extending the existing response and checker, preserving backwards compatibility and existing safeguards.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: actionable pupil-facing feedback and responsive controls.
  - Applied to: progressive hints beside feedback, wrapping fields, retained accessible labels and 48-point actions.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React state and rendering behavior.
  - Applied to: deriving hints from the current result, keeping only the revealed count in state, and clearing stale feedback on edits.

The exact Expo SDK 57 versioned documentation was read before implementation: https://docs.expo.dev/versions/v57.0.0/.
