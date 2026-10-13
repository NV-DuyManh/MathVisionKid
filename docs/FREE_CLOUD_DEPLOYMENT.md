# Free cloud trial: keep MathVisionKid running with the PC off

**Status, 10 October 2026:** Vercel hosts the websites. The API, OCR, queue, database and private image storage still run in the isolated PC preview. Oracle account creation and Console access are confirmed, with a Free Tier account in Singapore. Two A1 requests and one E2 Micro fallback request returned **out of capacity**; no VM has been provisioned. This guide is a migration plan, not evidence of a working cloud deployment.

## Selected option

Try one **Oracle Always Free Ampere A1 VM**, with the websites remaining on Vercel. This preserves the existing multi-container application rather than replacing OCR or authentication with simulated responses.

Oracle currently documents **2 OCPUs and 12 GB RAM total**, and **200 GB combined boot/block storage**, in the account's home region. Free capacity can be unavailable and idle instances can be reclaimed. Select resources explicitly covered by Always Free; introductory trial credit does not make other resources permanently free. See [Oracle's current limits](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

Render Free is a poor fit for this unchanged stack: web services sleep after 15 idle minutes, have no persistent disks, and its free database expires after 30 days. See [Render's documented limits](https://render.com/docs/free).

## Account handoff

The owner must supply accurate account details, verify their email, set the account password, complete any identity/card verification, and accept the service agreement themselves. Use the [official signup page](https://signup.cloud.oracle.com/). Oracle describes card verification and its temporary authorization hold in [the Free Tier FAQ](https://www.oracle.com/cloud/free/faq/). Never put card details, verification codes, passwords or private SSH keys in this repository or chat.

The owner completed registration after the announced 10 October maintenance window and signed into the Console on the computer. The Console shows a Free Tier account in **Singapore (Singapore), `ap-singapore-1`**. No VM has been created. A general account-creation support page shown earlier did not establish a rejection reason. The [home region cannot be changed](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingregions.htm); nearby geography does not guarantee free compute capacity.

## Current provisioning blocker

The owner authorized creation of `mathvisionkid-cloud` and a dedicated local SSH key. Oracle rejected both bounded creation attempts in AD-1: first **2 OCPUs / 12 GB**, then **1 OCPU / 12 GB**. Both used `VM.Standard.A1.Flex`, Ubuntu 24.04 Minimal ARM64, a 50 GB boot disk and automatic fault-domain placement. The Console offered only AD-1. The error reports a host-capacity shortage, not a failed account registration or application error.

After the failures, the Singapore root-compartment instance, VCN, block-volume and boot-volume inventories were empty. No cleanup deletion was needed.

### Two-node E2 fallback

The owner authorized two Always Free `VM.Standard.E2.1.Micro` instances, `mathvisionkid-api` and `mathvisionkid-ocr`, with Ubuntu 24.04 Minimal AMD64 and a 50 GB encrypted boot disk each. The first request returned the same **out-of-capacity** error in AD-1 with automatic fault-domain placement. A second identical request was not submitted because changing the instance name would not address that shortage. The instance, VCN, block-volume and boot-volume lists were checked again and remained empty.

Oracle documents at most two free E2 Micro instances, each with **1 GB RAM and a sustained 1/8 OCPU with burst capability**. Their RAM is separate; they do not provide one 2 GB machine. The split application must pass native memory, latency, worker and persistence checks before replacing the PC backend. The single-VM ARM64 commands below are not a tested E2 deployment profile.

A local AMD64 model compatibility check passed with networking disabled, one numerical-library thread, a 512 MiB container memory/swap limit and a 0.125 CPU limit. CRNN, YOLO and OpenCV ONNX inference completed in 68.0 seconds; the process peak RSS was 438,592 KiB and cgroup memory peak reached the full 512 MiB limit. No OOM kill occurred, but this is insufficient memory headroom evidence for the combined AI API, worker, Redis and operating system on an E2 node. It is not a real-photo accuracy result or native Oracle timing.

See [the E2 attempt report](../report/cloud-e2-fallback-2026-10-10.md). Free host capacity is still the immediate blocker; no SSH connection, cloud data transfer or website backend switch has occurred.

Do not switch to paid capacity, upgrade the account or create another trial account automatically. Retry later when free capacity is available, checking for existing instances and disks first. The [Oracle FAQ](https://www.oracle.com/cloud/free/faq/) describes capacity shortages and retry options.

The dedicated key and verified backups are retained only in the ignored, access-restricted local migration directory. No private SSH key, database backup, private image or provider credential has been uploaded to Oracle. The rejected creation reviews had public IPv4 disabled; successful provisioning must still be followed by explicit network configuration and a verified HTTPS endpoint before changing any website's backend. The browser session later reset the unsubmitted form; its configuration is documented here and must be reselected on the next attempt.

## Before provisioning or moving data

1. Confirm actual Always Free allowance and available host capacity in the console. The A1 plan is one Ubuntu ARM64 VM, 2 OCPUs, 12 GB RAM, 50 GB boot disk. The authorized fallback is two Ubuntu AMD64 E2 Micro VMs with 1 GB RAM and 50 GB boot disks each; that fallback needs its own tested split configuration. Neither option has been provisioned. Do not substitute a paid shape or upgrade billing automatically.
2. Verify the complete ARM64 build first. The AI, backend and storage images have built successfully under ARM64 emulation on this workstation. Real CRNN, YOLO and OpenCV ONNX CPU inference passed, with four model checksums verified; the backend packaged its application JAR and ran Java 21 as its non-root user. This is component compatibility evidence; native VM performance and the complete application still require verification after provisioning.
3. Use [the cloud storage override](../infra/production/compose.cloud.yml). Registry inspection of the existing MinIO tag returned access errors; the override builds the same server version from official GitHub release binaries, verifying published SHA-256 values. Run the isolated storage smoke check below. This keeps an old storage version for migration compatibility; it is not evidence of ongoing upstream security support. See [storage sources and licenses](../infra/production/storage/SOURCES.md).
4. Obtain a stable public HTTPS API hostname, owner-controlled DNS, and certificate contact. The temporary PC Quick Tunnel address must not remain baked into the cloud websites.
5. Back up PostgreSQL, private images and configuration separately. Verify a restore into an isolated environment before the existing trial is retired. A Drive shortcut, stream-only file or Docker volume alone is not a verified backup.

## Verified migration preparation

The local preview remains running. These checks used separate disposable Docker resources and did not replace its images or modify its database and images:

- An ARM64 AI image built from the existing runtime dependencies and ran the real models without provider networking. The generated input checks compatibility, not OCR accuracy.
- An ARM64 backend image built its application JAR and passed a Java runtime/non-root user check. This does not establish database-connected startup or successful cloud login.
- An ARM64 cloud storage image passed authenticated upload/read, anonymous denial and persistence after restart, using a dedicated non-root user.
- A PostgreSQL dump restored successfully in isolation: all 24 public tables matched the source row counts and content fingerprints. The source remained unchanged during the check.
- All six currently stored private images restored to isolated ARM64 storage: total 241,479 object bytes, with SHA-256, content types and preserved metadata matching before and after restart.

Backups and their private verification manifests are in the ignored `infra/local-runtime/cloud-migration/` directory with restricted Windows permissions. They contain user data and must not be committed or included in a public build. They have **not** been transferred to an Oracle server. Only the eight required runtime model artifacts (32,551,417 bytes) are needed; the training-photo archives stay off the VM.

See [the preparation report](../report/cloud-migration-preflight-2026-10-10.md) for component image IDs, verification boundaries and the remaining deployment checks.

## Reuse the production stack

Follow [the production deployment guide](PRODUCTION_DEPLOYMENT.md) for secrets, model checksums, private networking, bootstrap, accounts and recovery. Transfer only the required eight runtime model artifacts, application source/build inputs, and authorized persisted data. Training photos and archives are unnecessary on the VM.

On the server, install Docker Engine and Compose from [Docker's Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/), which cover ARM64. Enable Docker at boot. Use an owner-controlled SSH key; restrict SSH ingress to the owner's IP and publish only the Caddy gateway on 80/443. PostgreSQL, Redis, MinIO and internal AI endpoints remain private.

Commands below run from the repository root on the server, after preparing the ignored `infra/production/.env.production` and verified model bundle:

```sh
chmod 600 infra/production/.env.production
python3 scripts/deploy/check_production.py --env-file infra/production/.env.production
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml -f infra/production/compose.cloud.yml config --quiet
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml -f infra/production/compose.cloud.yml build ai backend minio
python3 scripts/deploy/smoke_cloud_storage.py --platform linux/arm64
docker run --rm --network none --entrypoint python --env PYTHONPATH=/app --mount type=bind,source=/srv/mathvision/models,target=/app/models,readonly --mount type=bind,source="$PWD/scripts/deploy",target=/checks,readonly mathvision-ai:production /checks/smoke_cloud_models.py
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml -f infra/production/compose.cloud.yml up -d
docker compose --env-file infra/production/.env.production -f infra/production/compose.yml -f infra/production/compose.cloud.yml ps
```

Stop on a failed preflight, pull, build or health check. The Compose services use persistent named volumes and `restart: unless-stopped`; ordinary maintenance must not delete those volumes. Confirm that total memory, disk and CPU usage fit the VM while OCR and the worker are both active.

The model smoke check verifies four artifact checksums and runs the real CRNN, YOLO and OpenCV ONNX models without networking or provider credentials. Its generated image checks runtime compatibility, not transcription accuracy. ARM emulation on the workstation is not performance evidence from an Oracle VM. The storage smoke check creates its own disposable Docker resources and verifies authenticated upload/read, anonymous denial and object retention across a restart; it never selects production resources.

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
