from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.hospitalization import AdmissionStatus
from app.schemas.Encounter import EncounterCreate, EncounterOut


class HospitalizationCreate(BaseModel):
  encounter: EncounterCreate


class HospitalizationOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  encounter_id: int
  encounter: EncounterOut
  admission_status: AdmissionStatus
  assessment_completed_at: datetime | None
