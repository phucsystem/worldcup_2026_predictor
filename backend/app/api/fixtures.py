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
from app.data.availability import build_team_status, last_match_contributors
from app.data.models import Match, StandingRow, TeamStatus
from app.data.repository import (
    finished_group_matches_for_team,
    make_engine,
    make_session_factory,
    matches_table,
    teams_table,
    top_scorers_table,
)
from app.data.standings_math import compute_group_table

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


class MatchStat(BaseModel):
    label: str
    # Display strings preserve API formatting ("58%", "2.90", "18").
    home: str
    away: str
    # Bar widths 0-100 (sum to 100 unless both values are 0). Computed in Python.
    home_pct: float
    away_pct: float


class ForecastFactor(BaseModel):
    name: str
    lean: str  # "home" | "away" | "even"
    why: str


class MatchForecast(BaseModel):
    # Integer win/draw/win split (sums to 100) + the factors driving it. Produced
    # by the forecast pipeline (app.pipeline.forecast); None on a fixture until
    # the backfill has run for it. `model` names the producing model.
    home_pct: int
    draw_pct: int
    away_pct: int
    factors: list[ForecastFactor] = []
    model: Optional[str] = None


class FixtureDetail(FixtureRow):
    events: list[MatchEvent] = []
    statistics: list[MatchStat] = []
    verdict: Optional[str] = None
    verdict_model: Optional[str] = None
    forecast: Optional[MatchForecast] = None
    # Per-team objective + availability, populated only for non-finished
    # fixtures (preview/live); None on finished fixtures and when a side has
    # nothing to show.
    home_status: Optional[TeamStatus] = None
    away_status: Optional[TeamStatus] = None


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


def _finished_fixtures_missing(matches, existing: set[int]) -> list[int]:
    """Finished fixture ids absent from `existing` — the once-only daily-backfill
    set shared by the events and statistics backfills. Live matches are handled by
    the live poller, not here, so they are skipped."""
    return [
        m.fixture_id
        for m in matches
        if (m.status or "").strip().upper() in FINISHED_STATUSES
        and m.fixture_id not in existing
    ]


# API-Football stat `type` → prototype S-10 label, in display order. A type absent
# from the payload is simply skipped (no zero-fill).
_STAT_LABELS: list[tuple[str, str]] = [
    ("Ball Possession", "Possession"),
    ("Total Shots", "Shots"),
    ("Shots on Goal", "Shots on target"),
    ("expected_goals", "Expected goals (xG)"),
    ("Corner Kicks", "Corners"),
]


def _stat_number(value) -> float:
    """Numeric magnitude of a stat value for bar widths. Strips '%', tolerates
    None/blank/non-numeric → 0.0."""
    if value is None:
        return 0.0
    try:
        return float(str(value).strip().rstrip("%"))
    except ValueError:
        return 0.0


def _stat_display(value) -> str:
    return "0" if value is None else str(value)


def normalize_statistics(
    raw: Optional[list[dict]], home_team: Optional[str], away_team: Optional[str]
) -> list[MatchStat]:
    """Map the raw /fixtures/statistics response (one entry per team) to ordered
    MatchStat bars. Teams are matched by name (falling back to payload order);
    stat types absent from the payload are omitted; bar percentages are computed
    here (deterministic) — never fabricated."""
    if not raw:
        return []

    def stats_of(entry: dict) -> dict:
        return {s.get("type"): s.get("value") for s in (entry.get("statistics") or [])}

    by_team = {(e.get("team") or {}).get("name"): stats_of(e) for e in raw}
    home_stats = by_team.get(home_team)
    away_stats = by_team.get(away_team)
    # Fall back to payload order if EITHER side failed to match by name — a
    # one-sided match would otherwise zero-fill the unmatched team's bars (a
    # fabricated-looking "0" for a team that actually had data).
    if (home_stats is None or away_stats is None) and len(raw) >= 2:
        home_stats, away_stats = stats_of(raw[0]), stats_of(raw[1])
    home_stats = home_stats or {}
    away_stats = away_stats or {}

    out: list[MatchStat] = []
    for api_type, label in _STAT_LABELS:
        hv = home_stats.get(api_type)
        av = away_stats.get(api_type)
        if hv is None and av is None:
            continue
        hn, an = _stat_number(hv), _stat_number(av)
        total = hn + an
        if total > 0:
            home_pct = round(hn / total * 100, 1)
            away_pct = round(100 - home_pct, 1)
        else:
            home_pct = away_pct = 0.0
        out.append(
            MatchStat(
                label=label,
                home=_stat_display(hv),
                away=_stat_display(av),
                home_pct=home_pct,
                away_pct=away_pct,
            )
        )
    return out


