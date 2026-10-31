# Lesson catalog

The application automatically collects **successfully checked, confirmed, source-only mathematical plans** and validated TTS WAVs. It reuses them for an exact normalized source and the same account; it never substitutes a similar problem, changes numbers/units, replays another pupil's work, or resumes another session's progress.

## Runtime

- Private SQLite at `ai/runtime/state/lesson-catalog.sqlite3` by default. No dependency or cloud call is needed to read it. Git and container builds exclude the private state.
- `LESSON_CATALOG_ENABLED=true`; set false to bypass collection/reuse. Optional `LESSON_CATALOG_PATH` selects a writable persistent server path.
- Defaults: 30-day expiry, 500 entries per kind, 128 MiB of audio payload. SQLite can retain freed pages at its prior high-water mark; this is a payload bound, not a promise that the filesystem immediately shrinks.
- The checked model plan and exact arithmetic are still validated. A source/code-policy mismatch, expired entry, invalid plan, damaged WAV or unavailable database follows the original generation path. Source text uses Unicode NFC and collapsed whitespace only; punctuation, digits, accents, signs and units remain significant.
- New sessions always receive new IDs, revision zero and no completed answers. A cached plan does not expose future answers or grant permission to play unissued text.
- Initial and private teaching paragraphs remain separate on disk. Draft/unconfirmed OCR sources and lessons containing pupil work are not collected as reusable plans.
- Speech keys include owner scope, exact paragraph order, voice, fallback mode and synthesis-policy version. Both male and female speech keep their exact existing identities. Existing session/revision/issued-text guards run before any audio catalog lookup.
- Content is **account scoped**. Cross-account publishing requires a separately reviewed, anonymized public catalog; it is not silently enabled here. SQLite is durable on one mounted server, not a distributed database for several hosts.
- Account scopes are hashes, not anonymization or encryption. Plans and generated TTS may contain source-derived text; keep the volume private and apply the application's data-retention rules.
- The Docker AI service mounts `lessoncatalog:/app/state`. Back up this private volume as application data; never upload it to GitHub or a public artifact. This is not a training dataset.

## GitHub bot

`.github/workflows/lesson-catalog.yml` runs on relevant pull requests/main pushes, manually, and daily at 02:17 UTC. It tests storage/owner/version isolation and checks the curated regression inventory for malformed or duplicated sources. It needs no API keys, package installation or pupil database, uses a read-only repository token, and publishes a numeric summary in the workflow run.

The application collects private runtime results immediately. The GitHub job audits the public source/inventory; it **does not connect to a developer's local machine, collect student data, automatically approve mathematical correctness, or push student content into the repository**. The workflow becomes executable after these files are pushed to GitHub; a successful cloud run has not been claimed before that happens.

Local equivalent:

```powershell
python ai/runtime/scripts/test_catalog_store.py -v
python ai/runtime/scripts/catalog_audit.py --corpus ai/runtime/tests/fixtures/student_learning_regression.json
```

Server-only inventory (aggregate counts, no lesson text/account IDs):

```powershell
python ai/runtime/scripts/catalog_audit.py --database ai/runtime/state/lesson-catalog.sqlite3
```

Add `--prune` only when explicitly maintaining expired/damaged private entries. Policy fingerprints reject old content when the corresponding validation/synthesis source changes. Existing data is not retroactively collected from logs, historical photos or model checkpoints.
