# Backend runtime repair — 2026-10-02

The mobile multiline submission failed because port 8080 belonged to a previously started backend in `E:/HandAI/backend`. The MathVision launcher accepted any open TCP port as the expected service. The shared PostgreSQL schema was still at Flyway V15; the running backend attempted to insert `gemini_confidence_source`, which did not exist. PostgreSQL logged that exact failure at 15:39:24, 15:39:28 and 15:39:34 UTC, matching the owner's repeated HTTP 500 submissions.

## Repair

- Verified the listening PID and its Java classpath immediately before stopping only that foreign backend process (PID 8308).
- Started MathVision's own backend from `backend/business-api` in a hidden process. Normal startup validated all 16 existing migrations and applied the pending V16. No migration contents, checksums, application data, passwords or model weights were changed.
- The current backend is PID 6060, serves port 8080 and reports `E:/MathVisionKid/backend/business-api` as its working directory. MathVision's existing FastAPI runtime on port 8000 was retained.
- `scripts/dev/start-all.ps1` now checks both the expected project path and application entry point before reusing Spring or FastAPI listeners. An unrelated process produces an actionable `PORT_CONFLICT` error and is left running.
- `tools/diagnostics/check_runtime.py` rejects an otherwise healthy Spring instance whose working directory belongs to another checkout.
- Live HTTP validation also found that multiline JSON emitted `testData` while mobile expects `isTestData`. The response now explicitly names that property, matching the existing single-line response contract.

## Verification

- Full backend regression: **22 suites, 154 tests, zero failures/errors/skips**, profile `test`, H2 isolated from live PostgreSQL. The focused multiline run also passed all 37 tests.
- Launcher identity checks: eight path/entry-point cases pass. A real temporary TCP listener is rejected without stopping it or launching a replacement process.
- Diagnostics regression: a healthy instance from this checkout passes; another checkout and missing runtime identity fail.
- Live HTTP used the previously supplied owner image through the real business API, AI runtime, PostgreSQL and MinIO: detection **200** with nine lines, trial creation **201**, read **200**, feedback **200**. Anonymous read returns **401**, another student returns **404**, and missing privacy consent is rejected with **400**.
- Stored page SHA-256 matches the uploaded image. Verification trials use test collection mode and no line is training eligible. The feedback exercised `SKIPPED`, not a fabricated correctness label.
- The last run took 3.72 seconds with warm detection cache; this is not a cold-start latency claim. No physical phone test was performed by the agent.
- No backend errors appeared during the successful live verification. Source migrations remain unchanged. No training, commit or push was performed.

Evidence: `backend-runtime-repair.json`, `spring-startup-proof.log`, `live-recognition-http.json`, `backend-tests.json` in this directory. The live verification creates developer test records; it does not modify an existing student's feedback or authorize training.

## Separate infrastructure interruption and recovery

At 23:20:44 local time, after the successful verification, Docker Desktop entered a requested graceful shutdown and removed the PostgreSQL, Redis and MinIO forwarding ports. MathVision's existing backend then reported database connection refusal. The shutdown actor is unknown; no inference of an out-of-memory event is made.

Docker Desktop's subsequent startup failed because its zero-byte `Docker/run/dockerInference` AF_UNIX reparse endpoint was inaccessible (Windows error 1920). The exact endpoint could not be renamed. This observed Windows build 26200 failure matches a [report in Docker's issue tracker](https://github.com/docker/desktop-feedback/issues/527).

Recovery was confined to the Docker runtime: terminate the stuck `docker-desktop` WSL instance, restart the verified Docker Desktop installation, preserve the three zero-byte IPC endpoints by moving the verified non-reparse `Docker/run` directory to a new sibling `Docker/run-stale-20261002`, create a fresh runtime directory and start Docker Desktop normally. No Docker data volume, settings, VHD or database was reset, deleted or unregistered.

After recovery all three infrastructure containers are healthy; PostgreSQL logs confirm a clean shutdown followed by startup of the existing database. The same MathVision backend PID 6060 reports `UP`, DB health is `UP`, and FastAPI reports `ready`. Schema V16 and the existing successful test trial remain intact; its nine lines, skipped feedback and stored image SHA-256 match the earlier evidence. This final preservation check created no additional trial records.

Evidence: `infrastructure-recovery.json`, `docker-run-quarantine.json`, `data-preservation-after-recovery.json`, `postgres-recovery-proof.log`.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: diagnose the actual failure and fix the shared launch/diagnostic path with the smallest changes.
  - Applied to: runtime ownership checks, native Flyway startup, multiline JSON contract and meaningful regression checks.
