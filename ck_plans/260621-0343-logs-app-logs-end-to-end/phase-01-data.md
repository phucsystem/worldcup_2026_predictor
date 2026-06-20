---
phase: 1
title: "Data"
status: completed
priority: P1
dependencies: []
---

# Phase 1: Data — `app_logs` table + repository helpers

## Overview

Add the `app_logs` table (migration `0006`) and the repository Core-table definition plus insert/query/prune helpers that later phases build on. No behavior change yet.

## Requirements

- Functional: a queryable, indexed table for line-level log events with optional JSONB context and `run_id` correlation; helpers to bulk-insert, page-query (with level/source/search filters + total count), and prune by age.
- Non-functional: indexes support newest-first listing and level filtering; batched insert path (list of dicts) so the Core handler can flush many rows in one statement.

## Architecture

Mirror migration `0001` style (Alembic `op.create_table` + `JSONB`) and the existing `repository.py` Core pattern (`sa.Table` on the shared `_metadata`, helper fns taking a `Session`).

Schema (`app_logs`):

| col | type | notes |
|-----|------|-------|
| `id` | BigInteger PK, autoincrement | high volume |
| `ts` | DateTime(timezone=True), not null | event time (UTC); index DESC |
| `level` | String, not null | Python levelname: `INFO`/`WARNING`/`ERROR`/`CRITICAL` |
| `source` | String, not null | logger name, e.g. `app.pipeline.run` |
| `message` | Text, not null | rendered message |
| `context` | JSONB, null | `{ "traceback": "...", "extra": {...} }` |
| `run_id` | String, null | correlate to `agent_runs.run_id` |

Indexes: `ix_app_logs_ts` on `ts DESC`; `ix_app_logs_level` on `level`. (Free-text search uses `ILIKE`; `pg_trgm` is out of scope.)

## Related Code Files

- Create: `backend/db/migrations/versions/0006_app_logs.py` (upgrade creates table+indexes; downgrade drops table).
- Modify: `backend/app/data/repository.py`
  - Add `app_logs_table = sa.Table("app_logs", _metadata, ...)`.
  - `insert_log_rows(session, rows: list[dict]) -> None` — single `app_logs_table.insert()` executemany; commit. Used by the Core handler.
  - `query_logs(session, *, levels: list[str] | None, q: str | None, source: str | None, limit: int, offset: int) -> tuple[list[Row], int]` — returns page rows (order by `ts DESC, id DESC`) + total count. `q` → `ILIKE %q%` across `message` and `source`. `levels` → `level IN (...)`.
  - `prune_logs(session, retention_days: int) -> int` — `DELETE WHERE ts < now() - interval`; returns deleted count.

## Implementation Steps

1. Write `0006_app_logs.py` following `0005_match_elapsed.py` / `0001_initial.py` conventions (down_revision = `0005`). Create table + both indexes; downgrade drops the table.
2. Add `app_logs_table` to `repository.py` mirroring the migration columns exactly (keep the "Mirror migration schema" comment style).
3. Add `insert_log_rows`, `query_logs`, `prune_logs` near the existing insert/query helpers. Keep them dependency-free (no logging calls inside — these run under the logging path; see Phase 2 recursion invariant).
4. Confirm migration applies on the dev DB (`alembic upgrade head` or the project's migration command) and `downgrade` reverts cleanly.

## Success Criteria

- [x] `0006_app_logs.py` upgrades and downgrades cleanly against the dev DB.
- [x] `app_logs_table` columns/indexes match the migration 1:1.
- [x] `insert_log_rows` inserts a batch in one statement; `query_logs` returns correct page + total under level/source/`q` filters ordered newest-first; `prune_logs` deletes only rows older than the cutoff.
- [x] Helpers contain no logging calls (recursion-safe).

## Risk Assessment

- Wrong `down_revision` chain breaks migrations → verify against `0005` head before writing.
- Helpers emitting logs would feed the loop later → keep them silent now (enforced again in Phase 2).
