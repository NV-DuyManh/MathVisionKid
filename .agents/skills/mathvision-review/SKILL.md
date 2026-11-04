---
name: mathvision-review
description: Review MathVisionKid changes for correctness, session isolation, student privacy, mathematical validity and regressions before integration.
---

Read acceptance criteria, final diff, callers and evidence. Use docs/engineering/quality-and-security.md for severity. Prioritize backend RBAC/resource ownership, stale responses across accounts, duplicated writes/uploads, source-confirmation boundaries, fractions/units, validator false rejections and narration cache/prefetch isolation.

Findings need a revision/file/line, reproducible trigger, impact and correction. Distinguish verified defects, questions and untested risks. Passing mocks/CI is not physical-device or cloud latency evidence. Do not fix false rejections by bypassing verification or inventing data. Review original author attribution during selective integration.

Report meaningful coverage limits even with no findings. Return blockers to implementation/verification. Keep correctness review separate from optional ponytail-review complexity checks. Do not auto-approve, auto-merge or silently resolve another reviewer's discussion.
