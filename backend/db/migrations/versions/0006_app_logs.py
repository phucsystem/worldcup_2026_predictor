"""app_logs line-level log events

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", JSONB(), nullable=True),
        sa.Column("run_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_app_logs_ts", "app_logs", [sa.text("ts DESC")])
    op.create_index("ix_app_logs_level", "app_logs", ["level"])


def downgrade() -> None:
    op.drop_index("ix_app_logs_level", table_name="app_logs")
    op.drop_index("ix_app_logs_ts", table_name="app_logs")
    op.drop_table("app_logs")
