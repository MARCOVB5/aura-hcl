"""seed locations, care types and practitioners

Revision ID: 7b01cabb0a1f
Revises: eb2d51b6c7d7
Create Date: 2026-11-02 19:57:46.546471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b01cabb0a1f'
down_revision: Union[str, Sequence[str], None] = 'eb2d51b6c7d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# rooms of the department: 5 rooms with 2 beds each
LOCATIONS = [
    {"code": f"REA-{room}-{bed}", "name": f"Réanimation · Chambre {room} · Lit {bed}"}
    for room in range(10, 15)
    for bed in ("A", "B")
]

# kinds of care, from the care list of the design and the project brief
CARE_TYPES = [
    ("PRISE_SANG", "Prise de sang"),
    ("EVAL_CLINIQUE", "Évaluation clinique"),
    ("REEVAL_CLINIQUE", "Réévaluation clinique"),
    ("REEVAL_RESP", "Réévaluation respiratoire"),
    ("REEVAL_VENTIL", "Réévaluation ventilatoire"),
    ("REEVAL_SEDATION", "Réévaluation sédation"),
    ("REEVAL_PERF", "Réévaluation perfusion"),
    ("REEVAL_PRESSION", "Réévaluation pression"),
    ("SURV_GLYCEMIE", "Surveillance glycémique"),
    ("PANSEMENT", "Pansement"),
    ("SOINS_BOUCHE", "Soins de bouche"),
    ("PREV_ESCARRES", "Prévention et soins d'escarres"),
    ("MOBILISATION", "Mobilisation au fauteuil"),
    ("KINE", "Kinésithérapie"),
    ("BILAN_SEJOUR", "Bilan de séjour"),
]

# demonstration staff, from the design (Bruno Azerty is the logged-in user of the mock-ups)
PRACTITIONERS = [
    ("Azerty", "Bruno", "Médecin"),
    ("Armand", "Simon", "Médecin"),
    ("Raoult", "Benoit", "Médecin"),
    ("Merveille", "Alice", "Infirmière"),
    ("Meurice", "Guillaume", "Infirmier"),
    ("Jeuneve", "Letitia", "Infirmière"),
]

location = sa.table("location", sa.column("code", sa.String), sa.column("name", sa.String))
activity_definition = sa.table(
    "activity_definition", sa.column("code", sa.String), sa.column("name", sa.String)
)
person = sa.table(
    "person",
    sa.column("id", sa.BigInteger),
    sa.column("name_family", sa.String),
    sa.column("name_given", sa.String),
)
practitioner = sa.table(
    "practitioner",
    sa.column("person_id", sa.BigInteger),
    sa.column("profession", sa.String),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(location, LOCATIONS)
    op.bulk_insert(activity_definition, [{"code": c, "name": n} for c, n in CARE_TYPES])

    bind = op.get_bind()
    for family, given, profession in PRACTITIONERS:
        result = bind.execute(person.insert().values(name_family=family, name_given=given))
        bind.execute(practitioner.insert().values(person_id=result.lastrowid, profession=profession))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    for family, given, _ in PRACTITIONERS:
        # only the persons who are practitioners: a patient may have the same name
        person_ids = (
            sa.select(person.c.id)
            .join(practitioner, practitioner.c.person_id == person.c.id)
            .where(person.c.name_family == family, person.c.name_given == given)
        )
        ids = [row[0] for row in bind.execute(person_ids)]
        if ids:
            bind.execute(practitioner.delete().where(practitioner.c.person_id.in_(ids)))
            bind.execute(person.delete().where(person.c.id.in_(ids)))
    op.execute(activity_definition.delete().where(
        activity_definition.c.code.in_([c for c, _ in CARE_TYPES])
    ))
    op.execute(location.delete().where(location.c.code.in_([l["code"] for l in LOCATIONS])))
