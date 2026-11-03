from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.encounter import EncounterStatus, EncounterTypeCode
from app.schemas.Patient import PatientOut
from app.schemas.Reference import LocationOut


class EncounterCreate(BaseModel):
  model_config = ConfigDict(extra="forbid")

  patient_id: int
  stay_number: str = Field(min_length=1, max_length=32)
  status: EncounterStatus
  encounter_type_code: EncounterTypeCode = EncounterTypeCode.INPATIENT
  admission_date: datetime
  expected_discharge_date: datetime | None = None
  reason: str | None = Field(default=None, max_length=255)
  current_location_id: int | None = None  # first location (room and bed)


class EncounterUpdate(BaseModel):
  """Only the fields that are sent are changed (send null to clear an optional field)"""
  model_config = ConfigDict(extra="forbid")

  stay_number: str | None = Field(default=None, min_length=1, max_length=32)
  status: EncounterStatus | None = None
  encounter_type_code: EncounterTypeCode | None = None
  admission_date: datetime | None = None
  expected_discharge_date: datetime | None = None
  actual_discharge_date: datetime | None = None
  reason: str | None = Field(default=None, max_length=255)
  current_location_id: int | None = None


class EncounterSummaryOut(BaseModel):
  """A stay without its patient, e.g. inside a care appointment"""
  model_config = ConfigDict(from_attributes=True)

  id: int
  stay_number: str
  status: EncounterStatus
  admission_date: datetime
  expected_discharge_date: datetime | None
  actual_discharge_date: datetime | None
  current_location: LocationOut | None


class EncounterOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  stay_number: str
  patient_id: int
  patient: PatientOut
  status: EncounterStatus
  encounter_type_code: EncounterTypeCode
  admission_date: datetime
  expected_discharge_date: datetime | None
  actual_discharge_date: datetime | None
  reason: str | None
  current_location_id: int | None
  current_location: LocationOut | None
  service_provider_id: int | None
