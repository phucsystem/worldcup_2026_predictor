"""match statistics + per-match verdict

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All nullable so existing rows and any caller that omits them round-trip
    # unchanged. Populated once per finished match by the daily backfill.
    op.add_column("matches", sa.Column("statistics_json", sa.JSON(), nullable=True))
    op.add_column("matches", sa.Column("verdict_text", sa.Text(), nullable=True))
    op.add_column("matches", sa.Column("verdict_model", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "verdict_model")
    op.drop_column("matches", "verdict_text")
    op.drop_column("matches", "statistics_json")
