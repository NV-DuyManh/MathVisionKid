# Student website parity — 9 October 2026

## Scope and current status

The owner requested that a student signing in on the website reach the same learning interface used in the existing app, instead of a separate portal landing page. The original student application is now exported to **`/study/` on the portal origin** and published in the same Vercel project:

[Open the portal](https://mathvisionkid-portal.vercel.app) → student login → [student learning interface](https://mathvisionkid-portal.vercel.app/study/).

The website reuses the app's screens, artwork, calculator, lesson library, and learning flows. Browser-specific authentication, startup, alerts, and API resolution use `.web` files. Existing native implementations remain unchanged; `app.config.js` adds an opt-in web export base path and preserves the default native configuration.

The shared student website was published and its main screens, actual gallery-to-tutor image flow, and confirmed logout were verified in a real desktop browser. Logout reached the portal's success screen, and revisiting `/study/` required login. One photographed division problem reached the correct structured reading with an unchecked human-review confirmation. This phase's stated web acceptance checks are complete; it is not a physical-device test, a full feature-parity certification, or an all-image OCR accuracy claim.

The [earlier cloud deployment report](cloud-deployment-readiness-2026-10-09.md) records the completed preceding phase's **48 web checks** and three-project deployment evidence. That count is historical and is not rewritten to represent this student-web phase.

## Implementation

- Portal's `/student` route calls the real backend `/me`, requires an active `STUDENT` role, and then opens `/study/`. Other roles do not gain student access from the portal route.
- The web student application shares the portal's same-origin `sessionStorage` access/refresh keys and independently validates `/me` before rendering protected screens. A saved profile does not grant access when the backend rejects the session.
- Only the student-safe profile fields are mapped into the UI/cache. Email-like display names fall back to `Học sinh`; account emails are not displayed in student UI.
- Web logout uses a bounded server request, clears shared tokens, cached student identity, recognition cache, and the current draft, then opens the portal's logged-out route. Native authentication/storage continue to use their existing implementations.
- The web root loads the existing Nunito fonts and illustration assets before opening learning screens, includes the app title, and centers the interface within a responsive maximum width of 860 px.
- A web-only alert adapter displays the existing confirmation actions as a modal. This restores confirmations that React Native Web's default `Alert.alert` does not display; it does not change the native alert implementation.
- Production API configuration requires a public HTTPS `/api/v1` address. Developer addresses and mock recognition are not enabled in the published export.

## Routing and publication

The opt-in `MATHVISION_WEB_EXPORT=true` setting configures the Expo SDK 57 export base path as **`/study`**. The actual SDK router parser is tested to preserve both `/study/learning/math-guide` and the application's learning route. An earlier `/learn` mount collided with the SDK's prefix stripping for `/learning`; the final `/study` namespace avoids that collision.

`Publish-Vercel-Web.ps1` builds and checks the portal, exports the shared student application, copies it into the static `study/` directory, and adds a `/study` SPA fallback before the portal fallback. It uploads only static output using the existing prebuilt deployment flow. API keys, model artifacts, datasets, and private runtime state remain local.

The publisher accepts `-Apps portal` for a portal/student-only deployment and preserves teacher/admin entries in its private deployment record. Normal `Start-PC-Preview.ps1 -PublishWeb` still publishes all three projects, including the student export, for the current tunnel address. When that address changes, all three projects need the new API build URL.

**A standalone portal Vite build does not include the student export.** A future Git/CI deployment must perform the same Expo export, `study/` asset merge, and path-specific fallback. Importing `apps/portal-web` with its Vite build alone would omit this student interface.

## Verification recorded so far

| Check | Recorded result | Limit |
| --- | --- | --- |
| Student shared-session/authentication checks | **7 Node test results passed**, including parent and six subtests | Real React rendering with controlled HTTP responses; backend remains access authority |
| Export identity, namespace, and production API configuration | **3 tests passed** | Includes the actual SDK router parser and preservation of native identity/default configuration |
| Web confirmation adapter | **1 targeted Jest test passed** | Action choice, safe dismissal, callback behavior, and restoration of the original alert function; 37 targeted Jest tests together with the existing 36 regressions below |
| Existing gallery/crop/upload regressions | **5 suites, 36 tests passed**, with TypeScript check passed | Targeted software regression checks; no physical-device evidence |
| Portal checks for the revised student handoff | **13 passed** | Separate from the earlier phase's aggregate count |
| Actual browser home | Artwork, tab navigation, and layout rendered at **375 px and 1280 px** | Narrow and desktop browser viewports, not a phone-device test |
| Calculator | Actual browser calculations **1 + 3 = 4** and **7 + 5 = 12** passed, including popup behavior | Two interaction cases, not exhaustive calculator certification |
| Lesson library | Grade 1 and grade 5 views passed in the actual browser | No claim of complete textbook coverage |
| Profile | Grade 5 display and absence of account email passed | Student-safe UI check |
| Gallery/privacy/crop web flow | Actual PNG selection, black privacy mask capture, 90° rotation plus fine 6° adjustment passed | Browser workflow using the existing canvas/crop implementation |
| Actual question reading/tutor flow | **Passed after the `/study` routing fix** | Real selected PNG → privacy-mask JPEG → crop/rotation confirmation → `/study/learning/math-guide` → actual inspect response with division structure; human confirmation remains unchecked |
| Student logout and protected reentry | **Passed in the actual browser** | Profile confirmation → `/logout?source=student` success; revisiting `/study/` redirected to portal login |

The real browser image flow selected the owner's PNG, captured a black privacy mask through `html2canvas`, applied 90° rotation and a fine +6° adjustment, confirmed the crop/full-image choice, and reached the tutor route. The actual inspect response filled dividend **49572**, divisor **6**, quotient **8262**, and intermediate rows **015**, **037**, **012**, **00**. The review checkbox was initially unchecked so the child must confirm the reading; the test did not supply expected labels as OCR input or force a canned result.

The actual profile logout confirmation completed and shared authentication was removed. A later direct visit to the protected student root required portal login, so the test did not rely only on an intermediate navigation state. The preceding raw per-line OCR trial still showed inaccurate `CRNN_RAW` final text with `UNVERIFIED` verdict despite real advisor suggestions. That earlier endpoint evidence and this successful structured inspect response are distinct results; neither establishes accuracy across all photos.

Root retained private browser screenshots at `infra/local-runtime/pc-preview/student-home-web.jpg` (37,711 bytes, 375 × 812 capture) and `student-web-logout.jpg` (44,387 bytes). Both exist and are Git-ignored. They are desktop-browser evidence and are not embedded into the public repository as physical-device screenshots.

## Documentation verification

The phase documentation's commands, export flags, namespace, session keys, and deployment merge were checked against the actual source. **48 local Markdown link targets** across the deployment documentation exist; code fences are balanced, UTF-8 text has no replacement characters, and `git diff --check` reports no whitespace errors. All phase reports include skill traceability. Private screenshot exclusion was verified with `git check-ignore`. No private secret environment or credential file was read by the documentation subtask.

## Operational limits

The exported website uses the same temporary HTTPS API tunnel and private PC runtime documented in [the PC preview guide](../docs/PC_PREVIEW_DEPLOYMENT.md). The PC must remain awake with Docker, internet, and tunnel active. A new tunnel hostname requires a new portal/student export as well as teacher/admin redeployment.

The student session lives in the current browser tab's `sessionStorage`. Opening the learning URL without that session redirects to portal login. Teacher/admin accounts cannot use a cached profile to enter the student application. Backend authentication and role checks remain authoritative.

Browser camera/gallery behavior depends on browser permissions and device capabilities. The narrow-viewport tests do not certify a native camera, Expo Go session, or physical handset. There was no model training, backend change, teacher/admin implementation change, or Git commit/push in this student-web phase.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Preserve the existing student learning interface across browser widths and touch-oriented controls.
  - Applied to: responsive web root, shared artwork/fonts, child-facing profile presentation, and browser interaction verification.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React/React Native web rendering, authentication lifecycle, and shared-session behavior.
  - Applied to: web-specific auth/root components, safe async session restoration, portal handoff, modal lifecycle, and rendering tests.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Reuse the established app and deployment flow with small platform-specific changes.
  - Applied to: `.web` adapters, opt-in export namespace, static output merge, existing validation helpers, and focused tests.

These entries record the skills applied by the implementation phase. The documentation subtask made documentation-only changes after inspecting the canonical registry; no installed documentation-specific skill matched that narrower task.
