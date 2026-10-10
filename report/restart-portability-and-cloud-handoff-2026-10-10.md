# Restart recovery, clone guidance and cloud handoff — 10 October 2026

> **Superseded for current login availability:** after the checks below, the Windows tunnel process disappeared and the public endpoint returned Cloudflare 530/1033. The reason that process terminated is not established. The executable resolver described here was subsequently removed in favor of a Docker-managed tunnel. Follow [the current recovery report](public-login-container-proxy-recovery-2026-10-10.md) for the deployed fix and post-launcher verification. The results below describe the earlier run, not continuous availability.

## Outcome

The real `RUN_MATHVISION.bat` invocation reached `Public Website: READY`, recovered the public connection and published portal, teacher and admin against its current API origin. Browser login succeeded for all three authorized demo roles. Cloud migration remains incomplete: Oracle registration is blocked by its scheduled signup maintenance and no account or VM has been created.

## Findings and changes

- The owner's attached restart log reached local readiness but failed public startup because the expected Cloudflare executable could not be found. Its earlier absence is established by the log; the reason it was unavailable is not proven.
- `Resolve-PreviewCloudflared` now checks the current Windows user's cache, then an installed PATH executable, then obtains the official pinned Cloudflare release when necessary. New downloads require the published SHA-256 and a valid Cloudflare publisher signature before installation. Failed downloads are cleaned up. An explicitly selected missing path fails without substituting another executable.
- An actual run through the batch launcher exposed another failure that a direct PowerShell invocation did not: inherited PowerShell 7 module paths prevented Windows PowerShell from loading `Microsoft.PowerShell.Security`. RUN now puts Windows PowerShell's own modules first, within its existing `setlocal` scope. User-wide environment settings were not changed.
- The existing tunnel ownership and readiness checks were retained. Only the verified project-owned tunnel was stopped to exercise connection recovery; unrelated processes and persistent Docker volumes were not stopped or deleted.
- Added `docs/CLONE_AND_HOSTING.md` and updated README, PC preview and free cloud instructions. A fresh clone starts its own local environment, without copying private configuration or taking over the owner's shared Vercel deployment. Source code alone does not supply private accounts, model artifacts or a running backend.

## Verification

- Windows PowerShell preview checks passed: process ownership, bounded public readiness probes and nine executable resolution/rejection scenarios.
- Four actual batch launcher regression tests passed, including loading the native security module from the launcher child process, configured publication, public failure and fresh-clone behavior.
- A real download into an isolated empty tools directory verified Cloudflare 2026.10.0's published hash, Windows signature and executable version. The temporary duplicate was removed afterward.
- Production input and runtime model checksum preflight passed. This does not prove cloud provisioning or ARM64 compatibility.
- Normal RUN startup completed local, Metro and diagnostic readiness; portal/teacher/admin builds and 52 web configuration/production checks passed; the student web export was regenerated and its service address checked before publication.
- RUN reached its intentional final QR/pause screen with `Public Website: READY`. No process exit code is claimed for the still-paused live launcher.
- The current public API health returned `UP`. Browser evidence: student reached `/study/`, teacher reached the teacher `/dashboard`, and admin reached the admin `/dashboard`. Student and teacher logout were verified; admin logout was also initiated and verified before leaving the browser.
- Focused whitespace checks passed. No physical PC reboot, physical-device OCR test or fresh-clone installation was claimed.

Ignored local evidence: `infra/local-runtime/pc-preview/restart-launcher-20261010.log` and `infra/local-runtime/pc-preview/restart-login-20261010.png`. Publication record time: `2026-10-10T12:09:10.954196Z`, scope `manh15`, API origin `https://flows-aerospace-bodies-hazards.trycloudflare.com`.

Public websites: [portal](https://mathvisionkid-portal.vercel.app), [teacher](https://mathvisionkid-teacher.vercel.app), [admin](https://mathvisionkid-admin.vercel.app).

## Remaining cloud work

Oracle's fully loaded [signup page](https://signup.cloud.oracle.com/) disabled its form and announced maintenance on 10 October 2026 from 11:23 to 14:00 GMT, equivalent to 18:23–21:00 Vietnam time. The owner can retry after the announced window; actual reopening depends on Oracle. Accurate personal details, email verification, password creation, any billing verification and acceptance of agreements still require the owner's participation.

After account creation, the migration must still verify free capacity, the complete ARM64 build and model inference, storage image availability, isolated data restore, stable public HTTPS routing and login/OCR while the owner's PC is off. `docs/FREE_CLOUD_DEPLOYMENT.md` lists these gates. The current shared website still depends on this PC for API/OCR availability.

No model training, new AI image build, Student Mobile source edit, commit or push was performed in this phase. Existing unrelated workspace changes were preserved.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Recover startup using the existing launcher and deployment helpers.
  - Applied to: Verified executable acquisition, process-local PowerShell compatibility, focused regression checks and clone/hosting documentation.

## References

- [Expo 57 versioned documentation](https://docs.expo.dev/versions/v57.0.0/) was read before implementation; no Expo/native code was changed.
- [Official Cloudflare release 2026.10.0](https://github.com/cloudflare/cloudflared/releases/tag/2026.10.0) supplies the pinned binary and published hashes.
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) describes the temporary trial connection.
