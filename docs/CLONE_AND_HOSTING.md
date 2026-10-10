# Clone the project or use the shared website

Source code, a running backend, and a published website are separate things. A Git clone gives you source code. It does not copy a running service, private credentials, accounts, images, or database volumes.

## Use the existing shared website

Open [MathVisionKid](https://mathvisionkid-portal.vercel.app/login). No clone is required. Your browser connects to the currently deployed backend and uses accounts stored in that backend.

**Current status:** the web is on Vercel, while API/OCR and persisted data remain on the owner's PC. Visitors from another computer can use the shared website while that backend and its tunnel are available. Turning off the owner's PC stops login and OCR for everyone; running a different clone does not automatically repair that shared deployment.

## Run your own copy locally

1. Follow [Local setup](LOCAL_SETUP.md) or [Vietnamese setup](HUONG_DAN_CAI_DAT.md) for Docker, Java, Node, Python, dependencies, models, and private provider settings.
2. Run `RUN_MATHVISION.bat` from your checkout. The local portals and mobile connection use your own backend.
3. A new clone has no private PC preview configuration, so public publication is skipped. This avoids uploading another developer's empty database connection to the owner's website.
4. Use accounts provisioned in your own local backend. An account existing in the owner's shared database is not automatically present in your local database.

Model artifacts and provider access are required for actual recognition. They are deliberately excluded from Git. Follow the artifact instructions in the setup guides; do not substitute prepared answers or fixture OCR for missing inputs.

## Publish an independent copy

Use [Production deployment](PRODUCTION_DEPLOYMENT.md) to configure your own Vercel projects, actual public app URLs, HTTPS API hostname, private service secrets, model bundle, and exact backend CORS allowlist. The PC preview publisher contains the owner's project names and MANH scope; it is an owner restart helper, not an automatic deployment to someone else's account.

Never copy the owner's `.env.preview`, credentials file, or private data into Git to make a clone run. Never point the owner's shared link at an unrelated developer database. Changes to public API build variables require a new web build and publication.

## Keep the shared link running independently of any developer PC

Host the existing API, AI worker, PostgreSQL, Redis, and private image storage on one owner-controlled online server. Keep the web workspaces on Vercel. The repository already contains production Dockerfiles, health checks, persistent volumes, restart policies, the HTTPS gateway and input validation.

Follow [the free cloud trial guide](FREE_CLOUD_DEPLOYMENT.md). Account registration and a real server are still required; this migration has not been completed. Before switching the shared website, verify model inference on the server architecture, restore persisted data in isolation, publish all web apps against the stable HTTPS API, and test login/OCR with the owner's PC off. Only then is PC-independent operation verified.

For the current PC trial, run the launcher and wait for `Public Website: READY`. Docker manages the tunnel, so it continues after the launcher closes. Browser API addresses remain on each app's stable Vercel origin. A tunnel restart can change the upstream hostname: rerun the launcher to update Vercel's routing. Reload once if a tab still has the older direct-tunnel bundle. This arrangement still requires the owner's PC and Docker; it is not PC-independent hosting.
