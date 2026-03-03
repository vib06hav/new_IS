"""enable_uuid_extension

Revision ID: fe57dd6ef27e
Revises: 
Create Date: 2026-03-02 00:49:39.722766

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe57dd6ef27e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')


def downgrade() -> None:
    """Downgrade schema."""
    import logging
    import sqlalchemy as sa
    logger = logging.getLogger('alembic.runtime.migration')
    conn = op.get_bind()
    
    # UUID extension downgrade constraint checking logic
    # Checks if tables exist and have > 0 rows
    tables_to_check = ["users", "applications", "canonical_records", "synthesis_records"]
    
    for table in tables_to_check:
        exists_query = sa.text(f"SELECT exists(SELECT 1 from information_schema.tables where table_schema='public' AND table_name='{table}')")
        if conn.execute(exists_query).scalar():
            result = conn.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()
            if result and result > 0:
                logger.warning(f"UUID-keyed table '{table}' contains rows. Refusing to drop uuid-ossp extension.")
                return

    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')
