---
phase: 3
title: "Admin management + logs relocation"
status: pending
priority: P2
dependencies: [1, 2]
effort: "M"
---

# Phase 3: Admin management + logs relocation

## Overview
The authenticated admin surface (`s14`): a Feedback tab to list and triage feedback (new → done / won't-do, with counts + filters) and a Logs tab that relocates the existing logs console into `/admin`. Depends on Phase 1 (auth gate) and Phase 2 (feedback data + list API).

## Requirements
- Functional: `/admin` shows tabs Feedback | Logs. Feedback: live counts (new/done/won't-do), status filter, per-item Mark done / Won't do / Reopen — each persists via a status-update API. Logs: the current `LogsView` rendered inside the admin shell. `/logs` is removed (redirect to `/admin/logs` or 404) and the route handler `/api/logs` requires the admin session.
- Non-functional: all status writes server-side through an authenticated route handler; admin data fetched server-side (API_BASE never in browser).

## Architecture
- **Status update API (core):** `backend/app/api/feedback.py` gains `PATCH /api/feedback/{id}` (or `POST /{id}/status`) → `set_feedback_status(id, status)`; sets `resolved_at` when status≠'new', clears it on reopen. Validate status in {'new','done','wont'}.
- **Next proxies (core):** `frontend/app/api/admin/feedback/route.ts` (`GET` list) and `.../[id]/route.ts` (`PATCH` status) — **both call `verifySessionToken` first and 401 if absent** (defence-in-depth on top of middleware). Add `listFeedback()` + `updateFeedbackStatus()` to `lib/api.ts`.
- **Feedback admin UI (ui):** `app/admin/page.tsx` (server component) fetches feedback server-side and renders the `s14` Feedback tab; a client island `components/admin-feedback.tsx` owns tab switching, filter, optimistic status flips calling the PATCH proxy, recount, empty-state, and a success toast. **UX (reworked `s14`):** counts and filter are merged into one clickable filter bar (`.fb-filterbar`/`.fb-fstat` with `aria-pressed`, count = filter — no separate stat cards); each card has a clear reading order (topic chip + page + time in `.fb-it-head`, prominent `.fb-it-text`, right-aligned `.fb-it-actions` footer) and a status-colored left border; no per-item mascot (topic chip carries meaning instead). Port `.fb-filterbar`, `.fb-fstat`, `.fb-item`, `.fb-it-head`, `.fb-topic`, `.fb-status`, `.fb-it-actions`, `.fb-empty`, `.fb-toast`, `.admin-tabs` CSS into `globals.css`.
- **Logs relocation (ui):** move the logs UI under `app/admin/logs/page.tsx` (or render `LogsView` inside the admin Logs tab). Update `frontend/app/api/logs/route.ts` to require the session (`requireAdmin`). **Remove `/logs` entirely (hard 404)** — delete `frontend/app/logs/page.tsx` so the route returns Next's 404 (validation decision; no redirect). `nav-links.tsx` already omits `/logs`; verify no other public link points at `/logs` (only a CSS comment references it — harmless).

## Related Code Files
- Create: `frontend/app/admin/page.tsx`, `frontend/components/admin-feedback.tsx`, `frontend/app/api/admin/feedback/route.ts`, `frontend/app/api/admin/feedback/[id]/route.ts`, (optional) `frontend/app/admin/logs/page.tsx`
- Modify: `backend/app/api/feedback.py` (PATCH status), `backend/app/data/repository.py` (`set_feedback_status` if not added in P2), `frontend/lib/api.ts` (list + update helpers), `frontend/app/api/logs/route.ts` (require session), `frontend/components/logs-view.tsx` (reuse as-is in admin)
- Delete: `frontend/app/logs/page.tsx` (hard 404 — no redirect)
- Reference: `prototypes/s14-admin-feedback.html`, `prototypes/interactions.js` (admin triage logic)

## Implementation Steps
1. Add backend status-update endpoint + repo helper; unit-test status transitions and `resolved_at` handling.
2. Add authenticated Next proxies for list + status update (session-checked); add `lib/api.ts` helpers.
3. Build `app/admin/page.tsx` + `admin-feedback.tsx` from `s14`; port CSS; wire counts/filter/triage to the PATCH proxy.
4. Relocate logs: render `LogsView` under `/admin`; gate `/api/logs` on the session (`requireAdmin`); delete `frontend/app/logs/page.tsx` (hard 404); confirm no public link references `/logs`.
5. Update `frontend/public/CHANGELOG.md` (new version, user-facing wording) — required by the CI changelog gate.

## Success Criteria
- [ ] Admin can mark feedback done / won't-do / reopen; change persists (reload reflects it); counts + filter update.
- [ ] Status-update and list APIs 401 without a valid session (test by calling the route handler cookie-less).
- [ ] `/logs` no longer publicly reachable; logs visible only inside authenticated `/admin`; `/api/logs` requires session.
- [ ] Backend tests pass; lint + `tsc` clean; CHANGELOG updated; CI green.

## Risk Assessment
- **Logs exposure regression:** if `/api/logs` isn't session-gated after the move, logs stay public. Mitigation: explicit cookie-less test in success criteria.
- **Auth-check duplication drift:** middleware + per-route checks could diverge. Mitigation: single shared `requireAdmin(request)` helper in `lib/admin-auth.ts` used by all admin route handlers.
- **Optimistic UI desync:** a failed PATCH could leave the pill out of sync. Mitigation: revert on non-2xx and surface a small error.
