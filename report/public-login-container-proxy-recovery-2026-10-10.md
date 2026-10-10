# Public login recovery — 10 October 2026

## Outcome

The public portal, teacher and admin were republished with stable browser API addresses and a Docker-managed upstream connection. The real RUN launcher reached `Public Website: READY` and exited with code 0 after its final pause was closed. The same tunnel container and start time remained active afterward, and public API health passed.

The earlier successful Windows-process login check did not establish continued availability. That connection subsequently disappeared; this report supersedes [the earlier restart report](restart-portability-and-cloud-handoff-2026-10-10.md).

## Root causes and changes

- The saved Windows tunnel process was no longer present. Its old public endpoint returned Cloudflare 530/1033, including through a Vercel proxy preview. The logs established loss of connection, but did not establish why Windows terminated the process.
- The preview Compose override now runs the official Cloudflare `2026.10.0` image, pinned to its multi-platform manifest digest. Docker manages its lifetime with `restart: unless-stopped`; it has no host port publication. Logs are limited to three files of 10 MB each.
- Startup reads only logs since the current container's `StartedAt`, checks actual public readiness, and restarts only this project's connection service when necessary. The earlier Windows executable downloader was removed. Ownership checks remain solely for safe migration/cleanup of legacy process state.
- Every deployed web app calls its own stable Vercel origin at `/api/v1`. The publisher generates a restricted proxy to the current upstream, with API response caching disabled. The student website uses the portal's same API address. Other private paths are not proxied. Backend authentication and RBAC remain authoritative.
- Two regression tests reproduced an old session check erasing a new login or attempting teacher SSO after a new student login. Manual login now aborts the previous session check; profile and SSO requests honor cancellation. Old refresh responses cannot replace or clear a newer session's tokens. Login requests have a bounded timeout and distinguish invalid credentials, permission rejection, rate limiting and connection/server failures.
- The launcher's process-local Windows PowerShell module-path fix from the earlier recovery was retained. Native student implementations/configuration were not changed for this repair.

## Verification

- Portal configuration/auth checks: **16 passed**, including five new stale-session/refresh regressions. The two component regressions failed before the fix and passed after it.
- The real publisher completed all three production builds, configuration/bundle checks and the student web export/API validation before upload. Vercel recorded all three deployments as `READY`.
- Windows PowerShell checks passed for legacy process ownership, bounded public health probing and five container readiness cases: current, delayed, missing, stopped and hostname timeout. Old log entries are excluded.
- Four batch launcher regression tests passed, including native security module loading, configured publication, failure handling and fresh-clone behavior.
- Actual RUN exit code: **0**. After closing it, the tunnel retained container ID `316d55beb20063af07fa2bdb3abdd24567c77d06d247fe9121a1b096f722684f` and start time `2026-10-10T12:28:31.867530287Z`; public readiness passed at `2026-10-10T12:36:46Z`.
- Each deployed `/api/v1/me` rejected anonymous access with **401** through the restricted proxy. Generated output pointed at the current upstream and disabled caching. A protected preview also returned the backend's JSON authentication error rather than Cloudflare 530/1033.
- Public browser checks after closing RUN: student login reached `/study/` and student logout succeeded; teacher portal SSO reached the real teacher dashboard and logout succeeded. Admin SSO reached the real admin dashboard, retained its backend-validated session after a page reload and logged out successfully. All three logout flows returned to the portal's logged-out screen.
- PowerShell syntax checks and focused whitespace checks passed. Documentation now describes the Docker tunnel, stable proxy, restart procedure and clone behavior.

Publication record: `2026-10-10T12:32:09.8789561Z`, scope `manh15`. Public applications: [portal](https://mathvisionkid-portal.vercel.app/login), [teacher](https://mathvisionkid-teacher.vercel.app), [admin](https://mathvisionkid-admin.vercel.app).

Ignored local evidence: `infra/local-runtime/pc-preview/login-container-verification-20261010.json`, `web-deployments.json` and `stable-proxy-login-20261010.png`. No credentials or authorization tokens were copied into this report.

## Availability limits

Closing RUN is now verified to leave the connection running. No physical PC reboot was performed. A restarted Quick Tunnel can choose another hostname: run RUN again to update Vercel's upstream routing. Docker's restart policy alone does not update that routing. Tabs from before the stable-address migration need one reload.

API/OCR still depend on the owner's PC, Docker and internet. Oracle registration and a server have not been completed; no PC-independent or 24/7 hosting result is claimed. The signup page announced maintenance from 18:23 to 21:00 Vietnam time on 10 October; its actual reopening requires checking the provider. Follow [the free cloud guide](../docs/FREE_CLOUD_DEPLOYMENT.md) for the remaining provisioning, restore and PC-off verification gates.

This phase did not train models, build a new AI image, test physical-device OCR, edit native student source, commit or push. Existing unrelated workspace changes and persistent data were preserved.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Repair connection lifetime using the existing Compose stack and publisher.
  - Applied to: Minimal container migration, scoped recovery, removal of the superseded downloader and restart/clone documentation.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Resolve asynchronous React login and session races.
  - Applied to: Cancelled profile/SSO checks, refresh guards and meaningful regression tests.

## References

- [Expo 57 versioned documentation](https://docs.expo.dev/versions/v57.0.0/) read before code changes.
- [Official Cloudflare container](https://hub.docker.com/r/cloudflare/cloudflared).
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
- [Vercel rewrites](https://vercel.com/docs/routing/rewrites) and [Build Output API routes](https://vercel.com/docs/build-output-api/configuration).
