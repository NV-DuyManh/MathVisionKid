# Local versus deployed MathVisionKid — 2026-10-13

Owner instruction: replace the deployed version if the current local version is better.

## Decision

**No replacement is justified by this comparison.** The serving student web bundle and the deployed AI runtime already contain the current application code. The latest private OCR candidate fails its quality gate and must not replace the production model.

No deployment, model promotion, Git commit/push or paid service was performed in this phase.

## Verified evidence

- Vercel CLI inspected project `mathvisionkid-portal` in team `manh15` and production deployment `dpl_GMcA3TidGAgcarJJA7erBZA6LoPd`.
- Deployment is `Ready`, created at 20:34:46 on 13 October 2026 (Asia/Saigon), and aliased to `https://mathvisionkid-portal.vercel.app`.
- Public `/index.html`, `/study/index.html` and the student JavaScript entry bundle all return HTTP 200 and have byte-identical SHA-256 values to the local output used for the latest publication.
- Compared all 69 Python application files in local `ai/runtime/app` with the serving `mathvision-pc-preview-ai-1` container. After normalizing LF/CRLF line endings, every file matches.
- This includes tutoring planning, provider calls, generalized OCR geometry, learned text detection and the CRNN provider.
- Local and serving AI configurations agree on MODEL runtime, enabled Groq/Gemini providers, model names and request timeout settings. Credentials were not printed.
- Serving production OCR checkpoint has SHA-256 `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`, identical to the retained local production checkpoint.

Serving student entry bundle:

`/study/_expo/static/js/web/entry-eafa7471a4cf84621a1b355ffab7fc68.js`

SHA-256: `fb2c0b4bfd13ded608f7caa9e9cac4c9d3fcbfb974ca8972677dd7fad82d2d90`.

The Vercel MCP project read returned a scope authorization error. The mapped CLI fallback succeeded with explicit `manh15` scope; that successful CLI read and public byte comparisons support the deployment conclusions.

## OCR experiment and guide failures

The latest four-epoch private head experiment improves fitted new TRAIN matches from 43/50 to 45/50, while DEV digit/operator errors worsen from 30 to 31. It loses a zero in a previously correct `300 cm²` reading. The private grid/field experiments are not runtime integrations. These results do not establish a better deployable model.

Recent local guide logs show a primary provider timeout followed by a fallback provider HTTP 503. Later provider responses succeed but lesson requests still return 503; their specific validation failures are not logged. Because deployed tutoring code matches local tutoring code, republishing the same version cannot by itself fix those failures. This phase did not change validation, retry budgets or provider configuration.

Backend/OCR still depend on the running PC and its temporary HTTPS connection. Byte-equivalent web output is not proof of 24/7 cloud hosting, physical-device acceptance or independent OCR accuracy.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: inspect the actual shared implementation and avoid a duplicate release when the relevant artifacts already match.
  - Applied to: bounded source/configuration/model comparison, explicit-scope deployment reads and the no-replacement decision.

This inspect/test/report phase is complete. A replacement release remains conditional on a verified improvement.
