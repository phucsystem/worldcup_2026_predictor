"""Read-only fixtures + stars API: upcoming fixtures (day-grouped), the knockout
bracket, and tournament top scorers. Shaping logic is split into pure functions
(no DB/network) so it can be unit-tested directly.
"""
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.config import settings
from app.data.repository import (
    make_engine,
    make_session_factory,
    matches_table,
    teams_table,
    top_scorers_table,
)

router = APIRouter(prefix="/api/fixtures", tags=["fixtures"])

_engine = None

# Knockout rounds in bracket order. Matching is case-insensitive on the raw
# API-Football `round` string; anything unrecognised sorts after these.
KNOCKOUT_ROUND_ORDER = [
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "3rd Place Final",
    "Final",
]
_KNOCKOUT_ORDER_INDEX = {name.lower(): i for i, name in enumerate(KNOCKOUT_ROUND_ORDER)}


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class FixtureRow(BaseModel):
    fixture_id: int
    home_team: Optional[str]
    away_team: Optional[str]
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    group_name: Optional[str] = None
    kickoff_utc: Optional[datetime] = None


class FixtureDay(BaseModel):
    date: date
    fixtures: list[FixtureRow]


class UpcomingFixtures(BaseModel):
    up_next: Optional[FixtureRow]
    days: list[FixtureDay]


class KnockoutRound(BaseModel):
    round: str
    ties: list[FixtureRow]


class KnockoutBracket(BaseModel):
    rounds: list[KnockoutRound]


class StarRow(BaseModel):
    player_id: int
    name: str
    team: Optional[str]
    goals: int
    photo_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Pure shaping functions (no I/O — unit-tested in test_fixtures_shaping.py)
# ---------------------------------------------------------------------------

def is_knockout_stage(stage: Optional[str]) -> bool:
    return bool(stage) and stage.strip().lower() in _KNOCKOUT_ORDER_INDEX


def _enrich(row: dict, logos: dict[str, str]) -> FixtureRow:
    return FixtureRow(
        fixture_id=row["fixture_id"],
        home_team=row.get("home_team"),
        away_team=row.get("away_team"),
        home_logo=logos.get(row.get("home_team")),
        away_logo=logos.get(row.get("away_team")),
        home_score=row.get("home_score"),
        away_score=row.get("away_score"),
        status=row.get("status"),
        stage=row.get("stage"),
        group_name=row.get("group_name"),
        kickoff_utc=row.get("kickoff_utc"),
    )


def shape_upcoming(rows: list[dict], logos: dict[str, str]) -> UpcomingFixtures:
    """Group upcoming fixtures by kickoff day (ascending) and surface the soonest
    as `up_next`. Rows are assumed already filtered to upcoming matches."""
    enriched = sorted(
        (_enrich(r, logos) for r in rows),
        key=lambda f: (f.kickoff_utc is None, f.kickoff_utc),
    )
    by_day: dict[date, list[FixtureRow]] = {}
    day_order: list[date] = []
    for f in enriched:
        if f.kickoff_utc is None:
            continue
        day = f.kickoff_utc.date()
        if day not in by_day:
            by_day[day] = []
            day_order.append(day)
        by_day[day].append(f)

    days = [FixtureDay(date=d, fixtures=by_day[d]) for d in day_order]
    up_next = next((f for f in enriched if f.kickoff_utc is not None), None)
    return UpcomingFixtures(up_next=up_next, days=days)


def shape_knockout(rows: list[dict], logos: dict[str, str]) -> KnockoutBracket:
    """Assemble knockout matches into bracket rounds in canonical order. Empty
    when no knockout matches exist yet."""
    by_round: dict[str, list[FixtureRow]] = {}
    order: list[str] = []
    for r in rows:
        stage = r.get("stage")
        if not is_knockout_stage(stage):
            continue
        label = stage.strip()
        if label not in by_round:
            by_round[label] = []
            order.append(label)
        by_round[label].append(_enrich(r, logos))

    order.sort(key=lambda name: _KNOCKOUT_ORDER_INDEX.get(name.lower(), len(KNOCKOUT_ROUND_ORDER)))
    for ties in by_round.values():
        ties.sort(key=lambda f: (f.kickoff_utc is None, f.kickoff_utc))
    return KnockoutBracket(
        rounds=[KnockoutRound(round=name, ties=by_round[name]) for name in order]
    )


# ---------------------------------------------------------------------------
# DB plumbing
# ---------------------------------------------------------------------------

def _logo_map(session) -> dict[str, str]:
    rows = session.execute(
        select(teams_table.c.name, teams_table.c.logo_url)
    ).fetchall()
    return {r.name: r.logo_url for r in rows if r.logo_url}


def _row_to_dict(r) -> dict:
    return {
        "fixture_id": r.fixture_id,
        "home_team": r.home_team,
        "away_team": r.away_team,
        "home_score": r.home_score,
        "away_score": r.away_score,
        "status": r.status,
        "stage": r.stage,
        "group_name": r.group_name,
        "kickoff_utc": r.kickoff_utc,
    }


@router.get("/upcoming", response_model=UpcomingFixtures)
def get_upcoming():
    session = _get_session()
    try:
        now = datetime.now(tz=timezone.utc)
        rows = session.execute(
            select(matches_table)
            .where(matches_table.c.home_score.is_(None))
            .where(matches_table.c.kickoff_utc.isnot(None))
            .where(matches_table.c.kickoff_utc >= now)
            .order_by(matches_table.c.kickoff_utc)
        ).fetchall()
        logos = _logo_map(session)
    finally:
        session.close()
    return shape_upcoming([_row_to_dict(r) for r in rows], logos)


@router.get("/knockout", response_model=KnockoutBracket)
def get_knockout():
    session = _get_session()
    try:
        rows = session.execute(
            select(matches_table)
            .where(matches_table.c.group_name.is_(None))
            .order_by(matches_table.c.kickoff_utc)
        ).fetchall()
        logos = _logo_map(session)
    finally:
        session.close()
    return shape_knockout([_row_to_dict(r) for r in rows], logos)


# `/api/stars` lives logically with fixtures enrichment; exposed via its own
# router prefix so the URL stays `/api/stars` (not `/api/fixtures/stars`).
stars_router = APIRouter(prefix="/api/stars", tags=["stars"])


@stars_router.get("", response_model=list[StarRow])
def get_stars():
    session = _get_session()
    try:
        rows = session.execute(
            select(top_scorers_table)
            .where(top_scorers_table.c.season == settings.API_FOOTBALL_SEASON)
            .order_by(top_scorers_table.c.goals.desc())
        ).fetchall()
    finally:
        session.close()
    return [
        StarRow(
            player_id=r.player_id,
            name=r.name,
            team=r.team,
            goals=r.goals or 0,
            photo_url=r.photo_url,
        )
        for r in rows
    ]
