"""care type as free text

Revision ID: 73688b2f7686
Revises: 8c73e914fc14
Create Date: 2026-11-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = '73688b2f7686'
down_revision: Union[str, Sequence[str], None] = '8c73e914fc14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# the care types seeded by 7b01cabb0a1f, put back by the downgrade
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


def _care_type_fk() -> str:
    # created without a name in eb2d51b6c7d7: MySQL named it (appointment_ibfk_N)
    for fk in sa.inspect(op.get_bind()).get_foreign_keys('appointment'):
        if fk['referred_table'] == 'activity_definition':
            return fk['name']
    raise RuntimeError("foreign key appointment -> activity_definition not found")


def upgrade() -> None:
    """Upgrade schema."""
    # the type of a care becomes free text: the name of its type is kept as that text
    op.add_column('appointment', sa.Column('care_type', sa.String(length=255), nullable=True))
    op.execute(
        "UPDATE appointment SET care_type = "
        "(SELECT name FROM activity_definition WHERE activity_definition.id = appointment.activity_definition_id)"
    )
    op.alter_column('appointment', 'care_type', existing_type=sa.String(length=255), nullable=False)
    op.drop_constraint(_care_type_fk(), 'appointment', type_='foreignkey')
    op.drop_column('appointment', 'activity_definition_id')
    op.drop_table('activity_definition')


def downgrade() -> None:
    """Downgrade schema."""
    activity_definition = op.create_table(
        'activity_definition',
        sa.Column('id', mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.bulk_insert(activity_definition, [{"code": c, "name": n} for c, n in CARE_TYPES])
    # a type typed freely becomes a row of its own
    bind = op.get_bind()
    # (MySQL compares text ignoring case: "prise de sang" is the seeded "Prise de sang")
    seeded = {name.casefold() for _, name in CARE_TYPES}
    typed = bind.execute(sa.text("SELECT DISTINCT care_type FROM appointment")).scalars()
    others = [name for name in typed if name.casefold() not in seeded]
    op.bulk_insert(activity_definition, [{"code": f"LIBRE-{i}", "name": name} for i, name in enumerate(others, 1)])

    op.add_column('appointment', sa.Column('activity_definition_id', mysql.BIGINT(unsigned=True), nullable=True))
    op.execute(
        "UPDATE appointment SET activity_definition_id = "
        "(SELECT id FROM activity_definition WHERE activity_definition.name = appointment.care_type "
        "ORDER BY id LIMIT 1)"
    )
    op.alter_column('appointment', 'activity_definition_id', existing_type=mysql.BIGINT(unsigned=True), nullable=False)
    op.create_foreign_key(None, 'appointment', 'activity_definition', ['activity_definition_id'], ['id'])
    op.drop_column('appointment', 'care_type')
