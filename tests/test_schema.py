from sqlalchemy import create_engine, inspect
import sys
from app.config import settings

def test_schema():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    required = {"users", "applications", "canonical_records", "synthesis_records"}
    actual_custom_tables = set(tables) - {"alembic_version"}

    assert actual_custom_tables == required, f"Found tables: {actual_custom_tables}"

    # users type
    users_cols = {col['name']: col for col in inspector.get_columns('users')}
    assert str(users_cols['id']['type']) == 'UUID'
    
    # check keys users
    user_pk = inspector.get_pk_constraint('users')
    assert user_pk['name'] == 'pk_users'
    assert user_pk['constrained_columns'] == ['id']

    app_fks = inspector.get_foreign_keys('applications')
    assert len(app_fks) == 1
    fk = app_fks[0]
    assert fk['constrained_columns'] == ['uploaded_by']
    assert fk['referred_table'] == 'users'
    assert fk['options']['ondelete'] == 'RESTRICT'
    assert fk['options']['onupdate'] == 'CASCADE'

    app_cols = {col['name']: col for col in inspector.get_columns('applications')}
    assert str(app_cols['pipeline_confidence']['type']).startswith('NUMERIC(5, 4)')

    can_fks = inspector.get_foreign_keys('canonical_records')
    assert can_fks[0]['options']['ondelete'] == 'CASCADE'

    syn_fks = inspector.get_foreign_keys('synthesis_records')
    assert syn_fks[0]['options']['ondelete'] == 'CASCADE'

    # jsons
    can_cols = {col['name']: col for col in inspector.get_columns('canonical_records')}
    assert str(can_cols['canonical_data']['type']) == 'JSONB'

    syn_cols = {col['name']: col for col in inspector.get_columns('synthesis_records')}
    assert str(syn_cols['synthesis_output']['type']) == 'JSONB'

    print("All Phase 4 schema validations passed.")

if __name__ == "__main__":
    test_schema()
