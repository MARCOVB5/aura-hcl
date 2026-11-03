"""practitioner user accounts

Revision ID: a82f964b1d30
Revises: 7b01cabb0a1f
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "a82f964b1d30"
down_revision = "7b01cabb0a1f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("practitioner_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.ForeignKeyConstraint(["practitioner_id"], ["practitioner.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("practitioner_id"),
    )


def downgrade() -> None:
    op.drop_table("app_user")
