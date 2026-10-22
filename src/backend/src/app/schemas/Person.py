import datetime

from pydantic import BaseModel, ConfigDict, Field

# field names must match the attributes of models.person.Person,
# since the service builds the ORM object with Person(**data.model_dump())

class PersonCreate(BaseModel):
  # everything is optional: an emergency patient can be unidentified
  name_family : str | None = Field(default=None, min_length=1, max_length=128)
  name_given : str | None = Field(default=None, min_length=1, max_length=128)
  birth_date : datetime.date | None = None

class PersonOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id : int
  name_family : str | None
  name_given : str | None
  birth_date : datetime.date | None
