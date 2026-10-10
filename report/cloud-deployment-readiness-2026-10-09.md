# Cloud deployment readiness — 9 October 2026

## Status and scope

The portal, teacher, and admin Vite apps are now published on Vercel team **MANH (`manh15`)**. The owner's selected PC API/OCR trial runs as the healthy, isolated **`mathvision-pc-preview`** Docker project with a real model runtime, active worker, durable volumes, and an outbound temporary HTTPS tunnel.

**The web publication and PC startup have succeeded. Actual public-browser student login/page/logout, teacher portal SSO/dashboard/logout, and admin SSO/dashboard/stable logout passed after the repairs and redeployment. Real OCR advisors responded, but the recorded final OCR text is still incorrect/unverified.** Native MCP configuration/OAuth succeeded, but the live connector's account/project read check has not passed, so Vercel agent setup must not be labeled fully ready. The CLI was used to publish instead. No Git commit/push, model training, paid server purchase, or Student Mobile change was performed by the documentation subtask.

## Changes covered

- All three static web builds require public HTTPS API/cross-app URLs. Production mocks and developer tools are disabled, and routed pages have Vercel SPA fallback configuration.
- Teacher workflows use actual assignment rosters, actual review-queue details, assignment maximum scores, and authenticated private image requests. Missing analysis is represented as uncertain instead of an invented grade.
- Backend production configuration rejects unsafe secrets/profile combinations, uses an exact CORS allowlist, omits demo seeding, and offers a one-time owner administrator bootstrap on a completely empty users table.
- The AI image runs the real CPU model configuration in production and rejects fixture/canonical overrides. Private AI jobs require the shared internal key.
- The prepared server Compose stack includes named PostgreSQL/Redis/MinIO volumes, a separate worker, read-only model mounts, bounded container logs, and a public gateway allowlist.
- Deployment preflight validates private settings and four recorded runtime model checksums without displaying secrets.
- PC preview scripts safely retain existing secrets/data, verify and disable first-run bootstrap, manage only the owned tunnel process, and rebuild/deploy all three static web outputs when requested.
- New operator guides explain the Vercel projects, private configuration, owner provisioning, persistence, PC tunnel lifecycle, and the difference between local evidence and a public release.

## Verification evidence

