# Phase 2 finalization evidence — 14/11/2026

Status remains in progress. These receipts describe executed checks, not final acceptance.

Latest verification adds Teacher B creating a fresh draft after Admin handover. The publish-confirmation dialog rendered the current roster count11 and the snapshot-time explanation. Publication was canceled to retain a draft for acceptance. At390px the teacher page did not overflow. Student error recovery on the re-exported web was exercised with Tab to focus the back button and Enter to return to the empty list. Latest Student lint exits0 with one existing QuizInvitation warning. The focused deferred-response Jest harness has timed out, so it is not passing evidence yet.

- Backend Assignment controller tests passed 19/19 after draft replay metadata and recipient count fixes. A subsequent concurrency test exposed a stale managed Assignment loaded before the Classroom lock. Publish now reads only the scalar class ID first, then locks Classroom and loads Assignment for update.
- PostgreSQL concurrency passed 3/3 after this fix. Scenarios cover simultaneous publish, roster removal while publish waits, Admin handover while publish waits, ownership after handover, one snapshot and no Submission/Decision/AiJob creation.
- PostgreSQL upgrade passed 7/7 with no skips. Legacy Assignment, Batch and Submission links survive migration and schema backup/restore. See phase2-migration-compatibility.md for the tested combined-history proposal and the applied-history integration constraint.
- Teacher config/regression tests passed 49/49. Portal config/session tests passed 35/35. Student session/privacy contracts passed 15/15. Governance passed 16/16. Student typecheck succeeded before the pending request-lifecycle fixes. Teacher lint completed with four warnings in existing AuthContext/SubmissionImage files. Teacher build succeeded with the existing 924 kB chunk warning.
- Initial invocation of Teacher's nonexistent npm test script failed. The correct repository script npm run test:config --workspace=teacher-web subsequently passed 49/49.

## Browser acceptance

Executed using Playwright against Spring and PostgreSQL isolated schema phase2_browser_20261114. Teacher runs at localhost:5173. Acceptance Portal runs at localhost:5192, after 5182 could not bind. Binding Portal to all interfaces recovered MCP connectivity after loopback-only binds timed out.

Teacher created “Nghiệm thu Phase 2 – Cộng trong phạm vi 1000”, saved draft, opened editor, changed prompt from 256 + 127 to 256 + 128, saved, previewed correct prompt and instruction, then published. List showed 11 recipients and removed edit/publish controls for that item.

Student Minh logged in and read the published assignment and instructions. Reloading the full detail URL retained correct content. Student Minh logged out with confirmation, protected URL redirected to login, and Student An logged in on the same browser. An saw the shared class assignments. This confirms account switching, but shared assignment results alone cannot prove isolation for content exclusive to Minh.

Student Hà initially belonged to the same class and correctly read the published item. Teacher removed Hà using the roster control and confirmed the dialog. Hà reloaded the direct detail URL and received the unavailable/not-assigned state without the prompt. SQL then confirmed snapshot recipients remain 11 while current roster is 10. This is the removed-recipient scenario, not an independent never-assigned outsider scenario.

At 390×844 Student list scrollWidth equaled viewport width 390. Teacher list and draft dialog were checked at 390×844 without horizontal overflow. Desktop, keyboard, new-member, independent outsider and handover browser checks remain to be completed on the final code.

## Review

Further executed acceptance: a newly seeded Student C (phase2.c@acceptance.local) logged in on the same browser after Hà signed out, saw a genuinely empty assignment list and received HTTP404 from the direct published detail URL. Adding C to the roster using an isolated SQL fixture after publication did not grant access; the same detail remained HTTP404. This distinguishes current membership from the immutable recipient snapshot.

Admin logged in through Portal SSO and reassigned Lớp3A using the Admin Web “Thay đổi giáo viên” dialog. The old teacher subsequently received HTTP403 on the class API. New Teacher B logged in through Portal and saw the pre-existing published assignments in the class tab. Admin's first handoff attempt was blocked by CORS on the alternate test port5194. Restarting the verified acceptance backend with that origin recovered the flow.

Admin regression initially failed two logout tests due to sandbox loopback EACCES. The unchanged full test:config command reran outside the network-restricted sandbox and passed42/42. No Admin source changes were required. Assignment19 and Batch18 tests reran successfully after the concurrency fix. Teacher build succeeded before the subsequent confirmation-count presentation update, which still requires its final build check.

Fresh EGM implementation-readiness review found no verified P0/P1 local completion defect in inspected code. Two P2 findings concern stale Student request responses and old detail content after an ID change/error. Fix and regression verification are in progress. The reviewer inspected source and test definitions, without executing tests or browser flows.

## Skills Applied

- `mathvision-quality`
  - SKILL.md: C:/Users/LOC/.codex/worktrees/classroom-foundation/MathVisionKid/.agents/skills/mathvision-quality/SKILL.md
  - Why selected: Require current execution evidence and clear verification limits.
  - Applied to: Backend, PostgreSQL, web test and browser receipts.
- `mathvision-review`
  - SKILL.md: C:/Users/LOC/.codex/worktrees/classroom-foundation/MathVisionKid/.agents/skills/mathvision-review/SKILL.md
  - Why selected: Authorization, snapshot integrity and session review.
  - Applied to: EGM findings and acceptance gaps.
