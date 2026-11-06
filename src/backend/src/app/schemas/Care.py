"""Define care appointment creation, update, and output schemas."""
import datetime

from typing import Annotated

from pydantic import BaseModel, ConfigDict, NaiveDatetime, StringConstraints, model_validator

from app.models.care import AppointmentStatus, TimeConstraint
from app.schemas.Encounter import EncounterSummaryOut
from app.schemas.Patient import PatientOut
from app.schemas.Reference import PractitionerOut


class AppointmentUpdate(BaseModel):
  """Validate editable care appointment fields and enforce `STRONG`/`WEAK` time-window rules."""

  model_config = ConfigDict(extra="forbid")

  # the kind of care, typed freely (e.g. "Prise de sang"); spaces around are removed
  care_type: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
  prescribed_on: datetime.date
  time_constraint: TimeConstraint
  # local times, like the database: a date with a time zone is refused (422)
  # STRONG: the precise time. WEAK: the start of the time window
  scheduled_start: NaiveDatetime
  # WEAK only: the end of the time window
  scheduled_end: NaiveDatetime | None = None
  performer_ids: list[int] = []  # caregivers in charge
  validated_by_id: int | None = None  # caregiver who validated the prescription
  note: str | None = None
  status: AppointmentStatus = AppointmentStatus.PLANNED

  @model_validator(mode="after")
  def check_time_window(self):
    if self.time_constraint == TimeConstraint.STRONG and self.scheduled_end is not None:
      raise ValueError("a STRONG constraint has a precise time: scheduled_end must be empty")
    if self.time_constraint == TimeConstraint.WEAK:
      if self.scheduled_end is None:
        raise ValueError("a WEAK constraint needs a time window: scheduled_end is required")
      if self.scheduled_end <= self.scheduled_start:
        raise ValueError("scheduled_end must be after scheduled_start")
    return self


class AppointmentCreate(AppointmentUpdate):
  """Extend `AppointmentUpdate` with `patient_id` while resolving the active stay automatically."""

  # the patient's current stay is attached automatically
  patient_id: int


class AppointmentOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  patient: PatientOut
  encounter: EncounterSummaryOut
  care_type: str
  prescribed_on: datetime.date
  time_constraint: TimeConstraint
  scheduled_start: datetime.datetime
  scheduled_end: datetime.datetime | None
  performers: list[PractitionerOut]
  validated_by: PractitionerOut | None
  note: str | None
  status: AppointmentStatus
