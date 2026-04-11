"""restore_last_activity_default

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-04-11 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "applications",
        "last_activity_at",
        existing_type=sa.DateTime(),
        server_default=sa.text("NOW()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "applications",
        "last_activity_at",
        existing_type=sa.DateTime(),
        server_default=None,
        existing_nullable=False,
    )
