# Integrate public web startup into RUN_MATHVISION — 2026-10-10

## Result

Opening `RUN_MATHVISION.bat` on the configured owner PC now starts and verifies the ordinary local services and Student Metro, then invokes the existing `scripts/deploy/Start-PC-Preview.ps1 -PublishWeb`. That script starts the separate public preview containers, starts or reuses their owned tunnel, and builds/publishes the three web apps for the current API address.

The owner's existing `.env.preview` and the preview startup script were confirmed present. The launcher reuses them without creating credentials, training models, or rebuilding runtime images.

## Behavior

- An existing private preview configuration enables the automatic fourth startup step.
- A fresh clone without that configuration skips public startup and displays the setup guide path.
- A public startup/publication failure is clearly reported as `FAILED`, leaves local services and QR available, and returns exit code 1 after the final pause.
- A successful publication is reported as `READY` with the stable Vercel portal address.
- A local startup failure stops before calling the public publisher.
- The launcher distinguishes the local stop command from the public preview stop script and reminds the owner to keep the PC awake and Docker running.
- README and the PC preview guide document the one-file restart workflow and the public-only command.

The public API still requires this PC, Docker, Internet, and its tunnel. This change does not provide independent cloud hosting or 24/7 service while the PC is off. Normal public startup republishes the current web source and requires authenticated access to the existing Vercel projects.

## Validation

- `ai/runtime/.venv/Scripts/python.exe scripts/test/test_run_launcher.py -v`: 4 tests passed.
- Tests execute the real batch flow in temporary directories whose paths contain spaces. Service commands are replaced by local stubs; only browser opening and final pauses are suppressed. They verify ordering, the required `-PublishWeb` flag, exit codes, QR continuation on publication failure, skip behavior, early local failure, and preservation of private configuration contents.
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/deploy/Test-PC-Preview.ps1`: ownership checks passed.
- `node scripts/test/test_student_qr.cjs`: project/LAN manifest and bounded retry checks passed.
- Scoped `git diff --check`: passed.

No real publication or container restart was performed during this phase's tests. These checks validate launcher integration and error handling, rather than claiming a new live deployment or a physical-device test. No commit or push was performed.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Integrate the existing deployment command with minimal additional launcher logic.
  - Applied to: Reusing the public startup/publisher, explicit batch error handling, and focused executable regression checks.

## Required documentation checked

- [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) was read before editing, as required by project instructions. Student application code was not changed.
