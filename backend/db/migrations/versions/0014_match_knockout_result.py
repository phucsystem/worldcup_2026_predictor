"""match knockout result — winner_side + penalty shootout score

Captures who advanced from a knockout tie (winner_side, from API-Football's
teams.winner flag) and the penalty-shootout score (home_pen/away_pen), so the
bracket can resolve a winner for matches decided in extra time or on penalties.

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("winner_side", sa.String(), nullable=True))
    op.add_column("matches", sa.Column("home_pen", sa.Integer(), nullable=True))
    op.add_column("matches", sa.Column("away_pen", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "away_pen")
    op.drop_column("matches", "home_pen")
    op.drop_column("matches", "winner_side")
