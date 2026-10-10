# Deployed photograph flow repair and free cloud handoff

Date: 10 October 2026. Scope: deployed student web photograph flow, real question classification, publication reliability, and the owner-selected free cloud plan. No training, commit or Git push was performed.

## Result

The production website was republished and its real login → capture picker → privacy → crop → question reading → lesson flow was exercised. The garden question remains an original question with its observed fractions and given count; it no longer falls into the missing-question screen merely because independent readings differ in worksheet numbering. API/OCR still run on the owner's PC. No cloud account or server was created.

## Repairs

### Keep the photographed original question

The owner-supplied garden screenshot was used to extract the actual printed photograph, without generating text or numerical labels for the reader. Before the repair, a real authenticated inspection returned `WORK`, an empty `problemText`, and `needsProblem=true`, while its physical lines contained the complete question. Tracing the actual provider calls showed two `PROBLEM` readings differing in the worksheet prefix.

Question comparison now ignores an initial worksheet number, trailing sentence punctuation, and paired numeric fraction operand parentheses. It continues to distinguish digits, operators, decimal separators and actual words. A genuine unresolved disagreement retains the first observed question with `[?]`; the student must edit/compare it before beginning. Neither the reviewer nor arithmetic is used to replace the photographed numbers. Backend validation rejects an unresolved `[?]` even when the caller sends confirmation.

The reading prompt now distinguishes an empty “Bài giải” heading below a printed question from written student work. Work-only pages still follow the existing safeguards against inventing an original question.

After rebuilding the owned AI and worker containers, an actual API read returned HTTP 200, `PROBLEM`, `needsProblem=false`, the observed `1/3`, `2/5` and `16`, and no unresolved marker in that reading. Its request took 3.47 seconds. This is sample-specific evidence, not a corpus accuracy percentage.

### Web capture and bounded crop export

The web camera route uses the browser's native capture file picker with rear-camera preference, plus a library option. The phone's camera application supplies focusing/flash; the old web live-video scene is no longer required. Cancellation preserves the previous draft; concurrent taps are blocked; a failed normalization retains the image and permits retry. Native `camera.tsx` is unchanged.

Web image normalization and crop export draw directly into one final JPEG canvas, capped at 3200 pixels on the long edge without enlarging small crops. Loading and encoding each have a 15-second failure deadline. Canvas allocation is released on success/error. Only the supplied privacy-approved crop source is read; export failure never substitutes the unmasked original. The existing screen catches failure, retains the image and unlocks its controls.

Native image normalization keeps its original implementation. Native crop export keeps its existing image-manipulator behavior; shared rotation geometry was extracted without changing its calculation.

### Reject stale exported service addresses

A live browser check exposed another defect: portal login succeeded but the student app returned to login. The actual exported student JavaScript still contained the expired previous tunnel address and contained no current tunnel address. The source configuration tests alone did not catch this.

Publication now uses `expo export --clear`, then checks the actual compiled JavaScript against the requested public `/api/v1` base. Missing/mixed/stale bases fail before upload. The checker rejected the original cached artifact; the fresh export passed. The rebuilt portal was then republished and real student login reached the shared home.

## Verification

| Check | Result |
| --- | --- |
| Four targeted AI suites: tutor, physical row panels, math layout, capacity | 155 passed; two dependency deprecation warnings |
| Native crop, web crop, web capture, tutor screen suites | 50 passed |
| Student TypeScript | `npx tsc --noEmit` passed |
| Export routing/configuration/stale-bundle checks | 4 passed; actual old bundle correctly rejected; actual fresh bundle passed |
| Portal configuration / production artifact tests | 11 / 2 passed |
| Teacher configuration, contracts and sessions / production artifact tests | 17 / 2 passed |
| Admin configuration and sessions / production artifact tests | 13 / 3 passed |
| Public health | HTTP 200, `UP` |
| Backend login/profile for the three owner-requested trial roles | HTTP 200 and each correct role |
| CORS with Authorization and X-Request-ID | Intended portal accepted; unrelated origin rejected with 403 |
| Public internal route | 404 |
| Owned preview AI/backend/database/storage/queue/worker | Healthy; data volumes retained |

