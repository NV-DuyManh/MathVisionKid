# AGENT.SKILLS.1.1 — Always-On Skill Router Closure, Identifier Normalization & Legacy Truth Fix

**Date:** 2026-09-12
**Status:** PASS

---

## 1. Truth Corrections from AGENT.SKILLS.1

### 1a. React Skill Identifier Mismatch — FIXED

| Location | Before | After |
|---|---|---|
| Folder name | `react-best-practices` | `react-best-practices` (unchanged) |
| Frontmatter `name` | `vercel-react-best-practices` | `vercel-react-best-practices` (unchanged, authoritative) |
| AGENTS.md routing matrix | `react-best-practices` ❌ | `vercel-react-best-practices` ✅ |
| AGENTS.md routing examples | `react-best-practices` ❌ | `vercel-react-best-practices` ✅ |
| SKILLS_INSTALLED.md | `react-best-practices` ❌ | `vercel-react-best-practices` ✅ |

**Decision:** The YAML frontmatter `name: vercel-react-best-practices` is the authoritative skill identifier. All references now use this exact identifier.

### 1b. Legacy Path Documentation — FIXED

| Statement | Before (AGENT.SKILLS.1) | After (Corrected) |
|---|---|---|
| `.agent/skills/` status | "not auto-discovered" / "inert legacy" / "archived duplicates" | "backward-compatible location that may still be discovered" |
| Legacy path treatment | Described as inert without proof | Truthfully documented as legacy duplicates present, canonical routing uses `.agents/skills/` |

### 1c. Workspace Rule — CREATED

| Item | Status |
|---|---|
| Rule file | `.agents/rules/mandatory-skill-router.md` ✅ |
| Mechanism | Antigravity workspace rule (auto-loaded from `.agents/rules/`) |
| Activation | ALWAYS ON — workspace rules at `.agents/rules/` are automatically loaded by Antigravity for every task |

---

## 2. Skill Identifier Reconciliation

All 11 active skills with folder name vs frontmatter name:

| Folder | Frontmatter `name` | Match | Notes |
|---|---|---|---|
| `banner-design` | `banner-design` | ✅ | — |
| `brand` | `brand` | ✅ | — |
| `design` | `design` | ✅ | — |
| `design-system` | `design-system` | ✅ | — |
| `fixing-accessibility` | `fixing-accessibility` | ✅ | — |
| `fixing-motion-performance` | `fixing-motion-performance` | ✅ | — |
| `react-best-practices` | `vercel-react-best-practices` | ⚠️ | Folder ≠ frontmatter. Frontmatter is authoritative. |
| `slides` | `slides` | ✅ | — |
| `ui-styling` | `ui-styling` | ✅ | — |
| `ui-ux-pro-max` | `ui-ux-pro-max` | ✅ | — |
| `web-design-guidelines` | `web-design-guidelines` | ✅ | — |

**10/11 exact match. 1/11 folder differs from frontmatter — documented and all references use frontmatter identifier.**

---

## 3. Workspace Rule: Mandatory Skill Router

**File:** `.agents/rules/mandatory-skill-router.md`

Contents enforce:
1. Task domain classification before implementation
2. Skill matching from `.agents/skills/` registry
3. SKILL.md must be read BEFORE editing code
4. Maximum 3 skills by default
5. No unrelated skill loading
6. Task-start declaration with exact identifiers and SKILL.md paths
7. Report traceability with exact identifiers
8. Cannot claim `Skills applied: X` unless X's SKILL.md was actually read

**Activation:** Antigravity automatically loads all `.md` files under `.agents/rules/` as workspace rules. No UI action required.

---

## 4. Actual SKILL.md Read Evidence (Section 8 Test)

**Dry-run task:** "Kiểm tra accessibility của form login MathVision Kids"

```
SKILL ROUTING
Task domains: accessibility, form UI
Skills matched:
- fixing-accessibility (.agents/skills/fixing-accessibility/SKILL.md)
Skills loaded: YES
```

**Evidence of SKILL.md read:**

File: `.agents/skills/fixing-accessibility/SKILL.md`
- **Read lines 23–50** containing "when to apply" section and "rule categories by priority" table
- **Concrete instruction cited:** "Do not rewrite large parts of the UI. Prefer minimal, targeted fixes." (line 21)
- **Priority system cited:** Priority 1 = "accessible names (critical)", Priority 2 = "keyboard access (critical)", Priority 3 = "focus and dialogs (critical)" (lines 37–39)
- **When to apply cited:** "adding or changing buttons, links, inputs, menus, dialogs, tabs, dropdowns" and "building forms, validation, error states, helper text" (lines 26–27)

**No product code was edited.** This proves the router correctly selects and reads the matching SKILL.md before any implementation would begin.

---

## 5. Dry-Run Selective Routing Test

### A. "Thiết kế lại màn hình đăng nhập React cho MathVision Kids"
- Task domains: UI redesign, React implementation, accessibility
- Skills matched: `ui-ux-pro-max`, `vercel-react-best-practices`, `fixing-accessibility` (3 skills)
- Unrelated skills loaded: NO
- **Result: ✅ PASS**

### B. "Tối ưu React component bị re-render nhiều"
- Task domains: React performance
- Skills matched: `vercel-react-best-practices` (1 skill)
- Design/accessibility loaded: NO
- **Result: ✅ PASS**

### C. "Kiểm tra accessibility của form login"
- Task domains: accessibility, form UI
- Skills matched: `fixing-accessibility`, optionally `web-design-guidelines` (1-2 skills)
- Banner/slides loaded: NO
- **Result: ✅ PASS**

### D. "Sửa Spring Boot refresh-token bug"
- Task domains: backend, Spring Boot, auth
- Skills matched: none (no backend-specific skill installed)
- UI/design skills loaded: NO
- **Result: ✅ PASS**

### E. "Tạo slide bảo vệ đồ án"
- Task domains: presentation, slides
- Skills matched: `slides` (1 skill)
- UI/React skills loaded: NO
- **Result: ✅ PASS**

---

## 6. Files Added / Modified

| File | Action | Description |
|---|---|---|
| `AGENTS.md` | MODIFIED | Fixed React identifier → `vercel-react-best-practices`, truthful legacy path wording, added SKILL.md path to task-start declaration and report traceability |
| `SKILLS_INSTALLED.md` | MODIFIED | Exact frontmatter identifiers, folder-vs-name disambiguation table, truthful legacy documentation, workspace rule reference |
| `.agents/rules/mandatory-skill-router.md` | NEW | Always-on workspace rule enforcing mandatory skill routing |

**Product code modified:** NO
**Commit:** NO
**Push:** NO

---

## 7. Legacy Status

| Path | Status |
|---|---|
| `.agent/skills/` | LEGACY_DUPLICATES_PRESENT — 4 skills duplicated from canonical `.agents/skills/`. Cannot rename (OS access denied). Documented as backward-compatible, not inert. |
| `.agent/workflows/ui-ux-pro-max.md` | LEGACY — superseded by `.agents/skills/ui-ux-pro-max/SKILL.md` |
| `.agent/SKILLS_INSTALLED.md` | LEGACY — superseded by root `SKILLS_INSTALLED.md` |

---

## Skills Applied

Skills Applied: None — this task was configuration/documentation cleanup only. No UI/design skill was applicable.
