# MinIO launcher fix after pulling main (2026-10-31)

## Cause and change

The checked-in development Compose file requested
`minio/minio:RELEASE.2024-01-28T22-35-53Z`, which is absent from Docker's
local cache. The existing healthy `mathvision-minio` container instead uses
`mathvision-minio-local:2024.01.28`. The launcher correctly refused to proceed.

Restored the verified local image in `infra/docker/docker-compose.yml` and
`pull_policy: never`. Kept the existing image/volume preservation guard.
Extended its existing test to catch a recurrence of this Compose mismatch.
This remains a local-image setup; a fresh machine still needs the verified image.

## Verification

- Compose config validation and `git diff --check`: PASS.
- Compose regression check and all seven image/volume preservation cases: PASS.
- Real `RUN_MATHVISION.bat`: passed infrastructure startup; PostgreSQL,
  MinIO and Redis ready. No MinIO pull or container recreation occurred.
- MinIO `mc ready local`: PASS. Original container ID, image ID and
  `business-api_miniodata:/data` mount unchanged.
- Full launcher did NOT reach its success banner: application diagnostics
  timed out on Spring Boot, FastAPI and Celery. FastAPI and Celery subsequently
  logged successful startup. Spring's Gradle process was still running;
  no Spring startup success is claimed. No application timeout or backend
  configuration was changed as part of this MinIO fix.
- Local execution logs: `runtime/minio-launcher-fix-20261031/launcher.stdout.log`
  and `launcher.stderr.log` (ignored runtime artifacts).

No volume deletion, migration, commit or push.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal Docker/launcher correction using existing safeguards.
  - Applied to: Compose image selection and the existing regression check.
