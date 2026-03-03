"""create_applications_table

Revision ID: a3ba4d865b1f
Revises: ad9fb8d26e40
Create Date: 2026-03-02 01:11:16.106806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3ba4d865b1f'
down_revision: Union[str, Sequence[str], None] = 'ad9fb8d26e40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'applications',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('uploaded_by', sa.UUID(), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('pipeline_status', sa.String(length=50), server_default='processing', nullable=False),
        sa.Column('pipeline_confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_applications'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name='fk_applications_uploaded_by', onupdate='CASCADE', ondelete='RESTRICT'),
        sa.CheckConstraint("pipeline_status IN ('processing', 'complete', 'failed')", name='chk_applications_pipeline_status'),
        sa.CheckConstraint("pipeline_confidence IS NULL OR (pipeline_confidence >= 0.0000 AND pipeline_confidence <= 1.0000)", name='chk_applications_pipeline_confidence')
    )
    op.create_index('idx_applications_uploaded_by', 'applications', ['uploaded_by'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    import logging
    import sqlalchemy as sa
    logger = logging.getLogger('alembic.runtime.migration')
    conn = op.get_bind()
    
    try:
        exists_query = sa.text("SELECT exists(SELECT 1 from information_schema.tables where table_schema='public' AND table_name='applications')")
        if conn.execute(exists_query).scalar():
            result = conn.execute(sa.text("SELECT COUNT(*) FROM applications")).scalar()
            if result and result > 0:
                logger.warning("Table 'applications' contains rows. Refusing to drop during downgrade.")
                return
    except Exception as e:
        logger.warning(f"Error checking table empty status: {e}")
        pass
        
    op.drop_index('idx_applications_uploaded_by', table_name='applications')
    op.drop_table('applications')
