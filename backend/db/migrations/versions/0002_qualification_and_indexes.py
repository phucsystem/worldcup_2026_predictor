"""add qualification column and performance indexes

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("standings", sa.Column("qualification", sa.String(), nullable=True))
    op.create_index("ix_standings_snapshot_date", "standings", ["snapshot_date"])
    op.create_index("ix_articles_status_brief_date", "articles", ["status", "brief_date"])


def downgrade() -> None:
    op.drop_index("ix_articles_status_brief_date", table_name="articles")
    op.drop_index("ix_standings_snapshot_date", table_name="standings")
    op.drop_column("standings", "qualification")
