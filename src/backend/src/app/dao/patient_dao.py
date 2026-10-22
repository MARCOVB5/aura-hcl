from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.models.patient import Patient


class PatientDAO:

  def __init__(self, session : Session):
    self.session = session

  def get(self, id : int) -> Patient | None:
    return self.session.get(Patient, id)

  def list_all(self, limit : int = 100) -> list[Patient]:
    stmt = (select(Patient)
      # one query per relationship for the whole page, instead of one per patient
      .options(selectinload(Patient.person), selectinload(Patient.allergies))
      .order_by(Patient.person_id).limit(limit)
    )

    return list(self.session.scalars(stmt))

  def get_by_ipp(self, ipp : str ) -> Patient | None:
    stmt = select(Patient).where(Patient.ipp == ipp)
    return self.session.scalar(stmt)

  def create(self, patient: Patient) -> Patient:
    self.session.add(patient)
    self.session.flush()

    return patient
