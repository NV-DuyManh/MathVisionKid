# AGENT.SKILLS.1.2 — Canonical Skill Path Enforcement & Legacy Duplicate Isolation

**Task Reference:** AGENT.SKILLS.1.2
**Project:** MathVision Kids
**Mode:** Micro Configuration Fix — No Product Code Changes
**Timestamp:** 2026-09-12T22:00:00+07:00
**Status:** PASS

---

## 1. Before State

### Observed routing drift (from AUTH.UX.1 login review):

| Skill Identifier | Path Actually Loaded | Expected Canonical Path | Status |
|---|---|---|---|
| `ui-ux-pro-max` | `.agents/skills/ui-ux-pro-max/SKILL.md` | `.agents/skills/ui-ux-pro-max/SKILL.md` | ✅ Correct |
| `web-design-guidelines` | `.agent/skills/web-design-guidelines/SKILL.md` | `.agents/skills/web-design-guidelines/SKILL.md` | ⚠️ Wrong path |
| `fixing-accessibility` | `.agent/skills/fixing-accessibility/SKILL.md` | `.agents/skills/fixing-accessibility/SKILL.md` | ⚠️ Wrong path |

### Legacy duplicates present in `.agent/skills/`:

| Legacy Path | Byte-identical to Canonical? |
|---|---|
| `.agent/skills/fixing-accessibility/SKILL.md` | YES (`fc /b` — no differences) |
| `.agent/skills/fixing-motion-performance/SKILL.md` | YES (`fc /b` — no differences) |
| `.agent/skills/react-best-practices/SKILL.md` | YES (`fc /b` — no differences) |
| `.agent/skills/web-design-guidelines/SKILL.md` | YES (`fc /b` — no differences) |

All 4 legacy duplicates were confirmed byte-identical to their canonical counterparts.

---

## 2. Rule Changes

### `.agents/rules/mandatory-skill-router.md`

Added new section **"Canonical Skill Resolution"** (between "Mandatory procedure" and "Required task-start declaration"):

```markdown
## Canonical Skill Resolution

- Canonical workspace skills live under `.agents/skills/`.
- When a matching skill exists in both `.agents/skills/` and `.agent/skills/`, **ALWAYS** use the `.agents/skills/` copy.
- **Never** load a legacy duplicate from `.agent/skills/` when a canonical copy exists under `.agents/skills/`.
- Use `.agent/skills/` only as a backward-compatible fallback when **no canonical skill exists** under `.agents/skills/`.
- The task-start declaration must show the exact canonical `SKILL.md` path actually read.
- If the loaded path begins with `.agent/skills/` and a `.agents/skills/` equivalent exists, the routing is **INCORRECT** and must be corrected.
```

No other sections modified. All existing project rules and precedence order preserved.

---

## 3. AGENTS.md Changes

Replaced the **"CANONICAL SKILL DIRECTORY"** section with an explicit priority ordering:

```markdown
### Canonical Path Priority

1. **`.agents/skills/<skill-name>/SKILL.md`** — Always use this path.
2. **`.agent/skills/<skill-name>/SKILL.md`** — Legacy fallback. Use ONLY if no canonical copy exists under `.agents/skills/`.

**Hard rule:** If a skill exists in both `.agents/skills/` and `.agent/skills/`, the agent MUST load from `.agents/skills/`. Loading from `.agent/skills/` when a canonical copy exists is a routing error.
```

No unrelated project rules changed. Instruction precedence order, project rules, routing matrix, selection rules — all preserved as-is.

---

## 4. Registry Changes

`SKILLS_INSTALLED.md` updated:

- Added **"Canonical Path Priority"** section at the top
- Each skill row now includes exact canonical path and legacy duplicate status
- Legacy duplicates marked as:
  - `REMOVED — moved to .agent/skills-legacy/` (3 skills)
  - `LEGACY_DUPLICATE_DO_NOT_ROUTE` (1 skill — OS access denied)
- Added **"Legacy Duplicate Status"** table with filesystem action and content match for each

---

## 5. Legacy Duplicate Status

### Filesystem isolation results:

