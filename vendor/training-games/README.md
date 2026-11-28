# Local training-game distribution

The active local application checkout is `C:\MathVisionKid`. The owner deleted
the former `C:\Tro_choi_cho_em` source checkout after integration on 25 November
2026. Do not recreate that checkout or sibling application checkouts for each
new game change. Running/installing MathVisionKid uses the relative tarball
dependency in this directory; it does not require the deleted source checkout.
The current tarball contains the shipped gameplay source, and PACKAGE_MANIFEST.json
records its provenance and per-file hashes.

## Profile grade and Defense portal update 0.1.26

The Student Web host passes the grade from the student profile. The embedded
Race, Terrain and Defense games use that grade immediately. Planet Rescue has
a grade 4 fraction bank, and Block Island uses the mission sets for grades 3
and 4. Enemies on the landscape web battlefield spawn at the portal opening
and render above the stone foreground. Verify the archive against baseline
0.1.22 with `node scripts/build-training-games-fixes.cjs`.

## Defense feedback update 0.1.22

The correct shot no longer displays an extra confirmation panel.
`defense-feedback-0.1.22.patch` records the change from baseline 0.1.21.

## Race regressions update 0.1.21

Version 0.1.21 restored desktop opening zoom and focus/follow
without changing touch camera targets, uses the selected grade in question titles,
and names automatic participants after their characters. Grade 5 starts with
advanced Race templates and decimal Defense questions instead of small natural
additions. Grade 1–4 banks and history isolation remain unchanged.

The 0.1.21 build used baseline 0.1.20 and `race-regressions-0.1.21.patch`.
The patch and baseline preserve a reviewable source delta without recreating the
deleted external repository. Install the resulting tarball through the normal
workspace dependency before exporting the app.

## Consolidated distribution 0.1.20

This distribution combines the verified 0.1.13 desktop baseline (camera,
three-dimensional dice and readable bot/dice pacing), the grade question
support from 0.1.19, and the previously authored terrain audio changes.
Race setup instructions now use the selected grade as well. The receipt
records the baseline hash, canonical source revision, dirty working-tree
state and every shipped file hash. No gameplay copy is maintained in the host.

The matching host includes the earlier full-width game catalog and scoped
desktop styles. Local backups and retired checkout remnants are outside
the application, under the owner's Codex backup directory.

The separate source checkout used for this distribution is no longer present by
owner choice. Do not edit node_modules or silently recreate an external checkout.
The updater instructions below describe the original packaging workflow and
require an explicitly supplied source location; the old sibling path is historical.

Stop the MathVisionKid Expo dev server first. The updater refuses installation
while that project's Metro is running, to avoid stale native module maps.
Rebuild and install from current canonical working files:

```sh
node scripts/update-training-games.cjs --source <source-location>
```

The source path is a CLI argument, not an absolute dependency. It may point to any
checkout with the source builder and five game modules. Bump the distribution
version in `training-package/package.json` and the result game version when changing
the shipped implementation. Review the regenerated tarball and SHA-256 manifest.
The builder refuses to overwrite an existing version with different content.
If that check fails, bump the distribution/game version and build again.
Then run the source/host checks documented in the integration report.
Restart MathVisionKid from `apps/student-mobile` with `expo start --go --clear`.
Perform one fresh Expo Go connection after a package update; game exit/navigation
never reloads JavaScript.

`package-lock.json` and the relative `file:../../vendor/training-games/<version>.tgz`
dependency let a future checkout install without requiring the source repository.
Only the canonical source checkout is needed to *update* the artifact. Do not publish
without reviewing the current local changes and acceptance results.

## Desktop layout update 0.1.8

Canonical source worktree: `Tro_choi_cho_em-desktop-ui`, local source revision
`27a9c10608fe405a37c961ca8e7157a1e0c04043` based on source remote `0a1d148`.
The remote lacks the previously uncommitted embedded Block Island/integration
source. Its canonical builder verifies the immutable deployed 0.1.2 archive and
every existing source hash, replaces only the two reviewed Race camera files,
and applies exact-once IslandIntro presentation/version patches. No unpublished
Terrain audio work is included. The full integrated source history remains
unavailable; this update does not pretend to restore that history.

