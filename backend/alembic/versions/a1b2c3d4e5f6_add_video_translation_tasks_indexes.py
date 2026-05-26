"""add video translation tasks indexes for performance

Revision ID: a1b2c3d4e5f6
Revises: 4a7102af09c7
Create Date: 2026-05-26 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4a7102af09c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite index on (user_id, created_at DESC) for efficient pagination
    op.create_index(
        'ix_video_translation_tasks_user_created',
        'video_translation_tasks',
        ['user_id', sa.text('created_at DESC')],
        unique=False
    )

    # Add index on is_auto for filtering
    op.create_index(
        'ix_video_translation_tasks_is_auto',
        'video_translation_tasks',
        ['is_auto'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_video_translation_tasks_is_auto', table_name='video_translation_tasks')
    op.drop_index('ix_video_translation_tasks_user_created', table_name='video_translation_tasks')
