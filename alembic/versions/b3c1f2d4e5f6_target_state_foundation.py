"""target_state_foundation

Revision ID: b3c1f2d4e5f6
Revises: ae34404b0e2f
Create Date: 2026-03-26 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3c1f2d4e5f6"
down_revision: Union[str, Sequence[str], None] = "ae34404b0e2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=255), nullable=True, server_default=""))
    op.execute("UPDATE users SET name = COALESCE(NULLIF(email, ''), 'Unknown User') WHERE name = ''")
    op.alter_column("users", "name", server_default=None, nullable=False)

    op.add_column("applications", sa.Column("status", sa.String(length=50), nullable=True, server_default="UPLOADED"))
    op.execute(
        """
        UPDATE applications
        SET status = CASE pipeline_status
            WHEN 'processing' THEN 'PROCESSING'
            WHEN 'complete' THEN 'READY'
            WHEN 'failed' THEN 'FAILED'
            ELSE 'UPLOADED'
        END
        """
    )
    op.alter_column("applications", "status", server_default=None, nullable=False)
    op.drop_constraint("chk_applications_pipeline_status", "applications", type_="check")
    op.drop_constraint("chk_applications_pipeline_confidence", "applications", type_="check")
    op.drop_column("applications", "pipeline_confidence")
    op.drop_column("applications", "pipeline_status")

    op.create_table(
        "assignments",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("interviewer_id", sa.UUID(), nullable=False),
        sa.Column("assigned_by", sa.UUID(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interviewer_id"], ["users.id"], onupdate="CASCADE", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], onupdate="CASCADE", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_assignments"),
        sa.UniqueConstraint("application_id", name="uq_assignments_application_id"),
    )

    op.create_table(
        "drafts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("generated_by", sa.UUID(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"], onupdate="CASCADE", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_drafts"),
        sa.UniqueConstraint("application_id", "version", name="uq_drafts_application_version"),
    )


def downgrade() -> None:
    op.drop_table("drafts")
    op.drop_table("assignments")

    op.add_column("applications", sa.Column("pipeline_confidence", sa.Numeric(precision=5, scale=4), nullable=True))
    op.add_column(
        "applications",
        sa.Column("pipeline_status", sa.String(length=50), nullable=False, server_default="processing"),
    )
    op.execute(
        """
        UPDATE applications
        SET pipeline_status = CASE status
            WHEN 'PROCESSING' THEN 'processing'
            WHEN 'READY' THEN 'complete'
            WHEN 'FAILED' THEN 'failed'
            WHEN 'ASSIGNED' THEN 'complete'
            WHEN 'DRAFT' THEN 'complete'
            WHEN 'PUBLISHED' THEN 'complete'
            ELSE 'processing'
        END
        """
    )
    op.drop_column("applications", "status")
    op.create_check_constraint(
        "chk_applications_pipeline_status",
        "applications",
        "pipeline_status IN ('processing', 'complete', 'failed')",
    )
    op.create_check_constraint(
        "chk_applications_pipeline_confidence",
        "applications",
        "pipeline_confidence IS NULL OR (pipeline_confidence >= 0.0000 AND pipeline_confidence <= 1.0000)",
    )

    op.drop_column("users", "name")