| Area | Recorded result | Practical meaning |
| --- | --- | --- |
| Backend full test run | **318 tests, 32 suites, 0 failures/errors** | Verified from the current Gradle JUnit XML results; includes production guards, auth/RBAC/SSO, bootstrap, and teacher image/detail behavior |
| Backend artifact/container | `bootJar` and Linux Java 21 container build passed | Production artifact builds; runtime uses a non-root user and has a health-check client |
| AI focused checks | **27 tests passed** | Production settings and private job authentication checks, reported by the AI container subtask |
| AI Linux CPU inference | Real CRNN, YOLO, and ONNX artifacts loaded and ran | Actual model execution; non-empty output is not an accuracy metric |
| Web configuration/contracts/bundles | **48 final checks passed** | Portal **13** (11 configuration + 2 production), teacher **19** (17 + 2), admin **16** (13 + 3); all three lints passed |
| Deployment preflight | **9 tests passed** | Private environment validation and model checksum failure cases |
| PC initialization | **1 Python test passed** | Secret/provider precedence, exact artifact copy, restart preservation, and incomplete-state protection; 10 Python tests together with the 9 preflight tests |
| PC tunnel process ownership | PowerShell self-check passed | Valid owned process accepted; executable, recycled-PID creation time, and target URL mismatches rejected; dead process not reused |
| PC gateway configuration | Compose publication and Caddy validation passed | Only `127.0.0.1:18081` published for the trial; HTTP gateway retains the explicit public path allowlist |
| Isolated production integration | **30 boolean checks passed** | Verified from the isolated stack's non-secret `results.json` |
| PC startup and web publication | `Start-PC-Preview.ps1 -PublishWeb` passed | Dedicated stack healthy; real `MODEL` ready; all three Vercel prebuilt production publications succeeded |
| Provisioned trial account checks | `ADMIN`, `TEACHER`, and `STUDENT` login/identity plus admin boundary passed | Verified against the isolated preview database; not a browser/UI acceptance claim |
| Public student portal browser check | Login, student page, and logout passed | Root verified through the production portal; logout also cleared the prior profile from the header |
| Production render repair/regression | Null-hook failure reproduced on the old built bundle; repaired bundles passed actual DOM rendering checks | All three apps deduplicate React; checks load built production JavaScript with HTTP fixtures, without mocking React |
| Public teacher browser check | **Passed after redeployment**: portal SSO reached `/dashboard` with the teacher identity and actual empty-database dashboard; teacher logout cleared portal identity | Root used the production browser and real trial credentials; SSO hash was consumed |
| Public admin browser check | **Passed after redeployment**: portal SSO reached `/dashboard` with the `ADMIN` role/profile and actual backend summary/audit rows | At verification the backend reported **1 student, 1 teacher, 0 classes**; these were real trial-database records |
| Admin logout regression | Two real HTTP checks passed for unauthorized and stalled logout responses | Explicit JSON body, 5-second request timeout, and logout excluded from the 401 refresh chain; session clears when logout fails or stalls |
| Built admin logout navigation regression | Actual production bundle check passed | One external portal `/logout` navigation, both local tokens cleared, and 50 ms settling; React was not mocked. The old-bundle regression was not claimed reproduced by this fixture timing |
| Public admin logout browser check | **Passed stably on the repaired bundle** | Actual logout reached `/logout?source=admin`; reopening portal login kept the user logged out without the old profile or an admin bounce |
| Public browser account switch | **Passed: admin logout → portal login → student page** | Actual student authentication reached `/student` with the student profile and no admin identity or redirect bounce |
| Public web HTTP/deep-link checks | **6 HTTP checks passed** | Each site's root and one real deep link returned HTML with the expected security and HTML revalidation headers; this does not prove React rendering or SSO |
| Public API boundary checks | Status-only health `UP`, internal OCR route **404**, anonymous admin **401** | Verified through the active HTTPS tunnel |
| Public OCR upload/detection/trial | **5 boxes in 4.64 s**, trial persisted with HTTP **201 in 0.8 s**, then retrieved with **200** | Real owner image and actual detected geometry/output; no expected transcription or synthetic geometry supplied |
| Public OCR cloud advisors | Real Groq and Gemini both returned **`SUCCESS`** with identical numeric suggestions | Provider connectivity verified; recorded final text still `CRNN_RAW`, correction source `NONE`, verdict `UNVERIFIED` |

The isolated Docker project used fresh production credentials, an empty database, a real model bundle, and disabled external cloud advisors. Its integration run verified health status privacy, initial owner login, absence of demo accounts, exact CORS behavior, SSO exchange/replay rejection, role denials, real account/class/roster/assignment/batch creation, image storage, authenticated byte-identical image retrieval with `no-store`, foreign-owner denials, worker callback completion, and safe teacher review contracts.

The uploaded owner-provided division photo intentionally did not match the smoke assignment's addition type. The resulting status was **`REVIEW_REQUIRED`**. This proves that a real upload passed through storage, queue, model runtime, callback, and review metadata; it is **not** evidence that the division was transcribed correctly or graded accurately. AI readiness was checked independently with Redis, model, and active-worker availability. The temporary smoke project was then cleaned up separately; its data was not the persistent PC trial's data.

The separate public OCR test used the owner's actual division photo. Raw CRNN confidences were **0.31–0.57**, and the raw text was incorrect. Both advisors suggested these five row readings: `49572 | 6`, `015 | 8262`, `037`, `012`, `00`. Their responses came from the configured `qwen/qwen3.8-27b` and `gemini-3.6-flash` services, rather than expected labels or a forced correction. The final text nevertheless remained `CRNN_RAW`, with `correctionSource=NONE` and verdict `UNVERIFIED`. This is provider/integration evidence, not automatic OCR accuracy. Advisor completion time was not measured. The non-secret public results are retained privately in `infra/local-runtime/pc-preview/public-ocr-results.json`; the [PC launcher report](pc-preview-launcher-2026-10-09.md) records the independent checks.

