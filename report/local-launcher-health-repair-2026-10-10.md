# Local launcher health check repair — 2026-10-10

## Problem and cause

The owner's launcher output reported a Spring Boot checkout mismatch and stopped before starting Student Metro. The running backend was actually from `E:\MathVisionKid\backend\business-api`, with its database migrations current and its health endpoint returning `{"status":"UP"}`.

Production hardening had changed the shared health configuration to hide details and components. The local diagnostic verifies checkout identity using `components.diskSpace.details.path`; the development profile no longer exposed that field. This caused a false failure.

## Change

- Restored health details and components in `backend/business-api/src/main/resources/application-dev.yml` only, with a comment explaining the launcher dependency.
- Extended existing profile configuration tests to require development health visibility and production component hiding.
- The shared and production health responses remain hidden. Production still rejects combined dev/prod profiles and health detail overrides.
- No runtime identity checks were removed or relaxed.

## Validation and recovery

- Regression test before the fix: 24 tests run, with the development health configuration assertion failing as expected.
- After the fix: 29 backend tests passed across `ProductionEnvironmentPostProcessorTest` and `SecurityDeploymentTest`.
- Python diagnostic regression: 1 test passed, including correct checkout, different checkout, and missing path cases.
- PowerShell runtime identity tests passed: 8 command cases, 8 Windows Python redirector cases, and a real foreign listener rejection without stopping it.
- Expo QR checks passed for correct project/LAN identity, rejected mismatches, and bounded readiness retries.
- Restarted only the verified local Spring application, then ran the core launcher successfully. Existing AI, Celery, web, and infrastructure services were reused.
- Started Student Metro with the existing launcher and verified its actual Expo Go manifest at `exp://192.168.1.19:8081`.
- Confirmed the running backend is accepted by the launcher's process identity guard.
- Final `tools/diagnostics/check_runtime.py` exited 0: all 11 service checks passed, LAN verdict `PASS`, overall `READY_FOR_FULL_DEMO`.
- Scoped `git diff --check` passed.

This confirms local startup and network readiness. No physical-device camera or lesson-quality claim is made. No model training, production deployment, commit, push, data deletion, or cloud configuration change was performed.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Diagnose and fix the launcher regression with the smallest change at its configuration source.
  - Applied to: Development health configuration, existing regression assertions, and targeted service recovery.

## Reference checked before editing

- [Expo SDK 57 documentation](https://docs.expo.dev/versions/v57.0.0/), as required by project instructions. No Expo or student UI code was changed.
