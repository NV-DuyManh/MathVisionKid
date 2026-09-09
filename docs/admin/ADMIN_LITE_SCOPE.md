# MathVision Kids — Track A1: Admin Lite Scope Specification

> **Notice:** Admin Lite is an approved controlled scope extension beyond the previously frozen Student/Teacher application surface. It does not alter Proposal v3.1, Capstone Registration, or AI Usage Disclosure documents. Phase 4.3 evaluation remains `BLOCKED_DATASET`.

---

## 1. Why Admin Exists
MathVision Kids initially implemented self-contained Student and Teacher workflows with development-time synthetic seed accounts. In realistic school settings, teachers should not be burdened with database provisioning, and students must not self-register arbitrary accounts.

The **ADMIN** ("Admin Lite") role provides an operational administrative boundary for:
1. Operational account provisioning (creating, inspecting, updating, disabling, and enabling Teacher and Student accounts).
2. Classroom management (creating classes, assigning teachers, adding/removing students to rosters).
3. System operational visibility (lightweight account and class metrics, audit trail inspection).

---

## 2. What Admin Can Do
- **User Provisioning:**
  - Create new `TEACHER` accounts.
  - Create new `STUDENT` accounts with enforced grade level ($1 \dots 5$).
  - List and search users with role, status, and text query filtering.
  - Inspect detailed account metadata and class enrollments.
  - Update allowed safe profile fields (e.g., `displayName`, student `gradeLevel`).
  - Disable user accounts (blocking future logins and revoking active refresh tokens).
  - Enable previously disabled user accounts.
  - Perform administrative password resets with temporary passwords.
- **Classroom & Roster Administration:**
  - Create classrooms specifying name, grade level ($1 \dots 5$), and academic year.
  - Assign active Teachers to classrooms.
  - Add active Students to classroom rosters.
  - Remove Students from classroom rosters.
  - Update classroom metadata.
- **Audit & Operational Metrics:**
  - View aggregate counts of students (total, active, disabled), teachers, and classes.
  - Inspect audit event logs recording administrative write operations.

---

## 3. What Admin Cannot Do (Strict Privacy & Authority Boundary)
- **Grading & Review:**
  - ADMIN is **not** an educational grading authority.
  - ADMIN cannot approve student grades (`POST /api/v1/teacher/submissions/{id}/approve` returns `403 Forbidden`).
  - ADMIN cannot override student grades (`POST /api/v1/teacher/submissions/{id}/override` returns `403 Forbidden`).
  - ADMIN cannot create `TeacherDecision` records or submit student feedback.
- **AI & Model Authority:**
  - ADMIN cannot alter deterministic math validation rules.
  - ADMIN cannot modify AI confidence thresholds or model hyperparameters.
  - ADMIN cannot access raw MinIO student handwriting images or evidence crops.
  - ADMIN cannot execute AI training jobs or access training workspaces.
- **Role Escalation:**
  - ADMIN cannot create another `ADMIN` user via the public Admin API.
  - ADMIN cannot disable their own account.
  - ADMIN cannot arbitrarily change a user's role from STUDENT to TEACHER or vice versa. Roles are immutable after creation.

---

## 4. Role Model & Authorization Boundaries
MathVision Kids strictly supports three distinct operational roles:
```
STUDENT   --> /api/v1/student/**
TEACHER   --> /api/v1/teacher/**
ADMIN     --> /api/v1/admin/**
Shared    --> /api/v1/me, /api/v1/auth/**
```
There is **no broad role hierarchy** (i.e. `ADMIN > TEACHER > STUDENT` is rejected). An administrator requesting teacher endpoints is rejected with `403 Forbidden`. A teacher or student requesting administrator endpoints is rejected with `403 Forbidden`.

---

## 5. Account Provisioning vs Demo Seeding
- **Development Seed Accounts (`@Profile("dev")`):**
  - Teacher: `lan.teacher@mathvision.local` / `MathVision123!`
  - Admin: `admin.demo@mathvision.local` / `MathVision123!`
  - 10 Synthetic Students: `minh.student@mathvision.local`, etc.
  - Dev seed runs idempotently on local startup and is never active in production profiles.
- **Production Provisioning:**
  - Public `/register` self-signup is strictly disabled.
  - All accounts must be explicitly provisioned by an authenticated Administrator via `POST /api/v1/admin/users`.

---

## 6. Classroom Roster Single Source of Truth
Classroom student rosters are stored in the canonical `classroom_students` join table mapped to `Classroom.students`. When an administrator adds or removes a student via `/api/v1/admin/classes/{classId}/students/{studentId}`, this updates the exact same relationship that the Teacher batch workflow inspects during image-to-student verification in `BatchService.uploadImages`. No duplicate roster tables exist.