## Remaining public acceptance checks

| Check | Recorded status |
| --- | --- |
| Correct Vercel CLI identity/team | CLI **63.1.0**, authenticated as **`nv-duymanh`**; team **MANH (`manh15`)** verified |
| Vercel plugin | `vercel@openai-curated` revision `0722921d` installed globally and enabled; root verified installed state |
| MCP global configuration and OAuth | Global `https://mcp.vercel.com` configured; native OAuth succeeded |
| MCP authenticated read-only check | **Not verified**: live connector returned an empty `list_teams` result and `get_project` 403; do not mark MCP setup complete |
| Portal production publication | Succeeded: [mathvisionkid-portal.vercel.app](https://mathvisionkid-portal.vercel.app) |
| Teacher production publication | Redeployed: [mathvisionkid-teacher.vercel.app](https://mathvisionkid-teacher.vercel.app); blank-page repair and actual public SSO/dashboard verified |
| Admin production publication | Redeployed: [mathvisionkid-admin.vercel.app](https://mathvisionkid-admin.vercel.app); blank-page repair and actual public SSO/dashboard verified |
| Dedicated persistent PC trial runtime with real provider settings | Healthy `mathvision-pc-preview` stack; real `MODEL` and worker readiness reported |
| Loopback gateway + outbound HTTPS tunnel | Active temporary origin `https://currency-fare-suffering-documented.trycloudflare.com`; API base appends `/api/v1`; gateway config validation passed |
| Public browser student login/page/logout | Passed through the production portal |
| Public browser teacher SSO/dashboard/logout | Passed; portal handoff reached the real teacher dashboard with correct profile; topbar logout returned through `/logout?source=teacher` to portal login and cleared the prior profile |
| Public browser portal logout identity cleanup | Passed; `/logout` returned to `/login` without the old profile in the header |
| Public browser admin SSO/dashboard | Passed; portal handoff reached the real admin dashboard with correct role/profile, backend counts, and audit rows |
| Public browser admin logout/account switch | Passed on the repaired deployed bundle `index-DjUOd5YF.js`: reached portal `/logout?source=admin`, then portal login and actual student login at `/student` with the new student profile; no return to admin |
| Public browser submission upload/review/worker workflow | Not yet established by these browser checks; separate API integration evidence recorded above |
| Restart/publish launcher | `Start-PC-Preview.ps1 -PublishWeb` successfully started/resumed the stack and published all three apps; ownership/initialization self-checks passed |
| Actual post-reboot/end-to-end tunnel replacement exercise | Not claimed; startup logic and current invocation were verified |
| Owner physical-device test | Not performed |
| Public division transcription correctness | **Not passed for recorded final text**: CRNN raw incorrect/low-confidence; both real advisors responded, but suggestions were not promoted to verified final text |
| Independent OCR transcription/arithmetic accuracy evaluation | Not established by deployment checks |

The temporary tunnel hostname can change after restarting. The published web apps use a build-time API URL, so the restart script must be run with `-PublishWeb` to update them. Turning the PC off makes API/OCR unavailable even when Vercel static pages still load.

The latest `Publish-Vercel-Web.ps1` invocation exited 0 and redeployed all three apps with **48/48 checks** and the current API origin. All three latest deployment records report `READY`; their IDs/URLs are retained in ignored `infra/local-runtime/pc-preview/web-deployments.json`. Admin logout now centralizes the loading state, bounded backend request, token cleanup, and one `location.replace` to portal logout; the sidebar no longer issues a competing navigation or clears the user before navigation. Root observed the original race in the public browser, then verified the repaired flow stayed logged out when reopening login. The production-bundle fixture also checks single navigation/token clearing but did not reproduce the old race with its initial fixture timing. Production HTTP checks and bundle rendering tests are not substituted for that live browser evidence. No broader submission/review UI workflow is claimed by the login/dashboard/logout checks.

The trial includes owner-requested accounts provisioned manually after the strong initial-owner bootstrap. Credential values are deliberately omitted from this public report. These test credentials do not establish readiness for wider public account use; remove or replace them before widening the trial. The normal account-password policy was unchanged.

## Requested Vercel agent setup

The root fetched and followed [Vercel's get-started playbook](https://vercel.com/get-started.md). The CLI and guidance plugin are usable, but the active MCP connector's resource access remains unresolved:

```text
▲ Vercel agent setup is partially complete
CLI: 63.1.0, authenticated as nv-duymanh
Guidance: plugin installed and enabled, user/global scope
MCP: blocked resource check despite successful native OAuth,
     global shared endpoint, https://mcp.vercel.com
MCP config: C:/Users/Admin/.codex/config.toml; default write approval retained
Authenticated MCP check: list_teams returned empty; get_project returned 403
Reload: not needed for the successful direct CLI deployments
```

Native OAuth success is not proof that the active connector can access the intended team/project. The root therefore used the verified CLI identity and explicit `manh15` scope for actual deployments and did not label MCP ready. Other Codex configuration was preserved.

## Operator documentation

- [Deploy the web workspaces](../docs/PRODUCTION_DEPLOYMENT.md): Vercel project settings, public build inputs, guarded private runtime, model artifacts, owner bootstrap, future owned-domain server, release checks, and persistence.
- [Vercel web + API/OCR on your PC](../docs/PC_PREVIEW_DEPLOYMENT.md): current owner-selected trial, temporary URL changes, restart/redeployment sequence, and troubleshooting.
- Existing [local setup](../docs/LOCAL_SETUP.md) remains the development workflow. Its demo credentials are not public deployment credentials.

## Skills Applied

- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React authentication/session handling and production rendering behavior.
  - Applied to: identity cleanup, React deduplication, and actual production bundle regression checks.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Minimal safe backend configuration and deployment tooling.
  - Applied to: standard-library preflight/provisioning helpers, private administrator bootstrap, and focused configuration changes.
- `deployments-cicd`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated/vercel/0722921d/skills/deployments-cicd/SKILL.md`
  - Why selected: Vercel CLI setup and production deployment verification.
  - Applied to: explicit team selection, tested prebuilt static deployments, and evidence checks.
- `vercel-services`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated/vercel/0722921d/skills/vercel-services/SKILL.md`
  - Why selected: Separate web, backend, AI worker, and persistent-storage hosting requirements.
  - Applied to: the owner-selected Vercel static web/private PC runtime arrangement and accurate platform capability boundaries.
- `openai-docs`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/openai-docs/SKILL.md`
  - Why selected: Codex global MCP setup and authentication.
  - Applied to: preserving global configuration, OAuth setup, write-approval inspection, and distinguishing native authentication from the unresolved connector read check.

These entries record the skills actually read and applied by the root implementation phases. The documentation-only subtask inspected `AGENTS.md`, `SKILLS_INSTALLED.md`, and the canonical `.agents/skills/` registry; no documentation-specific installed skill matched that narrower task. Implementation traceability is also recorded in [the backend production safety report](cloud-backend-production-safety-2026-10-09.md) and [the PC launcher report](pc-preview-launcher-2026-10-09.md).

Root retained an actual admin dashboard browser screenshot privately as `infra/local-runtime/pc-preview/admin-verified.jpg` (39,346 bytes, Git-ignored). It is desktop-browser evidence and is not included in the public repository or presented as a physical-device test.

## Documentation verification

Commands and variable names were checked against the current `infra/production/` templates, `scripts/deploy/check_production.py`, all three web environment templates/configuration files, and backend/AI production guards. Backend counts were read from JUnit XML, and integration checks were read from the isolated project's non-secret results file. No filled secret environment file was read by the documentation subtask.

Documentation checks passed: **43 local Markdown link targets** exist, code fences are balanced, UTF-8 text has no replacement characters, and `git diff --check` reported no whitespace errors. All three deployment reports include `## Skills Applied`. Git printed only the normal Windows LF/CRLF conversion notice for README.

Primary platform guidance checked on 9 October 2026: [Vercel Vite](https://vercel.com/docs/frameworks/frontend/vite), [Vercel monorepos](https://vercel.com/docs/monorepos), [Vercel Services](https://vercel.com/docs/services), and [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
