from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# an allergy is free text for now, the allergen catalogue comes later.
# surrounding spaces are removed before the length checks, so "   " is rejected
AllergyName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)] # same length as pathology.name

class AllergiesCreate(BaseModel):
  allergies : list[AllergyName] = Field(min_length=1)

class AllergyOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  # the id lets the frontend point at one allergy later (e.g. to deactivate it)
  id : int
  name : str | None
