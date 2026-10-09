# OCR, tutoring and mobile continuation — 2026-10-09

The continuation fixes lost small printed rows, exact arithmetic grading,
fraction guidance, duplicate recognition submissions and startup retry handling.
Drive processing advances by 28 saved provider responses. It is **not complete**:
1,035 source images remain pending because the provider stops responding.

## Changes

- **Row detection:** dense small letters no longer satisfy the thick-rule
  threshold solely because morphological closing joins their gaps. Thin rules
  remain filtered. Clipped grid strips at page boundaries have a separate
  condition so they do not become text rows. Three-row printed samples retain
  their rows at different vertical positions, including near the image edge.
- **Exact arithmetic:** decimal constants retain their original source digits;
  server grading uses exact rational equality. Rounded approximations of `1 ÷ 3`
  are rejected; `1/3` is accepted. Compound ratios display a division sign
  outside stacked literal fractions. Negative previous answers keep parentheses.
- **Teaching:** ordinary expressions with up to five operations get one checked
  operation per step in AST order. Two literal fractions get separate steps for
  a common denominator, each new numerator, the operation and the result;
  multiplication/division use numerator and denominator products. Each step
  has two progressive hints. Plans use supplied numbers, with no image-ID
  lookup or prefilled pupil answers. More complex expressions and unsupported
  word problems still require the existing provider/review path.
- **Mobile:** all calculation steps offer numerator/denominator input, including
  signed numerators. Narrow rows wrap instead of pushing units off-screen.
  A synchronous submission guard prevents two taps in the same render from
  issuing duplicate recognition requests. Cancellation invalidates stale
  responses. Illustration retries reuse other in-flight asset loads, preserving
  original artwork and the existing initial readiness gate.
- **Service diagnostics:** missing catalog evidence is reported as unknown;
  catalog membership is not a completed inference probe. Timeouts/HTTP failures
  retain diagnostic fields without exposing exception bodies or credentials.
- **Launcher:** the QR helper retries temporary manifest/network failures up to
  three times, validates the actual project/LAN manifest and refuses wrong
  projects. The mobile launcher returns a failure status when readiness times
  out. Its visible QR terminal remains open.

## Validation

The final full backend sweep passes with no failed tests. Skips and remaining
external evidence gaps are reported separately below.

| Check | Result / scope |
|---|---|
| Full backend pytest | 1,390 passed, 10 skipped; zero failed |
| Mobile Jest | 43 suites, 465 tests passed |
| Mobile TypeScript | `npx tsc --noEmit` passed |
| Affected OCR/integration checks | 83 passed, 5 skipped |
| QR helper | Project/LAN validation and bounded retry checks passed |
| PowerShell | Changed mobile launcher parsed successfully |
| Existing real development negatives | 140 original sources hash-checked; zero new text-positive sources |
| Browser lesson | Real local service; all five steps of `1/3 + 2/5` completed with `11/15` |
| Responsive browser checks | 375 × 812 and 812 × 375; no horizontal document overflow |
| Production OCR baseline | Checkpoint and vocabulary SHA-256 unchanged |

The full test sweep initially exposed old contracts that required projection
bands for learned text regions. The final integration checks instead verify
actual learned-region count, returned box count and the explicit unverified
geometry/review flags. No projection-band measurements were invented.
Historical private fixtures or catalogs that are absent produce explicit skips,
as do live probes without provider evidence; these skips are not successful
physical-image or provider-availability verification. An old decoder regression
now captures actual model output and verifies preservation without requiring a
historically incorrect transcription. OCR accuracy references are not altered.

The first relaxed rule threshold produced one false positive on the reviewed
negative set. It was repaired using the clipped-grid condition, then all 140
sources were checked again. These are development regression sources already
seen before, **not** an independent accuracy benchmark. Four existing framework
deprecation warnings remain. No physical phone test was performed.

## Drive evidence and remaining work

| Coverage | Count |
|---|---:|
| Source inventory | 1,319 |
| Historical immutable responses | 256 |
| New saved responses | 28 |
| Total saved responses | 284 |
| Pending sources | 1,035 |
| Automatically verified new training labels | 0 |

The new responses comprise 7 WORK, 2 MIXED, 16 MULTIPLE and 3 UNREADABLE.
The latter 19 responses return no transcribed rows: classification evidence is
not completed OCR. Four original images received limited visual spot reviews;
raw predictions remain unchanged and none becomes a full geometry/transcription
reference automatically. One pupil-written incorrect arithmetic result, `35%`,
is preserved literally instead of silently replaced with the computed answer.
A heading correction is kept separately from raw output.

The queue remains
`all_current_20261007/cloud_heading1063_20261008`, reader signature
`37837eb0ca97147be50113c444e6d142802861b2fc3929462d745835fc73f837`.
Its saved backoff survives restarts. Original bytes are read through the mounted
Drive source mapping with hash verification; no bulk original-image download
was performed. Resume using [the reading guide](../docs/OCR_REVIEW_AND_TRAINING.md#resume-page-reading-safely).
Completing the pending images and source-level review remains necessary before
any new OCR accuracy claim or training promotion.

The immutable supplement `ocr-lesson-continuation-20261009` on G retains queue
state, predictions, source reviews, negative comparison, code snapshots and test
logs. Its catalog entry lives in [drive-archives.json](../docs/drive-archives.json).
ZIP readback and a selected fresh restore are verified. Independent confirmation
of Google's background upload is unavailable, so working evidence is retained.

## Runtime and boundaries

The local core launcher reported `READY_FOR_FULL_DEMO`; the project AI runtime
was reloaded after verifying its executable, command and port ownership so the
final filter is active. The mobile manifest was verified against the current
local project. The browser lesson is real integration evidence, not phone
evidence. No checkpoint promotion, new model training, commit or push occurred.
The existing general/numeric model limitations remain; this phase does not
establish perfect fractions, long division or transcription for every photo.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded implementation and code simplification.
  - Applied to: exact arithmetic, existing detector condition, retry and guards.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: child-friendly fraction entry and narrow-screen usability.
  - Applied to: signed numerator input, wrapping and responsive verification.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React/React Native state and async loading behavior.
  - Applied to: synchronous submission ref, cancellation and per-asset promises.

Exact Expo v57 documentation was read before editing mobile code:
https://docs.expo.dev/versions/v57.0.0/ and its versioned Image reference.
