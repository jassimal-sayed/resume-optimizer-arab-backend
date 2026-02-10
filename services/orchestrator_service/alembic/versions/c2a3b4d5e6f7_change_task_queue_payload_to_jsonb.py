"""change_task_queue_payload_to_jsonb

Revision ID: c2a3b4d5e6f7
Revises: b1f2c3d4e5f6
Create Date: 2026-02-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'c2a3b4d5e6f7'
down_revision = 'b1f2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'task_queue',
        'payload',
        existing_type=sa.JSON(),
        type_=JSONB(),
        existing_nullable=False,
        postgresql_using='payload::jsonb',
    )


def downgrade() -> None:
    op.alter_column(
        'task_queue',
        'payload',
        existing_type=JSONB(),
        type_=sa.JSON(),
        existing_nullable=False,
        postgresql_using='payload::json',
    )
