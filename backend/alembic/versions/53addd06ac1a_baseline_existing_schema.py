"""baseline existing schema

Revision ID: 53addd06ac1a
Revises: 
Create Date: 2026-05-26 16:10:16.016595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '53addd06ac1a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
