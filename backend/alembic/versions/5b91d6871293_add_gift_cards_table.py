"""add_gift_cards_table

Revision ID: 5b91d6871293
Revises: a1b2c3d4e5f6
Create Date: 2026-05-27 16:21:14.703002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5b91d6871293'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'gift_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('card_code', sa.String(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=True, default=False),
        sa.Column('used_by_user_id', sa.Integer(), nullable=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gift_cards_card_code'), 'gift_cards', ['card_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_gift_cards_card_code'), table_name='gift_cards')
    op.drop_table('gift_cards')
