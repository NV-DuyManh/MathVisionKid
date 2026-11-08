# Lesson catalog

The application collects **successfully checked, confirmed, source-only mathematical plans** and validated TTS WAVs privately. It also ships a separately reviewed **public exercise catalog** with Git. Reuse always requires the exact normalized source; it never substitutes a similar problem, changes numbers/units, replays another pupil's work, or resumes another session's progress.

## Shared exercises included with every clone

`ai/runtime/app/tutoring/data/verified_exercises.json` contains 81 reviewed exercise groups (85 questions/subparts/table cells) from the owner-provided exam set. It includes confirmed problem text, checked base plans and independent reference answers. Two subparts missing a mass unit and one ambiguous rounding question are excluded. No account IDs, sessions, photographs, recordings, private SQLite files or model weights are shipped.

After `git pull` and restarting the AI service, every account on a fresh clone can reuse these exact exercises, with no private database migration or model call. Docker includes the file through its existing `COPY app`. New sessions and audio permissions remain private. The runtime checks the source and plan again; stale policy, malformed data or a different source uses the normal checked generation path. Policy hashing normalizes line endings so Windows/Linux checkouts agree.

When updating the math rules, refresh the public plans using the existing reviewed answers, then commit the JSON with the code:

```powershell
python ai/runtime/scripts/refresh_published_catalog.py --write
python ai/runtime/scripts/refresh_published_catalog.py
```

The tool never reads a pupil database or calls a cloud provider. It refuses to update when a current solver disagrees with the reviewed reference. New exercises need source/privacy and mathematical review before adding them to this public inventory; a successful private session is not automatic permission to publish pupil content. Include approved inventory updates in the same PR as the related code. AI CI checks every published exercise, both fresh accounts and Windows/Linux policy parity; the Catalog Bot displays the shared exercise count and checks its structure.

Git transfers this published catalog when pushed/pulled; it does not continuously synchronize separate computers or train model weights. Speech caches remain private, so shipping a plan does not claim instant speech on every new device.

## Runtime

- Private SQLite at `ai/runtime/state/lesson-catalog.sqlite3` by default. No dependency or cloud call is needed to read it. Git and container builds exclude the private state.
- `LESSON_CATALOG_ENABLED=true`; set false to bypass collection/reuse. Optional `LESSON_CATALOG_PATH` selects a writable persistent server path.
- Defaults: 30-day expiry, 500 entries per kind, 128 MiB of audio payload. SQLite can retain freed pages at its prior high-water mark; this is a payload bound, not a promise that the filesystem immediately shrinks.
- The checked model plan and exact arithmetic are still validated. A source/code-policy mismatch, expired entry, invalid plan, damaged WAV or unavailable database follows the original generation path. Source text uses Unicode NFC and collapsed whitespace only; punctuation, digits, accents, signs and units remain significant.
- New sessions always receive new IDs, revision zero and no completed answers. A cached plan does not expose future answers or grant permission to play unissued text.
- Initial and private teaching paragraphs remain separate on disk. Draft/unconfirmed OCR sources and lessons containing pupil work are not collected as reusable plans.
- Speech keys include owner scope, exact paragraph order, voice, fallback mode and synthesis-policy version. Both male and female speech keep their exact existing identities. Existing session/revision/issued-text guards run before any audio catalog lookup.
- Private runtime content is **account scoped**. Only the explicitly reviewed public inventory above is shared across accounts. SQLite is durable on one mounted server, not a distributed database for several hosts.
- Account scopes are hashes, not anonymization or encryption. Plans and generated TTS may contain source-derived text; keep the volume private and apply the application's data-retention rules.
- The Docker AI service mounts `lessoncatalog:/app/state`. Back up this private volume as application data; never upload it to GitHub or a public artifact. This is not a training dataset.

## GitHub bot

[**Open MathVision Catalog Bot → GitHub Actions**](https://github.com/NV-DuyManh/MathVisionKid/actions/workflows/lesson-catalog.yml)

`.github/workflows/lesson-catalog.yml` runs on relevant pull requests/main pushes, manually via **Run workflow**, and daily at 02:17 UTC (09:17 Vietnam time; scheduled runs can be delayed). It tests storage/owner/version/voice-key isolation, durable reuse, aggregate-report privacy and failure reporting. It also checks the curated regression inventory for malformed or duplicated sources. It needs no API keys, package installation or pupil database, and uses a read-only repository token.

Each run shows a Vietnamese table under **Summary**. The **mathvision-catalog-bot** artifact contains `index.html`, `summary.md` and `status.json`; download it to open the dashboard. Reports are retained for 14 days. Failed checks produce a failed workflow and a report, when checkout/Python and report generation remain available. Cancelled or infrastructure-failed runs may have no artifact.

The application collects private runtime results immediately. The GitHub job audits the public source/inventory; it **does not connect to a developer's local machine, collect student data, automatically approve mathematical correctness, or push student content into the repository**. This is a GitHub Actions bot, not a separate chat user or an app installed into the Student navigation. Updates to this workflow appear on GitHub only after the owner authorizes committing/pushing them.

## See the catalog on this machine

Double-click **`RUN_CATALOG_BOT.bat`** in the project root. It runs offline checks, reads aggregate counts from the local SQLite catalog and opens the generated dashboard. The launcher uses the existing Python virtual environment, falling back to `python` if needed. No service restart or provider token is required.

```powershell
.\RUN_CATALOG_BOT.bat
# Or inspect an explicitly selected server database:
python ai/runtime/scripts/catalog_bot.py --database "path/to/private/lesson-catalog.sqlite3"
```

The launcher uses `LESSON_CATALOG_PATH` from its process environment if set, otherwise `ai/runtime/state/lesson-catalog.sqlite3`. It does not parse private `.env` files; for a custom path set in such a file, use `--database` explicitly. A Docker named volume or another host needs an audit on that server; local counts do not represent every deployment.

The dashboard is a **timestamped snapshot**, not live polling. Re-run to refresh. It shows retained plan/audio counts and reuse hits on those retained entries, not a lifetime cumulative total. Expired and checksum-damaged counts are visible; inspection never prunes automatically. Missing/unreadable databases are reported as unknown, never as fabricated zeroes. Reports contain only allowlisted aggregate fields, not account hashes, text, images, WAVs or local database paths. Local reports stay in ignored `.local-artifacts/catalog-bot/`; `--database` is forbidden on GitHub Actions.

Local equivalent:

```powershell
python ai/runtime/scripts/test_catalog_store.py -v
python ai/runtime/scripts/test_catalog_bot.py -v
python ai/runtime/scripts/catalog_bot.py
python ai/runtime/scripts/catalog_audit.py --corpus ai/runtime/tests/fixtures/student_learning_regression.json
```

Server-only inventory (aggregate counts, no lesson text/account IDs):

```powershell
python ai/runtime/scripts/catalog_audit.py --database ai/runtime/state/lesson-catalog.sqlite3
```

Add `--prune` only when explicitly maintaining expired/damaged private entries. Policy fingerprints reject old content when the corresponding validation/synthesis source changes. Existing data is not retroactively collected from logs, historical photos or model checkpoints.
