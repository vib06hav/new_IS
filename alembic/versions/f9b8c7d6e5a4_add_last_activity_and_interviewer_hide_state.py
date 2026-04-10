"""add_last_activity_and_interviewer_hide_state

Revision ID: f9b8c7d6e5a4
Revises: f7a9c1d2e3b4
Create Date: 2026-04-09 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9b8c7d6e5a4"
down_revision: Union[str, Sequence[str], None] = "a8b7c6d5e4f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "applications",
        sa.Column("last_activity_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.execute("UPDATE applications SET last_activity_at = created_at")
    op.alter_column("applications", "last_activity_at", server_default=None)

    op.add_column(
        "assignments",
        sa.Column("is_hidden_for_interviewer", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
    )
    op.alter_column("assignments", "is_hidden_for_interviewer", server_default=None)


def downgrade() -> None:
    op.drop_column("assignments", "is_hidden_for_interviewer")
    op.drop_column("applications", "last_activity_at")
