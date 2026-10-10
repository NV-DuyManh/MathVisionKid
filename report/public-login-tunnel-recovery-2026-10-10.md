# Public login connection recovery — 2026-10-10

## Result

The public portal can log in again. Student, teacher, and admin sign-in succeeded through the deployed portal in a real browser and opened the corresponding student app or role dashboard. The three existing demo accounts and passwords were retained.

The isolated PC backend was healthy and accepted all three accounts locally. The deployed portal still contained an obsolete Quick Tunnel API address whose tunnel process was gone. That prevented authentication requests from reaching the backend and produced the generic login failure message. Older tunnel logs also showed UDP/IPv6 connection failures.

## Changes

- `scripts/deploy/PC-Preview.Common.ps1` checks the public health endpoint with bounded retries and restricts accepted origins to HTTPS Quick Tunnel hostnames.
- `scripts/deploy/Start-PC-Preview.ps1` validates public connectivity before reusing a saved tunnel. An unreachable tunnel is replaced only after confirming its process identity, executable, creation time, and private gateway target.
- Newly started tunnels use HTTP/2 and IPv4 to address the network failures observed on this PC.
- Publication begins only after public health reports `UP`. The first recovery attempt exposed a short new-hostname readiness window; the retry allowance was increased, then the complete startup and publication succeeded.
- `RUN_MATHVISION.bat` already invokes this script with `-PublishWeb`, so the same recovery runs during normal startup. The deployment guide explains this behavior.

## Live deployment and verification

The successful recovery command exited with code 0 and published all three existing projects in team MANH:

| App | Stable URL | Deployment verified this phase |
| --- | --- | --- |
| Portal | https://mathvisionkid-portal.vercel.app | https://mathvisionkid-portal-4e9sddjnt-manh15.vercel.app |
| Teacher | https://mathvisionkid-teacher.vercel.app | https://mathvisionkid-teacher-h7d8by9xh-manh15.vercel.app |
| Admin | https://mathvisionkid-admin.vercel.app | https://mathvisionkid-admin-iipbdnwbk-manh15.vercel.app |

At verification time the public API origin was `https://held-actress-precisely-nat.trycloudflare.com`. This is a temporary deployment snapshot, not a permanent address. The deployed portal bundle was checked to contain this current origin.

- Public API login and `/me` returned the expected STUDENT, TEACHER, and ADMIN roles.
- Browser student login opened `/study/` with the student homepage.
- Browser teacher login opened the teacher `/dashboard` and displayed the demo teacher.
- Browser admin login opened the admin `/dashboard` and displayed the demo admin.
- The public API accepted the exact portal CORS origin. The internal AI jobs route remained blocked with HTTP 404.
- Actual student browser screenshot: `infra/local-runtime/pc-preview/login-recovered-20261010.png` (private local evidence, no password or token shown).

## Tests

- Preview PowerShell ownership and readiness tests passed, including healthy, delayed, unreachable, DOWN, malformed-origin, unrelated-process, and recycled-PID cases.
- PowerShell parsing checks passed for the startup and common scripts.
- Launcher regression tests passed: 4 tests.
- Publisher checks passed: portal config/auth 11, portal production 2; student web configuration 4; teacher config/API/auth 17, teacher production 2; admin config/auth 13, admin production 3.
- All web builds and the fresh Student Web export passed before publication.

The readiness regression tests use mocked network responses; live public health, API sign-in, and browser sign-in were verified separately as described above. No physical-device test is claimed.

## Operating limits and scope

The current free PC preview still requires this PC to stay awake with Docker and Internet available. Running RUN again repairs a lost tunnel and updates Vercel, but does not provide cloud hosting while the PC is off or continuously supervise the connection after startup. A network outage, Docker failure, or Vercel publication/authentication failure is still possible and should leave an explicit failed startup status. Reload an already-open browser tab after a changed deployment.

No student UI, account credentials, model training, or AI runtime image was changed in this phase. This report makes no new OCR or tutor-quality claim. No commit or push was performed.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Recover the deployment connection by extending the existing launcher and publisher.
  - Applied to: Public health validation, owned tunnel recovery, bounded retries, and focused regression checks.

## Documentation checked

- [Cloudflare tunnel run parameters](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/run-parameters/) documents HTTP/2 transport and IPv4 edge selection used for the recovery.
- [Expo SDK 57 documentation](https://docs.expo.dev/versions/v57.0.0/) was read during the preceding launcher implementation, as required by the project. No Expo application code was edited during this recovery.
