"""Provide database queries and persistence for `Patient` entities."""
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.models.patient import Patient
from app.models.person import Person

# person (with the phone numbers) and allergies are always shown with a patient
PATIENT_OPTIONS = (
  selectinload(Patient.person).selectinload(Person.telecom),
  selectinload(Patient.allergies),
)


class PatientDAO:
  """Execute `Patient` queries with eager-loaded demographics and flush-only writes.

  `get` performs a lightweight primary-key lookup, whereas `get_detailed` and
  `list_all` eager-load `person.telecom` and `allergies` via `PATIENT_OPTIONS`.
  """

  def __init__(self, session : Session):
    self.session = session

  def get(self, id : int) -> Patient | None:
    return self.session.get(Patient, id)

  def get_detailed(self, id : int) -> Patient | None:
    stmt = select(Patient).options(*PATIENT_OPTIONS).where(Patient.id == id)
    return self.session.scalar(stmt)

  def list_all(self, limit : int = 100) -> list[Patient]:
    stmt = (select(Patient)
      # one query per relationship for the whole page, instead of one per patient
      .options(*PATIENT_OPTIONS)
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
