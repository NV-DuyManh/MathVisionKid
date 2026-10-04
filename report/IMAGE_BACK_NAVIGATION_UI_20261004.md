# Image back navigation and problem accordion — 2026-10-04

## Result

- Privacy now measures the displayed source URI instead of using mutable cropped draft dimensions. Going back from recognition through crop keeps the original photo fitted to the available canvas. Late callbacks from another source are ignored.
- Landscape privacy places confirmation controls beside the photo; existing masks scale with the fitted image when the viewport changes.
- The problem card uses document, chevron and edit icons with separate touch targets. It collapses during a lesson, keeps the current step, and remains plainly visible before a lesson starts. Both problem and work toggles expose their expanded state on native and web.
- Crop shared-value reads use the Reanimated `get`/`set` API supported by React Compiler. Previously, Expo compilation hoisted two `width.value` accesses into `StraightenRuler` render. The corrected compiled output has no render-time shared-value access; strict warnings were not suppressed.

## Validation

- Student mobile: **39 suites / 406 tests passed**; TypeScript and lint passed.
- New regressions cover source dimensions after crop and remount, stale size callbacks, resubmitting the original privacy photo, accordion state and preservation of the lesson, and actual Android Expo/React Compiler transforms.
- Headless Chromium with a synthetic 1080 × 2448 photo: gallery → privacy → wide crop → real problem recognition → back to crop → back to privacy. The image was **197.20 × 447 logical pixels before and after**. Landscape retained 232 pixels of image height.
- Real local lesson API plus browser UI: problem expands/collapses; narrow 320-pixel viewport retains a 48 × 48 edit target and a distinct toggle. No browser page errors or Reanimated warnings were recorded.
- Private evidence: `infra/local-runtime/logs/back-navigation-20261004/browser-evidence.json`, `compiler-evidence.json`, and screenshots in the same directory. Evidence and synthetic input are ignored runtime files.
- No physical Android device was operated. Browser checks and Android compilation do not establish physical-device confirmation.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: image fitting, responsive layout and clear accordion affordances.
  - Applied to: privacy canvas, landscape controls, problem header and touch spacing.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React state lifecycle and compiler compatibility.
  - Applied to: URI-specific dimension loading, callback cancellation, compiled shared-value regression.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: repair the cause with existing native APIs and components.
  - Applied to: `Image.getSize`, existing Ionicons and Reanimated APIs; no added dependencies.

## References

- Expo SDK 57 documentation: https://docs.expo.dev/versions/v57.0.0/
- Reanimated React Compiler support: https://docs.swmansion.com/react-native-reanimated/docs/core/useSharedValue/#react-compiler-support

No commit, push, model training or backend changes for this UI repair.
