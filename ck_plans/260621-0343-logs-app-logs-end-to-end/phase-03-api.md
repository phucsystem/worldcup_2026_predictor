---
phase: 3
title: "API"
status: completed
priority: P2
dependencies: [1]
---

# Phase 3: API — `GET /api/logs`

## Overview

Expose a read-only, paginated, filterable logs endpoint backed by `query_logs`, following the existing router/Pydantic/Core conventions.

## Requirements

- Functional: `GET /api/logs?level=&q=&source=&limit=50&offset=0` → `{ items: LogEvent[], total, limit, offset }`, newest-first.
- Non-functional: clamp `limit` (e.g. 1–200, default 50) and `offset` (≥0); read-only; same session-per-request pattern as `briefs.py`.

## Architecture

- `level` query param is the UI chip value, mapped to levelnames:
  - `info` → `["INFO"]`, `warn` → `["WARNING"]`, `error` → `["ERROR","CRITICAL"]`, absent/`all` → no filter.
- `q` → passed to `query_logs` (`ILIKE` on message+source). `source` → exact logger-name filter (optional).
- Response models (Pydantic):
  - `LogEvent { id: int; ts: datetime; level: str; source: str; message: str; context: dict | None; run_id: str | None }`
  - `LogPage { items: list[LogEvent]; total: int; limit: int; offset: int }`

## Related Code Files

- Create: `backend/app/api/logs.py` — `router = APIRouter(prefix="/api/logs", tags=["logs"])`; `_get_session()` helper (mirror `briefs.py`); `GET ""` handler calling `query_logs` and shaping `LogPage`.
- Modify: `backend/app/main.py` — `from app.api.logs import router as logs_router`; `app.include_router(logs_router)`.

## Implementation Steps

1. Create `logs.py` mirroring `briefs.py` structure (module engine, `_get_session`, Pydantic models, session close in `finally`).
2. Implement chip→levelname mapping + param clamping; call `query_logs`; map rows → `LogEvent`; return `LogPage`.
3. Mount the router in `main.py`.
4. Manual check: seed a few rows (or let Phase 2 produce them), hit `/api/logs?level=error&q=timeout&limit=50&offset=0`, verify shape, ordering, and `total`.

## Success Criteria

- [x] Endpoint returns newest-first page + correct `total` honoring `level`/`q`/`source`.
- [x] `limit`/`offset` clamped; bad input doesn’t 500.
- [x] Chip mapping correct (`error` includes CRITICAL).
- [x] Router mounted; follows existing API conventions (no new patterns).

## Risk Assessment

- Deep-offset cost on large tables → acceptable (volume bounded by retention); revisit keyset pagination only if needed.
- Unbounded `limit` → clamp to protect the DB and payload size.