`desktop-layout-0.1.8.patch` exposes every source edit for review (zero context,
line endings normalized for readability). `desktop-layout-0.1.8.recipe.json` is the canonical
builder recipe. `PACKAGE_MANIFEST.json` records baseline, source revision,
replacement/patch paths and distribution SHA-256. All 216 other source files are
byte-identical to 0.1.2. Host/native orientation, gameplay, storage and rewards
are unchanged. Desktop guards use web and a fine primary pointer.

## Desktop camera update 0.1.9

The original 0.1.8 packaging checkout is unavailable on the canonical remote.
The patch `desktop-layout-0.1.9-source.patch` applies to canonical revision
`0a1d148198448fbdd83fbc40ac3ad9d0a2a7e255`. It contains the Race camera
change, its geometry test, and the builder for this update. Apply it in a
checkout of `deptraivodich/Tro_choi_cho_em` with `git apply --unidiff-zero` and
commit it there so the builder can read the source from Git. Run the updater
above with `--source` pointing to that checkout.

The builder verifies the 0.1.8 archive and all 220 source hashes and stages
the next npm package in a temporary directory. It replaces the Race camera
from the committed canonical source and updates the embedded version. The
other 218 source files retain their 0.1.8 hashes. Desktop keeps the full
board after the intro even across resize or pause. Touch and native retain
their focus zoom and pan controls.

## Dice presentation update 0.1.9

The same canonical source worktree supplies `DiceOverlay.tsx` and the new
`DiceModel.tsx`. A shaded SVG cube replaces six flat raster faces; recessed pips,
short rolling/landing transforms and a separate contact shadow are presentation
only. Reduced Motion shows the confirmed face without movement. The controller,
RNG, pause/turn timers and all gameplay source bytes are unchanged from 0.1.8.

This local UI task has no new source commit. The receipt explicitly records
`sourceWorkingTreeDirty: true` on base revision `27a9c106`; it does not claim the
new dice edits are contained in that commit. All packaged file hashes are
verified. `dice-visual-0.1.9.patch` exposes the delta from 0.1.8, and
`dice-visual-0.1.9.recipe.json` preserves the canonical builder recipe. Of 221
source files, 218 are byte-identical to 0.1.8; only DiceOverlay, the new DiceModel
and the distribution version differ. No engine or dependency was added.

## Desktop framing and pacing update 0.1.11

The owner requested slower dice and bot turns on 21 November. Dice now settles
after 500 ms and holds its result for another 2 seconds. Bots answer after
10 active seconds; the existing scheduler still freezes remaining time on pause.
Desktop camera framing reserves 56 px above and below the board for the HUD,
and omits the duplicate background image behind the board. Phone framing stays
on the existing focus/follow path.

`desktop-pacing-0.1.11.patch` and `.recipe.json` expose this delta from 0.1.9.
Of 221 source files, 217 are byte-identical. The integrated RaceController keeps
learner-only result counts and question history: exact-once patches change only
its timing import and bot delay, plus CRLF normalization. RNG, reducer, scoring,
question generation, storage and the other four games are unchanged. The receipt
still marks the canonical source working tree dirty on base `27a9c106`.

Local candidate 0.1.10 failed typecheck because copying the older canonical
controller omitted integration extensions. It was replaced before delivery;
0.1.11 preserves those extensions and passes the installed-artifact checks.

## Desktop backgrounds and Planet layout update 0.1.12

Host web presentation now provides a dark wood surface around the Race map and
a warm trackside surface around Terrain's portrait scene. Planet's desktop
workspace prioritizes its question and answer grid. These styles are scoped to
their game roots, a fine pointer and a viewport at least 1,000 CSS px wide.
Native/touch layouts and the game cameras keep their existing behavior.

The canonical recipe adds 21 read-only layout identifiers to the integrated
Planet screen. `desktop-polish-0.1.12.patch` exposes that exact delta from 0.1.11;
`.recipe.json` records the builder recipe. Of 221 packaged source files, 219 are
byte-identical. Planet gains only these identifiers; the other changed file is
the distribution version. Controller timing, math, session counts, rewards,
storage and all five game engines remain byte-identical to 0.1.11.
