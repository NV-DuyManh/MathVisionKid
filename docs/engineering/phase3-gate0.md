# Phase 3 Gate 0 — 14/11/2026

Phase 2 is committed locally at `b62f30f667ca7730607a2f0920713a5ba58dd8df` on `feature/classroom-foundation`. Phase 1 commits `64816562` and `503007cc` remain in its ancestry. At inventory time the separate `LoginPage.tsx` edit and local browser/Gradle artifacts remained outside that commit.

## Source and applied histories before integration

Fresh fetch resolved `origin/develop` to `0cbbd267f60140f8bb64a6673c9e4f03f2e828a7`. Its verified-training V34 conflicts with local Classroom V34. Local Phase 2 also contains quota V35 and publication V36. No merge, rebase, migration rename or schema-history repair was performed by this check.

| Local container / database / schema | Latest applied versions and Flyway checksums |
|---|---|
| `mathvision-audit-classroom-final` / `mathvision_classroom_final_test` / `phase2_browser_20261114` | V32 `1352565662`, V33 `275867204`, Classroom V34 `1040884853`, quota V35 `1472075910`, publication V36 `-870374349` |
| `mathvision-classroom-foundation-db` / `mathvision_classroom_test` / `public` | Same V32–V35 checksums |
| `mathvision-postgres` / `mathvision` / `public` | Latest V32 `1352565662` |

These histories were read through `psql`. Remote deployment histories remain uninspected.

## Fresh PostgreSQL verification

Executed `./gradlew.bat test --tests com.mathvisionkids.api.PostgresUpgradeTest --offline --rerun-tasks` with the opt-in environment below.

```text
MATHVISION_POSTGRES_UPGRADE=true
PGHOST=127.0.0.1
PGPORT=55435
PGDATABASE=mathvision_classroom_final_test
PGUSER=classroom
PG_TOOLS_CONTAINER=mathvision-audit-classroom-final
MATHVISION_COMPAT_MIGRATIONS=<business-api>/.gradle-agent/phase2-compat
```

Password was supplied directly from container configuration without printing it. XML timestamp `2026-11-14T05:21:07.982Z` records **7 tests, 0 failures, 0 errors, 0 skipped**. Gradle reported BUILD SUCCESSFUL in 53 seconds. A local evidence copy resides at `.gradle-agent/phase3-gate0-upgrade-result.xml` and is excluded from commits.

The suite migrated generated isolated schemas from V28/V31/V32/V33/V34/V35 to local V36. It also reverified the proposed combined V33→V37 mapping using SQL copies of develop verified-training V34, Classroom V35, quota V36 and publication V37. Every case exercised `pg_dump`/`pg_restore` using matching container tools and asserted retained roster, ACTIVE legacy Assignment, COMPLETED Batch, linked Submission and image references after restore. Publication/recipient tables remained empty. The combined case preserved a seeded game run while adding the develop default mode and nullable reward status. Test schemas were cleaned afterward, leaving the existing browser schema present.

## Phase 3 migration recommendation

Reserve **V38** for the first Phase 3 schema migration on both local and proposed combined histories. Local retains its applied V34/V35/V36 and leaves V37 unused. The combined proposal uses V34/V35/V36/V37 then the same Phase 3 V38. Flyway supports noncontiguous versions, so this avoids a further Phase 3 version collision. The Phase 3 SQL itself still requires verification against both predecessor histories once implemented.

## State after the authorized develop merge

Local merge `71ef6d84` incorporated `origin/develop` at `0cbbd267`. The canonical history now uses V34 for verified training, V35 for Classroom, V36 for the join quota, and V37 for publication. Phase 3 adds V38 for assigned uploads and V39 for image returns and grade metadata. PostgreSQL registered V38 and V39 successfully in the isolated schema `phase3_acceptance_20261114`. The existing schemas listed above were preserved.

Databases already carrying the older local Classroom V34 have an incompatible history. They need a reviewed data-preserving cutover before adopting the merged branch. The isolated backup/restore tests from V33 establish a path under canonical numbering. A database that already ran the local Classroom V34 requires its own verification before any deployment.

## Skills Applied

- `mathvision-backend` — `.agents/skills/mathvision-backend/SKILL.md`, applied to applied-history inventory, migration ordering and preservation of legacy relationships.
- `mathvision-quality` — `.agents/skills/mathvision-quality/SKILL.md`, applied to enabled PostgreSQL execution, backup/restore evidence and explicit integration limits.
