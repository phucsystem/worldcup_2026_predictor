from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.data.repository import (
    matches_table,
    standings_table,
    teams_table,
    make_engine,
    make_session_factory,
)

router = APIRouter(prefix="/api/standings", tags=["standings"])

# Strict "match is over" set (mirror of `_NOT_STARTED` in api_football.py).
# In-play (1H/HT/2H/LIVE) and not-started statuses are deliberately excluded so
# recent-form views only ever count settled results.
_FINISHED = {"FT", "AET", "PEN"}
_RECENT_LIMIT = 5

_engine = None


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


class RecentResult(BaseModel):
    outcome: str  # "W" | "D" | "L" from the owning team's perspective
    fixture_id: int | None = None  # links the result row to its match page
    home_team: str | None
    away_team: str | None
    home_score: int | None
    away_score: int | None
    kickoff_utc: datetime | None
    # Whether the pre-match forecast called the right side; None when the match
    # carried no forecast (forecast scope is group-stage only).
    forecast_correct: bool | None = None


class TrendPoint(BaseModel):
    snapshot_date: date | None
    position: int | None
    points: int | None


class StandingRow(BaseModel):
    position: int | None
    prev_position: int | None
    team: str | None
    played: int | None
    won: int | None
    drawn: int | None
    lost: int | None
    gf: int | None
    ga: int | None
    gd: int | None
    points: int | None
    qualification: str | None
    logo: str | None = None
    recent_results: list[RecentResult] = []


class GroupStandings(BaseModel):
    group_name: str
    rows: list[StandingRow]


class StandingsSnapshot(BaseModel):
    snapshot_date: date | None
    groups: list[GroupStandings]


# ---------------------------------------------------------------------------
# Pure shaping functions (no I/O — unit-tested in test_recent_results.py /
# test_standings_trend.py)
# ---------------------------------------------------------------------------

def match_outcome(team: str, match: dict) -> str:
    """W/D/L from `team`'s perspective. Assumes scores are present."""
    hs, as_ = match.get("home_score"), match.get("away_score")
    gf, ga = (hs, as_) if match.get("home_team") == team else (as_, hs)
    if gf > ga:
        return "W"
    if gf == ga:
        return "D"
    return "L"


def forecast_correct(forecast: dict | None, home_score, away_score) -> bool | None:
    """Did the forecast call the right side? The forecast's most-probable side
    (argmax of home/draw/away pct) is compared with the actual result. Returns
    None when no forecast exists or scores are missing — never fabricated."""
    if not forecast or home_score is None or away_score is None:
        return None
    home_pct = forecast.get("home_pct")
    draw_pct = forecast.get("draw_pct")
    away_pct = forecast.get("away_pct")
    if home_pct is None or draw_pct is None or away_pct is None:
        return None
    if home_pct >= draw_pct and home_pct >= away_pct:
        predicted = "home"
    elif away_pct >= draw_pct:
        predicted = "away"
    else:
        predicted = "draw"
    actual = "home" if home_score > away_score else "away" if home_score < away_score else "draw"
    return predicted == actual


def recent_results_by_team(
    matches: list[dict], limit: int = _RECENT_LIMIT
) -> dict[str, list[RecentResult]]:
    """Group settled matches into per-team, most-recent-first result lists.

    A match attaches to both its home and away team. Only strictly finished
    matches with both scores present are counted; everything else is ignored
    (graceful degrade — never fabricate, never error)."""
    finished = [
        m
        for m in matches
        if m.get("status") in _FINISHED
        and m.get("home_score") is not None
        and m.get("away_score") is not None
    ]
    _epoch = datetime.min.replace(tzinfo=timezone.utc)
    finished.sort(key=lambda m: m.get("kickoff_utc") or _epoch, reverse=True)

    out: dict[str, list[RecentResult]] = {}
    for m in finished:
        for team in (m.get("home_team"), m.get("away_team")):
            if not team:
                continue
            bucket = out.setdefault(team, [])
            if len(bucket) >= limit:
                continue
            bucket.append(
                RecentResult(
                    outcome=match_outcome(team, m),
                    fixture_id=m.get("fixture_id"),
                    home_team=m.get("home_team"),
                    away_team=m.get("away_team"),
                    home_score=m.get("home_score"),
                    away_score=m.get("away_score"),
                    kickoff_utc=m.get("kickoff_utc"),
                    forecast_correct=forecast_correct(
                        m.get("forecast_json"),
                        m.get("home_score"),
                        m.get("away_score"),
                    ),
                )
            )
    return out


