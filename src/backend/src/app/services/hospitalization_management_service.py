from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dao.appointment_dao import AppointmentDAO
from app.dao.encounter_dao import EncounterDAO
from app.dao.hospitalization_dao import HospitalizationDAO
from app.dao.patient_dao import PatientDAO
from app.dao.reference_dao import ReferenceDAO
from app.errors import AppError, Conflict, NotFound
from app.models.encounter import Encounter
from app.models.hospitalization import Hospitalization
from app.models.location import Location
from app.schemas.Encounter import EncounterUpdate
from app.schemas.Hospitalization import HospitalizationCreate


class HospitalizationManagementService:

  def __init__(
    self,
    session: Session,
    patients: PatientDAO,
    encounters: EncounterDAO,
    hospitalizations: HospitalizationDAO,
    references: ReferenceDAO,
    appointments: AppointmentDAO,
  ):
    self.session = session
    self.patients = patients
    self.encounters = encounters
    self.hospitalizations = hospitalizations
    self.references = references
    self.appointments = appointments

  def _get_location(self, location_id: int | None) -> Location | None:
    if location_id is None:
      return None
    location = self.references.get_location(location_id)
    if location is None:
      raise NotFound("Location not found")
    return location

  def create_hospitalization(self, data: HospitalizationCreate) -> Hospitalization:
    patient = self.patients.get(data.encounter.patient_id)
    if patient is None:
      raise NotFound("Patient not found")
    self._get_location(data.encounter.current_location_id)

    try:
      encounter = self.encounters.create(Encounter(
        patient=patient,
        **data.encounter.model_dump(exclude={"patient_id"}),
      ))
      hospitalization = self.hospitalizations.create(Hospitalization(
        encounter=encounter,
      ))
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      if self.encounters.get_by_stay_number(data.encounter.stay_number):
        raise Conflict("Stay number already registered")
      raise
    except Exception:
      self.session.rollback()
      raise

    return hospitalization

  def list_hospitalizations(self, limit: int) -> list[Hospitalization]:
    return self.hospitalizations.list_all(limit)

  def get_hospitalization(self, encounter_id: int) -> Hospitalization:
    hospitalization = self.hospitalizations.get(encounter_id)
    if hospitalization is None:
      raise NotFound("Hospitalization not found")
    return hospitalization

  def get_hospitalization_by_patient(self, patient_id: int) -> list[Hospitalization]:
    if self.patients.get(patient_id) is None:
      raise NotFound("Patient not found")
    return self.hospitalizations.get_by_patient(patient_id)

  def get_current_hospitalization(self, patient_id: int) -> Hospitalization:
    """The stay in progress, to which new care appointments are attached"""
    if self.patients.get(patient_id) is None:
      raise NotFound("Patient not found")
    encounter = self.encounters.get_current(patient_id, datetime.now())
    if encounter is None:
      raise NotFound("No current stay")
    return self.get_hospitalization(encounter.id)

  def update_hospitalization(self, encounter_id: int, data: EncounterUpdate) -> Hospitalization:
    hospitalization = self.get_hospitalization(encounter_id)
    encounter = hospitalization.encounter
    changes = data.model_dump(exclude_unset=True)

    # these are required columns: null would mean "no change", so it is refused
    for required in ("stay_number", "status", "encounter_type_code", "admission_date"):
      if required in changes and changes[required] is None:
        raise AppError(f"{required} cannot be empty")
    # assign the location object, not only its id: the loaded `current_location` would stay stale
    if "current_location_id" in changes:
      encounter.current_location = self._get_location(changes.pop("current_location_id"))

    for field, value in changes.items():
      setattr(encounter, field, value)
    for end in (encounter.expected_discharge_date, encounter.actual_discharge_date):
      if end is not None and end < encounter.admission_date:
        raise AppError("Discharge date before admission date")

    try:
      self.session.commit()
    except IntegrityError:
      self.session.rollback()
      raise Conflict("Stay number already registered")
    return self.get_hospitalization(encounter_id)

  def delete_hospitalization(self, encounter_id: int) -> None:
    hospitalization = self.get_hospitalization(encounter_id)
    # deleting the stay would leave its care appointments without a stay
    if self.appointments.exists_for_encounter(encounter_id):
      raise Conflict("Stay has care appointments")
    self.encounters.delete(hospitalization.encounter)
    self.session.commit()
