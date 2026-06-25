"""live read + hybrid live win-probability fields on matches

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # All nullable so existing rows and any caller that omits them round-trip
    # unchanged. Populated on the live-poll path for in-play group-stage matches.
    # live_winprob_json: the final hybrid split (base + bounded AI adjustment).
    # live_winprob_adj_json: the agent's bounded per-outcome delta, re-applied each poll.
    # live_winprob_history_json: the swing-chart series (one point per significant event).
    # live_read_text/model/sig: the AI live read + producing model + event signature.
    op.add_column("matches", sa.Column("live_winprob_json", sa.JSON(), nullable=True))
    op.add_column("matches", sa.Column("live_winprob_adj_json", sa.JSON(), nullable=True))
    op.add_column("matches", sa.Column("live_winprob_history_json", sa.JSON(), nullable=True))
    op.add_column("matches", sa.Column("live_read_text", sa.Text(), nullable=True))
    op.add_column("matches", sa.Column("live_read_model", sa.String(), nullable=True))
    op.add_column("matches", sa.Column("live_read_sig", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "live_read_sig")
    op.drop_column("matches", "live_read_model")
    op.drop_column("matches", "live_read_text")
    op.drop_column("matches", "live_winprob_history_json")
    op.drop_column("matches", "live_winprob_adj_json")
    op.drop_column("matches", "live_winprob_json")
