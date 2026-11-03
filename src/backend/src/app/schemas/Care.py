import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.care import AppointmentStatus, TimeConstraint
from app.schemas.Encounter import EncounterSummaryOut
from app.schemas.Patient import PatientOut
from app.schemas.Reference import CareTypeOut, PractitionerOut


class AppointmentUpdate(BaseModel):
  model_config = ConfigDict(extra="forbid")

  activity_definition_id: int
  prescribed_on: datetime.date
  time_constraint: TimeConstraint
  # STRONG: the precise time. WEAK: the start of the time window
  scheduled_start: datetime.datetime
  # WEAK only: the end of the time window
  scheduled_end: datetime.datetime | None = None
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
  # the patient's current stay is attached automatically
  patient_id: int


class AppointmentOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  patient: PatientOut
  encounter: EncounterSummaryOut
  activity_definition: CareTypeOut
  prescribed_on: datetime.date
  time_constraint: TimeConstraint
  scheduled_start: datetime.datetime
  scheduled_end: datetime.datetime | None
  performers: list[PractitionerOut]
  validated_by: PractitionerOut | None
  note: str | None
  status: AppointmentStatus
