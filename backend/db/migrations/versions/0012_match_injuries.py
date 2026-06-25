"""per-match injury / doubtful player list

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable so existing rows round-trip unchanged. Refreshed each collect for
    # upcoming fixtures from API-Football /injuries; absent on a plan without
    # injury coverage, so the panel degrades to "no injuries" rather than erroring.
    op.add_column("matches", sa.Column("injuries_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "injuries_json")
