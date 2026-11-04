# MathVisionKid — skill registry

Canonical source: [.agents/registry.json](.agents/registry.json). Validate: `npm run check:governance`.
Canonical skills live under `.agents/skills/`; do not route legacy `.agent/skills/` duplicates. Routes are candidate lists, not authorization to load every skill or perform external actions.

| Identifier | SKILL.md | Origin |
| --- | --- | --- |
| `banner-design` | [.agents/skills/banner-design/SKILL.md](.agents/skills/banner-design/SKILL.md) | existing-workspace |
| `brand` | [.agents/skills/brand/SKILL.md](.agents/skills/brand/SKILL.md) | existing-workspace |
| `design` | [.agents/skills/design/SKILL.md](.agents/skills/design/SKILL.md) | existing-workspace |
| `design-system` | [.agents/skills/design-system/SKILL.md](.agents/skills/design-system/SKILL.md) | existing-workspace |
| `docx` | [.agents/skills/docx/SKILL.md](.agents/skills/docx/SKILL.md) | existing-workspace |
| `fixing-accessibility` | [.agents/skills/fixing-accessibility/SKILL.md](.agents/skills/fixing-accessibility/SKILL.md) | existing-workspace |
| `fixing-motion-performance` | [.agents/skills/fixing-motion-performance/SKILL.md](.agents/skills/fixing-motion-performance/SKILL.md) | existing-workspace |
| `mathvision-backend` | [.agents/skills/mathvision-backend/SKILL.md](.agents/skills/mathvision-backend/SKILL.md) | project |
| `mathvision-quality` | [.agents/skills/mathvision-quality/SKILL.md](.agents/skills/mathvision-quality/SKILL.md) | project |
| `mathvision-review` | [.agents/skills/mathvision-review/SKILL.md](.agents/skills/mathvision-review/SKILL.md) | project |
| `mathvision-workflow` | [.agents/skills/mathvision-workflow/SKILL.md](.agents/skills/mathvision-workflow/SKILL.md) | project |
| `ponytail` | [.agents/skills/ponytail/SKILL.md](.agents/skills/ponytail/SKILL.md) | existing-workspace |
| `ponytail-audit` | [.agents/skills/ponytail-audit/SKILL.md](.agents/skills/ponytail-audit/SKILL.md) | existing-workspace |
| `ponytail-debt` | [.agents/skills/ponytail-debt/SKILL.md](.agents/skills/ponytail-debt/SKILL.md) | existing-workspace |
| `ponytail-gain` | [.agents/skills/ponytail-gain/SKILL.md](.agents/skills/ponytail-gain/SKILL.md) | existing-workspace |
| `ponytail-help` | [.agents/skills/ponytail-help/SKILL.md](.agents/skills/ponytail-help/SKILL.md) | existing-workspace |
| `ponytail-review` | [.agents/skills/ponytail-review/SKILL.md](.agents/skills/ponytail-review/SKILL.md) | existing-workspace |
| `vercel-react-best-practices` | [.agents/skills/react-best-practices/SKILL.md](.agents/skills/react-best-practices/SKILL.md) | existing-workspace |
| `slides` | [.agents/skills/slides/SKILL.md](.agents/skills/slides/SKILL.md) | existing-workspace |
| `ui-styling` | [.agents/skills/ui-styling/SKILL.md](.agents/skills/ui-styling/SKILL.md) | existing-workspace |
| `ui-ux-pro-max` | [.agents/skills/ui-ux-pro-max/SKILL.md](.agents/skills/ui-ux-pro-max/SKILL.md) | existing-workspace |
| `web-design-guidelines` | [.agents/skills/web-design-guidelines/SKILL.md](.agents/skills/web-design-guidelines/SKILL.md) | existing-workspace |
| `xlsx` | [.agents/skills/xlsx/SKILL.md](.agents/skills/xlsx/SKILL.md) | existing-workspace |

Use `node scripts/skills.mjs route <domain>` to discover a phase. Read the chosen SKILL.md before implementing. Prefer correctness review for security/data/math and complexity review only for bloat. Preserve upstream notices and research provenance.
