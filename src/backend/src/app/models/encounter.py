from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.common import ID, enum_values

if TYPE_CHECKING:
  from app.models.hospitalization import Hospitalization
  from app.models.patient import Patient


class EncounterStatus(enum.Enum):
  PLANNED = "planned"
  ARRIVED = "arrived"
  TRIAGED = "triaged"
  IN_PROGRESS = "in-progress"
  ONLEAVE = "onleave"
  FINISHED = "finished"
  CANCELLED = "cancelled"
  ENTERED_IN_ERROR = "entered-in-error"
  UNKNOWN = "unknown"


class EncounterTypeCode(enum.Enum):
  INPATIENT = "INPATIENT"
  OUTPATIENT = "OUTPATIENT"
  EMERGENCY = "EMERGENCY"


class Encounter(Base):
  __tablename__ = "encounter"
  __table_args__ = (UniqueConstraint("stay_number", name="uq_encounter_stay_number"),)

  id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
  stay_number: Mapped[str] = mapped_column(String(32))
  patient_id: Mapped[int] = mapped_column(ID, ForeignKey("patient.id"))
  status: Mapped[EncounterStatus] = mapped_column(
    Enum(EncounterStatus, values_callable=enum_values)
  )
  encounter_type_code: Mapped[EncounterTypeCode] = mapped_column(
    Enum(EncounterTypeCode, values_callable=enum_values),
    default=EncounterTypeCode.INPATIENT,
    server_default="INPATIENT",
  )
  admission_date: Mapped[datetime] = mapped_column(DateTime)
  expected_discharge_date: Mapped[datetime | None] = mapped_column(DateTime)
  actual_discharge_date: Mapped[datetime | None] = mapped_column(DateTime)
  reason: Mapped[str | None] = mapped_column(String(255))
  current_location_id: Mapped[int | None] = mapped_column(ID)
  service_provider_id: Mapped[int | None] = mapped_column(ID)

  patient: Mapped[Patient] = relationship()
  hospitalization: Mapped[Hospitalization | None] = relationship(
    back_populates="encounter",
    cascade="all, delete-orphan",
  )
