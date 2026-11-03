"""location as free text

Revision ID: 2b5cf70ca236
Revises: 7b01cabb0a1f
Create Date: 2026-11-03 10:33:08.797763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '2b5cf70ca236'
down_revision: Union[str, Sequence[str], None] = '7b01cabb0a1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# the beds seeded by 7b01cabb0a1f, put back by the downgrade
BEDS = [
    {"code": f"REA-{room}-{bed}", "name": f"Réanimation · Chambre {room} · Lit {bed}"}
    for room in range(10, 15)
    for bed in ("A", "B")
]


def upgrade() -> None:
    """Upgrade schema."""
    # the location of a stay becomes free text: the name of its bed is kept as that text
    op.add_column('encounter', sa.Column('location', sa.String(length=128), nullable=True))
    op.execute(
        "UPDATE encounter SET location = "
        "(SELECT name FROM location WHERE location.id = encounter.current_location_id) "
        "WHERE current_location_id IS NOT NULL"
    )
    op.drop_constraint('fk_encounter_location', 'encounter', type_='foreignkey')
    op.drop_column('encounter', 'current_location_id')
    op.drop_table('location')


def downgrade() -> None:
    """Downgrade schema."""
    location = op.create_table(
        'location',
        sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.bulk_insert(location, BEDS)
    # a location typed freely becomes a row of its own
    bind = op.get_bind()
    beds = {bed["name"] for bed in BEDS}
    typed = bind.execute(sa.text(
        "SELECT DISTINCT location FROM encounter WHERE location IS NOT NULL"
    )).scalars()
    others = [name for name in typed if name not in beds]
    op.bulk_insert(location, [{"code": f"LIBRE-{i}", "name": name} for i, name in enumerate(others, 1)])

    op.add_column('encounter', sa.Column('current_location_id', mysql.BIGINT(unsigned=True), nullable=True))
    op.create_foreign_key('fk_encounter_location', 'encounter', 'location', ['current_location_id'], ['id'])
    op.execute(
        "UPDATE encounter SET current_location_id = "
        "(SELECT id FROM location WHERE location.name = encounter.location) "
        "WHERE location IS NOT NULL"
    )
    op.drop_column('encounter', 'location')
