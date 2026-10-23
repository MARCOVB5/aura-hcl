import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.person import AdministrativeGender

# field names must match the attributes of models.person.Person,
# since the service builds the ORM object with Person(**data.model_dump())


class PersonCreate(BaseModel):
    # everything is optional: an emergency patient can be unidentified
    name_family: str | None = Field(default=None, min_length=1, max_length=128)
    name_given: str | None = Field(default=None, min_length=1, max_length=128)
    birth_date: datetime.date | None = None
    gender: AdministrativeGender = Field(default=AdministrativeGender.UNKNOWN)
    address_line: str | None = Field(default=None)


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_family: str | None
    name_given: str | None
    birth_date: datetime.date | None
    gender: AdministrativeGender = Field(default=AdministrativeGender.UNKNOWN)
    address_line: str | None = Field(default=None)

    # persons created before the gender column was filled have NULL in the database
    @field_validator("gender", mode="before")
    @classmethod
    def null_gender_is_unknown(cls, value):
        return AdministrativeGender.UNKNOWN if value is None else value
