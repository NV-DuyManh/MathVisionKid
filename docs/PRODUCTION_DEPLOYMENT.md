# Deploy the web workspaces

MathVision Kids has three Vite applications deployed as separate Vercel projects. The portal project also contains the exported student learning interface at `/study/`, reusing the original Expo/React Native application screens. They share one business API, which remains responsible for authentication, authorization, records, storage access, and AI jobs.

The owner selected **Vercel team MANH (`manh15`)** and a **PC-hosted API/OCR trial** on 9 October 2026. All three web apps have been published, and the dedicated PC runtime is healthy. Student portal login/page/logout, teacher portal-to-workspace SSO/dashboard/logout, and admin SSO/dashboard/stable logout checks passed in the public browser after the fixes and redeployment. Final OCR text remains unverified on the tested division image. Follow [the PC preview guide](PC_PREVIEW_DEPLOYMENT.md) to resume testing after a restart. This document also describes the prepared container stack for a future server deployment.

## Choose the hosting arrangement

| Component | Current trial arrangement | Persistent server arrangement |
| --- | --- | --- |
| Portal, teacher, and admin web | Three Vercel projects; student learning export under portal `/study/` | Same project arrangement with a stable API origin |
| Business API, AI API, and Celery worker | Docker on the owner's PC | Docker on a provisioned server |
| PostgreSQL, Redis, and MinIO | Private Docker services with named volumes | Private Docker services with named volumes and backups |
| Public API connection | Temporary Cloudflare Quick Tunnel to a loopback gateway | Owned API domain with Caddy HTTPS |
| Availability | API/OCR require the PC, Docker, internet, and tunnel to remain running | Depends on the server and provider configuration |

