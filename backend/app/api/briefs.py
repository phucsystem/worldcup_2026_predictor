from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.data.repository import articles_table, make_engine, make_session_factory

router = APIRouter(prefix="/api/briefs", tags=["briefs"])

_engine = None


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


class BriefSummary(BaseModel):
    date: date
    title: str | None
    summary: str | None


class BriefDetail(BaseModel):
    date: date
    title: str | None
    summary: str | None
    body_md: str | None
    model_used: str | None
    created_at: str | None


@router.get("", response_model=list[BriefSummary])
def list_briefs():
    session = _get_session()
    try:
        rows = session.execute(
            select(
                articles_table.c.brief_date,
                articles_table.c.title,
                articles_table.c.summary,
            )
            .where(articles_table.c.status == "published")
            .order_by(articles_table.c.brief_date.desc())
        ).fetchall()
    finally:
        session.close()
    return [BriefSummary(date=r.brief_date, title=r.title, summary=r.summary) for r in rows]


@router.get("/latest", response_model=BriefDetail)
def get_latest_brief():
    session = _get_session()
    try:
        row = session.execute(
            select(articles_table)
            .where(articles_table.c.status == "published")
            .order_by(articles_table.c.brief_date.desc())
            .limit(1)
        ).fetchone()
    finally:
        session.close()
    if row is None:
        raise HTTPException(status_code=404, detail="No published briefs found")
    return _to_detail(row)


@router.get("/{brief_date}", response_model=BriefDetail)
def get_brief_by_date(brief_date: date):
    session = _get_session()
    try:
        row = session.execute(
            select(articles_table)
            .where(articles_table.c.brief_date == brief_date)
            .where(articles_table.c.status == "published")
        ).fetchone()
    finally:
        session.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Brief not found")
    return _to_detail(row)


def _to_detail(row) -> BriefDetail:
    created = row.created_at.isoformat() if row.created_at else None
    return BriefDetail(
        date=row.brief_date,
        title=row.title,
        summary=row.summary,
        body_md=row.body_md,
        model_used=row.model_used,
        created_at=created,
    )
