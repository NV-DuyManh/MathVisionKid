# Free cloud trial: keep MathVisionKid running with the PC off

**Status, 10 October 2026:** Vercel hosts the websites. The API, OCR, queue, database and private image storage still run in the isolated PC preview. No cloud account or VM has been provisioned. This guide is a migration plan, not evidence of a working cloud deployment.

## Selected option

Try one **Oracle Always Free Ampere A1 VM**, with the websites remaining on Vercel. This preserves the existing multi-container application rather than replacing OCR or authentication with simulated responses.

Oracle currently documents **2 OCPUs and 12 GB RAM total**, and **200 GB combined boot/block storage**, in the account's home region. Free capacity can be unavailable and idle instances can be reclaimed. Select resources explicitly covered by Always Free; introductory trial credit does not make other resources permanently free. See [Oracle's current limits](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

Render Free is a poor fit for this unchanged stack: web services sleep after 15 idle minutes, have no persistent disks, and its free database expires after 30 days. See [Render's documented limits](https://render.com/docs/free).

## Account handoff

The owner must supply accurate account details, verify their email, set the account password, complete any identity/card verification, and accept the service agreement themselves. Use the [official signup page](https://signup.cloud.oracle.com/). Oracle describes card verification and its temporary authorization hold in [the Free Tier FAQ](https://www.oracle.com/cloud/free/). Never put card details, verification codes, passwords or private SSH keys in this repository or chat.

The signup page was reopened during the 10 October 2026 restart-recovery work. After it finished loading, Oracle displayed scheduled maintenance from **11:23 to 14:00 GMT on 10 October 2026** (**18:23 to 21:00 Vietnam time**) and disabled the account-information fields. Retry after the announced window; reopening is subject to Oracle's actual service status. Registration has not been submitted and no VM has been created.

## Before provisioning or moving data

1. Confirm actual Always Free allowance and available A1 capacity in the console. Proposed trial size: one Ubuntu ARM64 VM, 2 OCPUs, 12 GB RAM, 50 GB boot disk, within the account's total free allowance. Do not substitute a paid shape or upgrade billing automatically.
2. Verify the complete ARM64 build first. This workstation's successful AMD64 container build does not prove ARM compatibility. The pinned PyTorch 2.14.0 and torchvision 0.29.0 CPU indexes list Python 3.12 ARM64 wheels, but the whole application must still build and pass inference on ARM64.
3. Resolve the storage image pull before cloud rollout: registry inspection of the pinned MinIO tag returned access errors on this workstation. A cached local image is insufficient proof that a fresh ARM64 server can pull it. Do not replace it with an unverified mirror or silently remove private storage.
4. Obtain a stable public HTTPS API hostname, owner-controlled DNS, and certificate contact. The temporary PC Quick Tunnel address must not remain baked into the cloud websites.
5. Back up PostgreSQL, private images and configuration separately. Verify a restore into an isolated environment before the existing trial is retired. A Drive shortcut, stream-only file or Docker volume alone is not a verified backup.

## Reuse the production stack

Follow [the production deployment guide](PRODUCTION_DEPLOYMENT.md) for secrets, model checksums, private networking, bootstrap, accounts and recovery. Transfer only the required eight runtime model artifacts, application source/build inputs, and authorized persisted data. Training photos and archives are unnecessary on the VM.

On the server, install Docker Engine and Compose from [Docker's Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/), which cover ARM64. Enable Docker at boot. Use an owner-controlled SSH key; restrict SSH ingress to the owner's IP and publish only the Caddy gateway on 80/443. PostgreSQL, Redis, MinIO and internal AI endpoints remain private.

Commands below run from the repository root on the server, after preparing the ignored `infra/production/.env.production` and verified model bundle:

```sh
chmod 600 infra/production/.env.production
python3 scripts/deploy/check_production.py --env-file infra/production/.env.production
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml config --quiet
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml build ai backend
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml up -d
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml ps
```

Stop on a failed preflight, pull, build or health check. The Compose services use persistent named volumes and `restart: unless-stopped`; ordinary maintenance must not delete those volumes. Confirm that total memory, disk and CPU usage fit the VM while OCR and the worker are both active.

Keep vision provider secrets only in the private server environment. Free VM hosting does not change a provider's API quota or billing. Local handwriting weights and the photographed-question vision reader are distinct parts of the pipeline.

After the stable cloud API is healthy, republish **all three** tested website builds from the owner's Windows checkout:

```powershell
./scripts/deploy/Publish-Vercel-Web.ps1 -ApiOrigin '<actual-cloud-HTTPS-origin>'
```

## Completion evidence required

- API health succeeds over the stable HTTPS hostname and CORS accepts only the intended website origins. Public internal routes remain denied.
- Backend-authorized student, teacher and admin logins work; logout and protected deep links work.
- Upload an owner-approved real photograph through the deployed student website, complete privacy/crop, and compare every read value with the source. Disputed text remains editable and must be confirmed before a lesson starts.
- Submit a genuine worker job and verify completion, private image access and retained data after a server restart.
- Turn off the owner's PC and repeat login and OCR from another device/network. This check has **not** yet been performed.
- Restore the data backup in isolation and inspect the resource allowance/usage in Oracle before calling the trial complete.

This is a free trial plan with availability limits, not a guarantee of uninterrupted 24/7 service.
