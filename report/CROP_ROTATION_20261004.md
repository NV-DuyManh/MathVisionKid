# Crop rotation — 2026-10-04

## Outcome

Implemented after completing the 200-image Drive test batch. The crop editor now
offers left/right 90-degree turns, signed 0.5-degree straightening steps and an
original-orientation reset. Crop thirds and purple handles match the application's
existing colours. The crop frame resets against the rotated bitmap's dimensions,
including a 180-degree turn where dimensions do not change.

Each preview is rendered from the immutable source, not the previous rotation.
Rotated previews use PNG; the final crop uses the existing JPEG export. Original
and privacy-masked source URIs are retained. A failed masked image never falls
back to an unmasked original. Controls are disabled while preparing/cropping;
stale asynchronous work cannot replace a new image session.

In short landscape windows, controls sit beside the image. During browser review,
the original vertical layout left only 9.6 px for the image at 812 × 375. The revised
layout provides a 472 × 264.8 px image container while keeping controls visible.

## Verification

- Read the exact SDK 57 documentation before changing Expo code:
  https://docs.expo.dev/versions/v57.0.0/sdk/imagemanipulator/.
- Used the current ImageManipulator context API, with rotate before crop.
- Jest: crop rotation plus existing crop geometry, **2 suites / 10 tests passed**.
  Covers signed/full-turn angles, source reuse, rotated dimensions, masked-source
  failure and coordinate conversion. This is mocked API verification, not a native
  image-rendering benchmark.
- TypeScript `tsc --noEmit`: passed after the responsive correction.
- ESLint on the changed screen/helper: passed without errors or warnings.
- Browser: used the real home → camera/library → privacy confirmation → crop flow
  with one downloaded math photograph containing no personal information.
- Verified +90°, 180°, original reset, +0.5° and −0.5° previews, enabled controls,
  and layouts at 375 × 812 and 812 × 375. Confirming a rotated crop reached the
  next learning screen. The subsequent reading request could not connect in that
  browser session; it is not claimed as end-to-end tutoring verification.
- Browser viewport restored after testing. Screenshots were visually inspected.
- No physical-device test, model training, dependency installation, commit or push.

## Files

- `apps/student-mobile/src/app/crop.tsx`
- `apps/student-mobile/src/utils/cropRotation.ts`
- `apps/student-mobile/src/utils/__tests__/cropRotation.test.ts`
- The independent data audit is `report/DRIVE_LINE_BATCH_20261004.md`; accurate
  annotation of all 200 photographs remains incomplete as documented there.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: mobile image-editing controls and responsive touch layout.
  - Applied to: labelled controls, adequate hit targets, busy states, existing
    theme reuse and portrait/landscape visual review.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native state and asynchronous rendering.
  - Applied to: ref-based processing lock, stale-effect cancellation, primitive
    dependencies and guarding image-session changes.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: extend the existing editor with minimal dependencies.
  - Applied to: existing Expo ImageManipulator, crop geometry and theme;
    focused regression checks rather than an additional editor framework.
