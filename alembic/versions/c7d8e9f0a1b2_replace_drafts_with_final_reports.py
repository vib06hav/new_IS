"""replace_drafts_with_final_reports

Revision ID: c7d8e9f0a1b2
Revises: f9b8c7d6e5a4
Create Date: 2026-04-11 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "f9b8c7d6e5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "final_reports",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("generated_by", sa.UUID(), nullable=False),
        sa.Column("report_version", sa.String(length=50), nullable=False, server_default="ROS_v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], onupdate="CASCADE", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"], onupdate="CASCADE", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_final_reports"),
        sa.UniqueConstraint("application_id", name="uq_final_reports_application_id"),
    )

    op.execute(
        """
        INSERT INTO final_reports (application_id, content, generated_by, report_version, created_at)
        SELECT ranked.application_id,
               ranked.content,
               ranked.generated_by,
               COALESCE(ranked.content->'report_metadata'->>'report_version', 'ROS_v1') AS report_version,
               ranked.created_at
        FROM (
            SELECT d.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY d.application_id
                       ORDER BY d.is_published DESC, d.version DESC, d.created_at DESC
                   ) AS row_num
            FROM drafts d
        ) ranked
        WHERE ranked.row_num = 1
        """
    )

    op.execute(
        """
        UPDATE applications
        SET status = CASE
            WHEN status IN ('DRAFT', 'PUBLISHED') THEN 'COMPLETE'
            ELSE status
        END
        """
    )

    op.drop_table("drafts")


def downgrade() -> None:
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

    op.execute(
        """
        INSERT INTO drafts (application_id, version, content, generated_by, is_published, created_at)
        SELECT application_id,
               1 AS version,
               content,
               generated_by,
               TRUE AS is_published,
               created_at
        FROM final_reports
        """
    )

    op.execute(
        """
        UPDATE applications
        SET status = CASE
            WHEN status = 'COMPLETE' THEN 'PUBLISHED'
            ELSE status
        END
        """
    )

    op.drop_table("final_reports")
