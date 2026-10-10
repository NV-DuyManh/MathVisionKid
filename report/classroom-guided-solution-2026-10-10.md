# Classroom guided solutions — 2026-10-10

The previous garden lesson asked for six arithmetic fragments, beginning with a denominator product, without explaining the dependency on the original question. It also showed the operation immediately and advanced as soon as an answer was accepted.

## Result

- The garden family now has three actual solution steps: combined fraction, remaining fraction, whole quantity. The parser still derives quantities and group names from confirmed source text, with its existing contradiction/extra-goal guards. No image identifiers, example lookup or substituted OCR numbers are used.
- The first explanation explains why the given count cannot yet yield the whole. Progressive help explains equal-sized parts, why multiplying both numerator and denominator preserves a fraction, and why finding the whole involves dividing then multiplying. Hints show the method without the current result.
- The learner initially sees the reason, question and classroom sentence. The operation is disclosed when help is requested. Fraction questions open numerator/denominator inputs automatically; exact equivalent answers are accepted and rounded answers rejected.
- After a correct answer, the UI pauses on a checked written solution and its explanation. Continuing is an explicit local action, with no additional answer submission. Choice checks are excluded from the final written solution.
- Completion assembles **Bài giải**, solution sentences, checked expressions, units, exact fraction working, a verified **Đáp số** where the plan identifies a final answer, and a separate explanation review. Results are not shown ahead of completion.
- Generated lessons now request classroom solution sentences, reasons linking successive quantities, progressive hints and an explicitly identified final answer. New prose fields retain source-number/public-content validation; final answer references must name a valid calculation. Unsupported plans still fail safely instead of guessing.
- Geometry explanations now explain why a shared height is needed and why the triangle/trapezoid formulas multiply and divide. Other supported local calculations retain their answer checks and receive written-solution formatting.
- The backend forwards only bounded public lesson fields, strips private answer keys, injects the authenticated owner and rejects a premature conclusion. No RBAC/auth authority moved into the client.

## Validation

| Check | Result |
| --- | --- |
| AI fraction, guided and primary lesson suites | 83 passed |
| Student lesson screen and API suites | 62 passed |
| Backend MathTutorService and MathTutorController suites | 75 passed |
| Student TypeScript | Passed |
| Portal config / production artifact gates | 11 / 2 passed |
| Student export address and router gates | 4 passed |
| Public API integration | Passed login, all three steps, two hints per step, wrong-answer non-advancement, full checked solution |

Public integration uses the genuine transcription retained from the owner's garden photo. Independent exact arithmetic is used only as a test assertion, not as an OCR response. Three additional garden variants and fraction operators are covered in the lesson suite. This does not establish universal OCR accuracy or demonstrate a physical phone.

## Browser Evidence

- Tested the production student page through its actual controls: confirmed the source transcription, started the lesson, opened progressive hints, entered fraction answers, paused on each checked solution, explicitly continued and completed the whole-count answer.
- Initial operation stays hidden until help is requested. Fraction questions open separate numerator and denominator fields. Completed steps show actual classroom sentences and vertically rendered fractions; the final view has three solution lines and **Đáp số: 60 cây.**
- A final visual pass removed redundant multiplication by 1 and writes a whole number directly as an equivalent fraction. The AI suites and public API probe passed again after this polish; the browser completed all three steps again against the updated runtime.
- Screenshots: `infra/local-runtime/pc-preview/classroom-step-reason.png` and `infra/local-runtime/pc-preview/classroom-completed-solution.png` (private local evidence, 1280×720 browser viewport). No physical-device or new photo-upload claim is made by this text-based browser lesson.

## Deploy Result

- URL: https://mathvisionkid-portal.vercel.app
- Unique deployment: https://mathvisionkid-portal-9p22lmheb-manh15.vercel.app
- ID: `dpl_H3tVWJ8cumBHJ8ndBuGiGDG3GiXf`
- Target: production; status: READY (CLI inspection)
- Base commit: `0e40db7` plus uncommitted workspace changes; no commit/push performed
- Framework: Vite portal + shared Expo Router student web export
- Build duration: unavailable from deployment inspection; student web bundle took about 25 seconds locally
- Runtime: existing isolated PC preview services rebuilt; existing data retained. This update does not create a 24/7 cloud backend.

## Post-Deploy Observability

- Vercel error scan, last hour: no logs found. This is a static-site log observation, not evidence of zero backend/provider errors.
- Drains: unchanged; none were installed for this task.
- Monitoring gap: backend still depends on the owner's PC and current tunnel. Oracle signup remains a separate blocked handoff from the prior task.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: learner interaction, readable explanations and progressive help.
  - Applied to: existing theme, explicit continue controls, fraction inputs and written-solution layout. Focused disclosure searches returned unrelated typography entries twice; no unverified dataset recommendation was applied.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: shared React Native/web screen implementation.
  - Applied to: small reusable solution-line component, primitive effect dependencies, event-driven pause/continue state; no new client dependency.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: grounded tutor logic and bounded DTO changes.
  - Applied to: reuse exact Fraction evaluation, existing sessions/hints and source confirmation; no parallel teaching service or model training.
- `deployments-cicd`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated/vercel/0722921d/skills/deployments-cicd/SKILL.md`
  - Why selected: publish and verify the already-authorized online update.
  - Applied to: tested static prebuilt publication, actual bundle endpoint verification, READY inspection and error scan.
