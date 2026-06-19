"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("group_name", sa.String(), nullable=True),
        sa.Column("home_team", sa.String(), nullable=True),
        sa.Column("away_team", sa.String(), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("kickoff_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("events_json", JSONB(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fixture_id"),
    )

    op.create_table(
        "standings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=True),
        sa.Column("group_name", sa.String(), nullable=True),
        sa.Column("team", sa.String(), nullable=True),
        sa.Column("played", sa.Integer(), nullable=True),
        sa.Column("won", sa.Integer(), nullable=True),
        sa.Column("drawn", sa.Integer(), nullable=True),
        sa.Column("lost", sa.Integer(), nullable=True),
        sa.Column("gf", sa.Integer(), nullable=True),
        sa.Column("ga", sa.Integer(), nullable=True),
        sa.Column("gd", sa.Integer(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("prev_position", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_date", "group_name", "team", name="uq_standings_snapshot"),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("brief_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body_md", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="draft", nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brief_date"),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(), nullable=True),
        sa.Column("brief_date", sa.Date(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("node_timings", JSONB(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("agent_runs")
    op.drop_table("articles")
    op.drop_table("standings")
    op.drop_table("matches")
