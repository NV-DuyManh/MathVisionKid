# Storage image sources

This image packages unmodified MinIO server and client binaries from official
GitHub release assets. Both are distributed under GNU AGPL v3. Included license
copies are in `/usr/share/doc/mathvision-storage/` inside the image.

- Server: [RELEASE.2024-01-28T22-35-53Z](https://github.com/minio/minio/releases/tag/RELEASE.2024-01-28T22-35-53Z),
  source commit [`7743d952dc16ccab26ca9240855089535e548062`](https://github.com/minio/minio/tree/7743d952dc16ccab26ca9240855089535e548062).
- Client: [RELEASE.2024-01-28T16-23-14Z](https://github.com/minio/mc/releases/tag/RELEASE.2024-01-28T16-23-14Z),
  source commit [`ba9fc6a3075df6d8a413cc7e423645706aaefae1`](https://github.com/minio/mc/tree/ba9fc6a3075df6d8a413cc7e423645706aaefae1).

The Dockerfile checks the SHA-256 values published in each release's
`*.sha256sum` assets for AMD64 and ARM64. A missing download, unsupported
architecture or checksum mismatch aborts the build. Build/source instructions
are included in the upstream repositories linked above.

The server version matches the existing PC preview so migration does not also
upgrade its storage format. This is an old release; the community repository
is now archived. Keeping this version is a migration compatibility choice,
not a claim of ongoing upstream security support. Storage and its console
must remain on the private Docker network. Review a maintained storage
replacement separately, after backup/restore and application compatibility
have been demonstrated.
