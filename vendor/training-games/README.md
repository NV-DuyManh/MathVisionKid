# Local training-game distribution

Canonical gameplay stays in the separate game repository. Do not edit an extracted
package in node_modules or maintain a second handwritten gameplay copy here.

Stop the MathVisionKid Expo dev server first. The updater refuses installation
while that project's Metro is running, to avoid stale native module maps.
Rebuild and install from current canonical working files:

```sh
node scripts/update-training-games.cjs --source ../Tro_choi_cho_em
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
