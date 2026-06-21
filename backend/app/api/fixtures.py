"""Read-only fixtures + stars API: upcoming fixtures (day-grouped), the knockout
bracket, and tournament top scorers. Shaping logic is split into pure functions
(no DB/network) so it can be unit-tested directly.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
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

# API-Football short status codes for an in-play match (excludes NS and any
# finished/postponed state). Drives the /live endpoint and the live poller.
LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE"}

# Finished short status codes — drive the once-only events backfill on the daily
# collect path.
FINISHED_STATUSES = {"FT", "AET", "PEN"}


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
    elapsed: Optional[int] = None
    stage: Optional[str] = None
    group_name: Optional[str] = None
    kickoff_utc: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MatchEvent(BaseModel):
    minute: int
    extra: Optional[int] = None
    type: Optional[str] = None
    detail: Optional[str] = None
    player: Optional[str] = None
    assist: Optional[str] = None
    team: Optional[str] = None
    side: Optional[str] = None  # "home" | "away" | None


class FixtureDetail(FixtureRow):
    events: list[MatchEvent] = []


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


def is_live_status(status: Optional[str]) -> bool:
    return bool(status) and status.strip().upper() in LIVE_STATUSES


def normalize_events(
    raw: Optional[list[dict]], home_team: Optional[str], away_team: Optional[str]
) -> list[MatchEvent]:
    """Map raw API-Football /fixtures/events entries to a stable, frontend-
    friendly shape. `side` is resolved by matching the event team name to the
    home/away team; the running timeline score is NOT computed here (the frontend
    derives it from goal events in Phase 2)."""
    if not raw:
        return []
    events: list[MatchEvent] = []
    for e in raw:
        time = e.get("time") or {}
        team = (e.get("team") or {}).get("name")
        if team and team == home_team:
            side = "home"
        elif team and team == away_team:
            side = "away"
        else:
            side = None
        events.append(
            MatchEvent(
                minute=time.get("elapsed") or 0,
                extra=time.get("extra"),
                type=e.get("type"),
                detail=e.get("detail"),
                player=(e.get("player") or {}).get("name"),
                assist=(e.get("assist") or {}).get("name"),
                team=team,
                side=side,
            )
        )
    return events


def select_fixtures_needing_events(matches, existing: set[int]) -> list[int]:
    """Fixture ids that are finished but have no stored events yet — the daily
    backfill set. Live matches are handled by the live poller, not here, so they
    are skipped. `existing` is the set of fixture ids that already have events."""
    return [
        m.fixture_id
        for m in matches
        if (m.status or "").strip().upper() in FINISHED_STATUSES
        and m.fixture_id not in existing
    ]


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
        elapsed=row.get("elapsed"),
        stage=row.get("stage"),
        group_name=row.get("group_name"),
        kickoff_utc=row.get("kickoff_utc"),
        updated_at=row.get("updated_at"),
    )


def shape_upcoming(rows: list[dict], logos: dict[str, str]) -> UpcomingFixtures:
    """Group upcoming fixtures by kickoff day (ascending) and surface the soonest
    as `up_next`. Rows are assumed already filtered to upcoming matches."""
    enriched = sorted(
        (_enrich(r, logos) for r in rows),
        key=lambda f: (f.kickoff_utc is None, f.kickoff_utc),
    )
    # Bucket by the calendar day in the brief timezone, not UTC: a 17:00Z match
    # is the next morning in Australia/Melbourne, so UTC bucketing splits one
    # local matchday across two day headers and mislabels each.
    brief_tz = ZoneInfo(settings.BRIEF_TIMEZONE)
    by_day: dict[date, list[FixtureRow]] = {}
    day_order: list[date] = []
    for f in enriched:
        if f.kickoff_utc is None:
            continue
        ko = f.kickoff_utc
        if ko.tzinfo is None:
            ko = ko.replace(tzinfo=timezone.utc)
        day = ko.astimezone(brief_tz).date()
        if day not in by_day:
            by_day[day] = []
            day_order.append(day)
        by_day[day].append(f)

    days = [FixtureDay(date=d, fixtures=by_day[d]) for d in day_order]
    up_next = next((f for f in enriched if f.kickoff_utc is not None), None)
    return UpcomingFixtures(up_next=up_next, days=days)


def shape_live(rows: list[dict], logos: dict[str, str]) -> list[FixtureRow]:
    """Filter to in-play matches and return them soonest-kicked first. Pure
    (no DB/network) so the live filter + ordering is unit-tested."""
    live = [_enrich(r, logos) for r in rows if is_live_status(r.get("status"))]
    live.sort(key=lambda f: (f.kickoff_utc is None, f.kickoff_utc))
    return live


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
        "elapsed": r.elapsed,
        "stage": r.stage,
        "group_name": r.group_name,
        "kickoff_utc": r.kickoff_utc,
        "updated_at": r.updated_at,
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


@router.get("/live", response_model=list[FixtureRow])
def get_live():
    """In-play matches, soonest-kicked first. Reads the DB only (the live poller
    refreshes scores/elapsed out-of-band), so this makes zero external calls.

    A finished match drops out of API-Football's ?live=all feed, so the live
    poller never writes its final FT status — only the full collect does. The
    kickoff-window guard keeps such a stale live row from rendering as "live"
    indefinitely between full collects."""
    session = _get_session()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=settings.LIVE_WINDOW_HOURS)
    try:
        rows = session.execute(
            select(matches_table)
            .where(matches_table.c.status.in_(LIVE_STATUSES))
            .where(matches_table.c.kickoff_utc >= cutoff)
            .order_by(matches_table.c.kickoff_utc)
        ).fetchall()
        logos = _logo_map(session)
    finally:
        session.close()
    return shape_live([_row_to_dict(r) for r in rows], logos)


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


# Registered last so the literal routes (/upcoming, /live, /knockout) win over
# this int path param.
@router.get("/{fixture_id}", response_model=FixtureDetail)
def get_fixture(fixture_id: int):
    session = _get_session()
    try:
        row = session.execute(
            select(matches_table).where(matches_table.c.fixture_id == fixture_id)
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="fixture not found")
        logos = _logo_map(session)
        events_json = row.events_json
        home_team, away_team = row.home_team, row.away_team
    finally:
        session.close()
    base = _enrich(_row_to_dict(row), logos)
    events = normalize_events(events_json, home_team, away_team)
    return FixtureDetail(**base.model_dump(), events=events)


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
