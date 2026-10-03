# Mobile reference UI and recognition wait repair — 2026-10-03

The rejected home screen was rebuilt around the owner's reference: a rounded student avatar and heading, lilac gradient hero, large star mascot, purple gradient camera button, three compact pastel utility cards, saved-activity streak and four functional bottom tabs. Recognition now shows a retained-photo illustration and horizontal activity bar without an elapsed stopwatch or invented percentage. Interactive detection no longer waits for duplicate cloud spelling advice.

## UI changes and actual navigation

- Bundled six static Nunito faces with Vietnamese glyph coverage and the OFL license. Header, home, capture, privacy, review, result, saved-history and shared controls use explicit font faces instead of synthesized system weights.
- Reused all seven owner illustrations byte-for-byte. Generated one separate fictional student avatar using the built-in image generator; its prompt, source, alpha range and hash are recorded in [avatar-generation.json](ui_reference_rework_20261003/avatar-generation.json).
- Hero opens a short acquisition sheet for handwriting, native image picking or arithmetic. Picking an image still opens the existing privacy step. Both recognition domains remain available.
- The four tabs open home, the existing grade 1–5 curriculum, actual saved activity and the student's profile. Lessons can switch grade, expand the real sample guidance and start a clean handwriting capture. No inert lesson or achievement tabs were added.
- Streaks and counts derive from account-scoped completed local records. Samples, benchmark records and future timestamps are excluded. Empty history shows an honest starting state, with no invented five-day streak or earned points.
- Tips and privacy dialogs retain fixed close and confirmation controls while their content scrolls on short screens. Content padding keeps the last item clear of the bottom navigation.
- Splash routing now follows restored authentication immediately; the previous artificial 1.2-second delay was removed. Auth and backend ownership checks remain unchanged.

## Waiting and late advice

Long recognition waits use one shared progress component with the actual caller's stage, retained image, horizontal activity bar and a reachable cancel action. Reduced-motion preference stops the animation. Cancel and retry preserve the student's adjusted line boxes. Short local action indicators remain in their existing controls.

The existing AI fast path preserves segmentation, optional Groq segmentation assistance and batch CRNN output, while deferring synchronous per-line spelling advisors. Existing document advisors run after successful transaction commit. Short row-locked writes reload the latest line and share feedback's lock; network requests run outside the transaction. Automatic text replacement is allowed only on unverified lines.

Client merging now recognizes the backend's actual `UNVERIFIED` verdict as untouched, while preserving confirmed, corrected, skipped, manual and actively edited text. Polling makes at most 24 sequential requests, with a three-second pause after each response. Incoming trial objects and text editing no longer reset that budget. Changed trial IDs and unmounted screens discard stale replies. Failed background batches settle pending provider states as unavailable without overwriting successful advice or human feedback.

Out-of-order pending replies also preserve already settled provider results and applied text. Feedback submits the exact displayed or explicitly chosen text, allowing the backend's integrity check to reject a confirmation if the prediction changed concurrently. Optimistic feedback reconciliation and rollback retain advice that arrived while the request was pending.

## Measured real HTTP result

The same 12-line, 253,206-byte image produced identical box geometry, line order, raw OCR, confidence and confidence provenance across ordinary and fast detection. Public backend detection returned in **4.900 seconds**, followed by trial creation in **1.320 seconds**. Later background advice settled **32.88 seconds** after the first read; that work was still pending when the initial result appeared. Exact human edits saved during that wait survived subsequent advice.

The earlier request log spent 30.65 seconds overall, including 27.37 seconds waiting for line advisors. The measured ordinary cold request took 25.461 seconds; an ordinary warm request with cached successful advice took 7.244 seconds. These runs have different model/cache conditions and are not a universal speed comparison. See [OCR_LATENCY.md](ui_reference_rework_20261003/OCR_LATENCY.md) for provider outcomes, caveats and the real public flow.

## Validation and previews

Final results are recorded in [verification.json](ui_reference_rework_20261003/verification.json). Browser checks use controlled authentication, gallery and failure fixtures, separately from the real backend HTTP checks. Chromium screenshots demonstrate web-rendered mobile layouts; they are not physical Android or iPhone evidence.

The final browser pass completed 33 checks with 25 screenshots and zero page errors across all three viewports. Six font files were explicitly fetched to verify assets as well as actual heading typography; fonts unused on the home screen normally load lazily in web rendering. Final mobile validation passed 278 tests across 29 suites and TypeScript compilation. Full backend validation passed 164 tests across 22 suites, and the two AI contract tests passed. Both Android and web export successfully, including all six font faces and eight illustrations. See [UI_QA.md](ui_reference_rework_20261003/UI_QA.md) for fixture details, intentional HTTP failures and the unedited development-preview overlay visible in some screenshots.

- [Home, 375 × 812](ui_reference_rework_20261003/ui/home-375x812.png)
- [Home, 430 × 932](ui_reference_rework_20261003/ui/home-430x932.png)
- [Recognition progress](ui_reference_rework_20261003/ui/recognition-detection-bar-375.png)
- [Lessons](ui_reference_rework_20261003/ui/lessons-375x812.png)
- [Achievements](ui_reference_rework_20261003/ui/achievements-375x812.png)
- [Browser interactions and viewport checks](ui_reference_rework_20261003/ui/browser-checks.json)
- [Owner illustration hashes and font assets](ui_reference_rework_20261003/assets.json)
- [Backend test results](ui_reference_rework_20261003/backend-tests.json)

The source and code were inspected against the required [Expo SDK 57 documentation](https://docs.expo.dev/versions/v57.0.0/), including [Font](https://docs.expo.dev/versions/v57.0.0/sdk/font/) and [LinearGradient](https://docs.expo.dev/versions/v57.0.0/sdk/linear-gradient/). The sole added runtime dependency is the SDK-matched official `expo-linear-gradient ~57.0.2`. Nunito comes from the [official project](https://github.com/googlefonts/nunito) and is accompanied by its license.

No training, model-weight change, database reset or migration change was performed. Standalone HandAI was not modified. Git publication is outside this repair report.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Reference-driven mobile visual and interaction redesign.
  - Applied to: Home proportions, typography, gradient surfaces, functional four-tab navigation and responsive layouts.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React and React Native implementation.
  - Applied to: Bundled font loading, shared presentation, focused effects and late-response cleanup.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Small reuse-based latency and correctness fixes.
  - Applied to: Existing curriculum/history, fast-path contract, native transaction hooks, shared row locking and bounded polling.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: Separate bitmap asset domain, extending the usual three implementation skills.
  - Applied to: One transparent fictional student avatar; the owner's original seven images remain unchanged.
