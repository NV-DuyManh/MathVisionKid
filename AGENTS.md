# MathVision Kids — Agent Instructions

## Expo HAS CHANGED

Read the exact versioned docs at https://docs.expo.dev/versions/v57.0.0/ before writing any code.

---

## INSTRUCTION PRECEDENCE ORDER

1. **Owner explicit instruction** (user's current message)
2. **MathVision Kids project rules** (this section)
3. **Task-specific acceptance criteria**
4. **Matching Agent Skills** from the project, personal catalog, and active plugins
5. **Generic agent preferences**

---

## PROJECT RULES

- Follow [team workflow](docs/engineering/team-working-agreement.md), [naming](docs/engineering/naming-conventions.md), [API/data contracts](docs/engineering/api-and-data.md), and [quality/security](docs/engineering/quality-and-security.md). Apply naming rules to new/changed code; never mass-rename working code, published contracts or research receipts.
- Machine-readable routing: `.agents/registry.json`; validate with `npm run check:governance`. Correctness review uses `mathvision-review`; `ponytail-review` is only the optional complexity pass.
- Inspect → implement → test → report → STOP
- No commit/push unless owner explicitly permits
- Git Flow is mandatory: new `feature/*` and `bugfix/*` start from current `develop` and target `develop`; `release/*` starts from `develop`, `hotfix/*` from released `main`. Only release/hotfix PRs target `main`, with reviewed version notes, then backmerge into `develop`. Follow `docs/engineering/git-flow.md` and `.github/git-flow.json`. Owner `NV-DuyManh` alone is exempt from PR approval; never bypass routing, CI or history protection to force a merge.
- Preserve contributor attribution: keep original author metadata on merge/cherry-pick; use `cherry-pick -x` for selected commits. For adapted code without original commits, record the source SHA and verified `Co-authored-by` identity. Never claim the integrator wrote all contributed code, invent identities, or rewrite published main solely for credit. Update `CONTRIBUTORS.md` for new integration credit and report the actual PR state.
- No model training unless explicitly authorized
- Preserve Student Mobile when task scope is web-only
- Backend remains authority for RBAC/auth
- Do not fabricate physical-device evidence
- For recoverable tooling and runtime failures, diagnose the cause, apply an authorized fix, and retry. This includes failed skill or MCP calls and web services that need restarting. Use an available fallback when the preferred tool remains unavailable. Report the exact failure and verification still missing if recovery fails.
- For web UI or workflow changes, run the application and exercise the actual routes and controls in a browser as each affected role. Use browser MCP tools such as Playwright or Chrome DevTools when available, alongside relevant skills. Check responsive behavior and important error or recovery paths. Record which flows ran against the real backend and which used test fixtures. Source inspection alone does not verify rendered UX.
- Student-facing UI must NOT show: Expo, Metro, LAN, localhost, ports, Spring Boot, FastAPI, MinIO, Redis, PostgreSQL, API URLs, developer instructions, terminal instructions, demo/test account emails, architecture/debug information

---

## MANDATORY SKILL ROUTING POLICY

**Required behavior before every substantial implementation task:**

1. Read the user's task description.
2. Identify task domains (e.g., "React UI", "accessibility", "animation").
3. Inspect the workspace skill registry at `.agents/skills/` and the available personal and active plugin skill catalogs. Discover relevant MCP tools from the active session, including deferred tools.
4. Match each implementation phase to the **most specific relevant skill(s)**. There is no fixed skill-count limit: load the skills needed for the phase before editing, then route again when entering a different domain.
5. **Read the selected skill instructions before editing code.** Use the canonical workspace path for project skills and the advertised path or provider for personal and plugin skills.
6. Follow skill instructions during implementation.
7. If multiple independent domains exist, use multiple relevant skills.
8. Do NOT load unrelated skills.
9. If no skill matches, explicitly state `Skills matched: none`.
10. Before final response/report, state: `Skills applied: <skill1>, <skill2>, ...`

### Task-Start Declaration

Every substantial implementation task must begin with:

```
SKILL ROUTING
Task domains: <identified domains>
Skills matched:
- <exact skill identifier> (<project, personal, or plugin source>)
Skills loaded: YES / NO
```

3–6 lines maximum. Do not make this verbose.

### Report Traceability

Every phase report under `report/` must include:

```markdown
## Skills Applied

- `<exact frontmatter identifier>`
  - SKILL.md: <canonical path or provider resource>
  - Why selected: <reason>
  - Applied to: <specific areas>
```

If no skills apply: `Skills Applied: None — no installed skill matched the task.`

---

## SKILL ROUTING MATRIX

Use this matrix for project skills and extend it with relevant personal and plugin skills available in the active session.

| Task Domain | Primary Skill | Secondary Skill(s) |
|---|---|---|
| UI / visual redesign / page layout | `ui-ux-pro-max` | `web-design-guidelines` |
| React / React Native implementation | `vercel-react-best-practices` | — |
| Accessibility audit / fix | `fixing-accessibility` | — |
| Animation / motion / rendering perf | `fixing-motion-performance` | — |
| Brand / logo / visual identity | `brand` | `design` |
| Design system / tokens | `design-system` | `design` |
| General UI styling / components | `ui-styling` | — |
| Presentations / slides | `slides` | — |
| Banner / poster / hero image | `banner-design` | `design` |
| Comprehensive design task | `design` | (sub-skills as needed) |
| Web UI review / audit | `web-design-guidelines` | `fixing-accessibility` |
| Code simplification / YAGNI / minimal diffs | `ponytail` | — |
| Code review / anti-bloat / over-engineering | `ponytail-review` | `ponytail-audit` |
| Technical debt audit / simplicity | `ponytail-debt` | `ponytail-gain` |
| Backend / Spring / database / API | `ponytail` (if simplifying/refactoring) | — |
| AI model / training / OCR | _(no UI/design skill)_ | — |

### Routing Examples

| Task | Skills Selected |
|---|---|
| "Redesign login page in React" | `ui-ux-pro-max`, `vercel-react-best-practices`, `fixing-accessibility` |
| "Fix animation stutter on dashboard" | `fixing-motion-performance` |
| "Create PowerPoint defense presentation" | `slides` |
| "Refactor authentication service cleanly" | `ponytail` |
| "Review PR for over-engineering and bloat" | `ponytail-review` |
| "Review portal accessibility" | `fixing-accessibility`, `web-design-guidelines` |
| "Design a social media banner" | `banner-design` |

### Selection Rules

- Prefer the **most specific** skill first.
- Do NOT load all skills on every task.
- Backend-only tasks must NOT trigger UI/design skills.
- No fixed maximum per task. Use as many relevant skills as the actual work requires, selected phase by phase; do not preload unrelated skills or treat the registry as a mandatory checklist.

---

## CANONICAL SKILL DIRECTORY

All workspace skills live at:

```
.agents/skills/<skill-name>/SKILL.md
```

### Canonical Path Priority

1. **`.agents/skills/<skill-name>/SKILL.md`** — Always use this path.
2. **`.agent/skills/<skill-name>/SKILL.md`** — Legacy fallback. Use ONLY if no canonical copy exists under `.agents/skills/`.

**Hard rule:** If a skill exists in both `.agents/skills/` and `.agent/skills/`, the agent MUST load from `.agents/skills/`. Loading from `.agent/skills/` when a canonical copy exists is a routing error.

See `SKILLS_INSTALLED.md` for the full registry.
