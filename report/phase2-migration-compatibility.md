# Phase 2 migration compatibility — 14/11/2026

Fetched develop at `0cbbd267f60140f8bb64a6673c9e4f03f2e828a7`. Its V1–V33 SQL matches the local branch. Develop adds `V34__verified_training_runs.sql`. Local Phase 1 already applies `V34__classroom_foundation.sql` and `V35__classroom_code_limit.sql`, and Phase 2 adds `V36__assignment_publications.sql`.

## Applied history inventory

Read through PostgreSQL `psql` without writing application data.

| Container / database / schema | Applied latest history |
|---|---|
| mathvision-audit-classroom-final / mathvision_classroom_final_test / phase2_browser_20261114 | V32 `1352565662`, V33 `275867204`, V34 Classroom `1040884853`, V35 quota `1472075910`, V36 publication `-870374349` |
| mathvision-classroom-foundation-db / mathvision_classroom_test / public | Same V32–V35 checksums |
| mathvision-postgres / mathvision / public | Latest V32 `1352565662` |

Remote/public deployment histories have not been inspected. The inventory covers local running containers only.

## Integration mapping

Two V34 files cannot coexist in a Flyway migration location. Git merge conflict detection cannot enforce this constraint. A database with local Classroom V34 also cannot validate against develop's different V34 definition.

For databases whose history ends at V33 or earlier, the proposed integration order is develop's verified-training V34, Classroom V35, quota V36, publication V37. A temporary SQL directory is used to exercise this proposal. Checked-in and already applied migration files remain intact.

The local test databases above have already applied Classroom V34. Renaming those files and starting the combined binary would invalidate their history. Before integrating Git, choose how to preserve those environments. One option is to back up and transfer their data into a separately migrated database under the agreed canonical history, validating all data and foreign keys before cutover. Another requires an explicitly reviewed history reconciliation procedure. No such conversion has been performed or approved by this report.

The mapping is therefore a proposal for unapplied histories, with an integration blocker for existing local Classroom histories. A passing isolated upgrade cannot authorize rewriting their schema history.

## Upgrade test changes

`PostgresUpgradeTest` now seeds an ACTIVE legacy Assignment, COMPLETED Batch and linked Submission before upgrade. After migration and schema backup/restore it verifies assignment fields, original Batch/Submission links and counts, retained Classroom membership and image references, and empty publication/recipient tables. The combined-history test additionally verifies the develop game-run columns exist.

Executed `./gradlew.bat test --tests com.mathvisionkids.api.PostgresUpgradeTest --offline` with `MATHVISION_POSTGRES_UPGRADE=true`, `PGHOST=127.0.0.1`, `PGPORT=55435`, `PGDATABASE=mathvision_classroom_final_test`, `PGUSER=classroom`, `PG_TOOLS_CONTAINER=mathvision-audit-classroom-final`, and `MATHVISION_COMPAT_MIGRATIONS` pointing to the temporary copied SQL under `.gradle-agent/phase2-compat`. Password came directly from Docker container configuration and was not printed. Final result was **7 tests, 0 failures, 0 errors, 0 skipped**, BUILD SUCCESSFUL. The XML timestamp is recorded in `.gradle-agent/phase2-upgrade-result.xml` as local evidence excluded from commits.

The seven cases cover local upgrades from V28, V31, V32, V33, V34 and V35 to V36, plus the proposed combined V33→V37 history. Each case used a new generated test schema, performed schema backup/restore through the matching container's PostgreSQL tools, and verified legacy data after restore. Existing application schemas were not modified. The first combined-case attempt failed to locate SQL in the sandbox TEMP directory; generating the copies under the workspace recovered discovery, and the final rerun included all seven cases.

The combined run proves migration execution and legacy data compatibility for the proposed order. It does not prove a deployment migration for a database whose applied local V34–V36 history must be preserved. The existing-history integration blocker remains open.

## Skills Applied

- `mathvision-backend`
  - SKILL.md: C:/Users/LOC/.codex/worktrees/classroom-foundation/MathVisionKid/.agents/skills/mathvision-backend/SKILL.md
  - Why selected: PostgreSQL/Flyway data preservation and migration ordering.
  - Applied to: Read-only history inventory, additive migration proposal and legacy fixtures.
- `mathvision-quality`
  - SKILL.md: C:/Users/LOC/.codex/worktrees/classroom-foundation/MathVisionKid/.agents/skills/mathvision-quality/SKILL.md
  - Why selected: Require executed PostgreSQL evidence for upgrade claims.
  - Applied to: Opt-in isolated upgrade, backup/restore and explicit pending results.