### Actual deployed browser evidence

- Login reached `/study/` after the cache repair.
- The new capture button opened a single-file chooser. Selecting the real garden photograph reached privacy, then crop, without a live video stream. This verifies capture handoff, not an actual phone camera shot.
- A 943 × 229 source was rotated and exported to 229 × 943. The crop action reached the recognition screen in approximately 406 ms on this workstation/browser.
- Actual vision recognition of that rotated photograph preserved the question and numbers.
- Returning to crop retained the source and usable controls. Reset/full-image export succeeded again, and actual reading again preserved `1/3`, `2/5` and `16`.
- Fractions displayed vertically in the question. Starting remained disabled until source confirmation.
- After confirmation, the actual service produced a six-step garden lesson beginning with choosing the common denominator through `3 × 5`, without entering an answer for the pupil.
- The original-question disclosure expanded and collapsed through its existing control.

Browser viewport observed: **614 × 668**. An attempted viewport override was not reflected in the in-app browser; this is desktop browser evidence, not physical Android/iOS evidence. Autofocus/flash, lower-memory phones, picker cancellation on each mobile browser and physical-device cropping still need handset checks.

Evidence is kept in ignored `infra/local-runtime/pc-preview/`:

- `owner-garden-question.jpg`, `owner-garden-read.json`
- `web-camera-fixed.png`, `web-crop-return-fixed.png`, `web-garden-reading-fixed.png`
- `public-repair-checks.json`, `web-deployments.json`
- `oracle-signup-maintenance.png`

## Deploy Result

- **URL:** https://mathvisionkid-portal.vercel.app
- **Target:** production, team `manh15`
- **Status:** READY
- **Deployment:** `dpl_CDfijXoxu2YFNB5QUUhis2JXydGv`
- **Commit:** base `0e40db7`; deployment includes authorized uncommitted working files. No commit/push was made.
- **Framework:** Vite portal plus shared Expo SDK 57 web export under `/study/`.
- **Build duration:** fresh local student export approximately 25 seconds; remote build timing not provided.

Teacher and admin were also republished for the current API origin. Their final IDs are `dpl_A8G7yBfetdLPWW3c3MDkQXt1bLGW` and `dpl_BVNzvLEXez2pAyGg1CzG54dyUs4R`.

### Post-deploy observability

`vercel logs` for portal errors over the last hour returned no records. This static-site query is not a complete backend/provider error audit. Browser warnings/errors were empty at the reading/lesson check. No new monitoring integration or drain was configured.

## Free cloud status

The owner selected free hosting and requested Oracle signup. The official signup page was opened, but a planned-maintenance notice disabled all form fields until **10 October 2026, 11:00 UTC / 18:00 Vietnam time**. Registration was not submitted. Email verification, choosing a password, identity/card verification and agreement acceptance require owner handoff when signup is available.

[Free cloud deployment](../docs/FREE_CLOUD_DEPLOYMENT.md) records the proposed single Always Free A1 server, current allowances, ARM64 build gate, data migration, stable HTTPS endpoint, account setup and PC-off acceptance checks. Official CPU package indexes list the pinned Python 3.12 ARM64 PyTorch/torchvision wheels. A complete ARM64 build/inference remains unverified, and the pinned MinIO tag returned registry-access errors during inspection. These must be resolved before cloud rollout. No paid resource, account upgrade or replacement mirror was selected.

The present temporary tunnel remains a PC trial. No claim of PC-independent or guaranteed 24/7 operation is made.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: student web capture/error-recovery interface.
  - Applied to: web capture choices, child-facing guidance and retained-image recovery.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React/React Native web implementation.
  - Applied to: platform-specific route, asynchronous capture lock and source-retaining state.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: small fixes to existing image/OCR/deployment pipelines.
  - Applied to: browser-native capture, single final canvas, reuse of the existing production stack, compiled-export gate.
- `deployments-cicd`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated/vercel/0722921d/skills/deployments-cicd/SKILL.md`
  - Why selected: separate Vercel publication domain.
  - Applied to: tested prebuilt production uploads, READY verification and bounded post-deploy log inspection.
