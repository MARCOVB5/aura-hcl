from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.encounter import EncounterStatus, EncounterTypeCode
from app.schemas.Patient import PatientCreate, PatientOut


class EncounterCreate(BaseModel):
  patient: PatientCreate
  stay_number: str = Field(min_length=1, max_length=32)
  status: EncounterStatus
  encounter_type_code: EncounterTypeCode = EncounterTypeCode.INPATIENT
  admission_date: datetime
  expected_discharge_date: datetime | None = None
  reason: str | None = Field(default=None, max_length=255)


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
  service_provider_id: int | None
