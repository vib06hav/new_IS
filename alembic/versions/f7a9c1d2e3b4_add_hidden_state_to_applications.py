"""add_hidden_state_to_applications

Revision ID: f7a9c1d2e3b4
Revises: d2f4e6a8b9c1
Create Date: 2026-03-30 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7a9c1d2e3b4"
down_revision: Union[str, Sequence[str], None] = "d2f4e6a8b9c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "applications",
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
    )
    op.alter_column("applications", "is_hidden", server_default=None)


def downgrade() -> None:
    op.drop_column("applications", "is_hidden")
