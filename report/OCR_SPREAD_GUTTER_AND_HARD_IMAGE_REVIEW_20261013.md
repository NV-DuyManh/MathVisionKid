# OCR: separate spread pages and inspect unresolved source crops — 2026-10-13

The owner requested careful follow-up on images still recognized poorly.
The deployed repair separates supported notebook spreads that previously
collapsed into full-width bands. It changes source-coordinate geometry, not
production weights or the recognized text's approval status.

## Actual repair and safeguards

The workspace contained an unfinished split-spread proposal. Its first caller
condition required three wide physical-row seeds, so it never ran on several
curved spreads with empty physical-row detection, including `335.jpeg` and
`307.jpeg`. Those images nevertheless had repeated full-width classical bands.

The final caller also considers those joined classical bands. Without physical
seeds, it requires the source-colour gutter check and clipped-boundary veto
before replacing geometry. It does not treat arbitrary gaps between words as
independent columns.

The shared recovery:

- Limits its attempt to large, light landscape images of supported proportions.
- Requires substantial coloured ink on both sides and an empty central corridor
  without a substantial pen component.
- Runs the existing pinned detector independently on each side of that corridor.
- Rejects missing/insufficient column evidence and text reaching the cut boundary.
- Returns coordinates on the original image without changing source pixels.
- Keeps results unverified and preserves limits, cache behaviour and ambiguous
  cases. The final detection cache version is `text-regions-v20`.

A broader first condition failed an existing regression: a synthetic one-column
image's three rows became eight fragments. That version was rejected before
deployment. The tightened condition passes the original test and explicit
no-physical-seed, neutral-ink, boundary, unsupported-layout and cache checks.
Interrupted exploratory runs remain separate and are not counted as final.

## Final detection and recognition

| Evidence | Result |
|---|---:|
| Images redetected with final code | 246 |
| Successful source reads/detection | 246 |
| Changed / unchanged images against previous release | 42 / 204 |
| Regions across this cohort before / after | 4,904 / 6,553 |
| Changed images recognized again | 42 |
| Regions recognized in that pass | 2,165 |
| Nonempty unverified drafts / empty drafts | 2,089 / 76 |
| Final execution failures | 0 |
| Relevant regression tests | 324 passed |

All 42 changed page layouts were viewed from verified original Drive bytes in
RAM, with final geometry overlays. The former bands spanning both page interiors
were separated. Individual boxes can still contain merged rows, annotations,
background text or printed footers; this is not per-character approval.

Recognition used the previously frozen experimental pair `4903062b…` /
`dc25d2de…`. It remains unpromoted. SQLite, JSONL, source membership/hashes,
integer coordinate bounds, reviewed orientation, geometry files and finite
scores were reconciled. All prediction/reference/training flags remain false.

The new changed-image queue has **592 regions**, with overlapping flags:
76 empty, 563 possible non-line layouts and 26 width-cap flags. These are
inspection signals, not verified errors. More regions and nonempty text do not
establish greater transcription accuracy. This follow-up covers the 246-image
orientation/stroke cohort, not another rescan of all 64,803 known images.

## Review of remaining difficult crops

The preceding contrast retry produced 47 nonempty hypotheses. All 47 crops on
36 source images were now inspected in RAM:

| Visual category | Crops |
|---|---:|
| Teacher annotations | 9 |
| Clipped writing | 8 |
| Rulings / underlines | 8 |
| Background / page edges | 11 |
| Publisher marks / decoration | 2 |
| Isolated or tracing glyphs | 6 |
| Structured mathematics block | 1 |
| Faint multiline answer | 1 |
| Stacked fraction fragment | 1 |

No predicted string was automatically approved or used for training. The review
explains why repeatedly turning every empty region into a nonempty prediction
would introduce false labels.

The merged pencil comparison block in `637.png` was inspected as a full source
and as proposed individual recrops. Six visible expressions were frozen as
targeted development references; uncertain punctuation/equality-bar proposals
were excluded. Recognition still made **five critical edits** on those six
references, including confusing `>` with `5` or `)`. None is an independent
accuracy test or a training-eligible reference. Source recropping alone does not
resolve this recognizer weakness; production weights are retained.

Layout inspection also identified `174.jpg` and `176.jpg` as related captures of
the same visible exercise pages. The current training cohort contains no
`176.jpg` reference, so this observation does not establish a TRAIN/HOLDOUT leak
there. It is recorded privately for grouping future splits. Different byte
hashes do not imply independent pages or writers.

## Deployment and retained state

- Final code is installed in both healthy AI and worker containers; their source
  hashes match the workspace. Production model/vocabulary hashes are unchanged.
- Live checks on `335.jpeg` return 52 separated regions with the gutter retry;
  `241.jpeg` retains its existing 55-region column recovery. Both preserve pixels,
  report unverified geometry and have no band spanning both page interiors.
- Internal HTTP OCR passes a synthetic-image check, and local student login
  retains the backend's STUDENT role. Production image capture stays disabled.
- Docker was initially stopped. After starting it, the restarted connection had
  a new hostname and all three public login routes returned 502. The existing
  publisher completed its builds, student web export, configuration/bundle checks
  and deployments with the current upstream. Final public login plus backend
  student-role checks pass through portal, teacher and admin origins.
- Static bundle-size warnings remain warnings; no UI/source redesign was made.
- Rollback image: `mathvision-ai:rollback-spread-20261013`.
- Sixteen protected source-index/model/reference/evidence files are unchanged.
  No source photos, contact sheets or archives were saved in this phase directory;
  deliberately deleted original-cache folders remain absent.
- No new model fitting, weight promotion, paid resource, commit/push or
  physical-device evidence. Backend/OCR hosting still depends on the running PC.

Private evidence is under
`ai-training/datasets/drive_math/spread_recovery_20261013/`: rejected/partial
attempts, final 246-image detection, geometry comparison, changed-image recognition,
visual-review records, pencil proposals/references, regression logs, source/model
integrity receipts, code snapshot, Docker build/deployment and final public checks.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: fix the shared caller and reuse the pinned detector, source
    reader, existing audit/recognition runners and deployment tools.
  - Applied to: bounded gutter retry, conservative rejection, regression repair,
    RAM-only review, unchanged-model recognition, reconciliation and deployment.
