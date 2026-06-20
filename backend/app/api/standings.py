from datetime import date
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.data.repository import standings_table, teams_table, make_engine, make_session_factory

router = APIRouter(prefix="/api/standings", tags=["standings"])

_engine = None


def _get_session():
    global _engine
    if _engine is None:
        _engine = make_engine()
    factory = make_session_factory(_engine)
    return factory()


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


class GroupStandings(BaseModel):
    group_name: str
    rows: list[StandingRow]


class StandingsSnapshot(BaseModel):
    snapshot_date: date | None
    groups: list[GroupStandings]


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
    finally:
        session.close()

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
        )
        groups.setdefault(r.group_name, []).append(row)

    return StandingsSnapshot(
        snapshot_date=snapshot_date,
        groups=[GroupStandings(group_name=g, rows=rows) for g, rows in groups.items()],
    )


def _latest_snapshot_date(session) -> date | None:
    from sqlalchemy import func
    result = session.execute(
        select(func.max(standings_table.c.snapshot_date))
    ).scalar()
    return result
