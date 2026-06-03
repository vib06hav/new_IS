"""add prebuild feedback tables

Revision ID: a9b8c7d6e5f4
Revises: 0f1a2b3c4d5e
Create Date: 2026-05-20 17:40:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a9b8c7d6e5f4"
down_revision = "0f1a2b3c4d5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "theme_ratings",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("focus_area_id", sa.String(length=255), nullable=False),
        sa.Column("surface_role", sa.String(length=50), nullable=False),
        sa.Column("surface_phase", sa.String(length=50), nullable=False),
        sa.Column("rated_by_user_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["rated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", "focus_area_id", "rated_by_user_id", name="uq_theme_rating_actor"),
    )
    op.create_index(op.f("ix_theme_ratings_application_id"), "theme_ratings", ["application_id"], unique=False)
    op.create_index(op.f("ix_theme_ratings_rated_by_user_id"), "theme_ratings", ["rated_by_user_id"], unique=False)

    op.create_table(
        "question_generation_threads",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("focus_area_id", sa.String(length=255), nullable=False),
        sa.Column("base_question_id", sa.String(length=255), nullable=False),
        sa.Column("question_group_label_snapshot", sa.String(length=255), nullable=True),
        sa.Column("theme_title_snapshot", sa.String(length=255), nullable=True),
        sa.Column("theme_direction_snapshot", sa.String(length=2000), nullable=True),
        sa.Column("current_active_version_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "application_id",
            "focus_area_id",
            "base_question_id",
            name="uq_question_generation_thread_identity",
        ),
    )
    op.create_index(op.f("ix_question_generation_threads_application_id"), "question_generation_threads", ["application_id"], unique=False)
    op.create_index(op.f("ix_question_generation_threads_focus_area_id"), "question_generation_threads", ["focus_area_id"], unique=False)

    op.create_table(
        "question_generated_versions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("thread_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("focus_area_id", sa.String(length=255), nullable=False),
        sa.Column("base_question_id", sa.String(length=255), nullable=False),
        sa.Column("version_index", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(length=4000), nullable=False),
        sa.Column("generation_source", sa.String(length=50), nullable=False),
        sa.Column("generated_by_user_id", sa.UUID(), nullable=True),
        sa.Column("parent_version_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("theme_title_snapshot", sa.String(length=255), nullable=True),
        sa.Column("theme_direction_snapshot", sa.String(length=2000), nullable=True),
        sa.Column("question_group_label_snapshot", sa.String(length=255), nullable=True),
        sa.Column("application_context_snapshot", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("retrieval_context_snapshot", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["generated_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["thread_id"], ["question_generation_threads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_generated_versions_thread_id"), "question_generated_versions", ["thread_id"], unique=False)
    op.create_index(op.f("ix_question_generated_versions_application_id"), "question_generated_versions", ["application_id"], unique=False)
    op.create_index(op.f("ix_question_generated_versions_focus_area_id"), "question_generated_versions", ["focus_area_id"], unique=False)
    op.create_index(op.f("ix_question_generated_versions_base_question_id"), "question_generated_versions", ["base_question_id"], unique=False)

    op.create_table(
        "question_version_ratings",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("question_version_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("rated_by_user_id", sa.UUID(), nullable=False),
        sa.Column("surface_role", sa.String(length=50), nullable=False),
        sa.Column("surface_phase", sa.String(length=50), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["question_version_id"], ["question_generated_versions.id"]),
        sa.ForeignKeyConstraint(["rated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_version_id", "rated_by_user_id", name="uq_question_version_rating_actor"),
    )
    op.create_index(op.f("ix_question_version_ratings_question_version_id"), "question_version_ratings", ["question_version_id"], unique=False)
    op.create_index(op.f("ix_question_version_ratings_application_id"), "question_version_ratings", ["application_id"], unique=False)
    op.create_index(op.f("ix_question_version_ratings_rated_by_user_id"), "question_version_ratings", ["rated_by_user_id"], unique=False)

    op.create_table(
        "vector_corpus_documents",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("document_text", sa.String(length=8000), nullable=False),
        sa.Column("token_vector", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("metadata", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_type", "entity_id", name="uq_vector_corpus_entity"),
    )
    op.create_index(op.f("ix_vector_corpus_documents_entity_type"), "vector_corpus_documents", ["entity_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vector_corpus_documents_entity_type"), table_name="vector_corpus_documents")
    op.drop_table("vector_corpus_documents")

    op.drop_index(op.f("ix_question_version_ratings_rated_by_user_id"), table_name="question_version_ratings")
    op.drop_index(op.f("ix_question_version_ratings_application_id"), table_name="question_version_ratings")
    op.drop_index(op.f("ix_question_version_ratings_question_version_id"), table_name="question_version_ratings")
    op.drop_table("question_version_ratings")

    op.drop_index(op.f("ix_question_generated_versions_base_question_id"), table_name="question_generated_versions")
    op.drop_index(op.f("ix_question_generated_versions_focus_area_id"), table_name="question_generated_versions")
    op.drop_index(op.f("ix_question_generated_versions_application_id"), table_name="question_generated_versions")
    op.drop_index(op.f("ix_question_generated_versions_thread_id"), table_name="question_generated_versions")
    op.drop_table("question_generated_versions")

    op.drop_index(op.f("ix_question_generation_threads_focus_area_id"), table_name="question_generation_threads")
    op.drop_index(op.f("ix_question_generation_threads_application_id"), table_name="question_generation_threads")
    op.drop_table("question_generation_threads")

    op.drop_index(op.f("ix_theme_ratings_rated_by_user_id"), table_name="theme_ratings")
    op.drop_index(op.f("ix_theme_ratings_application_id"), table_name="theme_ratings")
    op.drop_table("theme_ratings")
