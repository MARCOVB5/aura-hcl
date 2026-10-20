from __future__ import annotations

from typing import TYPE_CHECKING
from app.models import Base
from app.models.common import ID, enum_values

from sqlalchemy import String, Enum, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

import enum

if TYPE_CHECKING:
  from app.models.person import Person
  from app.models.pathology import Pathology, Allergen

'''
Enumeration / DataType classes for the Patient & Stay group
'''

class IdentificationStatus(enum.Enum):
  IDENTIFIED = "IDENTIFIED"
  PROVISIONAL = "PROVISIONAL"
  UNKNOWN = "UNKNOWN"

class Patient(Base):
  __tablename__ = "patient"
  __table_args__ = (UniqueConstraint("ipp", name="uq_patient_ipp"),)

  id : Mapped[int] = mapped_column(ID, primary_key = True, autoincrement=True)
  ipp : Mapped[str | None] = mapped_column(String(32)) # ig it works for now but actual length to see. (*maybe atmost 10)
  person_id : Mapped[int] = mapped_column(ID, ForeignKey("person.id"))
  identificationStatus : Mapped[IdentificationStatus] = mapped_column(Enum(IdentificationStatus, values_callable = enum_values),default = IdentificationStatus.PROVISIONAL) # check if provisional is better to define by default
  active : Mapped[bool] = mapped_column(Boolean, default = True) #????

  ## Asociations
  person : Mapped[Person] = relationship()
  # Patient --- Pathology
  pathologies : Mapped[list[Pathology]] = relationship(
    back_populates= "patient",
    cascade="all, delete-orphan"
  )

  allergies : Mapped[list[Pathology]] = relationship(
    primaryjoin = "and_(Pathology.patient_id == Patient.id, "
    "Pathology.pathology_type_code == 'ALLERGY')",
    viewonly=True,
  )

  @property
  def allergens(self) ->list[Allergen]:
    return [p.allergen for p in self.allergies if p.allergen is not None]
