"""Define patient creation, full-replacement update, and output schemas.

`PatientCreate` and `PatientOut` flatten the phone number (`contact`) and
allergy list (`allergies`) onto the top-level patient payload while mapping
to `Person.telecom` and `Pathology` in the ORM layer.
"""
from pydantic import BaseModel, ConfigDict, Field

from app.models.patient import IdentificationStatus
from app.schemas.Allergy import AllergyName, AllergyOut
from app.schemas.Person import PersonCreate, PersonOut


class PatientCreate(BaseModel):
    person: PersonCreate
    ipp: str | None = Field(
        default=None, min_length=1, max_length=32
    )  # same length as the column
    allergies: list[
        AllergyName
    ] = []  # the ones known at admission, more can be added later
    # UNKNOWN for a "Patient sous X" (anonymous): names are then optional
    identification_status: IdentificationStatus = IdentificationStatus.PROVISIONAL
    contact: str | None = Field(default=None, max_length=128)  # phone number
    personal_info: str | None = None  # history, context, particularities


class PatientUpdate(PatientCreate):
    """Replace the entire patient record and remove any allergies omitted from `allergies`."""


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ipp: str | None
    identification_status: IdentificationStatus
    active: bool
    person: PersonOut
    allergies: list[AllergyOut]
    contact: str | None
    personal_info: str | None
