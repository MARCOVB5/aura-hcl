from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.dao.appointment_dao import AppointmentDAO
from app.dao.encounter_dao import EncounterDAO
from app.dao.hospitalization_dao import HospitalizationDAO
from app.dao.patient_dao import PatientDAO
from app.dao.reference_dao import ReferenceDAO
from app.db import get_db
from app.services.care_management_service import CareManagementService
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
        ReferenceDAO(db),
        AppointmentDAO(db),
    )


HospitalizationManagementServiceDep = Annotated[
    HospitalizationManagementService, Depends(get_hospitalization_service)
]


def get_care_service(db: DBSession) -> CareManagementService:
    return CareManagementService(
        db,
        PatientDAO(db),
        EncounterDAO(db),
        AppointmentDAO(db),
        ReferenceDAO(db),
    )


CareManagementServiceDep = Annotated[CareManagementService, Depends(get_care_service)]
