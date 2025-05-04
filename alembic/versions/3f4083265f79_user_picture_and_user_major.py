"""Add User_Picture and User_Major columns to User table

Revision ID: 3f4083265f79
Revises: edbfdd8f2c5c
Create Date: 2025-05-04 23:06:22.183430
"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '3f4083265f79'
down_revision: Union[str, None] = 'edbfdd8f2c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema: add new columns to User table."""
    op.add_column('User', sa.Column('User_Picture', sa.String(length=255), nullable=True))
    op.add_column('User', sa.Column('User_Major', sa.String(length=255), nullable=True))

def downgrade() -> None:
    """Downgrade schema: remove added columns from User table."""
    op.drop_column('User', 'User_Major')
    op.drop_column('User', 'User_Picture')
