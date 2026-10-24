# Local training-game distribution

Canonical gameplay stays in the separate game repository. Do not edit an extracted
package in node_modules or maintain a second handwritten gameplay copy here.

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

`package-lock.json` and the relative `file:../../vendor/training-games/<version>.tgz`
dependency let a future checkout install without requiring the source repository.
Only the canonical source checkout is needed to *update* the artifact. Do not publish
without reviewing the current local changes and acceptance results.
