from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.data.repository import make_engine, make_session_factory, query_logs

router = APIRouter(prefix="/api/logs", tags=["logs"])

_engine = None

# UI level chip -> persisted levelnames. `error` includes CRITICAL so nothing
# severe is hidden; absent/`all` means no level filter.
_LEVEL_MAP = {
    "info": ["INFO"],
    "warn": ["WARNING"],
    "error": ["ERROR", "CRITICAL"],
}

_MAX_LIMIT = 200
_DEFAULT_LIMIT = 50


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


class LogEvent(BaseModel):
    id: int
    ts: datetime
    level: str
    source: str
    message: str
    context: dict | None = None
    run_id: str | None = None


class LogPage(BaseModel):
    items: list[LogEvent]
    total: int
    limit: int
    offset: int


@router.get("", response_model=LogPage)
def list_logs(
    level: str | None = Query(default=None),
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=_DEFAULT_LIMIT),
    offset: int = Query(default=0),
):
    levels = _LEVEL_MAP.get((level or "").lower())  # None for absent/"all"/unknown
    limit = max(1, min(limit, _MAX_LIMIT))
    offset = max(0, offset)

    session = _get_session()
    try:
        rows, total = query_logs(
            session, levels=levels, q=q, source=source, limit=limit, offset=offset
        )
    finally:
        session.close()

    items = [
        LogEvent(
            id=r.id,
            ts=r.ts,
            level=r.level,
            source=r.source,
            message=r.message,
            context=r.context,
            run_id=r.run_id,
        )
        for r in rows
    ]
    return LogPage(items=items, total=total, limit=limit, offset=offset)
