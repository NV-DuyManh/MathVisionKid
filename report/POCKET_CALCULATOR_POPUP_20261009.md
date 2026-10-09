# Unified pocket calculator popup — 2026-10-09

## Result

Replaced the three-mode full-screen calculator with one compact popup, following the owner's phone-calculator references. One expression display sits above a four-column, five-row keypad. Basic arithmetic, decimals, percent and a fraction key share the same surface. Parentheses and sign change are collapsed behind **Thêm**. There are no scientific-function pages or mode tabs.

The backdrop dims the current lesson. Close with ×, the backdrop or native Back. The parent route and lesson state remain mounted. History and explanations open only on request; quotient/remainder is an optional view of a completed division, rather than a separate calculator.

## Calculation behavior

- Complete bounded expression parser supports precedence, parentheses, signed numbers, fractions and postfix percent. It rejects unknown characters and incomplete expressions without evaluating code.
- Reuses the existing rational calculations and educational explanations. Decimal rendering uses integer long division with BigInt to keep small chained results exact. Safe intermediate arithmetic is validated, including cross-products before addition/subtraction.
- A slash entered with the fraction key groups a numerator/denominator into one operand; for example `6 ÷ 2/3 = 9`. Fraction results remain vertically rendered even when divided by another fraction.
- `%` has its literal mathematical meaning (divide by 100), documented explicitly. It does not use a context-dependent phone-calculator shortcut for percentage increases.
- Continuing after equals retains the prior exact expression rather than reparsing an arbitrarily rounded or oversized displayed result.
- Recent history remains 10 in-memory entries per parent screen. The calculator does not edit OCR, submit lesson answers or make AI calls.

## Validation

- Final full mobile run: **45 suites, 546 tests passed**, exit 0.
- TypeScript: `npx tsc --noEmit` passed, no diagnostics.
- `git diff --check` on this change passed (only the repository's LF/CRLF normalization warning).
- Actual browser keypad entry: `1+3 = 4`; `1/3+2/5 = 11/15`, stacked fractions on the same keypad.
- Actual browser division: `17÷5 = 3,4`; quotient/remainder view gives **Thương 3, dư 2**, with steps using 17, 5, 15 and 2.
- Browser history restored the fraction expression. Closing returned to the original division review with dividend 87, divisor 4, pupil quotient 21, rows `08` and `3`, and the review checkbox still unchecked.
- At **375×812**, the basic popup and all keypad rows fit without scrolling; bounds were x16–359.2, y116.4–695.6. At **812×375**, popup bounds were x206–606, y26.3–348.9, with scrollable content. Neither viewport had horizontal document overflow. Temporary viewport override reset afterward.

Browser source lesson text was an explicit fixture, not new OCR evidence. Physical phone Back/rotation, large native text sizes and screen-reader behavior remain to be checked; no physical-device evidence is claimed. Existing app artwork, theme and entry points were retained. No new dependencies, training, commit or push in this phase.

## Files and evidence

Implementation: `apps/student-mobile/src/features/calculator/PocketCalculator.tsx`, `calculate.ts`. Tests: calculator engine/screen suites and the existing tutor preservation test. Current usage guide: `docs/POCKET_CALCULATOR.md`.

Ignored local evidence: `infra/local-runtime/logs/calculator-popup-20261009/full-tests.txt`, `popup-basic.png`, `popup-fraction.png`, `popup-remainder.png`. Screenshots show the running app, not mockups.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: compact mobile popup and keypad redesign.
  - Applied to: existing theme, minimum 48px controls, visible focus, backdrop, explicit dismiss actions and portrait/landscape checks. Focus-state search matched modal controls; unrelated search results were not adopted.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native rendering and state management.
  - Applied to: event-driven result invalidation, derived displayed result, bounded history and preserving the parent lesson.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: simplify the calculator and reuse working arithmetic.
  - Applied to: replace mode pages with one shared popup; reuse MathText and calculation explanations; no new dependency or API; bounded parser and meaningful regression tests.

Expo SDK 57 documentation was inspected before editing: https://docs.expo.dev/versions/v57.0.0/ .
