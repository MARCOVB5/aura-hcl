from fastapi import APIRouter, Query, status

from app.deps import PatientManagementServiceDep
from app.schemas.Allergy import AllergiesCreate, AllergyOut
from app.schemas.Patient import PatientCreate, PatientOut

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
