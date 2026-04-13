"""add profile image fields to users

Revision ID: f1a2b3c4d5e6
Revises: e3f4a5b6c7d8
Create Date: 2026-04-12 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("profile_image_key", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("profile_image_content_type", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("profile_image_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "profile_image_updated_at")
    op.drop_column("users", "profile_image_content_type")
    op.drop_column("users", "profile_image_key")
