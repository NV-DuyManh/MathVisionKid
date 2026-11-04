---
name: mathvision-backend
description: Implement or review MathVisionKid Spring APIs, PostgreSQL migrations and data integrity when changing backend contracts or persistence.
---

Read docs/engineering/api-and-data.md and the affected contracts. Preserve Spring as RBAC/ownership authority. Trace request DTO, service, persistence and frontend consumers before changing a contract. Existing routes/errors/schema stay compatible unless a migration is explicitly part of the task.

Protect mutable state with appropriate transactions/uniqueness/idempotency. Do not trust frontend score/role/student identity. Reject unrelated-account access and old-session responses. Preserve original uploads and confirmed OCR source; do not log private data or expose runtime configuration.

Use versioned Flyway migrations, never edit a released migration or apply destructive changes to a shared DB as a test. Distinguish disposable PostgreSQL migration checks from H2 behavior tests. Verify success, validation, unauthorized/forbidden and relevant concurrency/retry cases before handoff.
