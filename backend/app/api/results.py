from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.standings import forecast_correct
from app.data.repository import (
    matches_table,
    make_engine,
    make_session_factory,
)

router = APIRouter(prefix="/api/results", tags=["results"])

# Settled-match statuses (mirror of standings._FINISHED). In-play and not-started
# matches are excluded so the results page only ever shows final scores.
_FINISHED = {"FT", "AET", "PEN"}

_engine = None


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


class ResultItem(BaseModel):
    fixture_id: int | None
    home_team: str | None
    away_team: str | None
    home_score: int | None
    away_score: int | None
    status: str | None  # "FT" | "AET" | "PEN" — drives the ET/penalty label
    winner_side: str | None  # "home" | "away" | None — advancing side for knockout ties
    home_pen: int | None
    away_pen: int | None
    kickoff_utc: datetime | None
    group_name: str | None  # "A"–"L" for group stage; None for knockout
    stage: str | None  # raw round, e.g. "Round of 16"; labels knockout matches
    forecast_correct: bool | None


def shape_results(matches: list[dict]) -> list[ResultItem]:
    """Flat, newest-first list of every finished match. Unlike
    `recent_results_by_team` there is NO per-team cap — once a team plays more
    than five games, the early matches must still appear here. Scoreless or
    non-finished rows are dropped (graceful degrade, never fabricated)."""
    finished = [
        m
        for m in matches
        if m.get("status") in _FINISHED
        and m.get("home_score") is not None
        and m.get("away_score") is not None
    ]
    _epoch = datetime.min.replace(tzinfo=timezone.utc)
    finished.sort(key=lambda m: m.get("kickoff_utc") or _epoch, reverse=True)
    return [
        ResultItem(
            fixture_id=m.get("fixture_id"),
            home_team=m.get("home_team"),
            away_team=m.get("away_team"),
            home_score=m.get("home_score"),
            away_score=m.get("away_score"),
            status=m.get("status"),
            winner_side=m.get("winner_side"),
            home_pen=m.get("home_pen"),
            away_pen=m.get("away_pen"),
            kickoff_utc=m.get("kickoff_utc"),
            group_name=m.get("group_name"),
            stage=m.get("stage"),
            forecast_correct=forecast_correct(
                m.get("forecast_json"), m.get("home_score"), m.get("away_score")
            ),
        )
        for m in finished
    ]


@router.get("", response_model=list[ResultItem])
def list_results():
    """Every finished match, newest kickoff first — the complete tournament
    history (no 5-per-team cap), so no early match drops off."""
    session = _get_session()
    try:
        rows = session.execute(
            select(
                matches_table.c.fixture_id,
                matches_table.c.group_name,
                matches_table.c.stage,
                matches_table.c.home_team,
                matches_table.c.away_team,
                matches_table.c.home_score,
                matches_table.c.away_score,
                matches_table.c.status,
                matches_table.c.winner_side,
                matches_table.c.home_pen,
                matches_table.c.away_pen,
                matches_table.c.kickoff_utc,
                matches_table.c.forecast_json,
            ).where(matches_table.c.status.in_(_FINISHED))
        ).fetchall()
    finally:
        session.close()

    return shape_results([row._mapping for row in rows])
