from datetime import date, datetime, timezone
from typing import Any

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.data.models import Match, StandingRow, Team, TopScorer

# Mirror migration 0001 schema — lightweight Core Table objects
_metadata = sa.MetaData()

matches_table = sa.Table(
    "matches",
    _metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("fixture_id", sa.Integer, nullable=False, unique=True),
    sa.Column("group_name", sa.String),
    sa.Column("home_team", sa.String),
    sa.Column("away_team", sa.String),
    sa.Column("home_score", sa.Integer),
    sa.Column("away_score", sa.Integer),
    sa.Column("status", sa.String),
    sa.Column("kickoff_utc", sa.DateTime(timezone=True)),
    sa.Column("events_json", sa.JSON),
    sa.Column("stage", sa.String),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)

teams_table = sa.Table(
    "teams",
    _metadata,
    sa.Column("team_id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String, nullable=False, unique=True),
    sa.Column("logo_url", sa.String),
    sa.Column("group_name", sa.String),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)

top_scorers_table = sa.Table(
    "top_scorers",
    _metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("season", sa.Integer, nullable=False),
    sa.Column("player_id", sa.Integer, nullable=False),
    sa.Column("name", sa.String),
    sa.Column("photo_url", sa.String),
    sa.Column("team", sa.String),
    sa.Column("goals", sa.Integer),
)

standings_table = sa.Table(
    "standings",
    _metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("snapshot_date", sa.Date),
    sa.Column("group_name", sa.String),
    sa.Column("team", sa.String),
    sa.Column("played", sa.Integer),
    sa.Column("won", sa.Integer),
    sa.Column("drawn", sa.Integer),
    sa.Column("lost", sa.Integer),
    sa.Column("gf", sa.Integer),
    sa.Column("ga", sa.Integer),
    sa.Column("gd", sa.Integer),
    sa.Column("points", sa.Integer),
    sa.Column("position", sa.Integer),
    sa.Column("prev_position", sa.Integer),
    sa.Column("qualification", sa.String),
)


articles_table = sa.Table(
    "articles",
    _metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("brief_date", sa.Date, nullable=False),
    sa.Column("title", sa.String),
    sa.Column("summary", sa.Text),
    sa.Column("body_md", sa.Text),
    sa.Column("status", sa.String, server_default="draft"),
    sa.Column("model_used", sa.String),
    sa.Column("created_at", sa.DateTime(timezone=True)),
)

agent_runs_table = sa.Table(
    "agent_runs",
    _metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("run_id", sa.String),
    sa.Column("brief_date", sa.Date),
    sa.Column("started_at", sa.DateTime(timezone=True)),
    sa.Column("finished_at", sa.DateTime(timezone=True)),
    sa.Column("node_timings", sa.JSON),
    sa.Column("tokens_in", sa.Integer),
    sa.Column("tokens_out", sa.Integer),
    sa.Column("cost_usd", sa.Numeric),
    sa.Column("status", sa.String),
    sa.Column("error", sa.Text),
)


def make_engine(url: str | None = None):
    return create_engine(url or settings.DATABASE_URL, pool_pre_ping=True)


def make_session_factory(engine=None) -> sessionmaker:
    engine = engine or make_engine()
    return sessionmaker(bind=engine)


def upsert_matches(session: Session, matches: list[Match]) -> None:
    if not matches:
        return
    now = datetime.now(tz=timezone.utc)
    for m in matches:
        stmt = (
            pg_insert(matches_table)
            .values(
                fixture_id=m.fixture_id,
                group_name=m.group_name,
                home_team=m.home_team,
                away_team=m.away_team,
                home_score=m.home_score,
                away_score=m.away_score,
                status=m.status,
                kickoff_utc=m.kickoff_utc,
                events_json=m.events,
                stage=m.stage,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["fixture_id"],
                set_={
                    "group_name": m.group_name,
                    "home_team": m.home_team,
                    "away_team": m.away_team,
                    "home_score": m.home_score,
                    "away_score": m.away_score,
                    "status": m.status,
                    "kickoff_utc": m.kickoff_utc,
                    "events_json": m.events,
                    "stage": m.stage,
                    "updated_at": now,
                },
            )
        )
        session.execute(stmt)
    session.commit()


def upsert_standings_snapshot(
    session: Session, snapshot_date: date, rows: list[StandingRow]
) -> None:
    if not rows:
        return
    # Replace the whole snapshot so stale rows (e.g. teams no longer in a group)
    # never linger when group membership changes between runs.
    session.execute(
        standings_table.delete().where(standings_table.c.snapshot_date == snapshot_date)
    )
    for row in rows:
        stmt = (
            pg_insert(standings_table)
            .values(
                snapshot_date=snapshot_date,
                group_name=row.group_name,
                team=row.team,
                played=row.played,
                won=row.won,
                drawn=row.drawn,
                lost=row.lost,
                gf=row.gf,
                ga=row.ga,
                gd=row.gd,
                points=row.points,
                position=row.position,
                prev_position=row.prev_position,
                qualification=row.qualification,
            )
            .on_conflict_do_update(
                constraint="uq_standings_snapshot",
                set_={
                    "played": row.played,
                    "won": row.won,
                    "drawn": row.drawn,
                    "lost": row.lost,
                    "gf": row.gf,
                    "ga": row.ga,
                    "gd": row.gd,
                    "points": row.points,
                    "position": row.position,
                    "prev_position": row.prev_position,
                    "qualification": row.qualification,
                },
            )
        )
        session.execute(stmt)
    session.commit()


def upsert_teams(session: Session, teams: list[Team]) -> None:
    if not teams:
        return
    now = datetime.now(tz=timezone.utc)
    for t in teams:
        stmt = (
            pg_insert(teams_table)
            .values(
                team_id=t.team_id,
                name=t.name,
                logo_url=t.logo_url,
                group_name=t.group_name,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["team_id"],
                set_={
                    "name": t.name,
                    "logo_url": t.logo_url,
                    "group_name": t.group_name,
                    "updated_at": now,
                },
            )
        )
        session.execute(stmt)
    session.commit()


def upsert_top_scorers(session: Session, season: int, rows: list[TopScorer]) -> None:
    if not rows:
        return
    for r in rows:
        stmt = (
            pg_insert(top_scorers_table)
            .values(
                season=season,
                player_id=r.player_id,
                name=r.name,
                photo_url=r.photo_url,
                team=r.team,
                goals=r.goals,
            )
            .on_conflict_do_update(
                constraint="uq_top_scorers_season_player",
                set_={
                    "name": r.name,
                    "photo_url": r.photo_url,
                    "team": r.team,
                    "goals": r.goals,
                },
            )
        )
        session.execute(stmt)
    session.commit()


def upsert_article(
    session: Session,
    article: dict[str, Any],
    status: str,
    brief_date: date,
) -> None:
    stmt = (
        pg_insert(articles_table)
        .values(
            brief_date=brief_date,
            title=article.get("title"),
            summary=article.get("summary"),
            body_md=article.get("body_md"),
            status=status,
            model_used="deepseek-chat",
            created_at=datetime.now(tz=timezone.utc),
        )
        .on_conflict_do_update(
            index_elements=["brief_date"],
            set_={
                "title": article.get("title"),
                "summary": article.get("summary"),
                "body_md": article.get("body_md"),
                "status": status,
                "model_used": "deepseek-chat",
            },
        )
    )
    session.execute(stmt)
    session.commit()


def insert_agent_run(session: Session, run_record: dict[str, Any]) -> None:
    stmt = agent_runs_table.insert().values(
        run_id=run_record["run_id"],
        brief_date=run_record["brief_date"],
        started_at=run_record["started_at"],
        finished_at=run_record["finished_at"],
        node_timings=run_record.get("node_timings", {}),
        tokens_in=run_record.get("tokens_in", 0),
        tokens_out=run_record.get("tokens_out", 0),
        cost_usd=run_record.get("cost_usd", 0.0),
        status=run_record.get("status", "unknown"),
        error=run_record.get("error"),
    )
    session.execute(stmt)
    session.commit()
