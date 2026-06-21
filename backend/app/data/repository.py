from datetime import date, datetime, timedelta, timezone
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
    sa.Column("elapsed", sa.Integer),
    sa.Column("kickoff_utc", sa.DateTime(timezone=True)),
    sa.Column("events_json", sa.JSON),
    sa.Column("statistics_json", sa.JSON),
    sa.Column("verdict_text", sa.Text),
    sa.Column("verdict_model", sa.String),
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
    sa.Column("intelligence", sa.JSON),
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


# Mirror migration 0006 schema — line-level log events
app_logs_table = sa.Table(
    "app_logs",
    _metadata,
    sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
    sa.Column("level", sa.String, nullable=False),
    sa.Column("source", sa.String, nullable=False),
    sa.Column("message", sa.Text, nullable=False),
    sa.Column("context", sa.JSON),
    sa.Column("run_id", sa.String),
)


def make_engine(url: str | None = None):
    return create_engine(url or settings.DATABASE_URL, pool_pre_ping=True)


def make_session_factory(engine=None) -> sessionmaker:
    engine = engine or make_engine()
    return sessionmaker(bind=engine)


def prune_matches_not_in(session: Session, keep_fixture_ids: list[int]) -> int:
    """Delete match rows whose fixture_id is not in the current fetch.

    Keeps the table scoped to the active season/league so stale data from a
    previous season config (e.g. a prior 2022 collect) can never linger and
    leak into standings or the brief. Returns the number of rows removed."""
    if not keep_fixture_ids:
        return 0
    result = session.execute(
        matches_table.delete().where(matches_table.c.fixture_id.notin_(keep_fixture_ids))
    )
    session.commit()
    return result.rowcount or 0


def upsert_matches(session: Session, matches: list[Match]) -> None:
    if not matches:
        return
    now = datetime.now(tz=timezone.utc)
    for m in matches:
        values = dict(
            fixture_id=m.fixture_id,
            group_name=m.group_name,
            home_team=m.home_team,
            away_team=m.away_team,
            home_score=m.home_score,
            away_score=m.away_score,
            status=m.status,
            elapsed=m.elapsed,
            kickoff_utc=m.kickoff_utc,
            stage=m.stage,
            updated_at=now,
        )
        set_ = dict(values)
        set_.pop("fixture_id")
        # Only write events_json when this payload actually carries events. The
        # daily collect fetches fixtures without events, so writing m.events
        # unconditionally would clobber events stored by the live poller/backfill.
        if m.events:
            values["events_json"] = m.events
            set_["events_json"] = m.events
        # Same clobber-guard for the once-only backfilled statistics + verdict:
        # only persist when this payload carries them (keep-last-good).
        if m.statistics:
            values["statistics_json"] = m.statistics
            set_["statistics_json"] = m.statistics
        if m.verdict_text:
            values["verdict_text"] = m.verdict_text
            set_["verdict_text"] = m.verdict_text
            values["verdict_model"] = m.verdict_model
            set_["verdict_model"] = m.verdict_model
        stmt = (
            pg_insert(matches_table)
            .values(**values)
            .on_conflict_do_update(index_elements=["fixture_id"], set_=set_)
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
            intelligence=article.get("intelligence"),
        )
        .on_conflict_do_update(
            index_elements=["brief_date"],
            set_={
                "title": article.get("title"),
                "summary": article.get("summary"),
                "body_md": article.get("body_md"),
                "status": status,
                "model_used": "deepseek-chat",
                "intelligence": article.get("intelligence"),
            },
        )
    )
    session.execute(stmt)
    session.commit()


# --- app_logs helpers ---------------------------------------------------------
# These run under the logging path (Phase 2 DBLogHandler). They MUST stay free of
# any logging calls, or a logged DB write would feed the handler and recurse.

def insert_log_rows(session: Session, rows: list[dict]) -> None:
    """Batch-insert log rows in a single statement. `rows` is a list of dicts
    keyed by app_logs columns (ts, level, source, message, context, run_id)."""
    if not rows:
        return
    session.execute(app_logs_table.insert(), rows)
    session.commit()


def query_logs(
    session: Session,
    *,
    levels: list[str] | None = None,
    q: str | None = None,
    source: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Any], int]:
    """Return (page_rows, total) for the logs console. Newest first.

    `levels` → `level IN (...)`; `q` → case-insensitive match across message and
    source; `source` → exact logger-name match. `total` reflects the same filters
    (ignoring limit/offset) so the UI can paginate."""
    conditions = []
    if levels:
        conditions.append(app_logs_table.c.level.in_(levels))
    if source:
        conditions.append(app_logs_table.c.source == source)
    if q:
        pattern = f"%{q}%"
        conditions.append(
            sa.or_(
                app_logs_table.c.message.ilike(pattern),
                app_logs_table.c.source.ilike(pattern),
            )
        )

    count_stmt = sa.select(sa.func.count()).select_from(app_logs_table)
    page_stmt = sa.select(app_logs_table)
    for cond in conditions:
        count_stmt = count_stmt.where(cond)
        page_stmt = page_stmt.where(cond)

    total = session.execute(count_stmt).scalar_one()
    rows = session.execute(
        page_stmt.order_by(app_logs_table.c.ts.desc(), app_logs_table.c.id.desc())
        .limit(limit)
        .offset(offset)
    ).fetchall()
    return list(rows), total


def prune_logs(session: Session, retention_days: int) -> int:
    """Delete log rows older than *retention_days*. Returns rows removed."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
    result = session.execute(
        app_logs_table.delete().where(app_logs_table.c.ts < cutoff)
    )
    session.commit()
    return result.rowcount or 0


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
