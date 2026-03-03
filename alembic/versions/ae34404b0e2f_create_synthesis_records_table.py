"""create_synthesis_records_table

Revision ID: ae34404b0e2f
Revises: 6ea7523611f4
Create Date: 2026-03-02 01:12:25.021293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae34404b0e2f'
down_revision: Union[str, Sequence[str], None] = '6ea7523611f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'synthesis_records',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('synthesis_output', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('policy_passed', sa.Boolean(), nullable=False),
        sa.Column('policy_violations_log', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_synthesis_records'),
        sa.UniqueConstraint('application_id', name='uq_synthesis_records_application_id'),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], name='fk_synthesis_records_application_id', onupdate='CASCADE', ondelete='CASCADE'),
        sa.CheckConstraint("policy_passed = TRUE AND policy_violations_log IS NULL OR policy_passed = FALSE", name='chk_synthesis_records_violations_consistency')
    )
    op.create_index('idx_synthesis_records_policy_passed', 'synthesis_records', ['policy_passed'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    import logging
    import sqlalchemy as sa
    logger = logging.getLogger('alembic.runtime.migration')
    conn = op.get_bind()
    
    try:
        exists_query = sa.text("SELECT exists(SELECT 1 from information_schema.tables where table_schema='public' AND table_name='synthesis_records')")
        if conn.execute(exists_query).scalar():
            result = conn.execute(sa.text("SELECT COUNT(*) FROM synthesis_records")).scalar()
            if result and result > 0:
                logger.warning("Table 'synthesis_records' contains rows. Refusing to drop during downgrade.")
                return
    except Exception as e:
        logger.warning(f"Error checking table empty status: {e}")
        pass
        
    op.drop_index('idx_synthesis_records_policy_passed', table_name='synthesis_records')
    op.drop_table('synthesis_records')
