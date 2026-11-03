from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.models.encounter import EncounterStatus, EncounterTypeCode
from app.schemas.Patient import PatientOut


# where the patient is, typed freely (e.g. "Chambre 12, lit A"); blank means no location
LocationText = Annotated[
  Annotated[str, StringConstraints(strip_whitespace=True, max_length=128)] | None,
  AfterValidator(lambda value: value or None),
]


class EncounterCreate(BaseModel):
  model_config = ConfigDict(extra="forbid")

  patient_id: int
  stay_number: str = Field(min_length=1, max_length=32)
  status: EncounterStatus
  encounter_type_code: EncounterTypeCode = EncounterTypeCode.INPATIENT
  admission_date: datetime
  expected_discharge_date: datetime | None = None
  reason: str | None = Field(default=None, max_length=255)
  location: LocationText = None


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
  location: LocationText = None


class EncounterSummaryOut(BaseModel):
  """A stay without its patient, e.g. inside a care appointment"""
  model_config = ConfigDict(from_attributes=True)

  id: int
  stay_number: str
  status: EncounterStatus
  admission_date: datetime
  expected_discharge_date: datetime | None
  actual_discharge_date: datetime | None
  location: str | None


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
  location: str | None
  service_provider_id: int | None
