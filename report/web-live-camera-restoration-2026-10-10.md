# Student web camera restoration — 2026-10-10

## Result

Restored the live rear-camera screen as the default student website capture flow. The preceding web-specific implementation replaced it with an introduction and system photo picker, which did not preserve the owner's expected camera interaction.

Only `apps/student-mobile/src/app/camera.web.tsx` and its dedicated tests were changed for this repair. Existing work in the checkout was preserved. No commit or push was performed.

## Behavior

- A granted camera permission opens the live rear preview, with the familiar framing corners, round shutter, gallery action and light control.
- First-time visitors see a camera permission action within that same screen. The gallery stays usable while the browser permission prompt is unanswered.
- A failed or denied preview offers retry and the phone's system camera as a fallback. A preview that never becomes ready also offers recovery after 15 seconds.
- The shutter stays disabled until the preview is ready. Duplicate taps are ignored while capturing.
- A successful capture or selection is normalized, retains the lesson context and navigates to the existing privacy step. Cancellation or normalization failure preserves the previous image.
- The preview is unmounted before privacy and when leaving the camera route. Late capture results after navigation are ignored.
- The light control checks the actual video track's torch capability; unsupported cameras receive a clear explanation instead of a false enabled state.
- Short screens use a compact layout that keeps permission controls and the footer separate. Portrait framing is preserved.

Native `camera.tsx` is unchanged. Its SHA256 remains `E756B93AFECF558C9E7AE631657C4F15E7F3F51E13A97D983EE0958C2F8316A4`. No auth/RBAC, OCR, model weights or training changes were made for this repair.

## Validation

- `npm test -- --runInBand src/__tests__/cameraWeb.test.tsx src/__tests__/recognitionHome.test.tsx`: **18 passed** in two suites. Coverage includes live capture, readiness, context retention, cancellation, denied permission, unanswered permission with usable gallery, normalization failure, duplicate capture, navigation cleanup and camera-start timeout.
- `npx tsc --noEmit`: passed.
- Publish gates: 11 portal configuration/auth tests, two production artifact tests and four student website routing/configuration tests passed. Portal build and fresh student web export succeeded.
- Production browser checks: **375 × 812 portrait** and **812 × 375 landscape**. The permission overlay and footer no longer overlap in landscape; all controls remain inside the viewport.
- Selected the real owner-provided garden question image via the site's gallery button. The browser reached `/study/privacy` with the correct image and the existing privacy confirmation unchecked. “Chụp lại ảnh khác” returned to the camera screen successfully.
- Scoped whitespace checks passed. The initial direct Jest invocation lacked this workspace's required `jest-expo` preset and failed before executing tests; rerunning through the configured `npm test` script passed. No test configuration changes were needed.

Browser camera permission was not granted in the verification session. Live hardware capture and torch operation are covered by code/tests but **have not been verified on a physical phone**. No simulated camera footage or fabricated phone evidence was used.

Local browser evidence (ignored runtime artifacts):

- `infra/local-runtime/pc-preview/web-camera-restored.png`
- `infra/local-runtime/pc-preview/web-camera-restored-landscape.png`
- `infra/local-runtime/pc-preview/web-camera-gallery-privacy.png`

## Deployment

- Production alias: <https://mathvisionkid-portal.vercel.app>
- Deployment: <https://mathvisionkid-portal-78w6nre48-manh15.vercel.app>
- ID: `dpl_32mPBBTT7fYZn8yLdwP18S6wLChU`
- Scope: `manh15`; status: **Ready**, confirmed by Vercel CLI.
- Student web entry artifact: `entry-1105048adbe838e601b8e7cc9da25681.js`.
- Deployment error-log query returned no matching logs; this static deployment log result is not evidence of physical-camera operation.

Published the tested static artifact using the existing `Publish-Vercel-Web.ps1` workflow. The backend/OCR deployment remains the previously configured PC preview environment; this camera repair does not make those services independent of the owner's machine.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: camera interaction, permission recovery and mobile responsive layout.
  - Applied to: framing, controls, recovery text, touch targets and portrait/landscape checks.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React implementation with asynchronous capture and lifecycle cleanup.
  - Applied to: event-driven capture, focus cleanup and the bounded camera-ready effect.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: scoped restoration using the existing camera and image pipeline.
  - Applied to: no new dependencies, no native refactor and reuse of normalization/privacy flow.
- `deployments-cicd`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated/vercel/0722921d/skills/deployments-cicd/SKILL.md`
  - Why selected: publishing and verifying the existing Vercel production deployment.
  - Applied to: checked production artifact, deployment status and log verification.

Versioned reference read before implementation: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) and [Camera](https://docs.expo.dev/versions/v57.0.0/sdk/camera/).
