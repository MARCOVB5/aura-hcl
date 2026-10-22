from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.dao.encounter_dao import EncounterDAO
from app.dao.hospitalization_dao import HospitalizationDAO
from app.dao.patient_dao import PatientDAO
from app.db import get_db
from app.services.hospitalization_management_service import HospitalizationManagementService
from app.services.patient_management_service import PatientManagementService

DBSession = Annotated[Session, Depends(get_db)]


def get_patient_service(db: DBSession) -> PatientManagementService:
    return PatientManagementService(db, PatientDAO(db))


PatientManagementServiceDep = Annotated[
    PatientManagementService, Depends(get_patient_service)
]


def get_hospitalization_service(db: DBSession) -> HospitalizationManagementService:
    return HospitalizationManagementService(
        db,
        PatientDAO(db),
        EncounterDAO(db),
        HospitalizationDAO(db),
    )


HospitalizationManagementServiceDep = Annotated[
    HospitalizationManagementService, Depends(get_hospitalization_service)
]
