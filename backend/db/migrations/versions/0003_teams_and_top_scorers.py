"""teams + top_scorers tables and matches.stage

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `stage` lets the knockout endpoint group matches into rounds; without it,
    # knockout matches (group_name NULL) carry no round label.
    op.add_column("matches", sa.Column("stage", sa.String(), nullable=True))

    op.create_table(
        "teams",
        sa.Column("team_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("logo_url", sa.String()),
        sa.Column("group_name", sa.String()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("name", name="uq_teams_name"),
    )

    op.create_table(
        "top_scorers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String()),
        sa.Column("photo_url", sa.String()),
        sa.Column("team", sa.String()),
        sa.Column("goals", sa.Integer()),
        sa.UniqueConstraint("season", "player_id", name="uq_top_scorers_season_player"),
    )
    op.create_index("ix_top_scorers_season_goals", "top_scorers", ["season", "goals"])


def downgrade() -> None:
    op.drop_index("ix_top_scorers_season_goals", table_name="top_scorers")
    op.drop_table("top_scorers")
    op.drop_table("teams")
    op.drop_column("matches", "stage")
