# PC preview launcher verification — 2026-10-09

The Windows launcher provisions a separate `mathvision-pc-preview` Docker project and keeps its database and uploads when stopped. Its HTTP gateway publishes only `127.0.0.1:18081`; the outbound Cloudflare quick tunnel exposes the allowed API routes over HTTPS. Internal callbacks, databases, storage and the AI runtime have no separate public ports.

Initialization copies only the eight required runtime files and verifies four recorded hashes. It copies the selected provider settings from the existing `.env`, followed by `.env.local`, generates independent service secrets and writes the owner credentials into the restricted, Git-ignored preview directory. Repeated initialization preserves the existing configuration. The launcher disables and removes one-time bootstrap credentials after verifying the owner login and administrator role.

Tunnel reuse and shutdown verify the saved process executable, target URL and creation timestamp. A mismatched or recycled PID is rejected. Stopping uses only the named preview Compose project and retains its volumes. `-PublishWeb` calls the separate web publishing script with the current API origin; a replacement quick tunnel requires a web redeployment.

## Verification

- Ten deployment Python checks passed in total: **9 production preflight tests + 1 PC initialization test**, including initialization idempotency and provider file precedence. The PowerShell process ownership check below is separate.
- The ownership self-check passed in Windows PowerShell: legitimate process accepted; unrelated executable, recycled PID and different target rejected; dead process not reused.
- The merged Compose configuration validated and published only the expected loopback gateway port.
- The real Caddy container validated the gateway configuration.
- Git ignore checks passed for preview environment files, owner credentials, temporary model bundles and Vercel project links.
- No persistent preview service or tunnel was started by this implementation agent. Live startup and public HTTP behavior require the root deployment verification.

## Independent public HTTP and OCR check

After the root launched the preview and deployed the three sites, six public requests succeeded: each site's root and one real deep link (`/student`, `/dashboard`, `/users`). Each returned HTML with `nosniff`, `DENY`, `no-referrer` and an HTML cache policy requiring revalidation. These HTTP checks do not prove React rendering or SSO; the root's browser verification remains separate.

The public API returned status-only health `UP`, blocked an internal OCR route with HTTP 404 and denied anonymous administrator access with HTTP 401. The isolated preview student authenticated successfully.

The owner's actual long-division image, SHA-256 `23d5352bb93920d4ee2e3f5a6902c8f4a26242ee31bd48bae69b3e859dec4bea`, produced five detector boxes in 4.64 seconds. A test trial persisted those actual boxes and output with HTTP 201 in 0.8 seconds, followed by HTTP 200 retrieval. No expected transcription or synthetic geometry was sent.

Raw CRNN output was inaccurate for this arithmetic image. Both advisors later reported `SUCCESS`, with identical suggestions `49572 | 6`, `015 | 8262`, `037`, `012`, `00`. The returned provider model names were `qwen/qwen3.8-27b` and `gemini-3.6-flash`. The recorded final text remained `CRNN_RAW` and `UNVERIFIED`; suggestions were not automatically promoted into accepted labels. Advisor completion wall time was not instrumented.

This verifies a real upload, detection, storage and provider response through the public connection. It does not establish dataset accuracy, physical-device behavior or correct final OCR text. Safe responses and HTTP metadata are recorded privately at `infra/local-runtime/pc-preview/public-ocr-results.json`, without access tokens, passwords or storage object keys.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Windows deployment scripts and minimal safe provisioning logic.
  - Applied to: reuse of the production Compose stack and existing validation helpers, Python standard-library provisioning, native Windows process ownership checks and runnable verification.
