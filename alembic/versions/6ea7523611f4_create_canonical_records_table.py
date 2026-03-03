"""create_canonical_records_table

Revision ID: 6ea7523611f4
Revises: a3ba4d865b1f
Create Date: 2026-03-02 01:11:41.724157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ea7523611f4'
down_revision: Union[str, Sequence[str], None] = 'a3ba4d865b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'canonical_records',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('canonical_version', sa.String(length=20), nullable=False),
        sa.Column('canonical_data', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_canonical_records'),
        sa.UniqueConstraint('application_id', name='uq_canonical_records_application_id'),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], name='fk_canonical_records_application_id', onupdate='CASCADE', ondelete='CASCADE'),
        sa.CheckConstraint("canonical_version ~ '^\\d+\\.\\d+$'", name='chk_canonical_records_version_format')
    )
    op.create_index('idx_canonical_records_version', 'canonical_records', ['canonical_version'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    import logging
    import sqlalchemy as sa
    logger = logging.getLogger('alembic.runtime.migration')
    conn = op.get_bind()
    
    try:
        exists_query = sa.text("SELECT exists(SELECT 1 from information_schema.tables where table_schema='public' AND table_name='canonical_records')")
        if conn.execute(exists_query).scalar():
            result = conn.execute(sa.text("SELECT COUNT(*) FROM canonical_records")).scalar()
            if result and result > 0:
                logger.warning("Table 'canonical_records' contains rows. Refusing to drop during downgrade.")
                return
    except Exception as e:
        logger.warning(f"Error checking table empty status: {e}")
        pass
        
    op.drop_index('idx_canonical_records_version', table_name='canonical_records')
    op.drop_table('canonical_records')
