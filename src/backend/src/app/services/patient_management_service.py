"""Manage patient records, contact phone numbers, and allergy lists."""
from app.errors import Conflict, NotFound
from app.models.patient import Patient
from app.models.pathology import ALLERGY_TYPE_CODE, Pathology
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dao.patient_dao import PatientDAO
from app.schemas.Patient import PatientCreate, PatientUpdate
from app.models.person import ContactPoint, ContactPointSystem, Person


def _set_contact(person: Person, phone: str | None) -> None:
  # the UI has a single "Contact" field: it is the person's phone number
  person.telecom = [t for t in person.telecom if t.system != ContactPointSystem.PHONE]
  if phone and phone.strip():
    person.telecom.append(ContactPoint(system=ContactPointSystem.PHONE, value=phone.strip()))


def _add_allergies(patient: Patient, names: list[str]) -> None:
  # an allergy that is already recorded (same text, case ignored) is not added twice
  known = {a.name.casefold() for a in patient.allergies if a.name is not None}
  for name in names:
    if name.casefold() in known:
      continue
    known.add(name.casefold())
    # through `pathologies`: `allergies` is read-only and would silently drop it
    patient.pathologies.append(Pathology(pathology_type_code=ALLERGY_TYPE_CODE, name=name))


def build_patient(data: PatientCreate) -> Patient:
  patient = Patient(
    person=Person(**data.person.model_dump()),
    ipp=data.ipp,
    identification_status=data.identification_status,
    personal_info=data.personal_info,
  )
  _set_contact(patient.person, data.contact)
  _add_allergies(patient, data.allergies)
  return patient


class PatientManagementService:
  """Coordinate patient creation, retrieval, updates, and allergy management."""

  def __init__(self, session: Session, patients : PatientDAO) :
    self.session = session
    self.dao = patients

  def create_patient(self, data : PatientCreate) -> Patient:
    """Create and commit a new patient record with its person, phone, and allergies.

    Args:
      data (PatientCreate): Validated patient creation payload.

    Returns:
      Patient: Persisted `Patient` with its `allergies` view refreshed.

    Raises:
      Conflict: If `data.ipp` is already assigned to another patient.
      IntegrityError: If an unrelated database constraint fails.
    """
    # what happens in the case that we don't know the patient's IPP and it turns out that he already had a account with an IPP defined but we already created a new one??
    patient = build_patient(data)

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
    """Add new allergies to an existing patient without duplicating existing entries.

    Args:
      patient_id (int): Primary key of the target patient.
      names (list[str]): Free-text allergy names to append.

    Returns:
      list[Pathology]: Complete list of the patient's allergy rows after commit.

    Raises:
      NotFound: If no patient exists with `patient_id`.
    """
    patient = self.dao.get(patient_id)
    if patient is None:
      raise NotFound("Patient not found")

    _add_allergies(patient, names)
    self.session.commit()

    # same as in create_patient: reload the list so it includes the new rows
    self.session.refresh(patient, ["allergies"])
    return patient.allergies

  def list_patients(self, limit: int) -> list[Patient]:
    return self.dao.list_all(limit)

  def get_patient(self, patient_id: int) -> Patient:
    patient = self.dao.get_detailed(patient_id)
    if patient is None:
      raise NotFound("Patient not found")
    return patient

  def update_patient(self, patient_id: int, data: PatientUpdate) -> Patient:
    """Replace a patient's demographics, identifiers, phone, and allergy list.

    Omitted allergies are removed from `patient.pathologies` while existing
    matching allergy rows and non-allergy pathologies are preserved.

    Args:
      patient_id (int): Primary key of the patient to update.
      data (PatientUpdate): Full replacement payload for the patient record.

    Returns:
      Patient: Updated `Patient` with its `allergies` collection refreshed.

    Raises:
      NotFound: If no patient exists with `patient_id`.
      Conflict: If `data.ipp` belongs to a different patient.
    """
    patient = self.get_patient(patient_id)
    if data.ipp is not None:
      owner = self.dao.get_by_ipp(data.ipp)
      if owner is not None and owner.id != patient.id:
        raise Conflict("IPP already registered")

    for field, value in data.person.model_dump().items():
      setattr(patient.person, field, value)
    patient.ipp = data.ipp
    patient.identification_status = data.identification_status
    patient.personal_info = data.personal_info
    _set_contact(patient.person, data.contact)

    # allergies: the list replaces the recorded one (case ignored, existing rows are kept)
    wanted = {name.casefold() for name in data.allergies}
    for pathology in list(patient.pathologies):
      if pathology.pathology_type_code == ALLERGY_TYPE_CODE and (pathology.name or "").casefold() not in wanted:
        patient.pathologies.remove(pathology)
    kept = {
      (p.name or "").casefold() for p in patient.pathologies if p.pathology_type_code == ALLERGY_TYPE_CODE
    }
    for name in data.allergies:
      if name.casefold() not in kept:
        kept.add(name.casefold())
        patient.pathologies.append(Pathology(pathology_type_code=ALLERGY_TYPE_CODE, name=name))

    try:
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      raise Conflict("IPP already registered")

    # `allergies` is view-only: reload it so it matches the new rows
    self.session.refresh(patient, ["allergies"])
    return patient
