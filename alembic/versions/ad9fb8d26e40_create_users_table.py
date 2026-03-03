"""create_users_table

Revision ID: ad9fb8d26e40
Revises: fe57dd6ef27e
Create Date: 2026-03-02 01:10:46.790003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad9fb8d26e40'
down_revision: Union[str, Sequence[str], None] = 'fe57dd6ef27e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.CheckConstraint("role IN ('admin', 'interviewer')", name='chk_users_role')
    )


def downgrade() -> None:
    """Downgrade schema."""
    import logging
    import sqlalchemy as sa
    logger = logging.getLogger('alembic.runtime.migration')
    conn = op.get_bind()
    
    try:
        exists_query = sa.text("SELECT exists(SELECT 1 from information_schema.tables where table_schema='public' AND table_name='users')")
        if conn.execute(exists_query).scalar():
            result = conn.execute(sa.text("SELECT COUNT(*) FROM users")).scalar()
            if result and result > 0:
                logger.warning("Table 'users' contains rows. Refusing to drop during downgrade.")
                return
    except Exception as e:
        logger.warning(f"Error checking table empty status: {e}")
        pass
        
    op.drop_table('users')
