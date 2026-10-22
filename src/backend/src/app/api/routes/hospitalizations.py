from fastapi import APIRouter, status

from app.deps import HospitalizationManagementServiceDep
from app.schemas.Hospitalization import HospitalizationCreate, HospitalizationOut


router = APIRouter(prefix="/api/hospitalizations", tags=["hospitalizations"])


@router.post("", response_model=HospitalizationOut, status_code=status.HTTP_201_CREATED)
def create_hospitalization(
    data: HospitalizationCreate,
    service: HospitalizationManagementServiceDep,
):
    return service.create_hospitalization(data)
