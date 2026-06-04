"""add question role and version why this

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-05-20 21:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "question_generation_threads",
        sa.Column("question_role", sa.String(length=2000), nullable=True),
    )
    op.add_column(
        "question_generated_versions",
        sa.Column("why_this", sa.String(length=2000), nullable=True),
    )

    op.execute(
        """
        UPDATE question_generation_threads
        SET question_role = COALESCE(
            NULLIF(theme_direction_snapshot, ''),
            'Preserve the original question role for this thread.'
        )
        WHERE question_role IS NULL
        """
    )
    op.alter_column("question_generation_threads", "question_role", nullable=False)


def downgrade() -> None:
    op.drop_column("question_generated_versions", "why_this")
    op.drop_column("question_generation_threads", "question_role")
