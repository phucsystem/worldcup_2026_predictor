"""per-match pre-kickoff forecast

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable so existing rows and any caller that omits them round-trip
    # unchanged. Populated once per match by the daily forecast backfill.
    op.add_column("matches", sa.Column("forecast_json", sa.JSON(), nullable=True))
    op.add_column("matches", sa.Column("forecast_model", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "forecast_model")
    op.drop_column("matches", "forecast_json")
