# Student responsive interface — approved implementation

**Goal:** Implement the owner's approved purple/cream utility artwork and duotone navigation, with phone bottom tabs and collapsible vertical navigation on larger devices.

**Architecture:** Keep the existing Expo Router screens, callbacks, learning data and authentication. Add one responsive tab shell, static image assets and adaptive card layouts. Use Expo Image's SDK 57 SVG support; add no runtime dependency.

**Tech stack:** Expo SDK 57, React Native 0.86, Expo Router, Expo Image.

**Spec:** Owner's three selected attachments: paper utility illustrations, duotone A icons and vertical navigation. The owner explicitly approved implementation on 2026-10-20. Existing design previews are under `docs/design/student-responsive-20261020/`.

**Global constraints:** No commits/push/deployment or model training. Do not modify authentication, tutoring logic or unrelated work. Preserve real camera/gallery and calculator entry points. Do not display developer information or account emails to students. Browser evidence is not physical-device evidence.

**Review focus:** Screen-width transitions, menu collapse/selection, actual available content width, keyboard/accessibility, reading widths, truthful learning activity and unchanged learning routes.

- [x] Add regression coverage for responsive navigation and camera/calculator entry points; observe the new behavior test fail first.
- [x] Isolate approved utility illustrations; create matching native-loadable SVG navigation assets.
- [x] Implement adaptive tab shell and dashboard; update the other three tab screens with consistent responsive layout and approved artwork.
- [x] Run typecheck, student tests and web export. Inspect browser rendering at phone, tablet and laptop widths, including collapsed navigation and calculator.
- [x] Review final change, fix findings, record verification and scope under `report/`; stop without committing.

Workflow adjustment: the workspace contains untracked owner design references and installed application dependencies. Work stays in this checkout on `codex/student-responsive-approved`; no owner files are reset, moved or staged. Owner's no-commit rule overrides workflow defaults.
