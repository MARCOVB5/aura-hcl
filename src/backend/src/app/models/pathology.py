from __future__ import annotations

from typing import TYPE_CHECKING
from app.models import Base
from app.models.common import ID, enum_values

from sqlalchemy import String, Enum, ForeignKey, Text, text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

import enum

if TYPE_CHECKING:
  from app.models.patient import Patient

'''
Enumeration / DataType classes for the Pathology group
'''

class AllergyCategory(enum.Enum):
  FOOD = "food"
  MEDICATION = "medication"
  ENVIRONMENT = "environment"
  BIOLOGIC = "biologic"

# pathology_type.code of the allergies, the row is inserted at startup (app/db/seed.py)
ALLERGY_TYPE_CODE = "ALLERGY"

class PathologyType(Base):
  __tablename__ = "pathology_type"

  code : Mapped[str] = mapped_column(String(32), primary_key=True)
  label : Mapped[str] = mapped_column(String(128))

class Allergen(Base):
  __tablename__ = "allergen"

  id : Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
  code : Mapped[str] = mapped_column(String(32), unique = True)
  name : Mapped[str] = mapped_column(String(255))
  category : Mapped[AllergyCategory | None] = mapped_column(
    Enum(AllergyCategory, values_callable=enum_values)
  )

class Pathology(Base):
  __tablename__ = "pathology"

  id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True )
  patient_id : Mapped[int] = mapped_column(ID, ForeignKey("patient.id"))
  pathology_type_code : Mapped[str] = mapped_column(String(32), ForeignKey("pathology_type.code"))
  allergen_id : Mapped[int | None] = mapped_column(ID, ForeignKey("allergen.id"))
  name : Mapped[str | None] = mapped_column(String(255))
  active : Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
  note : Mapped[str|None] = mapped_column(Text)

  # associations
  patient : Mapped[Patient] = relationship(back_populates = "pathologies") # idk

  type : Mapped[PathologyType] = relationship() # manytoone

  allergen : Mapped[Allergen | None] = relationship() # many to one
