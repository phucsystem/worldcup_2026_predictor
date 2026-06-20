---
title: "End-to-end app_logs (line-level logging across backend, collector, pipeline, scheduler, frontend)"
description: "Persist line-level INFO/WARN/ERROR events to a new app_logs table via a centralized, non-blocking logging config wired into every process; expose GET /api/logs; surface an unlinked /logs console in the frontend."
status: completed
priority: P2
branch: "feat/app-logs"
tags: [logging, observability, backend, frontend]
blockedBy: []
blocks: []
source: skill
---

# End-to-end app_logs (line-level logging across backend, collector, pipeline, scheduler, frontend)

## Overview

Today the backend logs only to stdout, and only in three batch modules; the web layer logs nothing and nothing is persisted or queryable. This plan persists line-level log events (`INFO`/`WARNING`/`ERROR`) from **every** process into a new `app_logs` Postgres table through a single centralized logging config, exposes them via `GET /api/logs`, and renders the prototype's log console at `/logs` (reachable but **not** in the nav).

Source brainstorm: `ck_plans/reports/brainstorm-260621-logs-end-to-end.md`. Reference UI: `prototypes/s09-logs.html` (+ its CSS in `prototypes/components.css`, JS in `prototypes/interactions.js`).

**Non-negotiable safety invariants** (carry through every phase):
- Logging is **non-blocking** — the request/app path never waits on a DB write (`QueueHandler` → background `QueueListener` → batched `DBLogHandler`).
- Logging **never crashes the app** — the DB handler swallows its own errors to stderr via `handleError`, never raising into caller code.
- **No feedback loop** — SQLAlchemy/psycopg loggers are quieted and excluded from the DB handler, so writing a log row cannot itself emit a logged row.
- **No lost records** — short-lived processes flush + join the listener on exit (`atexit`/`finally`).
- **Bounded volume** — DB persistence floor is `INFO` (DEBUG → stdout only); time-based retention prunes old rows.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Data](./phase-01-data.md) | Complete |
| 2 | [Core](./phase-02-core.md) | Complete |
| 3 | [API](./phase-03-api.md) | Complete |
| 4 | [UI](./phase-04-ui.md) | Complete |

Execution order: **Data → Core → API → UI** (per project convention). Phase 2 depends on Phase 1's table/helpers; Phase 3 on Phase 1's query helper; Phase 4 on Phase 3's endpoint.

## Decisions (locked, from brainstorm)

- Data source: **new `app_logs` line-level table** (not `agent_runs`).
- Access: **public but unlinked** — `/logs` reachable, NOT added to `nav-links.tsx`.
- Backend scope: **full centralization** — one `configure_logging()` wired into all entrypoints + FastAPI web-layer logging.
- Frontend fetch: **client island + same-origin proxy** (mirrors `app/api/live/route.ts`) — server-side pagination/filter.

## Entrypoints to wire (`configure_logging()`)

`app/main.py` (API startup), `app/pipeline/run.py`, `app/pipeline/scheduler_entry.py`, `app/data/collect.py`, `app/pipeline/live_poller.py`. Dev seed scripts (`seed_live_match.py`, `seed_openfootball.py`) are optional/low-priority.

Prune hook target: start of `run_pipeline()` (daily cadence — sufficient for a 14-day window; avoids coupling to the poller loop cadence).

## Acceptance criteria (whole plan)

1. A real `INFO`/`WARNING`/`ERROR` from any wired process lands in `app_logs` within seconds.
2. `/logs` lists newest-first with working level filter, free-text search, 50/page pagination, and expandable traceback/context rows.
3. Logging failures never crash or block the app (verified by fault-injection test).
4. Rows older than `LOG_RETENTION_DAYS` are pruned.
5. `/logs` is reachable directly but absent from the top nav; `API_BASE` never reaches the browser.

## Out of scope

Log aggregation/alerting, auth UI, `pg_trgm` search, structured JSON export, multi-tenant, real-time push/websockets (the prototype "Live" toggle stays a client-side poll/no-op).

## Dependencies

No cross-plan blockers. `260621-azure-vm-deploy` (deploy) and `260621-0327-home-inprogress-live` (home page) touch different files; `globals.css` is shared with the home-page plan but in non-overlapping sections (append the log-console block).
