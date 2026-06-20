---
phase: 4
title: "UI"
status: completed
priority: P2
dependencies: [3]
---

# Phase 4: UI — `/logs` console (client island + same-origin proxy), unlinked

## Overview

Port `prototypes/s09-logs.html` into the production Next.js app as `/logs`: a server shell + a client island that fetches a same-origin proxy (so `API_BASE` stays server-side), with level filter, debounced search, 50/page pagination, and expandable context rows. **Not** added to the nav.

## Requirements

- Functional: parity with the prototype's interactions (filter, search, pagination 50/page, expand traceback/context, Live toggle as client-side no-op/poll), backed by real `/api/logs` data.
- Non-functional: `API_BASE` never reaches the browser; no horizontal scroll; reduced-motion respected; reachable at `/logs` but absent from `nav-links.tsx`.

## Architecture

- **Proxy** `app/api/logs/route.ts` — mirrors `app/api/live/route.ts`: `export const dynamic = "force-dynamic"`; `GET` reads `request.nextUrl.searchParams`, calls `getLogs(params)` from `lib/api.ts`, returns `Response.json(page, { headers: { "Cache-Control": "no-store" } })`.
- **lib/api.ts** — add `LogEvent`/`LogPage` types (match Phase 3 models) + `getLogs(params): Promise<LogPage>` fetching `${API_BASE}/api/logs?...` with `NO_STORE`, returning an empty page on failure (mirror existing graceful fallbacks).
- **Page** `app/logs/page.tsx` — server component shell (title/deck + the `<LogsView/>` island). `export const dynamic = "force-dynamic"`.
- **Client island** `components/logs-view.tsx` (`"use client"`) — owns level/search/page state; fetches `/api/logs?level=&q=&limit=50&offset=` (debounced search, ~300ms; resets to page 1 on filter/search change); renders the prototype table markup (level chips w/ SVG icons, mono source/time, expandable `context` rows), pagination footer, and empty/no-results states. Port the prototype's `interactions.js` logic into React state/handlers (no global script).
- **CSS** — append the log-console block from `prototypes/components.css` (`.log-toolbar`, `.log-search`, `.lvl`, `.log-time/.log-source`, `.log-detail`, `.log-pagination`, responsive rules) into `frontend/app/globals.css`, reusing existing design tokens. Do not touch unrelated `globals.css` sections (home-page plan also edits this file).

## Related Code Files

- Create: `frontend/app/logs/page.tsx`, `frontend/components/logs-view.tsx`, `frontend/app/api/logs/route.ts`.
- Modify: `frontend/lib/api.ts` (types + `getLogs`), `frontend/app/globals.css` (append console styles).
- **Do NOT modify**: `frontend/components/nav-links.tsx` (intentionally unlinked).

## Implementation Steps

1. Add `LogEvent`/`LogPage` + `getLogs()` to `lib/api.ts`.
2. Add proxy route `app/api/logs/route.ts` (copy `/api/live` shape, forward query params).
3. Build `logs-view.tsx`: state (level, q, page), debounced fetch of the proxy, table render + expand + pagination; empty/error/no-results states.
4. Add `app/logs/page.tsx` shell rendering the island.
5. Append console CSS to `globals.css`.
6. Verify in-browser: `/logs` loads real rows newest-first; filter/search/pagination work; expanding a row shows `context` (traceback); `/logs` not present in nav; build/SSR has no `API_BASE` leak to client.

## Success Criteria

- [x] `/logs` renders real `/api/logs` data, newest-first, 50/page.
- [x] Level filter, debounced search, pagination, and row expand all work and compose (filter resets to page 1).
- [x] `API_BASE` never appears in client bundle/network (only same-origin `/api/logs` calls from the browser).
- [x] `/logs` reachable directly; absent from top nav.
- [x] No horizontal page scroll; reduced-motion respected; matches prototype visuals.

## Risk Assessment

- Porting `interactions.js` to React could drift from prototype behavior → use the prototype as the reference contract; verify each interaction in-browser.
- Shared `globals.css` edits with the home-page plan → append a clearly-scoped block; avoid touching existing selectors.
- Large pages over the proxy → server-side pagination already bounds payloads (Phase 3 clamps `limit`).
