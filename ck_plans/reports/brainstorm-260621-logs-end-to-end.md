# Brainstorm — End-to-end logs (app_logs) across backend, collector, pipeline, scheduler, frontend

- **Date**: 2026-06-21
- **Status**: Approved — ready for `/ck:plan`
- **Modes**: (none — no `--html` / `--wiki`)
- **Prototype**: `prototypes/s09-logs.html` (line-level console; reference UI)

## Problem statement

- **Users/context**: project operator wants visibility into the daily World Cup pipeline.
- **Struggle**: logs exist only as stdout in 3 batch modules; the web layer logs nothing; nothing is persisted or queryable. No in-app way to see INFO/WARN/ERROR events.
- **Cause**: `logging.basicConfig` scattered across `pipeline/run.py`, `pipeline/scheduler_entry.py`, `data/collect.py`; no central config, no persistence, no API, no UI.
- **Consequence**: debugging requires SSH/`docker logs`; no shareable in-product view; the prototype console has no real data behind it.
- **Success**: a real log event from any process appears in a queryable `/logs` page within seconds, with level filter, search, pagination, and expandable tracebacks.

### Problem-first note
User jumped from "logs page prototype" to "implement logs everywhere." Underlying problem = run-health/error visibility. `agent_runs` (run-level summaries) already covers much of that and was offered as the lower-effort path (Approach B). **User explicitly chose the line-level `app_logs` event stream (Approach A) + full centralization** — accepting the volume/retention cost for the richer breadcrumb-level view matching the prototype.

## Decisions (locked)

| Decision | Choice |
|----------|--------|
| Data source | **New `app_logs` line-level event table** (not `agent_runs`) |
| Access | **Public but unlinked** — reachable at `/logs`, NOT added to nav |
| Backend scope | **Full centralization** — central `dictConfig` + async DB handler wired into all 4 entrypoints + FastAPI web-layer logging |
| Frontend fetch | **Client island + same-origin proxy** (mirrors existing `/api/live`) — server-side pagination/filter |

## Approaches evaluated

- **A — `app_logs` event table + logging handler** ✅ chosen. Matches prototype exactly. Cost: per-line DB writes (mitigated by async batching), unbounded volume (mitigated by retention), new failure surface.
- **B — Surface existing `agent_runs` as run-history.** Least work, high signal/row, bounded volume; but not the line-level console. Rejected by user.
- **C — Hybrid (B now, A later).** Rejected — user wants line-level now.

## Recommended solution (as approved)

### Data flow
```
app.* loggers -> QueueHandler (non-blocking, per process)
                    -> QueueListener (bg thread, batched) -> DBLogHandler -> INSERT app_logs
console handler (stdout, always) for `docker logs`
Next /logs (client island) -> /api/logs proxy -> FastAPI GET /api/logs -> SELECT ... LIMIT/OFFSET
```
Four separate processes (API, scheduler, collect, pipeline-run) configure logging once and write to the same table; concurrent inserts are fine.

### 1. Schema — migration `0006_app_logs.py`
Columns: `id BIGSERIAL PK`, `ts TIMESTAMPTZ`, `level VARCHAR` (Python levelname), `source VARCHAR` (logger name), `message TEXT`, `context JSONB NULL` (traceback from `exc_info` + extras), `run_id VARCHAR NULL` (correlate to `agent_runs.run_id`).
Indexes: `(ts DESC)`, `(level)`. Search = `ILIKE` on message/source (pg_trgm is YAGNI).

### 2. Central logging — new `app/logging_config.py`
- `configure_logging()` builds `dictConfig`: console handler (stdout) + `QueueHandler` -> background `QueueListener` -> custom `DBLogHandler` with **batched** inserts (flush every N records / T seconds). App/request path never blocks.
- Safety invariants:
  - DB write off-thread; `DBLogHandler` swallows its own errors (`handleError` -> stderr), never raises into app code.
  - No feedback loop: SQLAlchemy/psycopg loggers quieted and excluded from the DB handler so insert-logging can't recurse.
  - DB persistence floor = INFO (DEBUG -> stdout only) to bound volume.
  - Short-lived processes (`collect`, `run`) flush + join the listener on exit (`atexit`/`finally`) so trailing records aren't lost.
