from fastapi import APIRouter, Query, Response, status

from app.deps import HospitalizationManagementServiceDep
from app.schemas.Encounter import EncounterUpdate
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


# only the fields that are sent are changed
@router.patch("/{encounter_id}", response_model=HospitalizationOut)
def update_hospitalization(
    encounter_id: int,
    data: EncounterUpdate,
    service: HospitalizationManagementServiceDep,
):
    return service.update_hospitalization(encounter_id, data)


# 409 "Stay has care appointments" if care is attached to the stay
@router.delete("/{encounter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hospitalization(
    encounter_id: int,
    service: HospitalizationManagementServiceDep,
):
    service.delete_hospitalization(encounter_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
