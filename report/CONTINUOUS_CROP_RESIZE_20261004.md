# Continuous crop resizing — 2026-10-04

## Result

- The minimum crop span is now 8 logical pixels instead of 60, allowing thin horizontal and vertical strips. Export accepts any nonempty crop; rounding and image-bound clamps remain in place.
- Four edge grips join the four corner grips. Touch targets remain 48 × 48; when targets overlap, the gesture chooses the closest actual edge/corner to the initial touch.
- Each gesture retains its original opposite anchor. Dragging across that anchor flips the selection to the other side, and dragging back restores it without releasing the pointer. A centered minimum span keeps the transition continuous and nonempty.
- Absolute pointer positions keep the finger anchor stable as the handle itself moves. This also avoids the activation offset of web pan gestures.
- The grid hides for thin selections and corner markings shrink with the rectangle. Preview continues on the UI thread; no intermediate image file is exported during dragging or rotation.

The earlier navigation and accordion repair is documented in `report/IMAGE_BACK_NAVIGATION_UI_20261004.md`.

## Validation

- Full student-mobile suite: **39 suites / 427 tests passed**. After the final grid/corner styling refinement, all **40 affected crop tests** passed again. TypeScript and lint passed on the final code.
- Geometry regressions cover thin lines, all eight handles crossing and returning, continuous motion around the minimum size, large displacements at image boundaries, overlapping targets, tiny image bounds and narrow exports.
- Actual headless browser gestures: every edge and corner crossed the opposite anchor and returned to its original rectangle in one pointer-down/pointer-up sequence. A **197 × 8** horizontal strip and an **8 × 48.31** vertical strip were measured. Regrabbing the upper edge of the thin strip selected the correct edge and expanded it; moving the whole rectangle still worked.
- Browser preview retained the original source URI. No page errors or Reanimated warnings were recorded. Rotation/ruler and landscape crop controls were checked again.
- Gallery → privacy → crop → real problem recognition → back to crop → back to privacy was rerun after the interaction change. The source photo retained **197.20 × 447** display dimensions; problem expansion/collapse still passed on a narrow viewport.
- Expo SDK 57 Android/React Compiler regression passed; the compiled crop components contain no shared-value access directly in their render bodies.
- Private ignored evidence: `infra/local-runtime/logs/back-navigation-20261004/continuous-crop-evidence.json`, `browser-evidence.json`, `compiler-evidence.json` and screenshots. These are browser and compilation checks, **not physical Android device evidence**.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: precise crop interactions and usable touch regions.
  - Applied to: edge grips, overlap resolution, thin-selection visual clarity.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native rendering and shared-value lifecycle.
  - Applied to: compiler-compatible callbacks, UI-thread geometry and animated styling.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: one shared resize calculation instead of separate corner algorithms.
  - Applied to: existing crop geometry and gesture handlers; no new dependency.

No commit, push, model training or backend changes were made for these UI tasks.
