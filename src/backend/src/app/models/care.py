"""Define care appointment models, time constraints, and performer associations.

`Appointment` represents a scheduled care action attached to a `Patient` and the
active `Encounter` at planning time. Caregivers are linked in two distinct roles:
`validated_by` (the single `Practitioner` who validated the prescription) and
`performers` (many-to-many via `appointment_performer`, ordered by
`Practitioner.id`). `TimeConstraint` distinguishes single-timestamp care
(`STRONG`, using `scheduled_start` only) from interval care (`WEAK`, spanning
`scheduled_start` to `scheduled_end`).
"""
from __future__ import annotations

import datetime
import enum
from typing import TYPE_CHECKING

from app.models import Base
from app.models.common import ID, enum_values

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
  from app.models.encounter import Encounter
  from app.models.patient import Patient
  from app.models.practitioner import Practitioner

class TimeConstraint(enum.Enum):
  WEAK = "WEAK"     # to do within a time window: scheduled_start -> scheduled_end
  STRONG = "STRONG" # to do at a precise time: scheduled_start


class AppointmentStatus(enum.Enum):
  PLANNED = "PLANNED"
  DONE = "DONE"
  CANCELLED = "CANCELLED"


# the caregivers in charge of a care appointment (0..*)
appointment_performer = Table(
  "appointment_performer",
  Base.metadata,
  Column("appointment_id", ID, ForeignKey("appointment.id", ondelete="CASCADE"), primary_key=True),
  Column("practitioner_id", ID, ForeignKey("practitioner.id"), primary_key=True),
)


class Appointment(Base):
  __tablename__ = "appointment"

  id : Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
  patient_id : Mapped[int] = mapped_column(ID, ForeignKey("patient.id"))
  # a care is always attached to the stay that was in progress when it was planned
  encounter_id : Mapped[int] = mapped_column(ID, ForeignKey("encounter.id"))
  # the kind of care, typed freely (e.g. "Prise de sang")
  care_type : Mapped[str] = mapped_column(String(255))
  prescribed_on : Mapped[datetime.date] = mapped_column(Date)
  time_constraint : Mapped[TimeConstraint] = mapped_column(Enum(TimeConstraint, values_callable=enum_values))
  scheduled_start : Mapped[datetime.datetime] = mapped_column(DateTime)
  scheduled_end : Mapped[datetime.datetime | None] = mapped_column(DateTime) # only for a WEAK constraint
  # the caregiver who validated the prescription (Prescrit par)
  validated_by_id : Mapped[int | None] = mapped_column(ID, ForeignKey("practitioner.id"))
  note : Mapped[str | None] = mapped_column(Text)
  status : Mapped[AppointmentStatus] = mapped_column(
    Enum(AppointmentStatus, values_callable=enum_values),
    default=AppointmentStatus.PLANNED,
    server_default="PLANNED",
  )

  patient : Mapped[Patient] = relationship()
  encounter : Mapped[Encounter] = relationship()
  validated_by : Mapped[Practitioner | None] = relationship()
  performers : Mapped[list[Practitioner]] = relationship(
    secondary=appointment_performer,
    order_by="Practitioner.id",
  )