Vercel also documents **Services (beta)** for container workloads. The arrangement here reflects the owner's choice and the repository's tested Compose stack; it is not a claim that Vercel cannot host Java or Python. See [Vercel Services](https://vercel.com/docs/services) when evaluating another hosting arrangement.

## Configure the three Vercel projects

For a repository-backed deployment, import the same repository three times and use these project settings:

| Setting | Portal | Teacher | Admin |
| --- | --- | --- | --- |
| Root Directory | `apps/portal-web` | `apps/teacher-web` | `apps/admin-web` |
| Framework | Vite | Vite | Vite |
| Build Command | `npm run build` | `npm run build` | `npm run build` |
| Output Directory | `dist` | `dist` | `dist` |

Install dependencies using the repository's root `package-lock.json` and npm workspaces. If setting an explicit install command from one of the application directories, use `cd ../.. && npm ci`. Enable access to files outside the Root Directory if required for the workspace installation. Vercel's [monorepo guide](https://vercel.com/docs/monorepos) describes a separate project for each imported application directory.

Each application includes `vercel.json` with the Vite build settings, an SPA fallback to `index.html`, and response headers. The fallback supports opening or refreshing a routed page directly. See [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite).

Reserve the three stable project origins before the final builds. Use the actual origins shown by Vercel, rather than a temporary deployment URL, for the cross-app links and API CORS allowlist.

The projects published during setup on 9 October 2026 are:

| Application | Published project origin | Verification status |
| --- | --- | --- |
| Portal | [mathvisionkid-portal.vercel.app](https://mathvisionkid-portal.vercel.app) | Student login/page/logout passed; stale-profile logout regression fixed |
| Teacher | [mathvisionkid-teacher.vercel.app](https://mathvisionkid-teacher.vercel.app) | Blank-page defect repaired; real portal SSO/dashboard passed |
| Admin | [mathvisionkid-admin.vercel.app](https://mathvisionkid-admin.vercel.app) | Render/logout defects repaired; real portal SSO/dashboard/stable logout passed |

The current PC publisher builds and checks the apps locally, then uploads only tested static output using Vercel's prebuilt deployment flow. For the portal it also exports the original student application and merges its assets and routed fallback under `/study/`. Source datasets, model weights, secret environments, and private runtime state are not uploaded. The project settings above apply to the Vite applications if a later owner-authorized Git integration builds from the repository; the portal/student project additionally needs the same Expo export and merge. A standalone `npm run build` in `apps/portal-web` does not include the student interface.

Since the 10 October login recovery, this prebuilt publisher sets each application's API base to its own stable Vercel origin at `/api/v1` and adds a restricted proxy to the current backend upstream, with API caching disabled. A standalone repository-backed deployment does not automatically receive this generated proxy: configure your own restricted rewrite, or build against a stable direct HTTPS API. See [Vercel rewrites](https://vercel.com/docs/routing/rewrites).

## Student learning website

For an owner-selected free server trial and the required PC-off verification, see [Free cloud deployment](FREE_CLOUD_DEPLOYMENT.md).

After student login, the portal validates the active `STUDENT` role through the backend and opens the shared learning app at [portal `/study/`](https://mathvisionkid-portal.vercel.app/study/). Its existing screens, artwork, calculator, lesson library, photo editing, and learning flows are reused. Browser-specific startup, session storage, and confirmation dialogs use web adapters; default native identity/configuration and native implementations remain preserved.

The web app shares the portal tab's session and validates `/me` before protected screens render. An unauthenticated deep link opens portal login; cached profile data cannot authorize access. This export uses public `EXPO_PUBLIC_API_BASE_URL` and `EXPO_PUBLIC_USE_MOCK=false`, set by the publisher. No provider credentials belong in `EXPO_PUBLIC_*` values either.

The publication namespace is `/study`, with a path-specific SPA fallback before the portal fallback. It must remain consistent with the opt-in `MATHVISION_WEB_EXPORT` base path and exported asset paths. The actual SDK route parser is tested to preserve the learning route. Actual browser checks passed for the shared home, calculator, lessons/profile, gallery/privacy/crop, one structured division reading, and logout/protected reentry. See [the student web parity report](../report/student-web-parity-2026-10-09.md) for the exact evidence and its limits.

### Public build variables

Set these for every Vercel environment that you deploy. All `VITE_*` values are included in browser code and must contain **public URLs or feature flags only**.

| Variable | Portal | Teacher | Admin | Value |
| --- | --- | --- | --- | --- |
| `VITE_API_BASE_URL` | Required | Required | Required | Public HTTPS API address ending in `/api/v1` |
| `VITE_TEACHER_URL` | Required | — | — | Teacher HTTPS origin |
| `VITE_ADMIN_URL` | Required | — | — | Admin HTTPS origin |
| `VITE_PORTAL_URL` | — | Required | Required | Portal HTTPS origin |
| `VITE_SHOW_DEV_TOOLS` | `false` | `false` | `false` | Development UI disabled |
| `VITE_USE_MOCK` | `false` | `false` | `false` | Real API calls |

An origin contains the scheme and hostname, with no path, trailing slash, query, fragment, or credentials. The API value includes its API base path. The per-app `.env.production.example` files show the required variable names without credentials.

Every static build validates its URLs and fails if a required value is missing or points to a local/non-HTTPS address. Mock data and developer tools stay disabled in static builds, including builds run with a different Vite mode.

Never put JWT secrets, internal callback keys, storage credentials, database passwords, or Groq/Gemini keys in Vercel's `VITE_*` settings. These belong only in the private backend/AI environment. Changing a build variable requires a new build and deployment before the browser uses the new value.

## Prepare the private container runtime

The future server configuration is [infra/production/compose.yml](../infra/production/compose.yml). It contains PostgreSQL, Redis, MinIO, private AI API and worker services, the business API, and Caddy. Java and AI run as non-root users. Model artifacts are mounted read-only, rather than bundled into the images.

The base Compose file publishes ports **80 and 443** for the owned-domain Caddy gateway. **Do not use its public gateway configuration directly for the PC Quick Tunnel trial**; the PC arrangement needs a loopback-only HTTP gateway and the override described in [the PC preview guide](PC_PREVIEW_DEPLOYMENT.md).

Copy [the production environment template](../infra/production/.env.production.example) to an ignored private environment file. Replace every placeholder and protect the file with owner-only filesystem permissions. The templates are safe to share; filled environment files are not.

| Private input | Requirement |
| --- | --- |
| `API_DOMAIN` | Actual API DNS hostname; no scheme or path |
| `CADDY_EMAIL` | Certificate contact email |
| `CORS_ALLOWED_ORIGINS` | Comma-separated exact public HTTPS origins of the three web apps |
| `MODEL_BUNDLE_DIR` | Absolute host directory containing the verified runtime artifacts |
| `DB_PASSWORD`, `JWT_SECRET`, `INTERNAL_API_KEY`, `MINIO_SECRET_KEY` | Different cryptographically generated secrets, at least 32 bytes each for deployment preflight |
| `REDIS_PASSWORD` | A different random hexadecimal secret, at least 64 characters |
| `MINIO_ACCESS_KEY` | Dedicated storage identity; not the development account |
| Provider flags and keys | A valid secret key for each enabled provider; disable a provider explicitly when unused |

Keep the `mathvision` storage bucket name. Backend and AI must share the same internal key and storage credentials. The Compose environment sets the backend to `prod`, AI to `production`, recognition to `MODEL`, the local handwriting provider to CRNN, and canonical fixture overrides to `false`. Development seed accounts are excluded from production.

The main photographed-question reader needs the configured cloud vision service. Loading local handwriting weights does not replace that service. Disabling both advisors is useful for an isolated integration test, but does not provide the full notebook-question experience. Preserve intended provider model names and check actual availability before releasing.

### Required runtime model bundle

Restore only these runtime artifacts using [Drive storage and recovery](DRIVE_DATA_STORAGE.md), or obtain the authorized bundle from the owner. Datasets, training runs, and evaluation archives are not needed in the deployment image.

```text
model_manifest.json
yolov8n_mathvision_det_v1.pt
label_map_detection.json
ocr/text_detection_cn_ppocrv3_2023may.onnx
ocr/text_detector_manifest.json
ocr/crnn_vi_handwriting_v1/best_cer.pth
ocr/crnn_vi_handwriting_v1/vocab.json
ocr/crnn_vi_handwriting_v1/model_manifest.json
```

From the repository root, validate the private environment and four recorded model checksums:

```powershell
py -3.12 scripts/deploy/check_production.py --env-file infra/production/.env.production
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml config --quiet
```

The validator prints the names of invalid settings without revealing their values. It does not contact a provider, establish DNS ownership, test backups, or prove cloud availability. Use `--models` to override the model directory for artifact verification before a transfer.

## Provision the first owner

A fresh production database has no demo accounts. On its first start, explicitly set `BOOTSTRAP_ADMIN_ENABLED=true` with the owner's valid email, a generated password of **16–72 UTF-8 bytes**, and a display name. The password must satisfy startup validation, including at least eight distinct characters.

Bootstrap creates one active administrator only when the **entire users table is empty**. It never replaces or updates an existing account. After verifying the owner's login, set `BOOTSTRAP_ADMIN_ENABLED=false`, remove the bootstrap email/password/name from the private deployment environment, and recreate the backend container. Store the initial credential in an owner-controlled password manager, not Git or a shared report.

Use the administrator workflow to create real teacher/student accounts. The backend enforces roles regardless of which web page was used. An administrator does not automatically acquire teacher access or teacher SSO.

## Start an owned-domain server

This section requires a provisioned server, the verified model bundle, configured DNS, and the private environment. No server purchase or paid subscription is implied by these commands.

```powershell
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml up -d --build
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml ps
```

Allow the build and health checks to finish. The Caddy gateway forwards only `/api/v1/*` and `/actuator/health`; other paths return 404. Internal AI routes and callback routes stay within the private Docker network. PostgreSQL, Redis, MinIO, and the AI API have no public host port in the base configuration.

Deploy or redeploy all three web projects after setting their public build values. With the authorized Vercel CLI account, run the deployment from each linked application directory using the intended team:

```powershell
vercel whoami
vercel teams ls
vercel --prod --scope manh15
```

Check the selected project and team before accepting CLI prompts. A deployment from local source does not commit or push code. Keep any generated `.vercel` linkage directory out of Git.

## Verify the public result

Use actual deployed origins and owner-provisioned accounts. Complete all of these before calling the deployment functional:

- Open each web app and refresh a nested route directly. Verify navigation uses the intended portal, teacher, and admin origins.
- Request `/actuator/health` through the public API; it must return status only. Request an internal callback path through the public gateway; it must return 404.
- Log in with the real owner and appropriate teacher account. Test SSO once; exchanging the same handoff ticket again must fail.
- Check that an allowed web origin can reach the API and an unrelated origin is denied. Preview deployments need their own exact CORS entries; do not use a wildcard.
- Create a class, student membership, assignment, and submission batch. Upload an authorized image, wait for the worker callback, and review the detected work.
- Check private image access using the owning teacher. Other teachers and student accounts must not gain teacher image access. Image responses must use `Cache-Control: no-store`.
- Review the transcription against the photo. A completed job or an HTTP 200 is not evidence that the text, arithmetic, or grade is correct.

The local verification evidence and remaining public checks are recorded in [the deployment readiness report](../report/cloud-deployment-readiness-2026-10-09.md).

The current trial includes owner-requested test accounts provisioned separately from production seeding. Their role/login checks passed in the isolated trial database. These are trial credentials, not the strong owner bootstrap credential or a general-release account setup; keep their credential details out of Git and remove or replace them before inviting users beyond the trial.

## Keep data and recover safely

Named volumes persist database, queue, images, and Caddy state across ordinary restarts or container rebuilds. Stop the project without deleting volumes:

```powershell
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml down
```

`down --volumes` deletes this project's persisted data. Do not use it for ordinary maintenance. Keep versioned PostgreSQL backups, private image backups, and protected copies of configuration/model manifests outside the running stack, then test a restore into an isolated project. A named Docker volume alone is not a backup, and Google Drive streaming alone does not prove that a backup has finished uploading.

SSO tickets currently live in one backend process and expire on a backend restart. Request a fresh ticket after restarting. This deployment uses one backend replica; multiple replicas need shared ticket storage or sticky routing before scale-out.
