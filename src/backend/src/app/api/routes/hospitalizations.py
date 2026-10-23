from fastapi import APIRouter, Query, status

from app.deps import HospitalizationManagementServiceDep
from app.schemas.Hospitalization import HospitalizationCreate, HospitalizationOut


router = APIRouter(prefix="/api/hospitalizations", tags=["hospitalizations"])


@router.get("", response_model=list[HospitalizationOut])
def list_hospitalizations(
    service: HospitalizationManagementServiceDep,
    limit: int = Query(100, ge=1, le=200),
):
    return service.list_hospitalizations(limit)


@router.get("/{encounter_id}", response_model=HospitalizationOut)
def get_hospitalization(
    encounter_id: int,
    service: HospitalizationManagementServiceDep,
):
    return service.get_hospitalization(encounter_id)


@router.post("", response_model=HospitalizationOut, status_code=status.HTTP_201_CREATED)
def create_hospitalization(
    data: HospitalizationCreate,
    service: HospitalizationManagementServiceDep,
):
    return service.create_hospitalization(data)
