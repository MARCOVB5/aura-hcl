"""remove mockup practitioners

Revision ID: 8c73e914fc14
Revises: be1ac16bf25c
Create Date: 2026-11-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c73e914fc14'
down_revision: Union[str, Sequence[str], None] = 'be1ac16bf25c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# the staff of the mock-ups seeded by 7b01cabb0a1f: the demo accounts of
# scripts/populate_practitioners.py replace them
PRACTITIONERS = [
    ("Azerty", "Bruno", "Médecin"),
    ("Armand", "Simon", "Médecin"),
    ("Raoult", "Benoit", "Médecin"),
    ("Merveille", "Alice", "Infirmière"),
    ("Meurice", "Guillaume", "Infirmier"),
    ("Jeuneve", "Letitia", "Infirmière"),
]

person = sa.table(
    "person",
    sa.column("id", sa.BigInteger),
    sa.column("name_family", sa.String),
    sa.column("name_given", sa.String),
)
practitioner = sa.table(
    "practitioner",
    sa.column("id", sa.BigInteger),
    sa.column("person_id", sa.BigInteger),
    sa.column("profession", sa.String),
)
app_user = sa.table("app_user", sa.column("practitioner_id", sa.BigInteger))
appointment = sa.table("appointment", sa.column("validated_by_id", sa.BigInteger))
appointment_performer = sa.table(
    "appointment_performer", sa.column("practitioner_id", sa.BigInteger)
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    for family, given, _ in PRACTITIONERS:
        rows = bind.execute(
            sa.select(practitioner.c.id, practitioner.c.person_id)
            .join(person, person.c.id == practitioner.c.person_id)
            .where(person.c.name_family == family, person.c.name_given == given)
            # someone who logs in with this name is a real user: kept
            .where(~sa.exists().where(app_user.c.practitioner_id == practitioner.c.id))
        ).all()
        for practitioner_id, person_id in rows:
            # their care stays, without them as caregiver or prescriber
            bind.execute(appointment_performer.delete().where(
                appointment_performer.c.practitioner_id == practitioner_id
            ))
            bind.execute(appointment.update()
                         .where(appointment.c.validated_by_id == practitioner_id)
                         .values(validated_by_id=None))
            bind.execute(practitioner.delete().where(practitioner.c.id == practitioner_id))
            bind.execute(person.delete().where(person.c.id == person_id))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    for family, given, profession in PRACTITIONERS:
        exists = bind.execute(
            sa.select(practitioner.c.id)
            .join(person, person.c.id == practitioner.c.person_id)
            .where(person.c.name_family == family, person.c.name_given == given)
        ).first()
        if exists:
            continue
        result = bind.execute(person.insert().values(name_family=family, name_given=given))
        bind.execute(practitioner.insert().values(person_id=result.lastrowid, profession=profession))
