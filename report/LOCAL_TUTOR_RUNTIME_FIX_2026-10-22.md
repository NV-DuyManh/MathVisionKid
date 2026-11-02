# Local tutor runtime investigation — 2026-10-22

## Scope and outcome

Investigated the reported Student Mobile math tutor failure across acquisition,
public Spring API, internal FastAPI, Gemini transport, key pool and lesson validation.
Checked the complete local service stack. This is not an audit of every repository feature.
Local fixes are implemented and loaded. End-to-end lesson creation remains affected
by Gemini HTTP 503 responses; do not report the feature as fully working.

## Evidence

- Runtime diagnostics: Docker, PostgreSQL, MinIO, Redis, Spring, FastAPI, Celery,
  portal/teacher/admin web and Student Metro all PASS; mobile LAN reachable.
- New failing `/internal/v1/tutor/inspect` request corresponds to upstream Gemini
  HTTP 503. Expo's update notice and API resolver log are not the cause of this request.
- `GROQ_ENABLED=false`, `GEMINI_ENABLED=true` are effective. No credentials are included here.
- A transient provider error previously put the key into the configured 300-second
  cooldown. Immediate manual retries could not acquire that key.
- Live public API test: seeded local student login HTTP 200; synthetic Vietnamese
  math image inspection HTTP 200, kind PROBLEM, approximately 33 seconds.
  The image inspection recovered from an upstream 503 on its bounded retry.
- Public lesson creation still encountered upstream 503/timeouts. One successful
  provider response before the schema fix failed local minimum-step validation;
  the repair request then failed upstream. After the schema fix, live lesson tests
  still received upstream 503. Lesson creation and hint delivery are NOT verified live.
- No physical-device test or test using the original phone image was performed.

## Changes

- Gemini tutor retries HTTP 503 once with jitter, using the same key and remaining
  request budget. Authentication and quota handling do not sweep keys on overload.
- Tutor overload/timeout cooldown is five seconds; quota cooldown behavior is preserved.
  The shared key pool now honors an explicitly supplied transient retry interval.
- Forward the existing lesson/review JSON schema to Gemini as `responseJsonSchema`.
  Mathematical checks, independent lesson review and answer-withholding remain intact.
- Student 503 message describes temporary service unavailability without blaming
  the source question. Development console adds only stage/status/error code.
- Earlier 24-second notebook first-read timeout remains in place.

## Validation

- AI: 425 tests passed across tutor, lessons, notebook and relevant Gemini transports/pools.
- Student Mobile: 69 tests passed (screen and API). The initial cold calculator test
  exceeded Jest's default five seconds; the full rerun passed with a 20-second test timeout.
- Spring: MathTutorControllerTest 27 and MathTutorServiceTest 53 passed on Java 21.
- `git diff --check` passed.
- Runtime FastAPI restarted with the final changes; Metro remains running.

## Remaining dependency

Gemini availability cannot be repaired by changing the mobile API address, removing
FIXTURE or accepting invalid model output. Wait for provider recovery or configure
an independently validated working provider/key. A future live test must confirm
photo inspection, confirmed-source lesson creation and a lesson answer/hint through
the public authenticated API. Do not claim full readiness from `/ready` alone:
it currently checks local arithmetic infrastructure, not successful cloud tutoring.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: root-cause repair with small changes and existing infrastructure.
  - Applied to: Gemini transport, shared key cooldown and focused regression tests.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native request/error handling.
  - Applied to: existing tutor screen failure handling without new state or request waterfalls.
