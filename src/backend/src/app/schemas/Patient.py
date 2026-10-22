from pydantic import BaseModel, ConfigDict, Field
from app.models.patient import IdentificationStatus
from app.schemas.Allergy import AllergyName, AllergyOut
from app.schemas.Person import PersonOut, PersonCreate


class PatientCreate(BaseModel):
  person : PersonCreate
  ipp : str | None = Field(default=None, min_length=1, max_length=32) # same length as the column
  allergies : list[AllergyName] = [] # the ones known at admission, more can be added later

class PatientOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id : int
  ipp : str | None
  identification_status : IdentificationStatus
  active : bool
  person: PersonOut
  allergies : list[AllergyOut]
