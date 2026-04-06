"""add_display_id_to_applications

Revision ID: a8b7c6d5e4f3
Revises: f7a9c1d2e3b4
Create Date: 2026-04-04 18:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8b7c6d5e4f3"
down_revision: Union[str, Sequence[str], None] = "f7a9c1d2e3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("display_id", sa.String(length=255), nullable=True))
    op.execute(
        r"""
        UPDATE applications
        SET display_id = regexp_replace(
            regexp_replace(file_path, '^.*[\\/]', ''),
            '\.pdf$',
            '',
            'i'
        )
        """
    )
    op.alter_column("applications", "display_id", nullable=False)
    op.create_unique_constraint("uq_applications_display_id", "applications", ["display_id"])


def downgrade() -> None:
    op.drop_constraint("uq_applications_display_id", "applications", type_="unique")
    op.drop_column("applications", "display_id")
