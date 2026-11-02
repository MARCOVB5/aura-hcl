"""seed pathology types

Revision ID: c29e21f37eca
Revises: 4d2a4deaeb2c
Create Date: 2026-11-02 19:03:47.039546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c29e21f37eca'
down_revision: Union[str, Sequence[str], None] = '4d2a4deaeb2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pathology_type = sa.table("pathology_type",
      sa.column("code", sa.String), sa.column("label", sa.String)
    )
    op.bulk_insert(pathology_type, [{"code" : "ALLERGY", "label": "Allergy"}])


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM pathology_type WHERE code = 'ALLERGY'")
