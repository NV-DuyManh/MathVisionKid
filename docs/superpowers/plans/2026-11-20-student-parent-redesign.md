# Student Profile and Parent Mode Implementation Plan

> **For agentic workers:** Use Superpowers subagent-driven-development for implementation and independent review. No commits.

**Goal:** Make Student Profile easier to navigate and Parent Mode equally useful for learning support and safe use.
**Architecture:** Expand existing shared Student React Native screens and preserve backend and API boundaries.
**Tech Stack:** Expo Router, React Native Web, Jest, Playwright, Chrome DevTools.
**Spec:** docs/superpowers/specs/2026-11-20-student-parent-redesign-design.md

## Constraints

Keep existing branch/workspace, auth rules, backend limits, and source-backed metrics. Test fixtures only in test contexts. No commit, push, merge, deploy.

## Tasks

- [x] Profile entry and settings. Edit profile.tsx, ProfileWeb.tsx and AccountScreen.tsx. Add a named parent action near identity on wide and compact/native, retain settings entry and existing progress on Của em. Remove redundant desktop settings metrics. Verify via settings and profile navigation.
- [x] Parent workspace. Edit ParentModePreview.tsx and new adjacent components if helpful. Converge PIN, dual-purpose overview, activity empty/error and limit editor. Verify duration intervals, save acknowledgement, PIN errors, keyboard and compact layout.
- [x] Rest and connection states. Edit StudentDailyLimit.tsx and games/[gameId].tsx. Preserve mounted work and enforcement. Show a centered popup over a translucent dimmed backdrop, isolate background interaction and focus, and make connection recovery distinct. Add regression tests where needed and check account/session isolation.
- [x] Review and verify. Run typecheck and relevant tests. Review each domain independently. Capture desktop and compact web states via MCP using real dev data and labeled fixtures. Verify native runtime when device/emulator available and record actual limits. Device/emulator unavailable in this pass; native bundles and renderer checks passed.

## Review focus

Mobile keyboard, backend error on save, missing data versus real zero, previously verified time exhaustion while offline, and unsaved task state behind the rest overlay.


