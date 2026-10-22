from app.errors import Conflict, NotFound
from app.models.patient import Patient
from app.models.pathology import ALLERGY_TYPE_CODE, Pathology
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dao.patient_dao import PatientDAO
from app.schemas.Patient import PatientCreate
from app.models.person import Person


"""
  This whole idea of management services is flawed because the uhh services should be
  grouped by business logic not by the entities, so uhh
  my bad.
"""
class PatientManagementService:
  def __init__(self, session: Session, patients : PatientDAO) :
    self.session = session
    self.dao = patients

  def create_patient(self, data : PatientCreate) -> Patient:
    # what happens in the case that we don't know the patient's IPP and it turns out that he already had a account with an IPP defined but we already created a new one??
    person = Person(**data.person.model_dump())
    patient = Patient(
      person = person,
      ipp = data.ipp,
    )
    self._add_allergies(patient, data.allergies)

    try:
      self.dao.create(patient)
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      if data.ipp is not None and self.dao.get_by_ipp(data.ipp):
        raise Conflict("IPP already registered")
      raise

    # patient.allergies still holds the list read before the insert (expire_on_commit=False)
    self.session.refresh(patient, ["allergies"])
    return patient

  def add_allergies(self, patient_id : int, names : list[str]) -> list[Pathology]:
    patient = self.dao.get(patient_id)
    if patient is None:
      raise NotFound("Patient not found")

    self._add_allergies(patient, names)
    self.session.commit()

    # same as in create_patient: reload the list so it includes the new rows
    self.session.refresh(patient, ["allergies"])
    return patient.allergies

  def list_patients(self, limit: int) -> list[Patient]:
    return self.dao.list_all(limit)

  def _add_allergies(self, patient : Patient, names : list[str]) -> None:
    # an allergy that is already recorded (same text, case ignored) is not added twice
    known = {a.name.casefold() for a in patient.allergies if a.name is not None}
    for name in names:
      if name.casefold() in known:
        continue
      known.add(name.casefold())
      # through `pathologies`: `allergies` is read-only and would silently drop it
      patient.pathologies.append(Pathology(pathology_type_code = ALLERGY_TYPE_CODE, name = name))
