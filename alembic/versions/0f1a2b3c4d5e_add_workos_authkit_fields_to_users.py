"""add workos authkit fields to users

Revision ID: 0f1a2b3c4d5e
Revises: d4e5f6a7b8c0
Create Date: 2026-04-19 17:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0f1a2b3c4d5e"
down_revision = "d4e5f6a7b8c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("access_status", sa.String(length=50), nullable=False, server_default="active"))
    op.add_column("users", sa.Column("workos_user_id", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("provider_profile_image_url", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("last_sign_in_at", sa.DateTime(), nullable=True))
    op.create_unique_constraint("uq_users_workos_user_id", "users", ["workos_user_id"])

    op.drop_column("users", "profile_image_updated_at")
    op.drop_column("users", "profile_image_content_type")
    op.drop_column("users", "profile_image_key")


def downgrade() -> None:
    op.add_column("users", sa.Column("profile_image_key", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("profile_image_content_type", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("profile_image_updated_at", sa.DateTime(), nullable=True))

    op.drop_constraint("uq_users_workos_user_id", "users", type_="unique")
    op.drop_column("users", "last_sign_in_at")
    op.drop_column("users", "provider_profile_image_url")
    op.drop_column("users", "workos_user_id")
    op.drop_column("users", "access_status")
