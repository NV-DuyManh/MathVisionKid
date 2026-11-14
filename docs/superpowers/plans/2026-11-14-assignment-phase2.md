# Assignment Phase 2 Implementation Plan

> **For agentic workers:** implement this plan task by task with TDD and verify each slice.

**Goal:** Let teachers draft, preview, and publish assignments to a transactionally frozen class roster, then let only current recipients access the assignment in Student Web.

**Architecture:** Extend legacy Assignment with nullable prompt and instructions plus DRAFT/PUBLISHED state. Keep the existing ACTIVE assignment creation route intact for paper Batch. Add one immutable publication row and unique recipient snapshots. All publication and draft mutations lock Classroom before Assignment, matching roster changes and teacher handover.

**Tech Stack:** Spring Boot, JPA, PostgreSQL/Flyway, Teacher React/Vite, Student Expo Web.

**Spec:** Owner Phase 2 directive in pasted-text-1.txt. The three referenced spec/plan files are absent from this worktree.

## Global Constraints

- Backend decides role, classroom ownership and recipient access.
- Legacy assignments remain ACTIVE and do not appear in Student assignments.
- Publish snapshots no more than 50 current roster members.
- No submissions, decisions, AI jobs, deadlines or upload flow.

## Review Focus

- Drafts and legacy assignments never enter Student results.
- Roster mutation and teacher handover serialize with publish on the class row.
- Concurrent publish calls return one publication and recipient set.
- Removed recipients lose Student read access while the published snapshot remains historical.
- Student APIs expose only current active account and current roster membership.
- Assignment details and previews remain inside Teacher Web and never expose recipient identities to Student.

### Slice 2A–2B: Backend Draft and Publish

Add V36 nullable assignment prompt/instructions and immutable publication/recipient tables. Add transactional class scoped draft, update, list/detail, publish, recipient list, Student list/detail. Keep legacy create and Batch semantics.

### Slice 2C: Teacher Web

Extend the class detail page with a real assignment tab, draft form, preview, publish confirmation and recipient count. Reuse API-backed services and preserve the paper Batch entry route.

### Slice 2D: Student Web

Add a web-only assigned-work route and tab. Implement current-account list/detail, loading, empty and error states. Preserve the native tab behavior.

### Slice 2E: Verification

Run PostgreSQL migration/transaction tests, existing Batch/Admin/Teacher/Student regression, builds, governance and Playwright through actual local apps. Run final mathvision-review and EGM readiness review, then commit Phase 2 locally.
