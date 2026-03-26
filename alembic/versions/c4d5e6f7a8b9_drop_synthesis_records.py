"""drop_synthesis_records

Revision ID: c4d5e6f7a8b9
Revises: b3c1f2d4e5f6
Create Date: 2026-03-26 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b3c1f2d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("idx_synthesis_records_policy_passed", table_name="synthesis_records")
    op.drop_table("synthesis_records")


def downgrade() -> None:
    op.create_table(
        "synthesis_records",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("synthesis_output", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("policy_passed", sa.Boolean(), nullable=False),
        sa.Column("policy_violations_log", sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_synthesis_records"),
        sa.UniqueConstraint("application_id", name="uq_synthesis_records_application_id"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], name="fk_synthesis_records_application_id", onupdate="CASCADE", ondelete="CASCADE"),
        sa.CheckConstraint("policy_passed = TRUE AND policy_violations_log IS NULL OR policy_passed = FALSE", name="chk_synthesis_records_violations_consistency"),
    )
    op.create_index("idx_synthesis_records_policy_passed", "synthesis_records", ["policy_passed"], unique=False)