def select_fixtures_needing_events(matches, existing: set[int]) -> list[int]:
    """Fixture ids that are finished but have no stored events yet. `existing` is
    the set of fixture ids that already have events."""
    return _finished_fixtures_missing(matches, existing)


def select_fixtures_needing_statistics(matches, existing: set[int]) -> list[int]:
    """Fixture ids that are finished but have no stored statistics yet. `existing`
    is the set of fixture ids that already have statistics."""
    return _finished_fixtures_missing(matches, existing)


def select_fixtures_needing_verdict(matches, existing: set[int]) -> list[int]:
    """Fixture ids that are finished but have no stored verdict yet. `existing` is
    the set of fixture ids that already have a verdict."""
    return _finished_fixtures_missing(matches, existing)


def select_fixtures_needing_forecast(matches, existing: set[int]) -> list[int]:
    """Fixture ids for group-stage matches with no stored forecast yet. `existing`
    is the set of fixture ids that already have one. Knockout matches are skipped
    — a forecast is grounded in group standings, which they lack."""
    return [
        m.fixture_id
        for m in matches
        if m.fixture_id not in existing and m.group_name
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


def _all_group_tables(session) -> dict[str, list[StandingRow]]:
    """Group-stage standings tables for every group, computed live from stored
    matches (mirrors tournament.py). Needed in full so qualification status can
    account for WC 2026 best-third advancement."""
    rows = session.execute(
        select(matches_table).where(matches_table.c.group_name.isnot(None))
    ).mappings().all()
    by_group: dict[str, list[Match]] = {}
    for r in rows:
        by_group.setdefault(r["group_name"], []).append(
            Match(
                fixture_id=r["fixture_id"],
                group_name=r["group_name"],
                home_team=r["home_team"],
                away_team=r["away_team"],
                home_score=r["home_score"],
                away_score=r["away_score"],
                status=r["status"],
                kickoff_utc=r["kickoff_utc"],
                stage=r["stage"],
            )
        )
    return {g: compute_group_table(ms) for g, ms in by_group.items()}


def _key_names_by_team(session) -> dict[str, set[str]]:
    """Tournament top-scorer names grouped by team — one half of the key-player
    set (the other half, last-match scorers/assisters, is per-fixture)."""
    rows = session.execute(
        select(top_scorers_table.c.name, top_scorers_table.c.team)
        .where(top_scorers_table.c.season == settings.API_FOOTBALL_SEASON)
    ).fetchall()
    by_team: dict[str, set[str]] = {}
    for r in rows:
        if r.name and r.team:
            by_team.setdefault(r.team, set()).add(r.name)
    return by_team


def _team_statuses(
    session, home_team: Optional[str], away_team: Optional[str]
) -> tuple[Optional[TeamStatus], Optional[TeamStatus]]:
    """Build (home_status, away_status) for a non-finished fixture. Each side
    gets its objective (from live group tables) and availability (replayed from
    its prior group matches), with key players emphasised."""
    group_tables = _all_group_tables(session)
    top_scorers = _key_names_by_team(session)

    def side(team: Optional[str]) -> Optional[TeamStatus]:
        if not team:
            return None
        prior = finished_group_matches_for_team(session, team)
        key_names = top_scorers.get(team, set()) | last_match_contributors(prior, team)
        return build_team_status(group_tables, team, prior, key_names=key_names)

    return side(home_team), side(away_team)


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
        statistics_json = row.statistics_json
        verdict_text = row.verdict_text
        verdict_model = row.verdict_model
        forecast_json = row.forecast_json
        forecast_model = row.forecast_model
        home_team, away_team = row.home_team, row.away_team
        # Objective + availability are a pre-match aid: compute them for
        # preview/live fixtures only, never for a finished result.
        is_finished = (row.status or "").strip().upper() in FINISHED_STATUSES
        home_status, away_status = (
            (None, None) if is_finished else _team_statuses(session, home_team, away_team)
        )
    finally:
        session.close()
    base = _enrich(_row_to_dict(row), logos)
    events = normalize_events(events_json, home_team, away_team)
    statistics = normalize_statistics(statistics_json, home_team, away_team)
    forecast = MatchForecast(**forecast_json, model=forecast_model) if forecast_json else None
    return FixtureDetail(
        **base.model_dump(),
        events=events,
        statistics=statistics,
        verdict=verdict_text,
        verdict_model=verdict_model,
        forecast=forecast,
        home_status=home_status,
        away_status=away_status,
    )


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
