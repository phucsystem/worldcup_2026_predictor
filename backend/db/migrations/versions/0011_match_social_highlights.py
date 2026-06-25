"""per-match social discussion highlights

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable so existing rows and any caller that omits them round-trip
    # unchanged. Refreshed daily for upcoming fixtures by the social backfill.
    op.add_column("matches", sa.Column("social_json", sa.JSON(), nullable=True))
    op.add_column("matches", sa.Column("social_model", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "social_model")
    op.drop_column("matches", "social_json")
