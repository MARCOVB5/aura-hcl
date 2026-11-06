"""Define the shared SQLAlchemy declarative base and register all ORM models.

Import every model submodule below `Base` so `Base.metadata` discovers all
tables for Alembic autogeneration and resolves string-based relationship targets.
"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
  pass

from app.models import person, practitioner, patient, pathology, encounter, hospitalization, care, user
