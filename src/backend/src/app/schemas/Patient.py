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
    """Replaces the whole patient record: allergies missing from the list are removed"""


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
