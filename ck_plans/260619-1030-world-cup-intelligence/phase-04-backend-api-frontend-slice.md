---
phase: 4
title: "Backend API & Frontend Slice"
status: done
priority: P1
effort: "2d"
dependencies: [3]
---

# Phase 4: Backend API & Frontend Slice

## Overview
Expose the brief via a FastAPI read API and render it on a minimal Next.js SSR site — completing the vertical slice (data → brief → visible on web).

## Requirements
- Functional: visiting the site shows the latest brief and a standings view; deep-link to a brief by date works.
- Non-functional: SSR (fresh per request), read-only API, no auth (public).

## Architecture
- FastAPI read endpoints (no writes from web):
  - `GET /api/briefs` → list (date, title, summary) of **published (successful) briefs only**; failed/partial runs are never surfaced. <!-- Updated: Validation Session 1 - keep last good brief on failure -->
  - `GET /api/briefs/{date}` → full article (body_md).
  - `GET /api/briefs/latest` → most recent published brief (home page uses this; stays on last good brief if today's run failed).
  - `GET /api/standings?date=` → standings snapshot (grouped).
- Next.js App Router (SSR):
  - `/` → list of briefs (server component fetches `/api/briefs`).
  - `/brief/[date]` → render `body_md` to HTML (e.g. `react-markdown`).
  - Standings table component.
- Markdown rendering sanitized. Tailwind base styling (polish deferred to Phase 6).
- Frontend reads API base URL from env (`NEXT_PUBLIC_API_BASE` / server-side var).

## Related Code Files
- Create: `backend/app/api/briefs.py`, `backend/app/api/standings.py`, `frontend/app/page.tsx`, `frontend/app/brief/[date]/page.tsx`, `frontend/components/standings-table.tsx`, `frontend/lib/api.ts`
- Modify: `backend/app/main.py` (mount routers), `frontend/app/layout.tsx`

## Implementation Steps
1. FastAPI routers for briefs + standings; Pydantic response models; mount in `main.py`.
2. `frontend/lib/api.ts`: typed fetch helpers (server-side).
3. `/` page: server component lists briefs.
4. `/brief/[date]` page: fetch + render markdown (sanitized).
5. `standings-table.tsx`: render grouped standings with position deltas.
6. Wire docker-compose so frontend can reach backend locally.

## Success Criteria
- [ ] `/` lists generated brief(s); clicking opens full article.
- [ ] `/brief/{date}` renders the markdown brief correctly.
- [ ] Standings view shows groups with points/GD/position deltas.
- [ ] API endpoints return correct JSON; no write paths exposed.

## Risk Assessment
- Markdown XSS → sanitize on render. Low (content is LLM-generated, still sanitize).
- SSR fetch of internal API in containers → use service DNS locally, env-driven base URL. Low.