- Replaces the three scattered `basicConfig` calls with one `configure_logging()` per entrypoint.
- FastAPI: call on startup; add exception handler + middleware logging unhandled errors (closes web-layer gap).
- Add `LOG_RETENTION_DAYS` (default 14) to `app/config.py`.

### 3. API — new `app/api/logs.py`
`GET /api/logs?level=&q=&source=&limit=50&offset=0` -> `{ items: LogEvent[], total, limit, offset }`. `level` maps chip->levelname (`error`->ERROR+CRITICAL, `warn`->WARNING, `info`->INFO). Mounted in `main.py`; follows existing router/Pydantic/Core pattern.

### 4. Frontend — `/logs` (reachable, NOT in `nav-links.tsx`)
- `app/logs/page.tsx` (shell) + client island `logs-view.tsx` fetching same-origin proxy `app/api/logs/route.ts` (mirrors `/api/live`) so `API_BASE` never reaches the browser. Debounced search, level toggle, 50/page pagination, expandable traceback rows from `context`.
- Port prototype log-console CSS into `globals.css`.

### 5. Retention
`prune_logs(retention_days)` (`DELETE WHERE ts < now() - interval`) called on each scheduler tick.

## Touchpoints

- **New**: `backend/db/migrations/versions/0006_app_logs.py`, `backend/app/logging_config.py`, `backend/app/api/logs.py`, `frontend/app/logs/page.tsx`, `frontend/components/logs-view.tsx`, `frontend/app/api/logs/route.ts`.
- **Modified**: `backend/app/data/repository.py` (add `app_logs` table + insert/query/prune helpers), `backend/app/main.py` (router + startup config + exception handler), `backend/app/config.py` (`LOG_RETENTION_DAYS`), `backend/app/pipeline/run.py` + `pipeline/scheduler_entry.py` + `data/collect.py` (swap `basicConfig` -> `configure_logging`; scheduler adds prune), `frontend/lib/api.ts` (`getLogs()` + `LogEvent`/`LogPage` types), `frontend/app/globals.css` (console styles).
- **Unchanged but referenced**: `agent_runs` (run_id correlation), `nav-links.tsx` (intentionally NOT touched — unlinked).

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Logging->DB feedback recursion | Dedicated insert path; SQLAlchemy/psycopg loggers excluded from DB handler + quieted |
| DB write blocks/crashes app | Async `QueueHandler`/`QueueListener` + batched writes; handler swallows errors to stderr |
| Lost records in short-lived processes | Flush + join listener on exit (`atexit`/`finally`) |
| Unbounded disk growth on small VM | INFO floor + time-based retention prune on scheduler tick |
| Deep-offset pagination cost | Bounded by retention; revisit keyset only if volume demands |

## Acceptance criteria

1. A real INFO/WARN/ERROR from any of the 4 processes lands in `app_logs` within seconds.
2. `/logs` lists newest-first with working level filter, search, 50/page pagination, expandable tracebacks.
3. Logging failures never crash or block the app (verified by fault injection / unit test).
4. Logs older than `LOG_RETENTION_DAYS` are pruned.
5. `/logs` reachable directly but absent from the top nav.

## Out of scope

Log aggregation/alerting, auth UI, pg_trgm search, structured JSON export, multi-tenant.

## Suggested phasing (for `/ck:plan`)

1. **Data** — migration `0006_app_logs` + repository table/insert/query/prune helpers.
2. **Core** — `logging_config.py` (async handler + safety) wired into all 4 entrypoints + FastAPI exception logging + retention.
3. **API** — `GET /api/logs` (filter/search/pagination).
4. **UI** — proxy route + client island + page + CSS port (unlinked).
