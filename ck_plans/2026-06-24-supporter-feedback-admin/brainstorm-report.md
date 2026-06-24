# Brainstorm — Supporter Feedback Bot + Admin Section

Date: 2026-06-24 · Mode: brainstorm (prototype-first) · Status: design locked, prototypes built

## Problem
Collect actionable feedback from platform users, and give the single maintainer a private place to triage that feedback and inspect system logs (currently public).

## Scope (one cohesive feature, 3 build-order phases)
1. **Auth/admin shell** — everything sits behind it.
2. **Public feedback capture** — supporter-bot widget + storage.
3. **Admin management** — feedback triage + relocate logs into admin.

## Locked decisions
- **Capture UX:** scripted chat widget (NO LLM). Rejected full LLM chatbot (token cost, latency, abuse/prompt-injection surface, moderation) — a scripted chat collects the same signal at zero marginal cost.
- **Theme:** three ORIGINAL host-nation supporter characters — moose (CAN), jaguar (MEX), eagle (USA). Deliberately NOT FIFA's trademarked 2026 mascots (Maple/Zayu/Clutch) — IP-safe for a public site. Light animation (idle bob, panel slide-in, confetti on submit), gated by `prefers-reduced-motion`.
- **Auth:** Next.js-owned single-admin session. Password compared server-side against env `ADMIN_PASSWORD` (value set only in the VM `.env`, never committed). Signed HttpOnly session cookie ("remembered on device"). Next middleware gates `/admin/*`. No user-accounts model (YAGNI).
- **Feedback model:** message + auto-captured page context + timestamp. Statuses: `new → done | wont`. Optional rating/email/admin-note were offered and deferred (kept minimal).
- **Logs:** move `/logs` → `/admin/logs`; drop from public nav.

## Architecture constraints (from scout)
- Backend (`backend:8000`) is NOT publicly exposed — Caddy only reverse-proxies `frontend:3000`. Browser reaches backend data only via Next.js route handlers (`frontend/app/api/*/route.ts`) or server components.
- CORS is GET-only → all writes (feedback POST, status update) go through Next route handlers server-side; no browser→backend writes.
- Existing `backend/app/api/admin.py` is dev-only/no-auth (collect / run-brief triggers); can later move behind the same session.
- DB uses Alembic; latest migration `0008_match_forecast` → feedback table = `0009`.
- Existing logs: `backend/app/api/logs.py` (GET), `frontend/app/logs/` + `components/logs-view.tsx`, nav in `components/nav-links.tsx`.

## Prototypes (built + verified in-browser)
- `prototypes/s12-supporter-feedback.html` — supporter-bot overlay (launcher → greeting → topic chips → bot follow-up → compose → thank-you + confetti).
- `prototypes/s13-admin-login.html` — single-admin login.
- `prototypes/s14-admin-feedback.html` — feedback triage (live counts, filters, done/won't-do/reopen) + Logs tab.
- Shared: mascot SVGs + widget/admin logic in `prototypes/interactions.js`; styles appended to `prototypes/components.css`.

## Implementation considerations & risks
- **Secret hygiene:** `ADMIN_PASSWORD` + `SESSION_SECRET` env-only; never in repo (repo is public). Constant-time compare.
- **Session:** signed HttpOnly, `SameSite=Lax`, reasonable expiry (e.g. 14–30d); clear on logout.
- **Feedback abuse:** public POST → add lightweight rate-limit / length cap / basic sanitisation server-side.
- **Logs gating:** the backend `/api/logs` is only reachable via Next today; ensure the Next `/api/logs` route handler + page require the admin session after the move.
- **Auth on backend admin endpoints:** acceptable to rely on network isolation now; document that exposing the backend later requires real auth on it.

## Success criteria
- A visitor can send feedback in ≤3 taps; entry persists with page context + timestamp.
- Admin logs in with the env password; session persists across reloads; logout clears it.
- Admin can flip each feedback item new ↔ done ↔ won't-do; counts/filters reflect it.
- `/logs` no longer publicly reachable; logs viewable only inside authenticated `/admin`.

## Next step
Hand to `/ck:plan` — phased plan grounded in `@prototypes/s12-…`, `s13-…`, `s14-…` and `@ck_docs/` conventions.
