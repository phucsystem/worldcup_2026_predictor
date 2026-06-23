---
phase: 2
title: "Feedback capture + storage"
status: pending
priority: P1
dependencies: []
effort: "M"
---

# Phase 2: Feedback capture + storage

## Overview
The public-facing supporter-bot widget (scripted chat, no LLM, moose/jaguar/eagle) mounted globally, plus the storage path: a `feedback` table, a backend create+list API, and a Next route handler the widget POSTs to. Independent of Phase 1 (can land in parallel); the admin *view* of this data is Phase 3.

## Requirements
- Functional: widget appears bottom-right on every page; launcher → greeting → topic chip (bug/feature/other) → bot follow-up → free-text → submit. Submit POSTs `{ message, topic, page }` to a same-origin route handler → backend insert → celebratory thank-you. Page URL is captured client-side (`window.location.pathname`) and sent in the body.
- Non-functional: no LLM, no account; respects `prefers-reduced-motion`; message length cap (e.g. 1–2000 chars) enforced server-side; basic rate limit; no PII solicited.

## Architecture
- **DB (data):** Alembic migration `0009_feedback` adding `feedback` table: `id` (pk), `created_at` (tz, default now), `message` (text, not null), `topic` (varchar: 'bug'|'feature'|'other'|null), `page` (varchar null), `status` (varchar default 'new': 'new'|'done'|'wont'), `resolved_at` (tz null). Index on `(status, created_at desc)`. Define `feedback_table` in `repository.py` on the shared `_metadata`, mirroring `app_logs_table`. Add repo helpers `insert_feedback(...)`, `list_feedback(status=None, limit, offset)`, `set_feedback_status(id, status)` (Phase 3 uses the latter two).
- **Backend API (core):** new `backend/app/api/feedback.py` router `prefix="/api/feedback"`: `POST ""` (validate length/topic, insert, return `{id}`) and `GET ""` (list, newest-first, optional `?status=`). Pydantic `FeedbackIn`/`FeedbackOut`. Register in `main.py`. **Leave CORS GET-only** — POST is server-to-server from the Next route handler, not browser-direct.
- **Next proxy (core):** `frontend/app/api/feedback/route.ts` — `POST` validates/trims, forwards to `${API_BASE}/api/feedback` server-side, returns `{ ok }`. Add `submitFeedback()` (and later `listFeedback`) to `frontend/lib/api.ts` (it currently only does GET — add a small POST helper).
- **Widget (ui):** `frontend/components/feedback-widget.tsx` (client island) porting `s12` markup + the scripted-chat logic from `prototypes/interactions.js` (launcher/open-close, prompt→follow-up, compose, submit→thank-you+confetti). Mascot SVGs as a tiny `frontend/components/mascot.tsx` (`<Mascot kind="moose|jaguar|eagle" />`). **Public pages only — exclude `/admin/*`:** mount in the root `app/layout.tsx` but the widget reads `usePathname()` and renders `null` when the path starts with `/admin` (avoids a separate route-group layout; the admin doesn't feed back to themselves). Port `.fb-*`, `.mascot-av`, confetti, and `prefers-reduced-motion` rules from `prototypes/components.css` into `globals.css`.

## Related Code Files
- Create: `backend/db/migrations/versions/0009_feedback.py`, `backend/app/api/feedback.py`, `frontend/app/api/feedback/route.ts`, `frontend/components/feedback-widget.tsx`, `frontend/components/mascot.tsx`
- Modify: `backend/app/data/repository.py` (`feedback_table` + helpers), `backend/app/main.py` (register router), `frontend/lib/api.ts` (`submitFeedback` POST helper + `Feedback` types), `frontend/app/layout.tsx` (mount widget), `frontend/app/globals.css` (port widget CSS)
- Reference: `prototypes/s12-supporter-feedback.html`, `prototypes/interactions.js` (mascot SVGs + scripted flow), `prototypes/components.css`

## Implementation Steps
1. Write migration `0009_feedback` (follow `0006_app_logs` / `0008_*` structure); define `feedback_table` + helpers in `repository.py`.
2. Add `feedback.py` router (POST insert + GET list) with Pydantic models + server-side length/topic validation; register in `main.py`. Keep CORS GET-only.
3. Add `frontend/app/api/feedback/route.ts` POST proxy + `submitFeedback()` in `lib/api.ts`.
4. Build `mascot.tsx` (port the three SVGs) and `feedback-widget.tsx` (port `s12` + scripted flow), mount in `app/layout.tsx`; port widget CSS to `globals.css`.
5. Tests: backend unit tests for insert/list + validation (mirror `test_recent_results.py` style); a small frontend test for the widget's topic→compose→submit state machine if practical.

## Success Criteria
- [ ] `POST /api/feedback` (via Next proxy) inserts a row with message, topic, page, status='new', created_at; over-length/empty rejected server-side.
- [ ] Widget mounts on every page, runs the full scripted flow, and shows the thank-you state after submit; reduced-motion disables animation.
- [ ] No CORS changes; backend `POST /api/feedback` only reachable server-side (browser uses the Next proxy).
- [ ] Backend tests pass; lint + `tsc` clean.

## Risk Assessment
- **Spam/abuse on a public POST:** v1 decision (validation) — server-side length cap + topic whitelist + trim/normalise only; **per-IP rate limit deferred** (accept-and-monitor given low traffic). Revisit if abuse appears; note IP handling behind Caddy needs `X-Forwarded-For` care when added.
- **Hydration/SSR for a global client island:** Mitigation: widget is `"use client"`, mounted in the layout; render nothing until interactive (no SSR-only state) to avoid mismatch.
- **Migration drift:** Mitigation: run `alembic upgrade head` in the dev DB and confirm `0009` applies cleanly on top of `0008`.
