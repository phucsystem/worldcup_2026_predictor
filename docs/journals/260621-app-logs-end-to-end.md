# End-to-End App Logs (Line-Level Logging Across All Processes)

**Date:** 2026-06-21
**Branch:** `feat/app-logs`
**Plan:** `ck_plans/260621-0343-logs-app-logs-end-to-end/` · **Phases:** data → core → api → ui

## What shipped

Backend and frontend now have persistent, queryable line-level logging. Every process (API, collector, scheduler, live poller) writes `INFO`/`WARNING`/`ERROR` events into a new `app_logs` Postgres table via a centralized, non-blocking logging config. A read-only `/logs` console surfaces them in the frontend with filtering, search, and pagination.

- **Data (P1):** Migration `0006_app_logs.py` creates `app_logs` table: `id BIGINT`, `ts TIMESTAMP WITH TIME ZONE (DESC index)`, `level` (indexed), `source`, `message`, `context JSONB`, `run_id`. Repository helpers: `insert_log_rows()` (batch insert, 50-row chunks), `query_logs()` (level/free-text search via ILIKE/source filters, newest-first), `prune_logs()` (age cutoff). Helpers are logging-free to prevent recursion.
- **Core (P2):** New `app/logging_config.py` with single `configure_logging()` entry point. Architecture: root logger enqueues via `_RawQueueHandler` (preserves exc_info for tracebacks), background `QueueListener` runs console + `DBLogHandler` off-thread. `DBLogHandler` buffers (BATCH_SIZE=50 / 2s timer), flushes on its own session, swallows all errors to stderr. Safety invariants: non-blocking (never waits on DB write), never crashes (all DBLogHandler errors → stderr only), no feedback loop (SQLAlchemy/psycopg excluded via `_DBExclusionFilter`), no lost records (atexit + explicit stop in CLI finally + SIGTERM handler). Wired into all 5 entrypoints (`main.py`, `pipeline/run.py`, `pipeline/scheduler_entry.py`, `data/collect.py`, `pipeline/live_poller.py`). Daily prune at `run_pipeline` start. Config: `LOG_RETENTION_DAYS=14`, `LOG_DB_ENABLED`. FastAPI unhandled-exception handler logs with traceback.
- **API (P3):** New `app/api/logs.py` — `GET /api/logs?level=&q=&source=&limit=&offset=` returns `{items, total, limit, offset}`. Chip-to-levelname mapping (error includes CRITICAL). Limit clamped 1–200. Mounted in `main.py`.
- **UI (P4):** Unlinked `/logs` console — `app/logs/page.tsx` server shell + `components/logs-view.tsx` client island (level filter, 300ms-debounced search, 50/page pagination, expandable context/traceback rows, Live poll toggle). Same-origin proxy `app/api/logs/route.ts`; `lib/api.ts` `getLogs()`. Log console CSS appended to `globals.css`. Intentionally NOT added to `nav-links.tsx`. API_BASE never reaches browser (verified: absent from client chunks).

## Decisions

- **Root=INFO, console floor=DEBUG:** A logger set to DEBUG reaches stdout but never the DB — the "DEBUG to stdout only" guarantee without chatty prod logs.
- **`_RawQueueHandler` override:** Default `QueueHandler.prepare()` clears exc_info; overrode it so the off-thread DB handler can still capture tracebacks.
- **Unlinked, not hidden:** `/logs` is reachable by direct URL but omitted from nav; intentional for observability without UI sprawl.

## Code review findings (DONE_WITH_CONCERNS)

Two real fixes applied post-review:

- **H2 (real): SIGTERM loses final buffer.** `atexit` doesn't fire on SIGTERM (how `docker stop` halts long-lived processes), losing the final buffered batch. Fixed: FastAPI lifespan shutdown calls `stop_logging()`; `live_poller` installs a SIGTERM handler that flushes + exits. Verified: buffered row survives SIGTERM.
- **M1 (real): Proxy silent failures.** Backend DB outage → proxy silent 200 + empty array → console error state dead. Fixed: `getLogs()` now throws on upstream failure; proxy returns 502 so client error UI engages.

## Verification

- Migration up/down round-trip verified.
- Repository helpers (batch insert, level/text/source filters, newest-first, prune cutoff).
- Logging smoke: `INFO`/`WARN`/`ERROR` persist, `DEBUG` stdout-only, SQLAlchemy excluded, tracebacks captured, `run_id` populated.
- Fault-injection: DB outage neither crashes nor blocks app.
- SIGTERM flush verified empirically.
- `/api/logs` filters + limit clamp.
- Frontend build clean, no `API_BASE` leak, `/logs` renders newest-first, expand/collapse works, absent from nav.
- Backend: 97 tests passed.

## Gotcha / follow-up

- **Log volume in prod:** `INFO` floor means feature/debug logs in lower environments must set explicit log levels per logger, or they'll pollute prod DB at scale. Consider adding a `LOG_LEVEL_OVERRIDES` config dict if production chatiness emerges.
