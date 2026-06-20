---
phase: 2
title: "Core"
status: completed
priority: P1
dependencies: [1]
---

# Phase 2: Core — centralized non-blocking logging + DB handler + retention

## Overview

Add `app/logging_config.py`: a single `configure_logging()` that sets up a stdout console handler plus a non-blocking, batched DB log handler, and wire it into every entrypoint. Add FastAPI web-layer error logging. Add `LOG_RETENTION_DAYS` and a daily prune. This is the safety-critical phase — the invariants in `plan.md` are the contract.

## Requirements

- Functional: every wired process emits its `app.*` logs to both stdout and `app_logs`; FastAPI logs unhandled exceptions; old rows pruned daily.
- Non-functional (hard invariants): non-blocking, never-crashes, no feedback loop, no lost records on exit, INFO persistence floor. See `plan.md`.

## Architecture

`app/logging_config.py`:

- `DBLogHandler(logging.Handler)` — buffers `LogRecord`s; flushes when buffer ≥ `BATCH_SIZE` or on a timer; maps each record to a row dict (`ts`=`datetime.fromtimestamp(record.created, tz=utc)`, `level`=`record.levelname`, `source`=`record.name`, `message`=`record.getMessage()`, `context`= `{traceback: formatException(exc_info)}` + whitelisted extras, `run_id`=`getattr(record, "run_id", None)`). Writes via `insert_log_rows` using its **own engine/session** (not request sessions). Overrides `handleError` → write to `sys.stderr`, never raise. `emit` wrapped in try/except → `handleError`.
- Concurrency: use stdlib `logging.handlers.QueueHandler` + `QueueListener`. App loggers get the `QueueHandler` (enqueue only — O(1), never blocks). A module-level `QueueListener(queue, DBLogHandler(), console_handler)` runs the actual I/O on a background thread. Expose `start_logging()`/`stop_logging()` (listener start + `atexit` stop that flushes).
- `configure_logging(*, db: bool = True)` — builds config (idempotent; guard against double-config). Root/`app` logger level INFO. Attaches console (stdout, always) + queue handler. **Recursion guard**: set `logging.getLogger("sqlalchemy").setLevel(WARNING)` and ensure the DB write path’s logger does not propagate into the queue handler (e.g. dedicated logger name excluded, or `DBLogHandler` filters out `sqlalchemy*`/its own source). DB floor: a filter dropping `< INFO` from the DB handler only.
- Flush-on-exit: `atexit.register(stop_logging)`; long-lived loops unaffected; short-lived CLIs (`collect`, `run`, one-shot `scheduler_entry`) call `stop_logging()` in a `finally` to guarantee flush before process exit.

## Related Code Files

- Create: `backend/app/logging_config.py`.
- Modify:
  - `backend/app/config.py` — add `LOG_RETENTION_DAYS: int = 14` (and optional `LOG_DB_ENABLED: bool = True`).
  - `backend/app/main.py` — call `configure_logging()` on startup; add an exception handler / middleware that logs unhandled errors at `ERROR` with `exc_info`; (keep existing CORS/health).
  - `backend/app/pipeline/run.py` — replace `logging.basicConfig(...)` (line 17) with `configure_logging()`; wrap `run_pipeline` body so `stop_logging()` runs in `finally`; call `prune_logs(retention_days)` at the start of `run_pipeline()` (its own session).
  - `backend/app/pipeline/scheduler_entry.py` — replace `basicConfig` in `main()` with `configure_logging()`; `stop_logging()` in `finally` before `sys.exit`.
  - `backend/app/data/collect.py` — replace module-level `basicConfig` (line 32) with `configure_logging()` in `main()`; `stop_logging()` in `finally`.
  - `backend/app/pipeline/live_poller.py` — call `configure_logging()` at startup of its loop entry; rely on `atexit` flush.
- Reference only: `backend/app/data/repository.py` (`insert_log_rows`, `prune_logs`, `make_engine`).

## Implementation Steps

1. Implement `DBLogHandler` (batching, mapping, `handleError`, own engine).
2. Implement queue plumbing + `configure_logging()`/`start_logging()`/`stop_logging()` with idempotency + recursion/level guards.
3. Wire each entrypoint (swap `basicConfig`, add `finally: stop_logging()` to short-lived ones).
4. Add `LOG_RETENTION_DAYS` to config; call `prune_logs` at `run_pipeline()` start.
5. Add FastAPI unhandled-exception logging in `main.py`.
6. Fault-injection check: force `insert_log_rows` to raise → app keeps running, error surfaces on stderr, no exception propagates to callers.

## Success Criteria

- [x] `configure_logging()` is idempotent and used by all five entrypoints; no `basicConfig` calls remain.
- [x] A logged line from each process appears in `app_logs` (via the listener) and on stdout.
- [x] DEBUG records reach stdout but not `app_logs`; `sqlalchemy`/handler-internal logs do not create new `app_logs` rows (no recursion).
- [x] Injected DB-write failure does not crash or block; error printed to stderr.
- [x] Short-lived CLI runs flush buffered records before exit (no lost tail).
- [x] FastAPI logs unhandled request exceptions with traceback in `context`.
- [x] `prune_logs` runs on each `run_pipeline()` invocation.

## Risk Assessment

- **Feedback loop** (highest): a logged DB write → more rows → loop. Mitigate via level/source filters on the DB handler + quieted `sqlalchemy` + the handler’s own non-logging session.
- **Blocking/crash**: only `QueueHandler.enqueue` runs on the app thread; all I/O is off-thread and error-swallowed.
- **Lost records**: enforce `finally: stop_logging()` in every short-lived entrypoint + `atexit`.
- **Double-config** (e.g. uvicorn reload) → idempotency guard.
- **Thread safety of engine**: handler uses a dedicated engine/connection on the listener thread, not shared request sessions.
