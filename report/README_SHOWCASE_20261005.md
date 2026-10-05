# Repository documentation and showcase — 5 October 2026

## Result

Rebuilt the repository landing README in English with a branded cover, actual app screenshots, product flow, technology stack, setup entry point, recognition boundaries, and documentation navigation.

Updated English installation, troubleshooting, architecture, and demo guides. Added Vietnamese installation and student usage guides, contributor guidance, media provenance, and the editable HTML cover source.

## Media

- One 1600 × 860 cover using existing mascot/logo/Nunito assets and real app screenshots.
- Five fresh student web captures at a requested 390 × 844 viewport; exported image pixels are 390 × 843.
- One original owner-supplied Android capture, reused with explicit provenance.
- All seven exported images together: 1,163,981 bytes, approximately 1.16 MB.

The cover uses decorative device frames. It does not invent app screens. The Android image is not evidence of a new physical-device test.

## Validation

- Checked nine primary documentation files: 91 relative link/anchor references resolved without errors.
- Checked all seven images with Pillow's decode/verification routines.
- Parsed 22 PowerShell command blocks with the PowerShell language parser; no syntax errors. Installation commands were inspected against source, not reinstalled in the existing workspace.
- Rendered the README locally; all 12 embedded images/badges loaded. Desktop and narrow-screen previews showed no page-wide overflow.
- Visually checked cover composition, fonts, screenshot proportions, and initial README layout.
- Completed the typed digit-append lesson through the real authenticated student UI: method choice, 9, 531, 59, and 537. This validates that demonstration, not image transcription accuracy.
- Independently audited configuration paths, artifact hashes, seeded development accounts, launcher behavior, and test commands against the repository.

Private validation JSON and preview screenshots are under `infra/local-runtime/logs/readme-showcase-20261005/` and are excluded from Git.

## Corrections and limits

- Fixed obsolete workspace/log paths and removed the old mock-button walkthrough.
- Documented explicit student API override with its required `/api/v1` prefix.
- Corrected nested npm test arguments and selected AI regression suites that mock cloud calls.
- Added backend test-profile selection and restoration.
- Distinguished CRNN line OCR from main-guide cloud vision and synthetic async grading.
- Explained that weights/keys are not supplied by a clone and that health readiness is not OCR/content validation.
- The grade-five movement practice request was unavailable during the capture session; the showcase uses the supported digit-append example and documents lesson availability limits.

No application behavior, model weights, training, or dataset annotations were changed in this documentation task. Existing application regression suites were not rerun for documentation-only changes.

## Skills Applied

- `brand`
  - SKILL.md: `.agents/skills/brand/SKILL.md`
  - Why selected: branded repository presentation and consistent product messaging.
  - Applied to: cover colors, mascot/logo reuse, typography, and README voice.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: visual hierarchy, readable layout, and app screenshot presentation.
  - Applied to: cover hierarchy, screenshot gallery, descriptive alt text, and visual review.
- `design`
  - SKILL.md: `.agents/skills/design/SKILL.md`
  - Why selected: branded cover composition and HTML-to-image export workflow.
  - Applied to: `docs/media/showcase.html`, cover rendering, media provenance, and independent setup verification.
