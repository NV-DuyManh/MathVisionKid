# Cloud migration preparation — 10 October 2026

## Outcome

Prepared and checked the existing application for the selected Oracle Always Free ARM64 server. No Oracle VM has been provisioned and no website has been switched to a cloud backend. Vercel still serves the websites while API/OCR and persisted data run in the PC preview; operation with the owner's PC off is not established.

Subsequent fallback: the owner authorized two E2 Micro AMD64 nodes. The first E2 provisioning request also returned out of capacity; see [the separate E2 report](cloud-e2-fallback-2026-10-10.md) for its resource check and unchanged deployment status.

The owner completed account setup and signed into the Console on the computer. The visible Console confirms a Free Tier account in Singapore. Two bounded A1 creation requests were rejected with an explicit host-capacity error. The general signup support page shown earlier did not establish a rejection reason. No paid service, billing upgrade or duplicate trial account was created.

## Oracle provisioning result

- The owner confirmed creation of `mathvisionkid-cloud` and administration using a new dedicated SSH key retained on their computer.
- Created an Ed25519 key in the ignored local migration directory, with inherited file access disabled and access limited to the owner, SYSTEM and Administrators. Only its public key was entered in the Console.
- Selected `VM.Standard.A1.Flex`, Ubuntu 24.04 Minimal aarch64 (`2026.09.18-0`), a 50 GB encrypted boot disk at 10 VPU and automatic fault-domain placement.
- First attempt: 2 OCPUs / 12 GB RAM. Oracle returned `Out of capacity` in AD-1.
- Second attempt: 1 OCPU / 12 GB RAM, retaining sufficient memory for the unchanged stack. Oracle returned the same capacity error. Only AD-1 was offered; no paid replacement was selected.
- After both attempts, the Singapore root-compartment Instances, VCN, block-volume and boot-volume lists all showed no items. No leftover compute, network or disk resource was found in those inventories; no cleanup deletion was needed.
- The networking follow-up remains necessary: both rejected creation reviews had no public IPv4 assigned. No SSH connection, Docker install, cloud data transfer or HTTPS endpoint has been established.
- A browser-session reconnection subsequently reset the unsubmitted creation form to defaults. That draft was closed; the selected A1 configuration must be re-entered from the documented values on the next attempt.

Screenshots of the reviewed configuration and capacity error are retained in the ignored local migration directory. They are evidence of configuration and rejection, not a successful deployment. The current blocker requires Oracle capacity to become available; repeated rapid creation requests, billing upgrades and duplicate trial accounts are not part of this phase.

## Changes

- Added `infra/production/compose.cloud.yml` to override cloud storage packaging without replacing the PC preview's cached image or changing its networking.
- Added `infra/production/storage/Dockerfile` and `SOURCES.md`. The image downloads unmodified official MinIO server/client releases, verifies pinned SHA-256 values for the selected architecture, includes both licenses and runs under a dedicated non-root user. Missing artifacts, unsupported architectures and checksum mismatches fail the build.
- Added isolated storage and real model compatibility checks in `scripts/deploy/smoke_cloud_storage.py` and `smoke_cloud_models.py`.
- Updated the production and free-cloud guides with the cloud override, bounded migration checks and the distinction between local ARM emulation and a verified server deployment.

The storage server version remains the existing 2024 release to preserve migration compatibility. Its community upstream is now archived; this packaging change does not establish ongoing security support. Its API and console remain private within the application network. A maintained replacement requires a separate compatibility review.

## Verification

All three test images were built under `linux/arm64` emulation on the Windows workstation. They use separate `cloud-arm64` tags; PC preview image tags were not replaced.

| Image | Verified result | Local image ID |
| --- | --- | --- |
| `mathvision-ai:cloud-arm64` | Build passed; four runtime artifact checksums matched; real CRNN, YOLO and OpenCV ONNX CPU forward passes completed with provider networking disabled. | `sha256:c9f2768f7e2457d3a9fa8226c53162f0688b3836419c9cf8605dde2d2dcb80b2` |
| `mathvision-storage:cloud-arm64` | Build passed; authenticated upload/read, anonymous denial and restart persistence passed as a non-root user. | `sha256:db74b915d68296fa8bd415f3b3c89a09e7132d99a8f76eac337adc5ffaa9bdf0` |
| `mathvision-business-api:cloud-arm64` | Gradle `bootJar` passed; packaged JAR exists; Java 21 runs on `aarch64` under UID 10001. | `sha256:f39c4bd29484a4f8996931389b0e73791a2dc5f26b393e493165e82a0781c5ed` |

The AI smoke input was generated solely to exercise inference. No OCR accuracy percentage, real photographed-question transcription result, physical-device test or native Oracle performance measurement is claimed. The backend packaging command skipped tests; its runtime check does not prove database-connected startup, authentication or a complete ARM64 stack.

The production-preflight unit suite passed all nine tests. New Python smoke scripts passed compilation. Base-plus-cloud Compose configuration passed validation without exposing private configuration. Focused whitespace checks passed.

### Data recovery checks

- Created a private PostgreSQL custom-format backup of 68,008 bytes and restored it in an isolated container. All 24 public tables matched source row counts and content fingerprints. The source remained unchanged during verification.
- Backed up the six real private image objects, totaling 241,479 object bytes. Restored them to an isolated ARM64 storage container and compared bytes, SHA-256, MIME types and preserved metadata, including after restart. All matched. An initial test-harness connection failure after restart was resolved by discovering the current Docker test port again; no production storage configuration was changed.
- Disposable test containers, networks and volumes were removed using only identifiers belonging to each check. The PC preview's existing AI, worker, backend, storage, PostgreSQL and Redis services remained running and healthy after the checks.

Backups and their verification manifests remain in the ignored, access-restricted `infra/local-runtime/cloud-migration/` directory. Their contents and user identifiers are excluded from this report and Git. No data has been transferred to Oracle. The required model bundle contains eight files totaling 32,551,417 bytes; training photographs and archives are unnecessary for migration.

## Remaining deployment gates

1. Account setup and Console access are confirmed. Wait for available Always Free A1 host capacity, then retry a bounded creation after checking current inventory; do not substitute paid capacity automatically.
2. Provision the selected Ubuntu ARM64 VM within the account's free allowance, configure owner-controlled SSH access, install Docker/Compose and transfer private configuration, the verified model bundle and authorized backups.
3. Restore data on the VM, start the complete stack, verify native CPU/memory/disk behavior, backend authentication and queued OCR jobs, and confirm persisted data survives a server restart.
4. Configure a stable public HTTPS API hostname and restricted public routes, then republish portal, teacher and admin against it. Provider API quota and billing must be checked separately from free VM hosting.
5. With the owner's PC off, verify deployed login and real-photo OCR from another device/network before reporting migration complete. This test has not happened.

No model training, Student Mobile source change, new Vercel publication, Git commit or push was performed during this preparation phase.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Reuse the existing production stack and migration inputs with a small deployment override.
  - Applied to: Storage packaging, isolated compatibility checks, private data restore checks and cloud handoff documentation.

## References

- [Oracle Always Free resources and current limits](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).
- [Oracle Free Tier signup and verification FAQ](https://www.oracle.com/cloud/free/faq/).
- [Docker Engine installation on Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
- [Storage release sources, checksums and licenses](../infra/production/storage/SOURCES.md).
- [Free cloud deployment guide](../docs/FREE_CLOUD_DEPLOYMENT.md).
- [Expo 57 versioned documentation](https://docs.expo.dev/versions/v57.0.0/) was read before implementation; no Expo/native source was edited.