def shape_trend(rows: list[dict], window: int = _RECENT_LIMIT) -> list[TrendPoint]:
    """Ordered (oldest→newest) position/points series, last `window` snapshots."""
    _min = date.min
    ordered = sorted(rows, key=lambda r: r.get("snapshot_date") or _min)
    points = [
        TrendPoint(
            snapshot_date=r.get("snapshot_date"),
            position=r.get("position"),
            points=r.get("points"),
        )
        for r in ordered
    ]
    return points[-window:] if window and window > 0 else points


@router.get("", response_model=StandingsSnapshot)
def get_standings(date: Optional[date] = None):
    session = _get_session()
    try:
        snapshot_date = date or _latest_snapshot_date(session)
        if snapshot_date is None:
            return StandingsSnapshot(snapshot_date=None, groups=[])

        rows = session.execute(
            select(standings_table)
            .where(standings_table.c.snapshot_date == snapshot_date)
            .order_by(standings_table.c.group_name, standings_table.c.position)
        ).fetchall()
        logos = {
            t.name: t.logo_url
            for t in session.execute(
                select(teams_table.c.name, teams_table.c.logo_url)
            ).fetchall()
            if t.logo_url
        }
        finished_rows = session.execute(
            select(
                matches_table.c.fixture_id,
                matches_table.c.home_team,
                matches_table.c.away_team,
                matches_table.c.home_score,
                matches_table.c.away_score,
                matches_table.c.status,
                matches_table.c.kickoff_utc,
                matches_table.c.forecast_json,
            ).where(matches_table.c.status.in_(_FINISHED))
        ).fetchall()
    finally:
        session.close()

    recent_map = recent_results_by_team(
        [
            {
                "fixture_id": m.fixture_id,
                "home_team": m.home_team,
                "away_team": m.away_team,
                "home_score": m.home_score,
                "away_score": m.away_score,
                "status": m.status,
                "kickoff_utc": m.kickoff_utc,
                "forecast_json": m.forecast_json,
            }
            for m in finished_rows
        ]
    )

    groups: dict[str, list[StandingRow]] = {}
    for r in rows:
        row = StandingRow(
            position=r.position,
            prev_position=r.prev_position,
            team=r.team,
            played=r.played,
            won=r.won,
            drawn=r.drawn,
            lost=r.lost,
            gf=r.gf,
            ga=r.ga,
            gd=r.gd,
            points=r.points,
            qualification=r.qualification,
            logo=logos.get(r.team),
            recent_results=recent_map.get(r.team, []),
        )
        groups.setdefault(r.group_name, []).append(row)

    return StandingsSnapshot(
        snapshot_date=snapshot_date,
        groups=[GroupStandings(group_name=g, rows=rows) for g, rows in groups.items()],
    )


@router.get("/trend", response_model=list[TrendPoint])
def get_standings_trend(team: str, window: int = _RECENT_LIMIT):
    """Standalone position/points history for one team across snapshots.

    No prototype element consumes this; kept per product decision, off the
    parity critical path."""
    session = _get_session()
    try:
        rows = session.execute(
            select(
                standings_table.c.snapshot_date,
                standings_table.c.position,
                standings_table.c.points,
            )
            .where(standings_table.c.team == team)
            .order_by(standings_table.c.snapshot_date)
        ).fetchall()
    finally:
        session.close()
    return shape_trend(
        [
            {"snapshot_date": r.snapshot_date, "position": r.position, "points": r.points}
            for r in rows
        ],
        window,
    )


def _latest_snapshot_date(session) -> date | None:
    from sqlalchemy import func
    result = session.execute(
        select(func.max(standings_table.c.snapshot_date))
    ).scalar()
    return result
