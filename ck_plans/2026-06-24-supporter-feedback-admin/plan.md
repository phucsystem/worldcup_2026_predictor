---
title: "Supporter Feedback Bot + Admin Section"
description: ""
status: pending
priority: P2
branch: "feat/forecast-accuracy-rate"
tags: []
blockedBy: []
blocks: []
created: "2026-06-23T22:51:13.626Z"
createdBy: "ck:plan"
source: skill
---

# Supporter Feedback Bot + Admin Section

## Overview

Add a public **supporter-bot feedback widget** (scripted chat, no LLM, themed with original moose/jaguar/eagle host-nation characters) and a **single-admin section** to triage that feedback and view system logs. Design locked in [`brainstorm-report.md`](./brainstorm-report.md); UI matches prototypes `s12`/`s13`/`s14`.

Build order is dependency-driven: the auth shell (Phase 1) must exist before admin management (Phase 3); feedback capture (Phase 2) is independent of auth and can land alongside Phase 1.

## Architecture (non-negotiable constraints)

- **Backend is not publicly exposed.** Caddy reverse-proxies only `frontend:3000`. The browser reaches the backend solely via Next.js route handlers (`frontend/app/api/*/route.ts`) or server components. Backend CORS is GET-only.
- **All writes go through Next route handlers** (server-side), which call the backend with `API_BASE`. No browser→backend writes; no CORS changes.
- **Auth is Next.js-owned.** Password compared server-side against env `ADMIN_PASSWORD`; signed HttpOnly session cookie; `middleware.ts` gates `/admin/*` and the admin route handlers. The backend stays auth-free (protected by network isolation) — documented as a known posture.
- **Secrets are env-only** (`ADMIN_PASSWORD`, `SESSION_SECRET`), set in the VM `.env`, never committed (repo is public).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Admin auth shell](./phase-01-admin-auth-shell.md) | Pending |
| 2 | [Feedback capture + storage](./phase-02-feedback-capture-storage.md) | Pending |
| 3 | [Admin management + logs relocation](./phase-03-admin-management-logs-relocation.md) | Pending |

Within-phase order follows the repo convention: **data → core → ui**.

## Success criteria (whole feature)

- Visitor sends feedback in ≤3 taps; entry persists with message + page context + timestamp.
- Admin signs in with the env password; session persists across reloads; logout clears it; `/admin/*` and admin APIs 401/redirect without a valid session.
- Admin flips each feedback item new ↔ done ↔ won't-do; counts/filters update.
- `/logs` is no longer publicly reachable; logs are viewable only inside authenticated `/admin`.
- Changelog updated; CI green (changelog gate, validate app, E2E).

## Dependencies

- **Satisfied prerequisite:** [`260621-0343-logs-app-logs-end-to-end`](../260621-0343-logs-app-logs-end-to-end/plan.md) (status: completed) — provides the `app_logs` table, `/api/logs` backend endpoint, and `LogsView`. Phase 3 relocates that surface; no active blocking relationship.

## Validation Log

### Session 1 — 2026-06-24

**Verification Results (Standard tier, 3 phases):**
- Claims checked: 6 load-bearing · Verified: 5 · Failed: 1 · Unverified: 0
- `frontend/middleware.ts` absent (clean to create) ✓ · Next 16.2.9 ✓ · Alembic `0006` template → `0009`/down `0008` format ✓ · no public `/logs` link beyond a CSS comment ✓ · `lib/api.ts` GET-only (POST helper to be added) ✓
- **FAILED → corrected:** Phase 1 specified `middleware.ts` + Edge-runtime crypto. Bundled Next 16 docs (`version-16.md`) confirm the `middleware` convention is **deprecated, renamed to `proxy`**, and `proxy` is **Node-runtime only (Edge unsupported)**. Phase 1 rewritten to use `proxy.ts` + `node:crypto`.

**Decisions confirmed:**
1. **Session impl:** Node-runtime middleware → Next 16 `proxy.ts` with `node:crypto` HMAC (no dependency, no Web Crypto). [Phase 1]
2. **Feedback spam guard (v1):** length cap + topic whitelist + trim only; per-IP rate limit **deferred** (accept-and-monitor). [Phase 2]
3. **Old `/logs`:** **hard 404** — delete `frontend/app/logs/page.tsx`, no redirect. [Phase 3]
4. **Widget surface:** public pages only — render `null` under `/admin/*` via `usePathname()`. [Phase 2]

### Whole-Plan Consistency Sweep
- Re-read `plan.md` + all 3 phase files. `proxy.ts` (not `middleware.ts`) consistent across Phase 1; `requireAdmin` helper referenced consistently in Phase 1 (defined) and Phase 3 (consumed); `/logs` 404 decision consistent in Phase 3 prose/files/steps/criteria; widget `/admin` exclusion consistent in Phase 2. No stale terms or contradictions remaining.
- **Result:** 0 unresolved contradictions → eligible for implementation.
