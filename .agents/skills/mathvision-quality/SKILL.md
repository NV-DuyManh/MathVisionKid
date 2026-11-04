---
name: mathvision-quality
description: Plan and execute risk-based MathVisionKid regression checks with accurate evidence for web, native, backend, tutoring and speech changes.
---

Use docs/engineering/quality-and-security.md and task criteria to choose meaningful checks. Reproduce the failure, test the correction and affected adjacent behavior. Cover relevant timeout/quota, expired/wrong sessions, retry/duplicate writes, both voice caches and units/fractions; do not add unrelated checks solely for coverage numbers.

Use existing scripts and fixture/provider mocks for offline CI. Live TTS/LLM tests consume quota and need task scope; training needs explicit owner authorization. Keep actual device/audio observations separate from player UI, HTTP timings, mock output and OCR/model accuracy. H2 does not verify PostgreSQL migrations.

Record command, revision, result and exclusions. Failed checks return to implementation with the reproduction. Do not weaken assertions, raise timeouts without a cause or report all tests passed for a subset. Avoid fresh full builds for docs-only changes unless a concrete risk warrants them.
