# Backend production safety and container verification

Date: 2026-10-09. Scope: `backend/business-api`; local container verification only. Cloud deployment belongs to the parent deployment task.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: focused Spring configuration/security refactoring with minimal new infrastructure.
  - Applied to: profile separation, native Spring environment validation, existing CORS/security flow, existing AI HTTP client, and Docker packaging.

The required [Expo SDK 57 versioned documentation](https://docs.expo.dev/versions/v57.0.0/) was read before editing. The Spring implementation follows the existing Boot 3.3 configuration model and its [EnvironmentPostProcessor registration contract](https://docs.spring.io/spring-boot/3.3/api/java/org/springframework/boot/env/EnvironmentPostProcessor.html).

## Implemented behavior

- Development credentials and localhost integration defaults live in `application-dev.yml`. Running locally without an active profile still selects `dev`.
- `ProductionEnvironmentPostProcessor`, registered through `META-INF/spring.factories`, rejects invalid production configuration before database initialization or seed execution. `prod` cannot be combined with `dev` or `test`.
- Demo seeding requires `dev & !prod`; production does not create demo accounts even if the two profiles are accidentally combined.
- Production administrator bootstrap is explicitly opt-in. It creates exactly one active `ADMIN` using the existing BCrypt encoder only when the entire users table is empty. Any existing user causes a skip without validating or mutating bootstrap credentials/accounts. Errors and action logs do not echo credentials.
- Production requires JWT/internal keys of at least 32 UTF-8 bytes, rejects low-diversity/published development placeholders, and requires nondefault database/storage passwords of at least 16 characters. Operators must generate secrets with a cryptographically secure generator; startup checks cannot establish how a value was generated.
- CORS uses the configured exact origin allowlist. The wildcard pattern is removed in every profile. Production permits only exact public HTTPS origins, without credentials, paths, queries, fragments, empty entries, loopback hosts, or wildcards. Existing localhost/127.0.0.1 web origins remain available in development.
- Anonymous health responses expose only status; other actuator paths require authentication. Production disables OpenAPI/Swagger and suppresses standard server error detail fields.
- The configured AI jobs HTTP client sends the shared `X-Internal-API-Key` while preserving existing connect/read timeouts. Callback authentication and backend role checks remain authoritative.
- `PORT` externalizes the listener; normal Spring overrides such as `SERVER_PORT` remain supported. Production honors forwarded headers from the trusted reverse proxy.
- The multistage Dockerfile builds with Java 21 and runs with the Java 21 JRE as UID 10001. It defaults to `prod`, creates a writable `/app/uploads`, and excludes environment files and local build/data directories from its context.

## Production environment contract

| Variable | Requirement |
| --- | --- |
| `SPRING_PROFILES_ACTIVE` | `prod` (Docker default) |
| `JWT_SECRET`, `INTERNAL_API_KEY` | Separate generated random secrets, at least 32 bytes; the internal key must match the AI service |
| `DB_URL`, `DB_USERNAME`, `DB_PASSWORD` | Explicit PostgreSQL settings; password at least 16 characters and nondefault |
| `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | Explicit durable object-store settings; access key cannot be `minioadmin`; secret at least 16 characters and nondefault |
| `MINIO_BUCKET` | Keep `mathvision`; the existing jobs image-reference conversion uses this bucket name |
| `AI_GATEWAY_MODE` | `FASTAPI` |
| `AI_SERVICE_URL` | Private AI jobs endpoint, e.g. `http://ai-service:8000/internal/v1/jobs` |
| `AI_SERVICE_BASE_URL` | Private AI service origin, e.g. `http://ai-service:8000` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated exact HTTPS origins for every deployed web application; no trailing slash |
| `PORT` | Optional; defaults to `8080` |
| `BOOTSTRAP_ADMIN_ENABLED` | Defaults to `false`; set `true` only for initial owner provisioning on an empty users table |
| `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`, `BOOTSTRAP_ADMIN_NAME` | Required when creating the initial admin; valid email, generated password of 16–72 UTF-8 bytes with at least 8 distinct characters and no default patterns, display name of 1–255 characters |

## Persistence review

`MinioObjectStorageService` is already the primary injected object-store service. Uploaded objects require a persistent MinIO volume, and users, refresh tokens, submissions, and analysis results require a persistent PostgreSQL volume. The local storage bean still initializes an upload directory; the runtime provides a writable path.

SSO handoff tickets are short-lived, single-use values in one backend process. The planned single-replica VPS deployment supports this existing design. A restart invalidates outstanding handoff tickets and the user can request a fresh ticket. Multiple backend replicas would require shared ticket storage or sticky routing and are outside this change.

A fresh production database contains no demo accounts. To provision the real initial owner, explicitly enable the production admin bootstrap with controlled credentials. After the first successful creation, set `BOOTSTRAP_ADMIN_ENABLED=false` and remove `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`, and `BOOTSTRAP_ADMIN_NAME` from the deployment configuration. Subsequent starts never create or overwrite users when any user already exists. Bootstrap supports the planned single backend replica; parallel initializers on multiple replicas would need a database lock.

## Verification

- Local Java 21.0.9 / Gradle 9.7.1: **74 tests across 9 suites passed**, with zero failures/errors. Coverage includes new production/profile/CORS/health/RBAC/internal-header/bootstrap checks plus existing authentication, SSO, callback, HTTP jobs, and application-context tests. Bootstrap checks cover BCrypt hashing, active admin role, normalized identity, restart idempotence, any-existing-user skips, profile/flag isolation, bounded strong password validation, and no account writes on invalid input.
- `bootJar`: passed; artifact is `backend/business-api/build/libs/business-api.jar`.
- `docker build --tag mathvision-business-api:cloud-check .`: passed from a clean multistage Java 21 build.
- Native production JAR startup without credentials: exited 1 with `JWT_SECRET is required in prod` before database initialization.
- Production container startup without credentials: exited 1 with the same expected rejection; no Hikari pool or entity manager started.
- Container runtime: UID **10001**, writable upload directory, and `/usr/bin/curl` available for deployment health checks.
- `git diff --check -- backend/business-api`: passed; only existing Windows line-ending conversion notices were printed.

No cloud endpoint, physical device, or full production service stack was claimed as verified by this subtask. No actual `.env` file was read, no model training ran, Student Mobile was unchanged, and no commit/push was performed.
