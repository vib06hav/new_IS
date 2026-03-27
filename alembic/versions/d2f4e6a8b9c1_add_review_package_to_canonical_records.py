"""add_review_package_to_canonical_records

Revision ID: d2f4e6a8b9c1
Revises: c4d5e6f7a8b9
Create Date: 2026-03-27 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2f4e6a8b9c1"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "canonical_records",
        sa.Column(
            "deterministic_signals",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
    )
    op.add_column(
        "canonical_records",
        sa.Column(
            "pages_1_3",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("canonical_records", "pages_1_3")
    op.drop_column("canonical_records", "deterministic_signals")
