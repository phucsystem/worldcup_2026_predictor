"""User feedback API.

Reachable only via the Next.js server (route handlers) — `backend:8000` is not
publicly exposed and CORS stays GET-only, so the public POST arrives server-to-
server. Status mutations are gated by the admin session at the Next layer.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.data.repository import (
    insert_feedback,
    list_feedback,
    make_engine,
    make_session_factory,
    set_feedback_status,
)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

_MESSAGE_MAX = 2000
_TOPICS = {"bug", "feature", "other"}
_STATUSES = {"new", "done", "wont"}

_engine = None


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


class FeedbackIn(BaseModel):
    message: str = Field(min_length=1, max_length=_MESSAGE_MAX)
    topic: Optional[str] = None
    page: Optional[str] = None

    @field_validator("message")
    @classmethod
    def _strip_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be blank")
        return v

    @field_validator("topic")
    @classmethod
    def _topic_whitelist(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v if v in _TOPICS else "other"


class FeedbackOut(BaseModel):
    id: int
    created_at: datetime
    message: str
    topic: Optional[str]
    page: Optional[str]
    status: str
    resolved_at: Optional[datetime]


class FeedbackCreated(BaseModel):
    id: int


class StatusIn(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        if v not in _STATUSES:
            raise ValueError(f"status must be one of {sorted(_STATUSES)}")
        return v


@router.post("", response_model=FeedbackCreated, status_code=201)
def create_feedback(body: FeedbackIn) -> FeedbackCreated:
    session = _get_session()
    try:
        new_id = insert_feedback(
            session, message=body.message, topic=body.topic, page=body.page
        )
    finally:
        session.close()
    return FeedbackCreated(id=new_id)


@router.get("", response_model=list[FeedbackOut])
def get_feedback(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[FeedbackOut]:
    if status is not None and status not in _STATUSES:
        raise HTTPException(status_code=422, detail="invalid status filter")
    session = _get_session()
    try:
        rows = list_feedback(session, status=status, limit=limit, offset=offset)
    finally:
        session.close()
    return [
        FeedbackOut(
            id=r.id,
            created_at=r.created_at,
            message=r.message,
            topic=r.topic,
            page=r.page,
            status=r.status,
            resolved_at=r.resolved_at,
        )
        for r in rows
    ]


@router.patch("/{feedback_id}", status_code=204)
def update_feedback_status(feedback_id: int, body: StatusIn) -> None:
    session = _get_session()
    try:
        ok = set_feedback_status(session, feedback_id, body.status)
    finally:
        session.close()
    if not ok:
        raise HTTPException(status_code=404, detail="feedback not found")
