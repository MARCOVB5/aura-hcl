"""merge location text and user accounts

Revision ID: be1ac16bf25c
Revises: 2b5cf70ca236, a82f964b1d30
Create Date: 2026-11-03 11:05:37.100750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be1ac16bf25c'
down_revision: Union[str, Sequence[str], None] = ('2b5cf70ca236', 'a82f964b1d30')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
