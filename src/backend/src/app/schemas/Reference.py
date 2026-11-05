from pydantic import BaseModel, ConfigDict

from app.schemas.Person import PersonOut

# reference list shown in the forms: caregivers


class PractitionerOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  profession: str | None
  person: PersonOut
