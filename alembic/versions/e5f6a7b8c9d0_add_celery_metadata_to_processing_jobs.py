"""add celery metadata to processing jobs

Revision ID: e5f6a7b8c9d0
Revises: b1c2d3e4f5a6
Create Date: 2026-06-08 19:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("processing_jobs", sa.Column("celery_task_id", sa.String(length=255), nullable=True))
    op.add_column("processing_jobs", sa.Column("queue_name", sa.String(length=100), nullable=True))
    op.add_column("processing_jobs", sa.Column("progress", sa.Float(), nullable=False, server_default="0"))
    op.add_column("processing_jobs", sa.Column("error_code", sa.String(length=100), nullable=True))
    op.create_index(op.f("ix_processing_jobs_celery_task_id"), "processing_jobs", ["celery_task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_processing_jobs_celery_task_id"), table_name="processing_jobs")
    op.drop_column("processing_jobs", "error_code")
    op.drop_column("processing_jobs", "progress")
    op.drop_column("processing_jobs", "queue_name")
    op.drop_column("processing_jobs", "celery_task_id")
