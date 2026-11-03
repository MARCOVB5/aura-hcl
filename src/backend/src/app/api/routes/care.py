import datetime

from fastapi import APIRouter, Query, status

from app.deps import CareManagementServiceDep
from app.schemas.Care import AppointmentCreate, AppointmentOut, AppointmentUpdate
from app.schemas.Reference import CareTypeOut, PractitionerOut

router = APIRouter(prefix="/api", tags=["care"])


@router.get("/care-types", response_model=list[CareTypeOut])
def list_care_types(service: CareManagementServiceDep):
  return service.list_care_types()


@router.get("/practitioners", response_model=list[PractitionerOut])
def list_practitioners(service: CareManagementServiceDep):
  return service.list_practitioners()


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
  service: CareManagementServiceDep,
  start: datetime.date | None = Query(None, description="first day, included"),
  end: datetime.date | None = Query(None, description="last day, included"),
  patient_id: int | None = None,
):
  return service.list_appointments(start, end, patient_id)


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, service: CareManagementServiceDep):
  return service.get_appointment(appointment_id)


# the patient's current stay is attached; 409 "No current stay" if they have none
@router.post("/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(data: AppointmentCreate, service: CareManagementServiceDep):
  return service.create_appointment(data)


@router.put("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
  appointment_id: int,
  data: AppointmentUpdate,
  service: CareManagementServiceDep,
):
  return service.update_appointment(appointment_id, data)
