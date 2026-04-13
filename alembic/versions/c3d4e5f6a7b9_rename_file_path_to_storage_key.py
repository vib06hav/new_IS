"""rename file_path to storage_key

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-04-12 22:45:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b9"
down_revision = "b2c3d4e5f6a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("applications", "file_path", new_column_name="storage_key")


def downgrade() -> None:
    op.alter_column("applications", "storage_key", new_column_name="file_path")
