# Separate Expo and web deployment launchers — 2026-10-14

## Behavior

- `RUN_EXPO.bat` reuses the established local launcher to start infrastructure,
  API/OCR, local development portals and the student Metro/QR. It never invokes
  Vercel publication, even when private preview configuration exists.
- `RUN_MATHVISION.bat` remains the compatible local entry point. Its automatic
  public deployment and automatic browser opening were removed.
- `DEPLOY_WEB.bat` requires the checkout's existing private preview configuration,
  then calls `Start-PC-Preview.ps1 -Build -PublishWeb`. It builds current backend,
  AI and worker images before startup and web publication. It does not start
  the local stack/Metro or request an Expo Go QR.
- Missing private setup or a deployment error returns failure. Existing preview
  data remains in its volumes. A fresh clone cannot automatically repoint the
  owner's website. API/OCR still need the configured PC and Docker running.
- README and hosting/restart instructions now point to the appropriate launcher.

## Validation

- Six Windows launcher tests passed, including both local entry points,
  configured and fresh checkouts, deployment success/failure and local failure.
  The real BAT files ran in paths containing spaces with service/publication
  stubs; no live Vercel upload or service restart occurred during these tests.
- PowerShell parser accepted the modified deployment script and its `Build`
  switch. Existing preview Compose configuration validated with `--quiet`.
- Root BAT files use CRLF and UTF-8 without BOM. `git diff --check` passed.
- Expo versioned SDK 57 reference was read before editing:
  [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/).
- No Student Mobile source, model, credentials, database, commit or push changed
  in this task. The user's existing unrelated skill edit was preserved.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the existing startup and publisher rather than duplicate them.
  - Applied to: launcher split, explicit image build switch, docs and regression tests.
