# Student fraction guidance and startup illustrations — 2026-10-08

## Outcome

The math guide now displays numeric fractions vertically, provides progressive help at every step, accepts exact fractional answers, and separates feedback for a completed step from the next unanswered step. Startup waits for the main illustrations to be decoded before mounting the application screens.

## Teaching and arithmetic

- The supplied garden problem is broken into six small actions: choose a common denominator, convert each given fraction, find the remaining parts, find the quantity in one part, and find the whole quantity. Explanations distinguish the whole garden from one equal part.
- The supported plan is constructed from the confirmed problem text and quantities. It uses no screenshot identity or fixed answer. Regression cases vary the fractions and counts and produce totals of 60, 48 and 63. Contradictory quantities, different targets and extra questions do not use this plan.
- Each supported step has two progressively clearer hints. Other existing plans receive a fallback explanation of the relevant operation or choice; generated plans may supply two specific hints. Asking for help preserves the student's answer and stays on the same step.
- Provider instructions now ask for smaller actions, concrete fraction reasoning, and distinct hints. Validation also checks hint text for unsupported numerical results and unsafe content. Fresh provider output was not evaluated in this change.
- Fraction arithmetic uses exact rational values. Equivalent answers such as 8/30 are accepted as 4/15, and dependent calculations use the exact value. Rounded recurring decimals such as 0.26 and 0.266667 are rejected for an exact fraction step. Invalid denominators and expressions entered as answers cannot advance a step.

## Student interface

- Fractions in the problem, guidance, expressions and completed steps use a numerator, horizontal bar and denominator. Literal division remains a division symbol. Dates, unresolved fractions and decimal operands are not partially converted into fractions.
- A fractional calculation offers separate numerator and denominator inputs, with a switch back to ordinary number entry. Missing or zero denominators disable submission.
- Every step has a help control. The hint appears in its own card; requesting the next hint does not discard an attempted answer.
- Success feedback is labelled as belonging to the previous completed step. Wrong-answer feedback clears when the student starts correcting an answer.
- Screen-reader text reads numeric fractions as “a phần b”. Buttons and fraction input controls retain appropriate accessible labels and touch sizes.

## Startup images

Previously, fonts gated the initial screen but React Native images loaded separately. In the development client, uncached illustration assets must also arrive from the development server and be decoded. The page could therefore appear before its illustrations.

The existing expo-image dependency now loads the nine main illustration/logo sources in parallel, retaining decoded references for the displayed images. Native decoding is requested at a maximum 640 by 640 pixels; the underlying web implementation has different resizing behavior. The original asset files and logos are preserved.

Fonts and art load concurrently. A short preparation screen is shown until the art is ready. A 15-second failure boundary offers a retry, with already decoded sources reused. This improves completeness of the first displayed application screen; it does not promise zero loading time or eliminate a slow development connection.

Versioned Expo 57 documentation was read before implementation:

- https://docs.expo.dev/versions/v57.0.0/
- https://docs.expo.dev/versions/v57.0.0/sdk/image/
- https://docs.expo.dev/versions/v57.0.0/sdk/asset/
- https://docs.expo.dev/versions/v57.0.0/sdk/splash-screen/

## Verification

- Backend: **198 passed**, covering fraction guidance, guided lessons, primary lessons, math tutoring, notebook tutoring and capacity checks.
- Mobile: **71 passed across six suites**, covering fraction rendering, startup readiness/failure/retry, illustration caching, guided screen interactions, tutoring API and recognition/home behavior.
- Student Mobile TypeScript check: passed.
- Git whitespace check: passed.
- Browser preview at **375 × 812**: stacked fractions wrapped within the problem card and the mascot was loaded. At **812 × 375**, fractions remained within the viewport and the page had no horizontal document overflow. This is browser evidence, not physical-device evidence.
- No model training, commit or push was performed for this request. Existing changes from the preceding OCR/storage task remain preserved.

## Operational limits

The existing AI service was not restarted. The earlier attempt to restart services was rejected by automatic approval review with “blocked by policy”; that action was not retried or bypassed. New backend lesson behavior becomes active after the owner's normal service restart. Mobile source changes were bundled by the local preview server.

Physical Expo Go cold-start timing, large system-font settings, and the complete on-phone lesson flow still require a real-device check. This report does not claim that all problem families now have ideal teaching content; supported garden problems received concrete expanded guidance, while the general progressive-help mechanism applies across steps.

## Owner-authorized startup follow-up

The owner subsequently requested startup and an Expo Go QR. The verified project
AI process was restarted through the normal launcher; the LAN mobile terminal
was opened and kept running. All runtime diagnostics passed, including Student
Metro and LAN reachability. The QR was generated from the verified Expo Go
manifest and decoded back to the same connection URL. The new backend source is
now loaded. This verifies service readiness, not a completed on-phone test.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: student-facing fraction readability and progressive assistance.
  - Applied to: fraction display, answer controls, hint disclosure, loading/error states and responsive visual review.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native component and startup implementation.
  - Applied to: concurrent asset initialization, shared decoded-image references and controlled step feedback state.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: focused implementation using existing dependencies and standard arithmetic tools.
  - Applied to: Python Fraction arithmetic, existing lesson API, small reusable fraction/image components and bounded loading retries.
