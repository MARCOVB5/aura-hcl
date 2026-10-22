from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.dao.patient_dao import PatientDAO
from app.services.patient_management_service import PatientManagementService

DBSession = Annotated[Session, Depends(get_db)]


def get_patient_service(db : DBSession) -> PatientManagementService:
  return PatientManagementService(db, PatientDAO(db))

PatientManagementServiceDep = Annotated[PatientManagementService, Depends(get_patient_service)]
