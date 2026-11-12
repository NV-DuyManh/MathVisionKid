---
name: mathvision-workflow
description: Coordinate MathVisionKid requirements, implementation, verification and an authorized release when a task spans multiple apps or contributors.
---

Read root AGENTS.md and docs/engineering/team-working-agreement.md. Use .agents/registry.json to select only the current phase's skills; a route is a candidate list, not automatic loading.

Follow docs/engineering/git-flow.md on every Git task. Work from current develop on feature/* or bugfix/*, integrate through a PR to develop, and release through release/<semver> or hotfix/<semver> to main. Keep the release/hotfix branch until its changes are also backmerged into develop. Owner approval exemption is scoped to the review ruleset; never bypass routing, required checks or shared history protections. Inspect live rulesets before claiming that server enforcement is enabled.

There is no fixed skill-count cap. For a task spanning OCR, mathematics, UI, backend or verification, load the specific skills needed before each phase, and record the skills actually applied. Do not preload unrelated skills. This routing flexibility does not change permissions, evidence standards or release requirements.

Carry scope, actual source/decision, acceptance criteria, revision, evidence and residual risks across phases. Use docs/templates/task-handoff.md for a handoff; small fixes can remain in the PR. Stop only dependent work when a requirement is unresolved, continue independent work. Preserve native Student when scope is web-only.

Release needs an authorized destination, exact revision, successful applicable checks, configuration/migration delta, smoke and rollback. Do not conflate merge, deployment, model training or physical-device testing. Skills/routing do not authorize any of them. Follow the existing owner authorization; do not introduce new approval steps for ordinary local work.
