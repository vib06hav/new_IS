"""add final report export fields

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-12 21:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("final_reports", sa.Column("export_key", sa.String(length=512), nullable=True))
    op.add_column("final_reports", sa.Column("export_content_type", sa.String(length=255), nullable=True))
    op.add_column("final_reports", sa.Column("export_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("final_reports", "export_updated_at")
    op.drop_column("final_reports", "export_content_type")
    op.drop_column("final_reports", "export_key")
