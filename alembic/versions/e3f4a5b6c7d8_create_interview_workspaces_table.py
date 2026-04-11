"""create_interview_workspaces_table

Revision ID: e3f4a5b6c7d8
Revises: d1e2f3a4b5c6
Create Date: 2026-04-11 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_workspaces",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("interviewer_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("content", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("launched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interviewer_id"], ["users.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_interview_workspaces"),
        sa.UniqueConstraint("application_id", name="uq_interview_workspaces_application_id"),
    )


def downgrade() -> None:
    op.drop_table("interview_workspaces")
