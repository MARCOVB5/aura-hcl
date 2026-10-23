from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.encounter import Encounter
from app.models.hospitalization import Hospitalization
from app.models.patient import Patient


_DETAIL_OPTIONS = (
  selectinload(Hospitalization.encounter)
    .selectinload(Encounter.patient)
    .options(selectinload(Patient.person), selectinload(Patient.allergies)),
)


class HospitalizationDAO:

  def __init__(self, session: Session):
    self.session = session

  def get(self, encounter_id: int) -> Hospitalization | None:
    stmt = (
      select(Hospitalization)
      .options(*_DETAIL_OPTIONS)
      .where(Hospitalization.encounter_id == encounter_id)
    )
    return self.session.scalar(stmt)

  def get_by_patient(self, patient_id: int) -> list[Hospitalization]:
    stmt = (
      select(Hospitalization)
      .join(Hospitalization.encounter)
      .options(*_DETAIL_OPTIONS)
      .where(Encounter.patient_id == patient_id)
      .order_by(Hospitalization.encounter_id)
    )
    return list(self.session.scalars(stmt))

  def list_all(self, limit: int) -> list[Hospitalization]:
    stmt = (
      select(Hospitalization)
      .options(*_DETAIL_OPTIONS)
      .order_by(Hospitalization.encounter_id)
      .limit(limit)
    )
    return list(self.session.scalars(stmt))

  def create(self, hospitalization: Hospitalization) -> Hospitalization:
    self.session.add(hospitalization)
    self.session.flush()
    return hospitalization