| Legacy Path | Action | Result |
|---|---|---|
| `.agent/skills/fixing-accessibility/` | `move → .agent/skills-legacy/` | ✅ Moved successfully |
| `.agent/skills/fixing-motion-performance/` | `move → .agent/skills-legacy/` | ✅ Moved successfully |
| `.agent/skills/web-design-guidelines/` | `move → .agent/skills-legacy/` | ✅ Moved successfully |
| `.agent/skills/react-best-practices/` | `move → .agent/skills-legacy/` | ❌ Access denied (OS permission) |

### Remaining state:

- `.agent/skills/` now contains **only** `react-best-practices/` (locked by OS)
- `.agent/skills-legacy/` contains 3 archived duplicates (non-discoverable path)
- Canonical `.agents/skills/` contains all 11 active skills (unchanged)
- The remaining `react-best-practices` legacy copy is documented as `LEGACY_DUPLICATE_DO_NOT_ROUTE` in registry and enforced by the canonical resolution rule

---

## 6. Real UI Routing Test

**Task:** "Review lại giao diện login MathVision Kids, chưa sửa code."

**Expected skills:** `ui-ux-pro-max`, `web-design-guidelines`, `fixing-accessibility`

| Skill | Required Canonical Path | Loaded Path | Legacy exists in `.agent/skills/`? | Verdict |
|---|---|---|---|---|
| `ui-ux-pro-max` | `.agents/skills/ui-ux-pro-max/SKILL.md` | `.agents/skills/ui-ux-pro-max/SKILL.md` | No | ✅ PASS |
| `web-design-guidelines` | `.agents/skills/web-design-guidelines/SKILL.md` | `.agents/skills/web-design-guidelines/SKILL.md` | No (moved to skills-legacy) | ✅ PASS |
| `fixing-accessibility` | `.agents/skills/fixing-accessibility/SKILL.md` | `.agents/skills/fixing-accessibility/SKILL.md` | No (moved to skills-legacy) | ✅ PASS |

**No loaded path begins with `.agent/skills/`.** ✅

---

## 7. React Routing Test

**Task:** "Tối ưu React component bị re-render nhiều, chưa sửa code."

**Expected skill:** `vercel-react-best-practices`

| Skill | Required Canonical Path | Loaded Path | Legacy exists in `.agent/skills/`? | Verdict |
|---|---|---|---|---|
| `vercel-react-best-practices` | `.agents/skills/react-best-practices/SKILL.md` | `.agents/skills/react-best-practices/SKILL.md` | Yes (locked, but ruled `LEGACY_DUPLICATE_DO_NOT_ROUTE`) | ✅ PASS |

**No UI/design/accessibility skills loaded.** ✅

---

## 8. Backend Negative Test

**Task:** "Sửa Spring Boot refresh-token bug, chưa sửa code."

**Expected:** `Skills matched: none`

| UI/Design Skill Loaded | Verdict |
|---|---|
| None | ✅ PASS |

---

## 9. Files Modified

| File | Change Type | Product Code? |
|---|---|---|
| `.agents/rules/mandatory-skill-router.md` | Added "Canonical Skill Resolution" section | No — workspace agent rule |
| `AGENTS.md` | Updated "CANONICAL SKILL DIRECTORY" section | No — agent instructions |
| `SKILLS_INSTALLED.md` | Full rewrite with canonical enforcement | No — skill registry |
| `.agent/skills/fixing-accessibility/` | Moved to `.agent/skills-legacy/` | No — legacy duplicate isolation |
| `.agent/skills/fixing-motion-performance/` | Moved to `.agent/skills-legacy/` | No — legacy duplicate isolation |
| `.agent/skills/web-design-guidelines/` | Moved to `.agent/skills-legacy/` | No — legacy duplicate isolation |

**Zero product code files modified.**

---

## 10. Final Verdict

| Criterion | Result |
|---|---|
| Always-On router updated | ✅ PASS |
| Canonical `.agents/skills` priority enforced | ✅ PASS |
| UI review loaded canonical paths only | ✅ PASS |
| React review loaded canonical path | ✅ PASS |
| Backend task loaded no UI skills | ✅ PASS |
| Legacy duplicates isolated | ✅ 3/4 REMOVED, 1/4 PRESENT_BUT_NOT_ROUTED (OS locked) |
| Product code modified | NO |
| Commit | NO |
| Push | NO |

**AGENT.SKILLS.1.2: PASS**

---

## Skills Applied

Skills Applied: None — this task is configuration/routing only, not a UI/design/implementation task.
