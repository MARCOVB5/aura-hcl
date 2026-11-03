from typing import Annotated

import jwt
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.security import decode_user_id
from app.services.auth_service import AuthService, unauthorized

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


# Bearer authentication shared by all application routes.


def get_auth_service(db: DBSession) -> AuthService:
    return AuthService(db, UserDAO(db))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise unauthorized()
    try:
        user_id = decode_user_id(credentials.credentials)
    except jwt.InvalidTokenError:
        raise unauthorized()
    user = UserDAO(db).get(user_id)
    if user is None or not user.practitioner.active:
        raise unauthorized()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
