# Architecture Decision Records (ADR)

## ADR-001: Clients communicate only with Spring Boot
**Decision:** Student Mobile and Teacher Web will only interact with the Spring Boot Business API.
**Reason:** Centralizes authentication, authorization, and business logic. Clients do not need to know about AI infrastructure.

## ADR-002: FastAPI is internal-only
**Decision:** The FastAPI service running the OCR and validation logic is strictly internal.
**Reason:** Protects the AI service from public exposure, simplifies auth (Spring Boot handles it), and allows asynchronous orchestration by Celery/Redis without exposing it to the UI.

## ADR-003: Submission processing is asynchronous
**Decision:** Submission uploads return `202 Accepted` and a `PROCESSING` status. Clients must poll for updates.
**Reason:** OCR and VLM diagnosis can take 5-15 seconds. Holding a synchronous HTTP connection is fragile on mobile networks.

## ADR-004: Recognition uncertainty is separate from student error
**Decision:** We model `recognitionConfidence` independently from `diagnosisConfidence`. Ambiguous tokens trigger a `NEEDS_CONFIRMATION` flow rather than automatically being marked wrong.
**Reason:** Fulfills the product principle that AI uncertainty should not penalize the student.

## ADR-005: Teacher is final grade authority
**Decision:** The `GradeProposal` model explicitly sets `isOfficial: false`. Final scores require a `TeacherDecision`.
**Reason:** AI handles repetitive checking, but the teacher makes the educational judgment.

## ADR-006: Evidence uses normalized bounding boxes
**Decision:** `BoundingBox` coordinates use normalized floats `[0.0, 1.0]` relative to image width/height. Origin is top-left, x increases right, y increases downward.
**Reason:** Allows drawing UI overlays consistently regardless of the device's screen size or original image scaling.

## ADR-007: AI proposed score is non-official
**Decision:** AI cannot create an official score.
**Reason:** Safety and correctness guarantee requires a human-in-the-loop for edge cases.

## ADR-008: Polling for MVP
**Decision:** MVP uses polling rather than WebSocket. Clients will poll the Submission or Batch status endpoint every 2-5 seconds.
**Reason:** Significantly reduces backend infrastructure complexity for Phase 2/3. WebSockets can be introduced later if real-time constraints tighten.

## ADR-009: /api/v1 API version
**Decision:** All public REST endpoints must be prefixed with `/api/v1`.
**Reason:** Ensures future backward compatibility when breaking changes are introduced.

## ADR-010: Batch lifecycle and review state are separate concepts
**Decision:** Batch status (`COMPLETED`, etc.) does not dictate if items need review. Review state is tracked via `reviewRequiredCount`.
**Reason:** A batch can finish processing (COMPLETED) but still have submissions requiring teacher intervention.
