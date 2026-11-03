from pydantic import BaseModel, ConfigDict

from app.schemas.Person import PersonOut

# reference lists shown in the forms: rooms, care types, caregivers


class LocationOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  code: str
  name: str


class CareTypeOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  code: str
  name: str


class PractitionerOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  profession: str | None
  person: PersonOut
