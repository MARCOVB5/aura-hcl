from fastapi import APIRouter, Query, status

from app.deps import HospitalizationManagementServiceDep, PatientManagementServiceDep
from app.schemas.Allergy import AllergiesCreate, AllergyOut
from app.schemas.Hospitalization import HospitalizationOut
from app.schemas.Patient import PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/api/patients", tags =["patients"])

@router.get("",response_model=list[PatientOut])
def list_patients(
  service : PatientManagementServiceDep,
  limit : int = Query(100, ge =1, le=200),
):
  return service.list_patients(limit)

@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
  data : PatientCreate,
  service : PatientManagementServiceDep,
):
  return service.create_patient(data)

# returns all of the patient's allergies, not only the new ones
@router.post("/{patient_id}/allergies", response_model=list[AllergyOut], status_code=status.HTTP_201_CREATED)
def add_allergies(
  patient_id : int,
  data : AllergiesCreate,
  service : PatientManagementServiceDep,
):
  return service.add_allergies(patient_id, data.allergies)


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
  patient_id : int,
  service : PatientManagementServiceDep,
):
  return service.get_patient(patient_id)

# replaces the whole record: send every field, allergies missing from the list are removed
@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(
  patient_id : int,
  data : PatientUpdate,
  service : PatientManagementServiceDep,
):
  return service.update_patient(patient_id, data)


@router.get("/{patient_id}/hospitalizations", response_model=list[HospitalizationOut])
def get_hospitalizations_by_patient(
  patient_id: int,
  service: HospitalizationManagementServiceDep,
):
  return service.get_hospitalization_by_patient(patient_id)

# the stay in progress (404 "No current stay" if there is none): care is attached to it
@router.get("/{patient_id}/current-hospitalization", response_model=HospitalizationOut)
def get_current_hospitalization(
  patient_id: int,
  service: HospitalizationManagementServiceDep,
):
  return service.get_current_hospitalization(patient_id)
