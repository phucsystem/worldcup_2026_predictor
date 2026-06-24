"""user feedback (supporter bot)

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("topic", sa.String(), nullable=True),  # bug | feature | other
        sa.Column("page", sa.String(), nullable=True),
        sa.Column(
            "status", sa.String(), server_default="new", nullable=False
        ),  # new | done | wont
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # Triage list orders by status then recency; this index serves it.
    op.create_index(
        "ix_feedback_status_created",
        "feedback",
        ["status", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_feedback_status_created", table_name="feedback")
    op.drop_table("feedback")
